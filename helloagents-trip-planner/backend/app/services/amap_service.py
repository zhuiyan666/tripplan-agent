import httpx
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AmapService:
    """高德地图 Web 服务 API 异步封装"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"

    async def search_poi(self, city: str, keywords: str, page: int = 1, offset: int = 20) -> List[Dict]:
        """搜索 POI（景点/酒店等）"""
        try:
            params = {
                "key": self.api_key,
                "keywords": keywords,
                "city": city,
                "page": page,
                "offset": offset,
                "output": "json",
                "children": 0,
                "extensions": "all"
            }
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self.base_url}/place/text", params=params)
            data = response.json()

            if data.get("status") != "1":
                logger.warning(f"高德 POI 搜索失败: {data.get('info', '未知错误')}")
                return []

            pois = data.get("pois", [])
            results = []
            for poi in pois:
                location = poi.get("location", "")
                lng, lat = 0.0, 0.0
                if "," in location:
                    try:
                        lng, lat = map(float, location.split(","))
                    except ValueError:
                        pass

                results.append({
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": {"longitude": lng, "latitude": lat},
                    "rating": poi.get("biz_ext", {}).get("rating", "4.5"),
                    "price": poi.get("biz_ext", {}).get("lowest_price", "0"),
                    "type": poi.get("type", ""),
                    "tel": poi.get("tel", ""),
                    "photos": poi.get("photos", [])
                })
            return results
        except Exception as e:
            logger.error(f"POI 搜索失败: {e}")
            return []

    async def get_weather(self, city: str) -> List[Dict]:
        """查询城市天气预报"""
        try:
            # 先获取城市编码
            city_code = await self._get_city_code(city)
            if not city_code:
                logger.warning(f"无法获取 {city} 的城市编码")
                return []

            params = {
                "key": self.api_key,
                "city": city_code,
                "extensions": "all",
                "output": "json"
            }
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self.base_url}/weather/weatherInfo", params=params)
            data = response.json()

            if data.get("status") != "1":
                logger.warning(f"高德天气查询失败: {data.get('info', '未知错误')}")
                return []

            forecasts = data.get("forecasts", [])
            if not forecasts:
                return []

            results = []
            casts = forecasts[0].get("casts", [])
            for cast in casts:
                results.append({
                    "date": cast.get("date", ""),
                    "day_weather": cast.get("dayweather", "晴"),
                    "night_weather": cast.get("nightweather", "晴"),
                    "day_temp": cast.get("daytemp", "25"),
                    "night_temp": cast.get("nighttemp", "15"),
                    "day_wind": cast.get("daywind", "东南"),
                    "night_wind": cast.get("nightwind", "东南"),
                    "day_power": cast.get("daypower", "3"),
                    "night_power": cast.get("nightpower", "3")
                })
            return results
        except Exception as e:
            logger.error(f"天气查询失败: {e}")
            return []

    async def search_nearby_poi(self, location: str, keywords: str, offset: int = 20) -> List[Dict]:
        """周边搜索 POI（基于坐标搜索附近餐厅等）

        Args:
            location: 中心点坐标 "经度,纬度"（与高德 API 一致）
            keywords: 搜索关键词
            offset: 返回数量
        """
        try:
            params = {
                "key": self.api_key,
                "location": location,
                "keywords": keywords,
                "offset": offset,
                "output": "json",
                "extensions": "all",
                "sorttype": "distance",  # 按距离排序
            }
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self.base_url}/place/around", params=params)
            data = response.json()

            if data.get("status") != "1":
                logger.warning(f"高德周边搜索失败: {data.get('info', '未知错误')}")
                return []

            pois = data.get("pois", [])
            results = []
            for poi in pois:
                poi_loc = poi.get("location", "")
                lng, lat = 0.0, 0.0
                if "," in poi_loc:
                    try:
                        lng, lat = map(float, poi_loc.split(","))
                    except ValueError:
                        pass

                results.append({
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": {"longitude": lng, "latitude": lat},
                    "rating": poi.get("biz_ext", {}).get("rating", "4.5"),
                    "price": poi.get("biz_ext", {}).get("lowest_price", "0"),
                    "type": poi.get("type", ""),
                    "tel": poi.get("tel", ""),
                    "distance": poi.get("distance", ""),
                    "photos": poi.get("photos", [])
                })
            return results
        except Exception as e:
            logger.error(f"周边搜索失败: {e}")
            return []

    async def _get_city_code(self, city: str) -> Optional[str]:
        """获取城市编码"""
        try:
            params = {
                "key": self.api_key,
                "keywords": city,
                "subdistrict": 0,
                "output": "json"
            }
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/config/district", params=params)
            data = response.json()
            if data.get("status") == "1":
                districts = data.get("districts", [])
                if districts:
                    return districts[0].get("adcode", "")
            return None
        except Exception:
            return None
