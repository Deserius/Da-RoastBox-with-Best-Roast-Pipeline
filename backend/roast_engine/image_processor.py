import base64
import io
from typing import Tuple, Dict, Any
from PIL import Image, ImageOps


MAX_DIMENSION = 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def process_image(image_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    Stage 1: Image Ingestion
    - Validates actual image bytes via Pillow
    - Normalizes EXIF orientation
    - Resizes to max 1024x1024 while preserving aspect ratio
    - Encodes as clean JPEG base64 data URL for OpenRouter/OpenAI compatibility
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image file: {str(e)}")

    orig_format = (img.format or "JPEG").upper()
    if orig_format not in ALLOWED_FORMATS:
        # Convert GIF/BMP/TIFF etc. to JPEG
        orig_format = "JPEG"

    # Normalize EXIF orientation
    img = ImageOps.exif_transpose(img)

    # Convert to RGB if RGBA/P for clean JPEG encoding
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (15, 15, 20))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    orig_size = img.size
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=88, optimize=True)
    encoded = base64.b64encode(out_buf.getvalue()).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{encoded}"

    meta = {
        "original_dimensions": f"{orig_size[0]}x{orig_size[1]}",
        "processed_dimensions": f"{img.size[0]}x{img.size[1]}",
        "mime_type": "image/jpeg",
        "size_kb": round(len(out_buf.getvalue()) / 1024, 1),
    }
    return data_url, meta
