import os
from pathlib import Path

from cloudinary import uploader
from cloudinary_storage.storage import MediaCloudinaryStorage, RESOURCE_TYPES
from django.core.files.uploadedfile import UploadedFile


class PostMediaCloudinaryStorage(MediaCloudinaryStorage):
    """Store post videos as Cloudinary video resources and images as images."""

    video_extensions = {".mp4"}
    video_content_type_prefix = "video/"
    video_prefix = "__video__/"

    def _is_video_name(self, name):
        return name.startswith(self.video_prefix) or (
            Path(name).suffix.lower() in self.video_extensions
        )

    def _is_video_upload(self, name, content):
        """Classify supported uploads before Cloudinary chooses an image path."""

        if self._is_video_name(name):
            return True

        content_type = (getattr(content, "content_type", "") or "").lower()
        return content_type.startswith(self.video_content_type_prefix)

    def _get_resource_type(self, name):
        if self._is_video_name(name):
            return RESOURCE_TYPES["VIDEO"]

        return RESOURCE_TYPES["IMAGE"]

    def _cloudinary_name(self, name):
        if name.startswith(self.video_prefix):
            return name[len(self.video_prefix) :]

        return name

    def _save(self, name, content):
        # Do not delegate to MediaCloudinaryStorage._save(). That method
        # delegates resource selection to the generic image storage path,
        # which is what caused MP4 uploads to reach Cloudinary as images.
        name = self._normalise_name(name)
        name = self._prepend_prefix(name)
        is_video = self._is_video_upload(name, content)
        content = UploadedFile(
            content,
            name,
            content_type=getattr(content, "content_type", None),
        )
        response = self._upload(name, content)
        public_id = response["public_id"]

        # Cloudinary removes non-raw file extensions from public IDs. Keep a
        # storage-only marker so future URL, delete, and open calls retain the
        # correct video resource type.
        return f"{self.video_prefix}{public_id}" if is_video else public_id

    def _upload(self, name, content):
        content_name = getattr(content, "name", "")
        is_video = self._is_video_upload(name, content) or self._is_video_name(
            content_name
        )

        # Uploaded files can have been inspected by validation before storage
        # saves them. Cloudinary consumes the stream from its current offset,
        # so always start the upload at byte zero. Django's in-memory and
        # temporary uploaded files are seekable; surfacing a non-seekable
        # stream is preferable to submitting a partial/corrupt asset.
        try:
            content.seek(0)
        except (AttributeError, OSError, ValueError) as exc:
            raise ValueError("Post media uploads must use a seekable file stream.") from exc

        options = {
            "use_filename": True,
            "resource_type": (
                RESOURCE_TYPES["VIDEO"] if is_video else RESOURCE_TYPES["IMAGE"]
            ),
            "tags": self.TAG,
        }
        folder = os.path.dirname(name)
        if folder:
            options["folder"] = folder

        return uploader.upload(content, **options)

    def _get_url(self, name):
        from cloudinary import CloudinaryResource

        return CloudinaryResource(
            self._cloudinary_name(name),
            default_resource_type=self._get_resource_type(name),
        ).url

    def delete(self, name):
        from cloudinary import uploader

        response = uploader.destroy(
            self._cloudinary_name(name),
            invalidate=True,
            resource_type=self._get_resource_type(name),
        )
        return response["result"] == "ok"
