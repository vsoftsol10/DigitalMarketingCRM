import os
from io import UnsupportedOperation
from pathlib import Path

import requests
from cloudinary import uploader
from cloudinary_storage.storage import MediaCloudinaryStorage, RESOURCE_TYPES
from django.core.files.base import File
from django.core.files.uploadedfile import UploadedFile


CLOUDINARY_MEDIA_DOWNLOAD_TIMEOUT = (10, 120)


class CloudinaryStreamingFile(File):
    """Read a Cloudinary asset without buffering its full response in memory."""

    def __init__(self, response, name, mode="rb"):
        super().__init__(response.raw, name=name)
        self._response = response
        self._position = 0
        self.mode = mode
        try:
            self._content_length = int(response.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            self._content_length = 0
        if not self._content_length:
            raw_length = getattr(response.raw, "length_remaining", None)
            if isinstance(raw_length, int) and raw_length > 0:
                self._content_length = raw_length
        response.raw.decode_content = True

    @property
    def size(self):
        return self._content_length

    def read(self, size=-1):
        data = self.file.read(size)
        self._position += len(data)
        return data

    def tell(self):
        return self._position

    def seek(self, *args, **kwargs):
        raise UnsupportedOperation("Cloudinary media streams are not seekable.")

    def close(self):
        try:
            super().close()
        finally:
            self._response.close()


class PostMediaCloudinaryStorage(MediaCloudinaryStorage):
    """Store post videos as Cloudinary video resources and images as images."""

    video_extensions = {".mp4"}
    video_content_type_prefix = "video/"
    video_prefix = "__video__/"
    image_prefix = "__image__/"
    version_marker = "::v"

    def _decode_name(self, name):
        resource_type = None
        cloudinary_name = name
        if name.startswith(self.video_prefix):
            resource_type = RESOURCE_TYPES["VIDEO"]
            cloudinary_name = name[len(self.video_prefix) :]
        elif name.startswith(self.image_prefix):
            resource_type = RESOURCE_TYPES["IMAGE"]
            cloudinary_name = name[len(self.image_prefix) :]

        version = None
        if self.version_marker in cloudinary_name:
            cloudinary_name, version_value = cloudinary_name.rsplit(
                self.version_marker,
                1,
            )
            try:
                version = int(version_value)
            except (TypeError, ValueError):
                version = None

        return cloudinary_name, version, resource_type

    def _is_video_name(self, name):
        decoded_resource_type = self._decode_name(name)[2]
        return decoded_resource_type == RESOURCE_TYPES["VIDEO"] or (
            Path(name).suffix.lower() in self.video_extensions
        )

    def _is_video_upload(self, name, content):
        """Classify supported uploads before Cloudinary chooses an image path."""

        if self._is_video_name(name):
            return True

        content_type = (getattr(content, "content_type", "") or "").lower()
        return content_type.startswith(self.video_content_type_prefix)

    def _get_resource_type(self, name):
        decoded_resource_type = self._decode_name(name)[2]
        if decoded_resource_type:
            return decoded_resource_type
        if self._is_video_name(name):
            return RESOURCE_TYPES["VIDEO"]

        return RESOURCE_TYPES["IMAGE"]

    def _cloudinary_name(self, name):
        return self._decode_name(name)[0]

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

    def _open(self, name, mode="rb"):
        response = requests.get(
            self._get_url(name),
            stream=True,
            timeout=CLOUDINARY_MEDIA_DOWNLOAD_TIMEOUT,
        )
        try:
            if response.status_code == 404:
                raise IOError
            response.raise_for_status()
            return CloudinaryStreamingFile(response, name=name, mode=mode)
        except Exception:
            response.close()
            raise

    def size(self, name):
        response = requests.head(
            self._get_url(name),
            timeout=CLOUDINARY_MEDIA_DOWNLOAD_TIMEOUT,
        )
        try:
            if response.status_code == 200:
                return int(response.headers["content-length"])
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return None
        finally:
            response.close()

    def _get_url(self, name):
        from cloudinary import CloudinaryResource

        cloudinary_name, version, resource_type = self._decode_name(name)
        return CloudinaryResource(
            cloudinary_name,
            version=version,
            default_resource_type=resource_type or self._get_resource_type(name),
        ).url

    def delete(self, name):
        from cloudinary import uploader

        response = uploader.destroy(
            self._cloudinary_name(name),
            invalidate=True,
            resource_type=self._get_resource_type(name),
        )
        return response["result"] == "ok"
