"""
Product Submissions API Routes
Handles user product photo submissions and admin review workflow
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from functools import wraps
import boto3
import uuid
import os
from PIL import Image
import io

from app import db
from models import User, Business, Product, ProductSubmission
from auth_api import require_jwt_auth

submissions_bp = Blueprint('submissions', __name__)


def login_required(f):
    """Decorator to require authentication (wraps require_jwt_auth)"""
    @wraps(f)
    @require_jwt_auth
    def decorated_function(*args, **kwargs):
        user = User.query.get(request.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return f(user, *args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @require_jwt_auth
    def decorated_function(*args, **kwargs):
        user = User.query.get(request.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(user, *args, **kwargs)
    return decorated_function


def get_s3_client():
    """Get configured S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'eu-central-1')
    )


def upload_submission_image(file_data, user_id, business_id):
    """
    Upload submission image to S3 with resizing
    Returns the S3 URL
    """
    s3 = get_s3_client()
    bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')

    # Generate unique filename
    ext = 'jpg'
    filename = f"submissions/{user_id}/{business_id}/{uuid.uuid4()}.{ext}"

    # Process image - resize to max 1200px width while maintaining aspect ratio
    img = Image.open(io.BytesIO(file_data))

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize if larger than 1200px wide
    max_width = 1200
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    buffer.seek(0)

    # Upload to S3
    s3.upload_fileobj(
        buffer,
        bucket,
        filename,
        ExtraArgs={
            'ContentType': 'image/jpeg'
        }
    )

    # Return full URL
    return f"https://{bucket}.s3.eu-central-1.amazonaws.com/{filename}"


# ==================== USER ENDPOINTS ====================

@submissions_bp.route('/api/submissions', methods=['POST'])
@login_required
def create_submission(user):
    """
    Create a new product submission
    Expects multipart form data with:
    - image: File upload
    - business_id: Store ID
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    business_id = request.form.get('business_id')
    if not business_id:
        return jsonify({'error': 'business_id is required'}), 400

    try:
        business_id = int(business_id)
    except ValueError:
        return jsonify({'error': 'Invalid business_id'}), 400

    # Verify business exists
    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    # Check file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400

    # Check file size (max 10MB)
    file_data = file.read()
    if len(file_data) > 10 * 1024 * 1024:
        return jsonify({'error': 'File too large. Maximum 10MB allowed'}), 400

    try:
        # Upload to S3
        image_url = upload_submission_image(file_data, user.id, business_id)

        # Create submission record
        submission = ProductSubmission(
            user_id=user.id,
            business_id=business_id,
            image_url=image_url,
            status='pending'
        )
        db.session.add(submission)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Submission received! You will earn 10 credits if approved.',
            'submission': submission.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error creating submission: {e}")
        return jsonify({'error': 'Failed to process submission'}), 500


@submissions_bp.route('/api/submissions/my', methods=['GET'])
@login_required
def get_my_submissions(user):
    """Get current user's submissions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    submissions = ProductSubmission.query.filter_by(user_id=user.id)\
        .order_by(ProductSubmission.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'submissions': [s.to_dict() for s in submissions.items],
        'total': submissions.total,
        'page': page,
        'pages': submissions.pages
    })


@submissions_bp.route('/api/submissions/stats', methods=['GET'])
@login_required
def get_my_stats(user):
    """Get user's submission statistics"""
    total = ProductSubmission.query.filter_by(user_id=user.id).count()
    approved = ProductSubmission.query.filter_by(user_id=user.id, status='approved').count()
    pending = ProductSubmission.query.filter_by(user_id=user.id, status='pending').count()
    processing = ProductSubmission.query.filter_by(user_id=user.id, status='processing').count()
    rejected = ProductSubmission.query.filter_by(user_id=user.id, status='rejected').count()

    # Calculate total credits earned from submissions
    from sqlalchemy import func
    total_credits = db.session.query(func.coalesce(func.sum(ProductSubmission.credits_awarded), 0))\
        .filter(ProductSubmission.user_id == user.id, ProductSubmission.status == 'approved').scalar()

    return jsonify({
        'total': total,
        'approved': approved,
        'pending': pending,
        'processing': processing,
        'rejected': rejected,
        'credits_earned': int(total_credits or 0)
    })


# ==================== ADMIN ENDPOINTS ====================

