"""Service for processing book cover images."""

from io import BytesIO

import blurhash
from PIL import Image

MAX_WIDTH = 300
MAX_HEIGHT = 420
JPEG_QUALITY = 85
BLURHASH_X_COMPONENTS = 4
BLURHASH_Y_COMPONENTS = 3


class CoverImageService:
    """Resizes cover images and generates blurhash strings."""

    def process_cover(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Process a cover image: resize and generate blurhash.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)

        Returns:
            Tuple of (resized JPEG bytes, blurhash string)
        """
        img = Image.open(BytesIO(image_bytes))

        # Convert RGBA/palette to RGB for JPEG output
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # Resize to fit within MAX_WIDTH x MAX_HEIGHT, preserving aspect ratio.
        # Only downscale, never upscale.
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

        # Save as JPEG first
        output = BytesIO()
        img.save(output, format="JPEG", quality=JPEG_QUALITY)
        jpeg_bytes = output.getvalue()

        # Generate blurhash from a fresh read of the saved JPEG
        hash_img = Image.open(BytesIO(jpeg_bytes))
        hash_str = blurhash.encode(
            hash_img, x_components=BLURHASH_X_COMPONENTS, y_components=BLURHASH_Y_COMPONENTS
        )

        return jpeg_bytes, hash_str
