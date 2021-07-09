import tempfile

from django.conf import settings

settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
