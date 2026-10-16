from abc import ABC, abstractmethod
from typing import Callable, Optional
from backend.app.schemas.media import VideoMetadata, SearchResponse

class BaseMediaProvider(ABC):
    @abstractmethod
    async def analyze(self, url: str) -> VideoMetadata:
        """Extract metadata and available streams without downloading the full video."""
        pass

    @abstractmethod
    async def search(self, query: str, page: int = 1, limit: int = 10) -> SearchResponse:
        """Search videos using authorized provider."""
        pass

    @abstractmethod
    async def download_stream(
        self,
        url: str,
        format_id: str,
        output_template: str,
        progress_callback: Optional[Callable[[dict], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> str:
        """Download stream to specified output template."""
        pass
