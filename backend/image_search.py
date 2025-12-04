"""
Image search service using DuckDuckGo for product image suggestions.
"""
import requests
import os
import boto3
from botocore.exceptions import ClientError


def clean_search_query(query: str, is_custom_query: bool = False) -> str:
    """
    Clean and optimize search query for better image results.

    - Extracts main product name from titles like "Sok Cola/Cola Zero 1 L Sky"
    - Removes store/brand names that might be local
    - Adds "product" to help find product photos (only for auto-generated queries)

    Args:
        query: The search query
        is_custom_query: If True, the user provided this query manually, so don't modify it much
    """
    import re

    # If it's a custom query, just use it as-is (user knows what they want)
    if is_custom_query:
        return query.strip()

    # Common local brand/store names to remove (case insensitive)
    local_brands = ['sky', 'bingo', 'konzum', 'mercator', 'dm', 'rossmann', 'lidl', 'aldi', 'hofer']

    # Remove size/volume info like "1 L", "500ml", "250g", etc.
    cleaned = re.sub(r'\b\d+\s*(l|ml|g|kg|kom|pcs)\b', '', query, flags=re.IGNORECASE)

    # Split by common separators and take first meaningful part
    # e.g., "Sok Cola/Cola Zero 1 L Sky" -> prioritize "Cola" or "Coca Cola"
    parts = re.split(r'[/|,]', cleaned)

    # Clean each part
    cleaned_parts = []
    for part in parts:
        part = part.strip()
        # Skip if it's just a local brand name
        if part.lower() in local_brands:
            continue
        # Remove local brand names from within the part
        for brand in local_brands:
            part = re.sub(rf'\b{brand}\b', '', part, flags=re.IGNORECASE)
        part = part.strip()
        if part and len(part) > 2:
            cleaned_parts.append(part)

    # Use the first non-empty part, or original if nothing left
    if cleaned_parts:
        result = cleaned_parts[0].strip()
    else:
        result = query

    # Clean up extra whitespace
    result = ' '.join(result.split())

    # Add "product" to help find product photos instead of logos/ads
    if result and 'product' not in result.lower():
        result = f"{result} product"

    return result


def search_duckduckgo_images(query: str, num_results: int = 5, is_custom_query: bool = False) -> list[str]:
    """
    Search DuckDuckGo for images and return URLs.

    Args:
        query: Search query (product title)
        num_results: Number of image URLs to return
        is_custom_query: If True, don't modify the query (user knows what they want)

    Returns:
        List of image URLs
    """
    try:
        from duckduckgo_search import DDGS

        # Clean the query for better results (unless it's a custom query)
        cleaned_query = clean_search_query(query, is_custom_query=is_custom_query)
        print(f"Image search: '{query}' -> '{cleaned_query}'")

        with DDGS() as ddgs:
            results = list(ddgs.images(
                cleaned_query,
                region='wt-wt',
                safesearch='moderate',
                max_results=num_results + 3  # Get extra in case some fail
            ))

        image_urls = []
        for result in results:
            img_url = result.get('image')
            if img_url and img_url.startswith('http'):
                image_urls.append(img_url)
                if len(image_urls) >= num_results:
                    break

        return image_urls

    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        import traceback
        traceback.print_exc()
        return []


def download_image(url: str, timeout: int = 10) -> tuple[bytes, str] | None:
    """
    Download an image from URL.

    Returns:
        Tuple of (image_bytes, content_type) or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get('Content-Type', 'image/jpeg')
        if 'image' not in content_type:
            return None

        # Limit size to 5MB
        content = resp.content
        if len(content) > 5 * 1024 * 1024:
            return None

        return content, content_type

    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None


def get_extension_from_content_type(content_type: str) -> str:
    """Get file extension from content type."""
    mapping = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
    }
    return mapping.get(content_type.split(';')[0].strip(), '.jpg')


def upload_to_s3(image_bytes: bytes, s3_path: str, content_type: str) -> str | None:
    """
    Upload image to S3.

    Args:
        image_bytes: Image data
        s3_path: Path in S3 bucket (e.g., 'popust/suggestions/123/1.jpg')
        content_type: MIME type

    Returns:
        S3 path if successful, None otherwise
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'eu-central-1')
        )

        bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')

        s3_client.put_object(
            Bucket=bucket,
            Key=s3_path,
            Body=image_bytes,
            ContentType=content_type,
            CacheControl='max-age=31536000'
        )

        return s3_path

    except ClientError as e:
        print(f"S3 upload error: {e}")
        return None


def search_and_upload_suggestions(product_id: int, query: str, num_images: int = 5, is_custom_query: bool = False) -> list[str]:
    """
    Search for images and upload them to S3.

    Args:
        product_id: Product ID for organizing S3 paths
        query: Search query (product title)
        num_images: Number of images to fetch
        is_custom_query: If True, don't modify the query (user provided it manually)

    Returns:
        List of S3 paths for successfully uploaded images
    """
    # Search for images
    image_urls = search_duckduckgo_images(query, num_images + 3, is_custom_query=is_custom_query)  # Get extra in case some fail

    if not image_urls:
        return []

    uploaded_paths = []

    for i, url in enumerate(image_urls):
        if len(uploaded_paths) >= num_images:
            break

        result = download_image(url)
        if not result:
            continue

        image_bytes, content_type = result
        ext = get_extension_from_content_type(content_type)

        # S3 path: popust/suggestions/<product_id>/<index><ext>
        s3_path = f"popust/suggestions/{product_id}/{len(uploaded_paths) + 1}{ext}"

        uploaded = upload_to_s3(image_bytes, s3_path, content_type)
        if uploaded:
            uploaded_paths.append(uploaded)

    return uploaded_paths


def delete_suggestions_from_s3(product_id: int):
    """Delete all suggested images for a product from S3."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'eu-central-1')
        )

        bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')
        prefix = f"popust/suggestions/{product_id}/"

        # List and delete objects
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if 'Contents' in response:
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            s3_client.delete_objects(Bucket=bucket, Delete={'Objects': objects})

    except Exception as e:
        print(f"Error deleting S3 suggestions: {e}")
