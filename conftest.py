import tempfile

import pytest
from django.test import override_settings


@pytest.fixture(autouse=True, scope='session')
def _use_temp_media_root():
    """Uploaded files in tests must never land in the real media/ directory."""
    with tempfile.TemporaryDirectory() as tmp_media, override_settings(MEDIA_ROOT=tmp_media):
        yield
