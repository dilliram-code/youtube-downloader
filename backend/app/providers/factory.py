from backend.app.providers.base import BaseMediaProvider
from backend.app.providers.ytdlp_provider import YtDlpProvider
from backend.app.providers.mock_provider import MockMediaProvider

_mock_instance = None
_ytdlp_instance = None

def get_provider_for_url(url: str) -> BaseMediaProvider:
    global _mock_instance, _ytdlp_instance
    if "test-media.local" in url:
        if not _mock_instance:
            _mock_instance = MockMediaProvider()
        return _mock_instance

    if not _ytdlp_instance:
        _ytdlp_instance = YtDlpProvider()
    return _ytdlp_instance

def get_default_provider() -> BaseMediaProvider:
    global _ytdlp_instance
    if not _ytdlp_instance:
        _ytdlp_instance = YtDlpProvider()
    return _ytdlp_instance
