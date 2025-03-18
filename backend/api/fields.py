import base64
from typing import Any

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data: Any) -> ContentFile:
        if isinstance(data, str) and "data:image" in data:
            try:
                metadata, encoded = data.split(";base64,")
                extension = metadata.rsplit("/", 1)[-1]
                binary_data = base64.b64decode(encoded)
                data = ContentFile(binary_data, name=f"uploaded_image.{extension}")
            except Exception:
                raise serializers.ValidationError("Ошибка обработки изображения")
        return super().to_internal_value(data)
