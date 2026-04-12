"""Tests for cover image processing service."""

from io import BytesIO

from PIL import Image

from src.infrastructure.library.services.cover_image_service import CoverImageService


def _create_test_image(width: int, height: int, color: str = "red") -> bytes:
    """Create a test JPEG image of given dimensions."""
    img = Image.new("RGB", (width, height), color)
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestProcessCover:
    def test_resizes_large_image_to_fit_within_target(self) -> None:
        service = CoverImageService()
        original = _create_test_image(600, 840)

        resized_bytes, _blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 300
        assert img.height == 420

    def test_preserves_aspect_ratio_for_wide_image(self) -> None:
        service = CoverImageService()
        original = _create_test_image(800, 600)

        resized_bytes, _blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 300
        assert img.height == 225

    def test_preserves_aspect_ratio_for_tall_image(self) -> None:
        service = CoverImageService()
        original = _create_test_image(400, 1000)

        resized_bytes, _blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 168
        assert img.height == 420

    def test_does_not_upscale_small_image(self) -> None:
        service = CoverImageService()
        original = _create_test_image(100, 150)

        resized_bytes, _blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 100
        assert img.height == 150

    def test_returns_valid_blurhash_string(self) -> None:
        service = CoverImageService()
        original = _create_test_image(600, 840)

        _, blurhash = service.process_cover(original)

        assert isinstance(blurhash, str)
        assert len(blurhash) > 0
        assert len(blurhash) <= 40

    def test_output_is_jpeg(self) -> None:
        service = CoverImageService()
        original = _create_test_image(600, 840)

        resized_bytes, _ = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.format == "JPEG"

    def test_handles_png_input(self) -> None:
        service = CoverImageService()
        img = Image.new("RGBA", (600, 840), (255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        resized_bytes, _blurhash = service.process_cover(png_bytes)

        result_img = Image.open(BytesIO(resized_bytes))
        assert result_img.format == "JPEG"
        assert result_img.mode == "RGB"
