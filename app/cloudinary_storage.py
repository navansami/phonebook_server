"""Cloudinary storage service for profile pictures."""

import cloudinary
import cloudinary.uploader
from typing import Optional
from .config import settings


class CloudinaryStorage:
    """Handle uploads to Cloudinary."""

    def __init__(self):
        """Initialize Cloudinary configuration."""
        # Check if Cloudinary is configured
        if not all([
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET
        ]):
            print("[WARNING] Cloudinary not configured. Profile pictures will not be uploaded.")
            self.enabled = False
            return

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        self.enabled = True
        print(f"[OK] Cloudinary initialized: {settings.CLOUDINARY_CLOUD_NAME}")

    def upload_profile_picture(
        self,
        file_content: bytes,
        contact_id: str
    ) -> Optional[str]:
        """
        Upload a profile picture to Cloudinary and return the public URL.

        Args:
            file_content: Image file bytes
            contact_id: Contact ID to use in filename

        Returns:
            Public URL of the uploaded image, or None if upload fails
        """
        if not self.enabled:
            print("[ERROR] Cloudinary is not enabled")
            return None

        try:
            # Upload to Cloudinary with transformations
            result = cloudinary.uploader.upload(
                file_content,
                folder="telbook/profile-pictures",
                public_id=f"contact_{contact_id}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {"width": 400, "height": 400, "crop": "limit"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )

            public_url = result.get('secure_url')
            print(f"[OK] Uploaded profile picture to Cloudinary: {public_url}")
            return public_url

        except Exception as e:
            print(f"[ERROR] Failed to upload to Cloudinary: {e}")
            return None

    def delete_profile_picture(self, public_id: str) -> bool:
        """
        Delete a profile picture from Cloudinary.

        Args:
            public_id: Cloudinary public ID (e.g., "telbook/profile-pictures/contact_0001")

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            result = cloudinary.uploader.destroy(public_id)
            success = result.get('result') == 'ok'
            if success:
                print(f"[OK] Deleted profile picture: {public_id}")
            return success

        except Exception as e:
            print(f"[ERROR] Failed to delete from Cloudinary: {e}")
            return False

    def extract_public_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract Cloudinary public_id from URL.

        Args:
            url: Cloudinary URL

        Returns:
            Public ID or None
        """
        try:
            # Example URL: https://res.cloudinary.com/{cloud_name}/image/upload/v123456/telbook/profile-pictures/contact_0001.jpg
            parts = url.split('/upload/')
            if len(parts) == 2:
                # Get everything after /upload/ and remove version number
                path = parts[1]
                # Remove version (v123456/)
                if path.startswith('v'):
                    path = '/'.join(path.split('/')[1:])
                # Remove file extension
                public_id = path.rsplit('.', 1)[0]
                return public_id
            return None
        except Exception as e:
            print(f"[ERROR] Failed to extract public_id: {e}")
            return None


# Global Cloudinary storage instance
cloudinary_storage = CloudinaryStorage()
