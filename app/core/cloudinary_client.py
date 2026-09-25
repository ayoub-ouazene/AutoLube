import cloudinary
import cloudinary.uploader
import cloudinary.utils

from app.config import settings


def _configure() -> None:
    if settings.cloudinary_configured:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )


def upload_image(file_bytes: bytes, folder: str = "autolube/products") -> str:
    """
    Upload raw image bytes to Cloudinary and return the secure HTTPS URL.
    Raises RuntimeError if Cloudinary is not configured.
    """
    if not settings.cloudinary_configured:
        raise RuntimeError("Cloudinary is not configured.")

    _configure()
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type="image",
    )
    return result["secure_url"]


def delete_image_by_url(url: str) -> bool:
    """
    Best-effort deletion of a Cloudinary image given its secure_url.
    Returns True on success, False on any failure or if not configured.
    """
    if not settings.cloudinary_configured or not url:
        return False

    try:
        _configure()
        public_id = _public_id_from_url(url)
        if not public_id:
            return False
        cloudinary.uploader.destroy(public_id, resource_type="image")
        return True
    except Exception:
        return False


def _public_id_from_url(url: str) -> str | None:
    """
    Extract the Cloudinary public_id from a secure_url.

    Example:
        https://res.cloudinary.com/<cloud>/image/upload/v123/autolube/products/abc.jpg
        -> autolube/products/abc
    """
    try:
        marker = "/upload/"
        idx = url.find(marker)
        if idx == -1:
            return None
        after = url[idx + len(marker):]
        # strip version segment like "v12345/"
        if after.startswith("v"):
            slash = after.find("/")
            if slash != -1:
                after = after[slash + 1:]
        # strip extension
        if "." in after:
            after = after.rsplit(".", 1)[0]
        return after
    except Exception:
        return None