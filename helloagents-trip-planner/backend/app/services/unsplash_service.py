import httpx
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class UnsplashService:
    """Unsplash 图片服务（异步）"""

    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"

    async def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        """搜索图片"""
        try:
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key
            }
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self.base_url}/search/photos", params=params)
                response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            photos = []
            for result in results:
                photos.append({
                    "url": result["urls"]["regular"],
                    "description": result.get("description", ""),
                    "photographer": result["user"]["name"]
                })

            return photos

        except Exception as e:
            logger.error(f"搜索图片失败: {e}")
            return []

    async def get_photo_url(self, query: str) -> Optional[str]:
        """获取单张图片URL"""
        photos = await self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None