@submissions_bp.route('/api/admin/submissions', methods=['GET'])
@admin_required
def get_all_submissions(user):
    """Get all submissions for admin review"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', None)

    query = ProductSubmission.query

    if status:
        query = query.filter_by(status=status)

    submissions = query.order_by(ProductSubmission.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # Add user info to each submission
    result = []
    for s in submissions.items:
        data = s.to_dict()
        data['user_email'] = s.user.email if s.user else None
        data['user_name'] = f"{s.user.first_name or ''} {s.user.last_name or ''}".strip() or s.user.email if s.user else None
        result.append(data)

    return jsonify({
        'submissions': result,
        'total': submissions.total,
        'page': page,
        'pages': submissions.pages
    })


@submissions_bp.route('/api/admin/submissions/<int:submission_id>/process', methods=['POST'])
@admin_required
def process_submission(user, submission_id):
    """
    Process a submission with AI extraction
    This triggers GPT-4o Vision to extract product details from the image
    Uses the same extract_product_from_image function as business owners
    """
    import base64
    import requests as http_requests
    from openai_utils import extract_product_from_image

    submission = ProductSubmission.query.get(submission_id)
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    # Allow processing for both pending and processing status (retry)
    if submission.status not in ['pending', 'processing']:
        return jsonify({'error': f'Cannot process submission with status: {submission.status}'}), 400

    # Mark as processing
    submission.status = 'processing'
    db.session.commit()

    try:
        # Download the image from S3 URL
        image_url = submission.image_url
        if not image_url:
            return jsonify({'error': 'Submission has no image URL'}), 400

        response = http_requests.get(image_url, timeout=30)
        if response.status_code != 200:
            raise Exception(f'Failed to download image: HTTP {response.status_code}')

        # Convert to base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')

        # Call AI to extract product info (same function as business owners use)
        extracted_data = extract_product_from_image(image_base64)

        # Store extracted data in the submission
        submission.extracted_title = extracted_data.get('title')
        submission.extracted_old_price = extracted_data.get('base_price')
        submission.extracted_new_price = extracted_data.get('discount_price')
        # extracted_valid_until needs date conversion if present
        if extracted_data.get('expires'):
            try:
                from datetime import date as date_type
                submission.extracted_valid_until = date_type.fromisoformat(extracted_data['expires'])
            except (ValueError, TypeError):
                pass
        submission.processed_at = datetime.now()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'AI processing complete',
            'submission': submission.to_dict(),
            'extracted_data': extracted_data
        })

    except Exception as e:
        submission.status = 'pending'  # Revert status on failure
        db.session.commit()
        print(f"Error processing submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process submission: {str(e)}'}), 500


@submissions_bp.route('/api/admin/submissions/<int:submission_id>/approve', methods=['POST'])
@admin_required
def approve_submission(user, submission_id):
    """
    Approve a submission and create/update product
    Request body:
    - title: Product title (required)
    - base_price: Original price (required)
    - discount_price: Discounted price (optional)
    - expires: Expiry date ISO string (optional)
    - is_price_update: If true, updates existing product instead of creating new one
    - existing_product_id: ID of product to update (required if is_price_update)
    """
    submission = ProductSubmission.query.get(submission_id)
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    if submission.status not in ['pending', 'processing']:
        return jsonify({'error': f'Cannot approve submission with status: {submission.status}'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    is_price_update = data.get('is_price_update', False)

    try:
        if is_price_update:
            # Update existing product price
            product_id = data.get('existing_product_id')
            if not product_id:
                return jsonify({'error': 'existing_product_id required for price update'}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404

            # Update prices
            if 'base_price' in data:
                product.base_price = float(data['base_price'])
            if 'discount_price' in data:
                product.discount_price = float(data['discount_price']) if data['discount_price'] else None
            if 'expires' in data and data['expires']:
                from datetime import date
                product.expires = date.fromisoformat(data['expires'])

            # Track that this update was contributed
            if not product.contributed_by:
                product.contributed_by = submission.user_id

        else:
            # Create new product
            title = data.get('title')
            base_price = data.get('base_price')

            if not title or base_price is None:
                return jsonify({'error': 'title and base_price are required for new products'}), 400

            from datetime import date as date_type

            product = Product(
                business_id=submission.business_id,
                title=title,
                base_price=float(base_price),
                discount_price=float(data['discount_price']) if data.get('discount_price') else None,
                expires=date_type.fromisoformat(data['expires']) if data.get('expires') else None,
                image_path=submission.image_url,
                contributed_by=submission.user_id
            )
            db.session.add(product)
            db.session.flush()  # Get product ID

            # AI Enrichment: Generate description and category for the new product
            try:
                from openai_utils import generate_enriched_description
                # Generate enriched description for semantic search
                enriched_desc = generate_enriched_description(product.title)
                product.enriched_description = enriched_desc
                # Default category for user submissions (can be changed later by admin)
                if not product.category:
                    product.category = "Higijena"  # Most submissions are hygiene products
                # Generate basic tags from title
                product.tags = [word.lower().strip() for word in product.title.split() if len(word) > 2][:10]
                db.session.commit()
                print(f"AI enriched product {product.id}: {product.title}")
            except Exception as enrich_err:
                print(f"Warning: AI enrichment failed for product {product.id}: {enrich_err}")

            # Generate embedding for the new product so it shows up in search
            try:
                from auto_vectorize import vectorize_product
                vectorize_product(product, force=True)
                print(f"Generated embedding for product {product.id}: {product.title}")
            except Exception as embed_err:
                print(f"Warning: Failed to generate embedding for product {product.id}: {embed_err}")

        # Award credits to user (10 credits for approved submission)
        credits_awarded = 10
        submitter = User.query.get(submission.user_id)
        if submitter:
            submitter.extra_credits = (submitter.extra_credits or 0) + credits_awarded

            # Log credit transaction
            from models import CreditTransaction
            transaction = CreditTransaction(
                user_id=submission.user_id,
                delta=credits_awarded,
                balance_after=(submitter.monthly_credits - submitter.monthly_credits_used) + (submitter.extra_credits or 0),
                action='SUBMISSION_APPROVED',
                transaction_metadata={
                    'submission_id': submission.id,
                    'product_id': product.id if not is_price_update else data.get('existing_product_id')
                }
            )
            db.session.add(transaction)

        # Update submission
        submission.status = 'approved'
        submission.reviewed_by = user.id
        submission.reviewed_at = datetime.now()
        submission.resulting_product_id = product.id if not is_price_update else data.get('existing_product_id')
        submission.credits_awarded = credits_awarded

        db.session.commit()

        # Send approval email
        if submitter and submitter.email:
            product_title = data.get('title') or (product.title if product else 'Proizvod')
            store_name = submission.business.name if submission.business else 'Nepoznata radnja'
            send_approval_email(submitter.email, submitter.first_name or 'Korisnik', product_title, store_name, credits_awarded)

        return jsonify({
            'success': True,
            'message': f'Submission approved! User awarded {credits_awarded} credits.',
            'submission': submission.to_dict(),
            'product_id': submission.resulting_product_id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error approving submission: {e}")
        return jsonify({'error': f'Failed to approve submission: {str(e)}'}), 500


@submissions_bp.route('/api/admin/submissions/<int:submission_id>/reject', methods=['POST'])
@admin_required
def reject_submission(user, submission_id):
    """
    Reject a submission with reason
    Request body:
    - reason: Rejection reason (required)
    - send_email: Whether to send rejection email (default: true)
    """
    submission = ProductSubmission.query.get(submission_id)
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    if submission.status not in ['pending', 'processing']:
        return jsonify({'error': f'Cannot reject submission with status: {submission.status}'}), 400

    data = request.get_json() or {}
    reason = data.get('reason', 'Ne ispunjava uslove za prihvatanje.')
    send_email = data.get('send_email', True)

    try:
        submission.status = 'rejected'
        submission.reviewed_by = user.id
        submission.reviewed_at = datetime.now()
        submission.rejection_reason = reason

        db.session.commit()

        # Send rejection email with tips
        if send_email:
            submitter = User.query.get(submission.user_id)
            if submitter and submitter.email:
                send_rejection_email(submitter.email, submitter.first_name or 'Korisnik', reason, submission.business.name if submission.business else 'Nepoznata radnja')

        return jsonify({
            'success': True,
            'message': 'Submission rejected',
            'submission': submission.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting submission: {e}")
        return jsonify({'error': 'Failed to reject submission'}), 500


@submissions_bp.route('/api/admin/submissions/<int:submission_id>/mark-duplicate', methods=['POST'])
@admin_required
def mark_duplicate(user, submission_id):
    """
    Mark submission as duplicate of existing product
    Request body:
    - duplicate_of: Product ID that this duplicates
    """
    submission = ProductSubmission.query.get(submission_id)
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    data = request.get_json()
    if not data or 'duplicate_of' not in data:
        return jsonify({'error': 'duplicate_of product ID required'}), 400

    product = Product.query.get(data['duplicate_of'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    submission.status = 'duplicate'
    submission.potential_duplicate_id = product.id
    submission.duplicate_similarity = 1.0  # Manual confirmation = 100% match
    submission.reviewed_by = user.id
    submission.reviewed_at = datetime.now()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Submission marked as duplicate',
        'submission': submission.to_dict()
    })


def send_rejection_email(email, name, reason, store_name):
    """Send rejection email with tips for better submissions"""
    from sendgrid_utils import send_email, get_base_template

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Vaš prijedlog nije prihvaćen</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani/a {name},</p>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Nažalost, Vaš prijedlog proizvoda za <strong>{store_name}</strong> nije mogao biti prihvaćen.</p>

<div style="margin:24px 0;padding:16px;background:#FEF2F2;border-left:4px solid #EF4444;border-radius:0 8px 8px 0;">
<p style="margin:0;font-size:14px;color:#991B1B;"><strong>Razlog:</strong> {reason}</p>
</div>

<h2 style="margin:24px 0 16px;font-size:16px;font-weight:600;color:#1a1a1a;">Savjeti za uspješan prijedlog:</h2>
<ul style="margin:0;padding:0 0 0 20px;font-size:14px;color:#444;line-height:1.8;">
<li><strong>Jasna slika cijene</strong> - Fotografirajte etiketu tako da se jasno vidi cijena</li>
<li><strong>Čitljiv naziv proizvoda</strong> - Uključite naziv proizvoda na etiketi</li>
<li><strong>Dobro osvjetljenje</strong> - Izbjegavajte mutne ili tamne fotografije</li>
<li><strong>Jedan proizvod</strong> - Fotografirajte jedan proizvod po prijedlogu</li>
</ul>

<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;">
<p style="margin:0;font-size:13px;color:#666;line-height:1.5;">
Hvala Vam što doprinosite zajednici! Svaki prihvaćeni prijedlog donosi Vam <strong>10 kredita</strong>.
</p>
</div>
'''

    html = get_base_template(content, "#EF4444")
    if send_email(email, 'Vaš prijedlog proizvoda - Popust.ba', html):
        print(f"Rejection email sent to {email}")
    else:
        print(f"Failed to send rejection email to {email}")


def send_approval_email(email, name, product_title, store_name, credits_awarded):
    """Send approval email with congratulations"""
    from sendgrid_utils import send_email, get_base_template

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">🎉 Čestitamo!</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani/a {name},</p>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Vaš prijedlog proizvoda za <strong>{store_name}</strong> je pregledan i prihvaćen!</p>

<div style="margin:24px 0;padding:16px;background:#F0FDF4;border-left:4px solid #10B981;border-radius:0 8px 8px 0;">
<p style="margin:0 0 8px;font-size:14px;color:#065F46;"><strong>Proizvod:</strong> {product_title}</p>
<p style="margin:0;font-size:14px;color:#065F46;"><strong>Nagrada:</strong> +{credits_awarded} kredita</p>
</div>

<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Vaš doprinos pomaže zajednici da pronađe najbolje ponude. Hvala Vam!</p>

<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;">
<p style="margin:0 0 8px;font-size:14px;font-weight:600;color:#1a1a1a;">Nastavite doprinositi!</p>
<p style="margin:0;font-size:13px;color:#666;line-height:1.5;">
Za svaki prihvaćeni prijedlog dobijate <strong>10 kredita</strong>. Fotografirajte cijene proizvoda u trgovinama i pomozite drugima da uštede!
</p>
</div>
'''

    html = get_base_template(content, "#10B981")
    if send_email(email, '🎉 Vaš prijedlog je prihvaćen! - Popust.ba', html):
        print(f"Approval email sent to {email}")
    else:
        print(f"Failed to send approval email to {email}")


# ==================== PUBLIC PROFILE ENDPOINTS ====================

@submissions_bp.route('/api/korisnik/<user_id>', methods=['GET'])
def get_public_profile(user_id):
    """
    Get public profile for a user contributor.
    Only shows:
    - First name (or email username if no first name)
    - Number of approved contributions
    - Total credits earned from contributions
    - Member since date
    - List of contributed products
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get contribution stats
    total_contributions = ProductSubmission.query.filter_by(
        user_id=user_id,
        status='approved'
    ).count()

    # Get total credits earned from contributions
    from sqlalchemy import func
    total_credits = db.session.query(func.coalesce(func.sum(ProductSubmission.credits_awarded), 0))\
        .filter(ProductSubmission.user_id == user_id, ProductSubmission.status == 'approved').scalar()

    # Get contributed products (products where contributed_by = user_id)
    contributed_products = Product.query.filter_by(contributed_by=user_id)\
        .order_by(Product.created_at.desc())\
        .limit(20).all()

    # Import product serializer
    from routes import product_to_dict

    # Determine display name (privacy-conscious)
    display_name = user.first_name
    if not display_name and user.email:
        # Use email username without domain
        display_name = user.email.split('@')[0]
    if not display_name:
        display_name = 'Korisnik'

    return jsonify({
        'profile': {
            'id': user.id,
            'display_name': display_name,
            'member_since': user.created_at.strftime('%B %Y') if user.created_at else None,
            'total_contributions': total_contributions,
            'credits_earned': int(total_credits or 0),
        },
        'contributed_products': [product_to_dict(p, include_price_history=False) for p in contributed_products]
    })
