"""
AI Image Matcher using GPT-4o Vision for product image matching.
"""
import os
import base64
import requests
from openai import OpenAI


def get_openai_client():
    """Get OpenAI client instance."""
    return OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))


def download_image_as_base64(url: str, timeout: int = 10) -> str | None:
    """Download image and convert to base64."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        content_type = resp.headers.get('Content-Type', '')
        if 'image' not in content_type:
            return None

        # Limit to 5MB
        if len(resp.content) > 5 * 1024 * 1024:
            return None

        return base64.standard_b64encode(resp.content).decode('utf-8')
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return None


def get_image_url(path: str) -> str:
    """Convert S3 path to full URL."""
    if not path:
        return ''
    if path.startswith('http'):
        return path
    bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')
    region = os.environ.get('AWS_REGION', 'eu-central-1')
    return f"https://{bucket}.s3.{region}.amazonaws.com/{path}"


def match_product_images(
    product_title: str,
    original_image_path: str | None,
    suggested_image_paths: list[str]
) -> dict:
    """
    Use GPT-4o Vision to match product images.

    Args:
        product_title: The product title/name
        original_image_path: Path to original product image (can be None)
        suggested_image_paths: List of S3 paths to suggested images

    Returns:
        Dict with matches, best_match, and analysis
    """
    client = get_openai_client()

    if not suggested_image_paths:
        return {
            'matches': [],
            'best_match': None,
            'analysis': 'No suggested images to match'
        }

    # Build the message content with images
    content = []

    # Add text prompt
    prompt = f"""You are an expert product image matcher. Your task is to analyze images and determine which ones best match the product.

Product Name: "{product_title}"

"""

    if original_image_path:
        prompt += "I'm showing you the ORIGINAL product image first, followed by suggested images numbered 1-10.\n"
        prompt += "Compare each suggested image to the original and rate similarity.\n\n"
    else:
        prompt += "I'm showing you suggested images numbered 1-10 for this product.\n"
        prompt += "Determine which images best match the product name.\n\n"

    prompt += """For each suggested image, provide:
1. A confidence score (0-100%) indicating how well it matches the product
2. A brief reason

Then identify the BEST match.

IMPORTANT:
- 100% = EXACT same product (same brand, same variant, same packaging)
- 80-99% = Same product, minor differences (different size, slightly different packaging)
- 60-79% = Similar product (same type, different brand or significant differences)
- 40-59% = Related product (same category, but clearly different)
- 0-39% = Wrong product

Respond in this JSON format:
{
    "matches": [
        {"index": 1, "confidence": 95, "reason": "Exact match - same brand and packaging"},
        {"index": 2, "confidence": 60, "reason": "Similar product but different brand"},
        ...
    ],
    "best_match_index": 1,
    "analysis": "Brief overall analysis"
}"""

    content.append({"type": "text", "text": prompt})

    # Add original image if available
    image_urls = []
    if original_image_path:
        original_url = get_image_url(original_image_path)
        image_urls.append(("Original", original_url))
        content.append({
            "type": "text",
            "text": "ORIGINAL PRODUCT IMAGE:"
        })
        content.append({
            "type": "image_url",
            "image_url": {"url": original_url, "detail": "low"}
        })

    # Add suggested images
    content.append({
        "type": "text",
        "text": "\nSUGGESTED IMAGES:"
    })

    for i, path in enumerate(suggested_image_paths[:10], 1):
        img_url = get_image_url(path)
        image_urls.append((f"Suggestion {i}", img_url))
        content.append({
            "type": "text",
            "text": f"\nImage {i}:"
        })
        content.append({
            "type": "image_url",
            "image_url": {"url": img_url, "detail": "low"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        import json
        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # Map results to include image paths
        matches = []
        best_match = None

        for match in result.get('matches', []):
            idx = match.get('index', 0) - 1  # Convert to 0-based
            if 0 <= idx < len(suggested_image_paths):
                match_data = {
                    'index': idx + 1,
                    'image_path': suggested_image_paths[idx],
                    'confidence': match.get('confidence', 0),
                    'reason': match.get('reason', ''),
                    'is_best': (idx + 1) == result.get('best_match_index')
                }
                matches.append(match_data)

                if match_data['is_best']:
                    best_match = match_data

        # Sort by confidence descending
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        # If no best match was identified, use highest confidence
        if not best_match and matches:
            best_match = matches[0]
            matches[0]['is_best'] = True

        return {
            'matches': matches,
            'best_match': best_match,
            'analysis': result.get('analysis', '')
        }

    except Exception as e:
        print(f"GPT-4o Vision error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'matches': [],
            'best_match': None,
            'analysis': f'Error: {str(e)}'
        }
