import json
import re
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from app.models.schemas import (
    TripPlanRequest, TripPlan, Attraction, Location,
    DayPlan, WeatherInfo, Budget, Meal, Hotel
)
from app.config import get_settings
from app.services.llm_client import LLMClient
from app.services.amap_service import AmapService

logger = logging.getLogger(__name__)


# =============================================================================
# 城市餐饮参考
# =============================================================================
CITY_MEALS: Dict[str, Dict] = {
    "北京": {
        "bf": {"name": "老北京早餐（豆汁、焦圈、烧饼夹肉）", "cost": 25},
        "lc": {"name": "京味午餐（炸酱面、卤煮火烧、爆肚）", "cost": 50},
        "dn": {"name": "北京晚餐（烤鸭、涮羊肉、京酱肉丝）", "cost": 120},
    },
    "上海": {
        "bf": {"name": "上海早餐（生煎包、小笼包、豆浆）", "cost": 25},
        "lc": {"name": "本帮午餐（红烧肉、白斩鸡、糖醋排骨）", "cost": 60},
        "dn": {"name": "上海晚餐（蟹粉豆腐、葱油拌面、响油鳝糊）", "cost": 150},
    },
    "杭州": {
        "bf": {"name": "杭式早餐（片儿川、小笼包、葱包桧）", "cost": 20},
        "lc": {"name": "杭帮午餐（西湖醋鱼、东坡肉、龙井虾仁）", "cost": 80},
        "dn": {"name": "杭州晚餐（叫花鸡、宋嫂鱼羹、东坡肘子）", "cost": 100},
    },
    "拉萨": {
        "bf": {"name": "藏式早餐（酥油茶、糌粑、藏面、甜茶）", "cost": 20},
        "lc": {"name": "藏式午餐（牦牛肉火锅、酸奶、青稞饼）", "cost": 80},
        "dn": {"name": "藏式晚餐（石锅鸡、烤羊排、青稞酒）", "cost": 100},
    },
    "成都": {
        "bf": {"name": "川味早餐（担担面、红油抄手、锅盔）", "cost": 15},
        "lc": {"name": "成都午餐（麻婆豆腐、回锅肉、宫保鸡丁）", "cost": 40},
        "dn": {"name": "成都晚餐（火锅、串串香、兔头、冒菜）", "cost": 80},
    },
    "西安": {
        "bf": {"name": "陕西早餐（肉夹馍、凉皮、胡辣汤）", "cost": 15},
        "lc": {"name": "西安午餐（羊肉泡馍、Biangbiang面、水盆羊肉）", "cost": 30},
        "dn": {"name": "西安晚餐（葫芦鸡、甑糕、粉蒸肉）", "cost": 60},
    },
    "广州": {
        "bf": {"name": "广式早茶（虾饺、叉烧包、皮蛋瘦肉粥）", "cost": 60},
        "lc": {"name": "粤菜午餐（烧鹅、白切鸡、煲仔饭）", "cost": 60},
        "dn": {"name": "广州晚餐（海鲜、啫啫煲、老火汤）", "cost": 120},
    },
    "深圳": {
        "bf": {"name": "粤式早餐（肠粉、及第粥、叉烧包）", "cost": 25},
        "lc": {"name": "深圳午餐（椰子鸡、潮汕牛肉、海鲜）", "cost": 60},
        "dn": {"name": "深圳晚餐（潮汕牛肉火锅、海鲜大排档）", "cost": 100},
    },
    "重庆": {
        "bf": {"name": "重庆早餐（重庆小面、抄手、油茶）", "cost": 15},
        "lc": {"name": "重庆午餐（辣子鸡、毛血旺、水煮鱼）", "cost": 50},
        "dn": {"name": "重庆晚餐（火锅、江湖菜、烤鱼）", "cost": 80},
    },
    "武汉": {
        "bf": {"name": "武汉早餐（热干面、豆皮、面窝）", "cost": 15},
        "lc": {"name": "武汉午餐（排骨藕汤、武昌鱼、鸭脖）", "cost": 40},
        "dn": {"name": "武汉晚餐（小龙虾、烧烤、蟹脚面）", "cost": 80},
    },
    "长沙": {
        "bf": {"name": "长沙早餐（米粉、糖油粑粑、葱油饼）", "cost": 15},
        "lc": {"name": "长沙午餐（辣椒炒肉、口味虾、臭豆腐）", "cost": 40},
        "dn": {"name": "长沙晚餐（口味虾、烧烤、剁椒鱼头）", "cost": 80},
    },
    "南京": {
        "bf": {"name": "南京早餐（鸭血粉丝汤、小笼包、锅贴）", "cost": 20},
        "lc": {"name": "南京午餐（盐水鸭、狮子头、大煮干丝）", "cost": 50},
        "dn": {"name": "南京晚餐（烤鸭包、美龄粥、桂花鸭）", "cost": 80},
    },
    "苏州": {
        "bf": {"name": "苏式早餐（苏式汤面、蟹壳黄、生煎）", "cost": 20},
        "lc": {"name": "苏州午餐（松鼠桂鱼、响油鳝糊、藏书羊肉）", "cost": 60},
        "dn": {"name": "苏州晚餐（阳澄湖大闸蟹、苏帮菜、奥灶面）", "cost": 100},
    },
    "厦门": {
        "bf": {"name": "闽南早餐（沙茶面、花生汤、烧肉粽）", "cost": 20},
        "lc": {"name": "厦门午餐（海蛎煎、姜母鸭、土笋冻）", "cost": 50},
        "dn": {"name": "厦门晚餐（海鲜大排档、沙茶面、姜母鸭）", "cost": 80},
    },
    "青岛": {
        "bf": {"name": "青岛早餐（甜沫、馅饼、豆腐脑）", "cost": 15},
        "lc": {"name": "青岛午餐（辣炒蛤蜊、鲅鱼饺子、海鲜）", "cost": 60},
        "dn": {"name": "青岛晚餐（啤酒+海鲜、烧烤、墨鱼水饺）", "cost": 100},
    },
    "大理": {
        "bf": {"name": "大理早餐（饵丝、米线、乳扇、稀豆粉）", "cost": 15},
        "lc": {"name": "大理午餐（白族酸辣鱼、乳扇、生皮）", "cost": 40},
        "dn": {"name": "大理晚餐（野生菌火锅、烤乳扇、洱海鲜鱼）", "cost": 80},
    },
    "丽江": {
        "bf": {"name": "丽江早餐（丽江粑粑、鸡豆凉粉、米线）", "cost": 15},
        "lc": {"name": "丽江午餐（腊排骨火锅、纳西烤鱼、鸡豆凉粉）", "cost": 40},
        "dn": {"name": "丽江晚餐（腊排骨、黑山羊火锅、纳西烤肉）", "cost": 80},
    },
    "桂林": {
        "bf": {"name": "桂林早餐（桂林米粉、油茶、马蹄糕）", "cost": 10},
        "lc": {"name": "桂林午餐（啤酒鱼、荔浦芋扣肉、田螺酿）", "cost": 50},
        "dn": {"name": "桂林晚餐（啤酒鱼、竹筒饭、荔浦芋头）", "cost": 80},
    },
    "郑州": {
        "bf": {"name": "河南早餐（胡辣汤、油条、水煎包）", "cost": 10},
        "lc": {"name": "河南午餐（烩面、鲤鱼焙面、桶子鸡）", "cost": 30},
        "dn": {"name": "郑州晚餐（烩面、烧烤、黄河大鲤鱼）", "cost": 60},
    },
    "张家界": {
        "bf": {"name": "湘西早餐（米粉、糍粑、酸汤面）", "cost": 15},
        "lc": {"name": "湘西午餐（三下锅、腊肉、酸汤鱼）", "cost": 40},
        "dn": {"name": "湘西晚餐（土家腊肉、合菜、社饭）", "cost": 60},
    },
    "黄山": {
        "bf": {"name": "徽州早餐（徽州毛豆腐、石头粿、包袱饺）", "cost": 15},
        "lc": {"name": "徽州午餐（臭鳜鱼、毛豆腐、一品锅）", "cost": 50},
        "dn": {"name": "徽州晚餐（徽墨酥、黄山炖鸽、问政山笋）", "cost": 80},
    },
    "三亚": {
        "bf": {"name": "海南早餐（抱罗粉、清补凉、海南粉）", "cost": 20},
        "lc": {"name": "海南午餐（文昌鸡、加积鸭、和乐蟹）", "cost": 80},
        "dn": {"name": "三亚晚餐（海鲜大餐、椰子鸡、糟粕醋）", "cost": 150},
    },
    "哈尔滨": {
        "bf": {"name": "东北早餐（大列巴、红肠、豆腐脑）", "cost": 15},
        "lc": {"name": "东北午餐（锅包肉、地三鲜、小鸡炖蘑菇）", "cost": 40},
        "dn": {"name": "哈尔滨晚餐（俄式西餐、东北烧烤、铁锅炖）", "cost": 80},
    },
    "昆明": {
        "bf": {"name": "云南早餐（过桥米线、饵块、豆花米线）", "cost": 15},
        "lc": {"name": "云南午餐（汽锅鸡、野生菌、宣威火腿）", "cost": 50},
        "dn": {"name": "昆明晚餐（野生菌火锅、过桥米线、汽锅鸡）", "cost": 80},
    },
}


def _get_city_meals(city: str) -> Dict:
    if city in CITY_MEALS:
        return CITY_MEALS[city]
    return {
        "bf": {"name": f"{city}特色早餐", "cost": 20},
        "lc": {"name": f"{city}特色午餐", "cost": 50},
        "dn": {"name": f"{city}特色晚餐", "cost": 60},
    }


def _safe_int(value, default=0):
    """安全地将值转为整数，处理字符串中的°C等"""
    if isinstance(value, int):
        return value
    s = str(value).replace('°C', '').replace('℃', '').replace('°', '').strip()
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


# =============================================================================
# Agent 1: 景点搜索专家
# =============================================================================
class AttractionSearchAgent:
    """景点搜索专家 - 负责通过高德 API 搜索景点 POI"""

    def __init__(self, amap: AmapService):
        self.amap = amap
        self.name = "AttractionSearchAgent"

    async def search(self, city: str, preferences: str) -> List[Dict]:
        """搜索景点，返回按评分排序的 POI 列表

        逐个关键词搜索 + 合并去重，避免高德 API 空格分隔关键词的 AND 逻辑导致结果为 0。
        """
        logger.info(f"[{self.name}] 搜索 {city} 的 {preferences} 景点...")

        keywords_map = {
            "历史文化": ["博物馆", "古迹", "文化遗址", "寺庙", "历史"],
            "自然风光": ["公园", "景区", "山", "湖", "湿地"],
            "美食探索": ["美食街", "小吃", "夜市"],
            "购物休闲": ["购物中心", "商业街"],
            "亲子游": ["乐园", "动物园", "科技馆", "海洋馆"],
            "冒险户外": ["漂流", "攀岩", "徒步", "滑雪场"],
        }
        keywords_list = keywords_map.get(preferences, ["景点"])

        try:
            # 逐个关键词搜索，合并去重
            seen_names = set()
            all_pois = []
            for kw in keywords_list:
                pois = await self.amap.search_poi(city, kw, offset=25)
                if not pois:
                    continue
                for p in pois:
                    name = p.get("name")
                    if name and name not in seen_names and p.get("location"):
                        seen_names.add(name)
                        all_pois.append(p)

            if not all_pois:
                logger.warning(f"[{self.name}] 未找到景点")
                return []

            # 评分排序
            def get_rating(p):
                try:
                    return float(p.get("rating", 0) or 0)
                except (ValueError, TypeError):
                    return 0

            all_pois.sort(key=get_rating, reverse=True)

            logger.info(f"[{self.name}] 找到 {len(all_pois)} 个景点（评分≥4.5: {len([p for p in all_pois if get_rating(p) >= 4.5])}个）")
            return all_pois[:30]

        except Exception as e:
            logger.error(f"[{self.name}] 搜索失败: {e}")
            return []


# =============================================================================
# Agent 2: 天气查询专家
# =============================================================================
class WeatherQueryAgent:
    """天气查询专家 - 负责通过高德 API 查询天气预报"""

    def __init__(self, amap: AmapService):
        self.amap = amap
        self.name = "WeatherQueryAgent"

    async def query(self, city: str, days: int) -> List[Dict]:
        """查询未来 days 天天气预报"""
        logger.info(f"[{self.name}] 查询 {city} 未来 {days} 天天气...")

        try:
            forecasts = await self.amap.get_weather(city)
            if forecasts:
                result = forecasts[:days]
                logger.info(f"[{self.name}] 获取到 {len(result)} 天天气")
                return result
            else:
                logger.warning(f"[{self.name}] 未获取到天气数据")
                return []
        except Exception as e:
            logger.error(f"[{self.name}] 查询失败: {e}")
            return []


# =============================================================================
# Agent 3: 酒店推荐专家
# =============================================================================
class HotelSearchAgent:
    """酒店推荐专家 - 负责通过高德 API 搜索酒店 POI"""

    def __init__(self, amap: AmapService):
        self.amap = amap
        self.name = "HotelSearchAgent"

    async def search(self, city: str, accommodation: str) -> List[Dict]:
        """搜索酒店，返回按评分排序的 POI 列表"""
        logger.info(f"[{self.name}] 搜索 {city} 的 {accommodation}...")

        keywords_map = {
            "经济型酒店": "快捷酒店 经济型",
            "舒适型酒店": "商务酒店 全季 亚朵",
            "豪华酒店": "五星级酒店 希尔顿 万豪",
            "民宿": "民宿 客栈",
            "青年旅社": "青年旅舍",
        }
        keywords = keywords_map.get(accommodation, "酒店")

        try:
            pois = await self.amap.search_poi(city, keywords, offset=30)
            if not pois:
                logger.warning(f"[{self.name}] 未找到酒店")
                return []

            valid = [p for p in pois if p.get("name") and p.get("address")]

            def get_rating(p):
                try:
                    return float(p.get("rating", 0) or 0)
                except (ValueError, TypeError):
                    return 0

            valid.sort(key=get_rating, reverse=True)
            logger.info(f"[{self.name}] 找到 {len(valid)} 个酒店")
            return valid[:15]

        except Exception as e:
            logger.error(f"[{self.name}] 搜索失败: {e}")
            return []


# =============================================================================
# Agent 4: 餐厅搜索专家
# =============================================================================
class RestaurantSearchAgent:
    """餐厅搜索专家 - 负责通过高德 API 搜索餐厅 POI"""

    def __init__(self, amap: AmapService):
        self.amap = amap
        self.name = "RestaurantSearchAgent"

    async def search(self, city: str) -> List[Dict]:
        """搜索城市餐厅"""
        logger.info(f"[{self.name}] 搜索 {city} 的餐厅...")

        try:
            pois = await self.amap.search_poi(city, "餐厅 美食 特色菜", offset=30)
            if not pois:
                return []

            valid = [p for p in pois if p.get("name")]

            def get_rating(p):
                try:
                    return float(p.get("rating", 0) or 0)
                except (ValueError, TypeError):
                    return 0

            valid.sort(key=get_rating, reverse=True)
            logger.info(f"[{self.name}] 找到 {len(valid)} 个餐厅")
            return valid[:20]

        except Exception as e:
            logger.error(f"[{self.name}] 搜索失败: {e}")
            return []


# =============================================================================
# Agent 5: 门票价格推断专家
# =============================================================================
class TicketPriceAgent:
    """门票价格推断专家 - 负责通过 LLM 推断景点门票价格"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.name = "TicketPriceAgent"

    async def infer_prices(self, city: str, attractions: List[Dict]) -> List[Dict]:
        """推断景点门票价格"""
        if not attractions:
            return []

        logger.info(f"[{self.name}] 推断 {len(attractions)} 个景点门票价格...")

        attr_lines = []
        for i, p in enumerate(attractions, 1):
            attr_lines.append(f"{i}. {p['name']} - {city}")
        attr_text = "\n".join(attr_lines)

        system_prompt = f"""你是旅游行业专家，熟悉中国各地景点门票价格。
请根据景点名称和所在城市，推断每个景点的成人门票价格（人民币/元）。

**规则：**
1. 只返回 JSON 数组，每个元素包含 "index"、"price"
2. 价格必须是整数（0 表示免费）
3. 不确定的景点写 0
4. 不要编造，只写你有信心的价格

**输出格式：**
[{{"index": 1, "price": 60}}, {{"index": 2, "price": 0}}]
"""

        user_prompt = f"""请推断以下 {city} 景点的门票价格：

{attr_text}

返回纯 JSON 数组，不要 Markdown 代码块。"""

        try:
            response = await self.llm.generate(system_prompt, user_prompt, temperature=0.1)

            # 解析 JSON
            prices = []
            try:
                prices = json.loads(response.strip())
            except json.JSONDecodeError:
                start = response.find('[')
                end = response.rfind(']')
                if start >= 0 and end > start:
                    prices = json.loads(response[start:end+1])

            if isinstance(prices, list):
                logger.info(f"[{self.name}] 成功推断 {len(prices)} 个价格")
                for p in prices:
                    idx = p.get("index", 0)
                    price = p.get("price", 0)
                    if 1 <= idx <= len(attractions):
                        attractions[idx - 1]["_ticket"] = int(price)

            for p in attractions:
                if "_ticket" not in p:
                    p["_ticket"] = 0

            return attractions

        except Exception as e:
            logger.error(f"[{self.name}] 推断失败: {e}")
            for p in attractions:
                p["_ticket"] = 0
            return attractions


# =============================================================================
# Agent 6: 酒店价格推断专家
# =============================================================================
class HotelPriceAgent:
    """酒店价格推断专家 - 负责通过 LLM 推断酒店每晚价格"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.name = "HotelPriceAgent"

    async def infer_prices(self, city: str, accommodation: str, hotels: List[Dict]) -> List[Dict]:
        """推断酒店每晚价格

        Args:
            city: 城市名
            accommodation: 住宿类型
            hotels: 酒店列表，每个酒店有 name/address/rating 等字段

        Returns:
            酒店列表，每个酒店新增 "_price" 字段（预估每晚价格）
        """
        if not hotels:
            return []

        logger.info(f"[{self.name}] 推断 {len(hotels)} 个酒店价格...")

        hotel_lines = []
        for i, h in enumerate(hotels, 1):
            rating = h.get("rating", "N/A")
            hotel_lines.append(f"{i}. {h['name']} - {city} - 评分：{rating}")
        hotel_text = "\n".join(hotel_lines)

        system_prompt = """你是酒店行业专家，熟悉中国各地酒店价格。
请根据酒店名称、所在城市和住宿类型，推断每个酒店的大致每晚价格（人民币/元）。

**规则：**
1. 只返回 JSON 数组，每个元素包含 "index"、"price"
2. 价格必须是整数，代表每晚价格（元）
3. 价格应基于酒店品牌、星级、城市消费水平合理推断
4. 不确定的酒店根据城市和住宿类型估算均价

**参考价格范围：**
- 经济型/快捷酒店：100-300元/晚
- 舒适型/商务酒店：300-600元/晚
- 豪华/五星级酒店：600-2000元/晚
- 民宿/客栈：150-500元/晚

**输出格式：**
[{"index": 1, "price": 350}, {"index": 2, "price": 600}]
"""

        user_prompt = f"""请推断以下 {city} 的 {accommodation} 酒店每晚价格：

{hotel_text}

返回纯 JSON 数组，不要 Markdown 代码块。"""

        try:
            response = await self.llm.generate(system_prompt, user_prompt, temperature=0.1)

            # 解析 JSON
            prices = []
            try:
                prices = json.loads(response.strip())
            except json.JSONDecodeError:
                start = response.find('[')
                end = response.rfind(']')
                if start >= 0 and end > start:
                    prices = json.loads(response[start:end+1])

            if isinstance(prices, list):
                logger.info(f"[{self.name}] 成功推断 {len(prices)} 个酒店价格")
                for p in prices:
                    idx = p.get("index", 0)
                    price = p.get("price", 0)
                    if 1 <= idx <= len(hotels):
                        hotels[idx - 1]["_price"] = int(price)

            for h in hotels:
                if "_price" not in h:
                    h["_price"] = self._default_price(accommodation)

            return hotels

        except Exception as e:
            logger.error(f"[{self.name}] 推断失败: {e}")
            for h in hotels:
                h["_price"] = self._default_price(accommodation)
            return hotels

    @staticmethod
    def _default_price(accommodation: str) -> int:
        """LLM 不可用时的通用价格"""
        if "豪华" in accommodation:
            return 800
        elif "经济" in accommodation:
            return 200
        elif "民宿" in accommodation:
            return 300
        else:
            return 400


# =============================================================================
# Agent 7: 行程规划专家（主协调器）
# =============================================================================
class TripPlannerAgent:
    """行程规划专家 - 主协调器

    协调 6 个子 Agent 完成旅行规划：
    1. AttractionSearchAgent - 搜索景点
    2. WeatherQueryAgent - 查询天气
    3. HotelSearchAgent - 搜索酒店
    4. RestaurantSearchAgent - 搜索城市高评分餐厅（参考）
    5. TicketPriceAgent - 推断门票价格
    6. HotelPriceAgent - 推断酒店价格
    7. 自身整合所有信息生成完整行程
    """

    def __init__(self):
        self.settings = get_settings()
        self.use_llm = bool(self.settings.llm_api_key and self.settings.llm_api_key.strip())
        self.use_amap = bool(self.settings.amap_api_key and self.settings.amap_api_key.strip())

        # 初始化服务
        self.llm: Optional[LLMClient] = None
        self.amap: Optional[AmapService] = None

        if self.use_llm:
            self.llm = LLMClient(
                base_url=self.settings.llm_base_url or "https://api.deepseek.com/v1",
                api_key=self.settings.llm_api_key,
                model=self.settings.llm_model or "deepseek-chat",
                timeout=180
            )
            logger.info(f"✅ LLM 已连接：{self.settings.llm_model}")

        if self.use_amap:
            self.amap = AmapService(self.settings.amap_api_key)
            logger.info("✅ 高德地图服务已连接")
        else:
            logger.error("❌ 未配置高德地图 API Key")

        # 创建子 Agent
        if self.amap:
            self.attraction_agent = AttractionSearchAgent(self.amap)
            self.weather_agent = WeatherQueryAgent(self.amap)
            self.hotel_agent = HotelSearchAgent(self.amap)
            self.restaurant_agent = RestaurantSearchAgent(self.amap)
        else:
            self.attraction_agent = None
            self.weather_agent = None
            self.hotel_agent = None
            self.restaurant_agent = None

        if self.llm:
            self.ticket_agent = TicketPriceAgent(self.llm)
            self.hotel_price_agent = HotelPriceAgent(self.llm)
        else:
            self.ticket_agent = None
            self.hotel_price_agent = None

    async def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        """执行旅行规划 - 协调各 Agent 完成"""
        city = request.city
        days_count = request.days

        logger.info(f"🚀 [TripPlannerAgent] 开始规划 {city} {days_count}天行程")
        logger.info(f"   服务状态: LLM={'✅' if self.use_llm else '❌'}  高德={'✅' if self.use_amap else '❌'}")

        # === Step 1: 景点搜索 Agent ===
        attractions_raw = []
        if self.attraction_agent:
            attractions_raw = await self.attraction_agent.search(city, request.preferences)

        # === Step 2: 天气查询 Agent ===
        weather_data = []
        if self.weather_agent:
            weather_data = await self.weather_agent.query(city, days_count)

        # === Step 3: 酒店搜索 Agent ===
        hotels_raw = []
        if self.hotel_agent:
            hotels_raw = await self.hotel_agent.search(city, request.accommodation)

        # === Step 3.5: 酒店价格推断 Agent ===
        if self.hotel_price_agent and hotels_raw:
            hotels_raw = await self.hotel_price_agent.infer_prices(city, request.accommodation, hotels_raw)

        # === Step 4: 餐厅搜索 Agent（全城搜索，作为参考）===
        restaurants_raw = []
        if self.restaurant_agent:
            restaurants_raw = await self.restaurant_agent.search(city)

        # === Step 4.5: 基于景点位置的周边餐厅搜索 ===
        nearby_restaurants = {}
        if self.amap and attractions_raw:
            nearby_restaurants = await self._search_nearby_restaurants(city, attractions_raw)

        # === Step 5: 门票价格推断 Agent ===
        if self.ticket_agent and attractions_raw:
            attractions_raw = await self.ticket_agent.infer_prices(city, attractions_raw)

        # === Step 6: 行程规划 Agent 整合生成行程 ===
        if self.use_llm and self.llm:
            try:
                logger.info("🤖 [TripPlannerAgent] 调用 LLM 生成完整行程...")
                trip_plan = await self._plan_with_llm(
                    request, attractions_raw, weather_data, hotels_raw, restaurants_raw, nearby_restaurants
                )
                logger.info("✅ [TripPlannerAgent] LLM 规划完成")
                return trip_plan
            except Exception as e:
                logger.error(f"❌ [TripPlannerAgent] LLM 规划失败: {e}")
                import traceback
                logger.error(traceback.format_exc())

        # === Step 7: 兜底构建 ===
        logger.info("📝 [TripPlannerAgent] 兜底构建行程")
        return self._fallback_build(request, attractions_raw, weather_data, hotels_raw, nearby_restaurants)

    async def _search_nearby_restaurants(self, city: str, attractions: List[Dict]) -> Dict[str, List[Dict]]:
        """基于景点位置搜索附近餐厅

        取评分最高的几个景点的坐标为中心点，搜索周边餐厅。
        返回格式: {"景点名": [餐厅列表], ...}
        """
        # 选取评分最高的景点作为搜索中心点（最多取 5 个）
        def get_rating(p):
            try:
                return float(p.get("rating", 0) or 0)
            except (ValueError, TypeError):
                return 0

        sorted_attractions = sorted(attractions, key=get_rating, reverse=True)
        top_attractions = sorted_attractions[:5]

        result = {}
        seen_names = set()  # 全局去重

        for attr in top_attractions:
            loc = attr.get("location", {})
            lng = loc.get("longitude", 0)
            lat = loc.get("latitude", 0)
            if not lng or not lat:
                continue

            location_str = f"{lng},{lat}"
            attr_name = attr.get("name", "")

            try:
                pois = await self.amap.search_nearby_poi(location_str, "餐厅 美食", offset=10)
                restaurants = []
                for p in pois:
                    name = p.get("name")
                    if name and name not in seen_names:
                        seen_names.add(name)
                        restaurants.append(p)
                if restaurants:
                    result[attr_name] = restaurants
                    logger.info(f"[TripPlannerAgent] 搜索到 {attr_name} 附近 {len(restaurants)} 家餐厅")
            except Exception as e:
                logger.error(f"[TripPlannerAgent] 搜索 {attr_name} 附近餐厅失败: {e}")

        if not result:
            logger.warning(f"[TripPlannerAgent] 未能搜索到 {city} 的附近餐厅")

        return result

    # ---- LLM 规划 ----

    async def _plan_with_llm(self, request, attractions, weather_data, hotels_raw, restaurants_raw, nearby_restaurants) -> TripPlan:
        if not self.llm:
            raise RuntimeError("LLM 未初始化")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            request, attractions, weather_data, hotels_raw, restaurants_raw, nearby_restaurants
        )

        response = await self.llm.generate(system_prompt, user_prompt, temperature=0.3)
        logger.info(f"📨 [TripPlannerAgent] LLM 返回 {len(response)} 字符")

        trip_plan = self._parse_llm_json(response)
        if trip_plan:
            return trip_plan
        raise RuntimeError("LLM 返回无法解析为有效行程")

    def _build_system_prompt(self) -> str:
        return """你是资深旅行规划师，有15年从业经验。请根据高德地图提供的真实 POI 数据，生成严格的 JSON 格式旅行计划。

**数据来源说明：**
- 景点名称、地址、坐标、评分：来自高德地图 API（真实数据）
- 门票价格：来自旅游知识库推断的公开票价
- 酒店名称、地址：来自高德地图 API（真实数据）
- 酒店价格：来自 LLM 推断的合理价格
- 天气：来自高德地图 API（真实预报数据）
- 餐饮：来自景点附近搜索的真实餐厅数据

**规划原则：**
1. 每天安排 3-4 个景点，上午2个、下午1-2个
2. 景点按地理位置聚类，避免全天跨城奔波
3. 门票价格使用提供的价格数据，不得改动
4. 酒店使用真实名称和推断价格，多天行程可以更换
5. 餐饮必须使用提供的真实餐厅名称，标注推荐菜品和预估费用
6. 优先选择景点附近的餐厅，参考"景点附近餐厅参考"数据
7. 预算精确计算

**输出 JSON 格式：**
{
  "city": "城市名",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "上午：景点A、景点B → 午餐 → 下午：景点C",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {"name": "真实酒店名", "address": "真实地址", "estimated_cost": 400},
      "attractions": [
        {"name": "真实景点名", "address": "真实地址", "location": {"longitude": 116.0, "latitude": 39.9},
         "visit_duration": 120, "description": "", "ticket_price": 60, "rating": 4.9}
      ],
      "meals": [
        {"type": "breakfast", "name": "真实餐厅名（推荐菜品1、菜品2）", "estimated_cost": 25},
        {"type": "lunch", "name": "真实餐厅名（推荐菜品1、菜品2）", "estimated_cost": 50},
        {"type": "dinner", "name": "真实餐厅名（推荐菜品1、菜品2）", "estimated_cost": 100}
      ]
    }
  ],
  "weather_info": [...],
  "overall_suggestions": "行程建议",
  "budget": {"total_attractions": 0, "total_hotels": 0, "total_meals": 0, "total_transportation": 0, "total": 0}
}
"""

    def _build_user_prompt(self, request, attractions, weather_data, hotels_raw, restaurants_raw, nearby_restaurants) -> str:
        attr_lines = []
        for i, p in enumerate(attractions[:25], 1):
            loc = p.get("location", {})
            ticket = p.get("_ticket", 0)
            attr_lines.append(
                f"{i}. {p['name']} - {p['address']} - "
                f"坐标：{loc.get('longitude', 0):.4f},{loc.get('latitude', 0):.4f} - "
                f"评分：{p.get('rating', 'N/A')} - 门票：{ticket}元"
            )
        attr_text = "\n".join(attr_lines) if attr_lines else "未获取到景点数据"

        hotel_lines = []
        for i, p in enumerate(hotels_raw[:12], 1):
            price = p.get("_price", "N/A")
            hotel_lines.append(
                f"{i}. {p['name']} - {p['address']} - 评分：{p.get('rating', 'N/A')} - 推断价格：{price}元/晚"
            )
        hotel_text = "\n".join(hotel_lines) if hotel_lines else "未获取到酒店数据"

        rest_lines = []
        for i, p in enumerate(restaurants_raw[:8], 1):
            rest_lines.append(f"{i}. {p['name']} - 评分：{p.get('rating', 'N/A')}")
        rest_text = "\n".join(rest_lines) if rest_lines else "未获取到餐厅数据"

        # 景点附近餐厅数据
        nearby_lines = []
        for attr_name, rests in nearby_restaurants.items():
            rest_items = []
            for r in rests[:5]:
                dist = r.get("distance", "")
                dist_info = f"（距{attr_name}{dist}米）" if dist else f"（{attr_name}附近）"
                rest_items.append(f"    - {r['name']} - 评分：{r.get('rating', 'N/A')}{dist_info}")
            if rest_items:
                nearby_lines.append(f"  {attr_name}附近：\n" + "\n".join(rest_items))
        nearby_text = "\n".join(nearby_lines) if nearby_lines else "未获取到景点附近餐厅数据"

        weather_lines = []
        for i, w in enumerate(weather_data, 1):
            weather_lines.append(
                f"第{i}天({w.get('date', 'N/A')}): "
                f"白天{w.get('day_weather', 'N/A')} {w.get('day_temp', 'N/A')}°C, "
                f"夜间{w.get('night_weather', 'N/A')} {w.get('night_temp', 'N/A')}°C"
            )
        weather_text = "\n".join(weather_lines) if weather_lines else "未获取到天气数据"

        meals = _get_city_meals(request.city)
        meal_ref = f"""早餐参考：{meals['bf']['name']}（约{meals['bf']['cost']}元）
午餐参考：{meals['lc']['name']}（约{meals['lc']['cost']}元）
晚餐参考：{meals['dn']['name']}（约{meals['dn']['cost']}元）"""

        return f"""请为 {request.city} 规划 {request.days} 天旅行计划。

**用户要求：**
- 日期：{request.start_date} 至 {request.end_date}
- 偏好：{request.preferences}
- 预算：{request.budget}
- 交通：{request.transportation}
- 住宿：{request.accommodation}

**真实景点数据（来自高德地图 + 门票价格推断）：**
{attr_text}

**真实酒店数据（来自高德地图 + LLM价格推断）：**
{hotel_text}

**热门餐厅参考（来自高德地图全城搜索）：**
{rest_text}

**景点附近餐厅参考（来自高德地图周边搜索，优先使用）：**
{nearby_text}

**天气预报（来自高德地图）：**
{weather_text}

**城市餐饮参考（菜品和价格参考）：**
{meal_ref}

**要求：**
1. 每天安排 3-4 个景点，按地理位置相近原则分组
2. 门票价格严格使用提供的数值
3. 酒店选择真实名称，使用提供的推断价格，多天可安排不同酒店
4. 餐饮必须使用景点附近餐厅参考中的真实餐厅名称，在括号内标注推荐菜品
5. 如果附近餐厅数据不足，可以参考城市餐饮参考中的菜品来标注推荐菜品
6. 预算精确计算
7. 返回纯 JSON
"""

    def _parse_llm_json(self, response: str) -> Optional[TripPlan]:
        # 1. 尝试提取 markdown 代码块中的 JSON
        m = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if m:
            result = self._try_parse_json(m.group(1))
            if result:
                return result

        # 2. 尝试无语言标记的代码块
        m = re.search(r'```\s*\n(.*?)\n```', response, re.DOTALL)
        if m:
            result = self._try_parse_json(m.group(1))
            if result:
                return result

        # 3. 从响应中提取最外层 { ... }
        start = response.find('{')
        end = response.rfind('}')
        if start >= 0 and end > start:
            # 用括号平衡找到真正的顶层 JSON 边界
            depth = 0
            json_end = -1
            for i in range(start, len(response)):
                if response[i] == '{':
                    depth += 1
                elif response[i] == '}':
                    depth -= 1
                    if depth == 0:
                        json_end = i
                        break
            if json_end > start:
                result = self._try_parse_json(response[start:json_end+1])
                if result:
                    return result

        # 4. 整段尝试
        result = self._try_parse_json(response.strip())
        if result:
            return result

        logger.error(f"❌ JSON 解析失败。LLM 返回:\n{response[:800]}")
        return None

    def _try_parse_json(self, text: str) -> Optional[TripPlan]:
        """尝试将文本解析为 TripPlan，先修复再验证"""
        try:
            data = json.loads(text)
            if "city" in data and "days" in data:
                # 始终先修复再验证，避免 LLM 字段偏差
                data = self._repair_json_data(data)
                return TripPlan.model_validate(data)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON 语法错误: {e}")
        except Exception as e:
            logger.warning(f"TripPlan 修复+验证失败: {e}")
        return None

    def _repair_json_data(self, data: dict) -> dict:
        """修复 LLM 返回 JSON 中的常见字段问题"""
        # LLM 常用的天气字段名映射到 Pydantic 模型字段名
        weather_field_map = {
            "day_temperature": "day_temp",
            "night_temperature": "night_temp",
            "day_wind": "wind_direction",
            "night_wind": "wind_direction",
            "day_wind_power": "wind_power",
            "night_wind_power": "wind_power",
            "wind": "wind_direction",
            "wind_level": "wind_power",
        }
        # 修复 weather_info：LLM 可能返回字符串而非对象
        repaired_weather = []
        for w in data.get("weather_info", []):
            if isinstance(w, str):
                # LLM 把天气写成了字符串，跳过，由后续兜底构建补充
                continue
            if not isinstance(w, dict):
                continue
            # 字段名重映射
            for src, dst in weather_field_map.items():
                if src in w and dst not in w:
                    w[dst] = w.pop(src)
            # 补充缺失的天气字段
            w.setdefault("day_weather", "晴")
            w.setdefault("night_weather", "晴")
            w.setdefault("day_temp", 25)
            w.setdefault("night_temp", 15)
            w.setdefault("wind_direction", "东南")
            w.setdefault("wind_power", "3级")
            repaired_weather.append(w)
        data["weather_info"] = repaired_weather

        # 修复 days 中的字段
        for day in data.get("days", []):
            hotel = day.get("hotel")
            if hotel and isinstance(hotel, dict):
                if "estimated_cost" in hotel and not isinstance(hotel["estimated_cost"], int):
                    try:
                        hotel["estimated_cost"] = int(float(str(hotel["estimated_cost"])))
                    except (ValueError, TypeError):
                        hotel["estimated_cost"] = 0
                        hotel["estimated_cost"] = 0

            # 修复 attractions
            for attr in day.get("attractions", []):
                # ticket_price 必须是 int
                if "ticket_price" in attr and not isinstance(attr["ticket_price"], int):
                    try:
                        attr["ticket_price"] = int(float(str(attr["ticket_price"])))
                    except (ValueError, TypeError):
                        attr["ticket_price"] = 0
                # visit_duration 必须是 int
                if "visit_duration" in attr and not isinstance(attr["visit_duration"], int):
                    try:
                        attr["visit_duration"] = int(float(str(attr["visit_duration"])))
                    except (ValueError, TypeError):
                        attr["visit_duration"] = 120
                # rating 可选，但必须是 float 或 null
                if "rating" in attr and attr["rating"] is not None:
                    try:
                        attr["rating"] = float(attr["rating"])
                    except (ValueError, TypeError):
                        attr["rating"] = None
                # location 必须存在且包含 longitude/latitude 两个正确字段
                loc = attr.get("location")
                if not loc or not isinstance(loc, dict):
                    attr["location"] = {"longitude": 0, "latitude": 0}
                else:
                    # 修复 LLM 生成的异常 location 格式
                    # 如 {"longitude": 126.6387, "45.7514": 45.7514} → 提取数值
                    if "longitude" not in loc or "latitude" not in loc:
                        lng, lat = 0.0, 0.0
                        values = []
                        for k, v in loc.items():
                            try:
                                values.append(float(v) if not isinstance(v, (int, float)) else float(v))
                            except (ValueError, TypeError):
                                pass
                        if len(values) >= 2:
                            lng, lat = values[0], values[1]
                        elif len(values) == 1:
                            lng = values[0]
                        loc.clear()
                        loc["longitude"] = lng
                        loc["latitude"] = lat
                    else:
                        for key in ["longitude", "latitude"]:
                            if key in loc and not isinstance(loc[key], (int, float)):
                                try:
                                    loc[key] = float(loc[key])
                                except (ValueError, TypeError):
                                    loc[key] = 0.0

            # 修复 meals
            for meal in day.get("meals", []):
                if "estimated_cost" in meal and not isinstance(meal["estimated_cost"], int):
                    try:
                        meal["estimated_cost"] = int(float(str(meal["estimated_cost"])))
                    except (ValueError, TypeError):
                        meal["estimated_cost"] = 0

        # 修复 weather_info
        for w in data.get("weather_info", []):
            for key in ["day_temp", "night_temp"]:
                if key in w and not isinstance(w[key], int):
                    try:
                        w[key] = int(float(str(w[key]).replace('°C', '').replace('℃', '').replace('°', '').strip()))
                    except (ValueError, TypeError):
                        w[key] = 25

        # 修复 budget
        budget = data.get("budget")
        if budget and isinstance(budget, dict):
            for key in ["total_attractions", "total_hotels", "total_meals", "total_transportation", "total"]:
                if key in budget and not isinstance(budget[key], int):
                    try:
                        budget[key] = int(float(str(budget[key])))
                    except (ValueError, TypeError):
                        budget[key] = 0

        return data

    # ---- 兜底构建 ----

    def _fallback_build(self, request, attractions_raw, weather_data, hotels_raw, nearby_restaurants=None) -> TripPlan:
        city = request.city
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        days_count = request.days

        if nearby_restaurants is None:
            nearby_restaurants = {}

        # 酒店价格：优先使用推断价格，否则用通用计算
        def get_hotel_price(hotel_data, accommodation):
            if "_price" in hotel_data:
                return hotel_data["_price"]
            if "豪华" in accommodation:
                return 800
            elif "经济" in accommodation:
                return 200
            elif "民宿" in accommodation:
                return 300
            else:
                return 400

        # 收集所有附近餐厅，按距离排序（兜底时从所有景点附近餐厅中选取）
        all_nearby_restaurants = []
        seen_rest_names = set()
        for attr_name, rests in nearby_restaurants.items():
            for r in rests:
                name = r.get("name")
                if name and name not in seen_rest_names:
                    seen_rest_names.add(name)
                    all_nearby_restaurants.append(r)

        # 按评分排序附近餐厅
        def get_rating(p):
            try:
                return float(p.get("rating", 0) or 0)
            except (ValueError, TypeError):
                return 0
        all_nearby_restaurants.sort(key=get_rating, reverse=True)

        # 城市餐饮参考（作为 LLM 不可用时的菜品/价格参考）
        meals_data = _get_city_meals(city)

        transport_map = {"公共": 30, "自驾": 150, "出租": 200, "步行": 10}
        tk = "公共" if "公共" in request.transportation else "自驾" if "自驾" in request.transportation else "出租" if "出租" in request.transportation else "步行"
        tc = transport_map.get(tk, 50)

        days_plan = []
        weather_info = []
        attraction_idx = 0
        total_attractions = len(attractions_raw)
        hotel_idx = 0
        total_hotels = len(hotels_raw)
        restaurant_idx = 0
        total_nearby_restaurants = len(all_nearby_restaurants)

        for i in range(days_count):
            day_date = (start + timedelta(days=i)).strftime("%Y-%m-%d")

            day_attractions = []
            num_per_day = min(4, max(2, total_attractions // days_count + 1))
            if total_attractions == 0:
                num_per_day = 0

            for _ in range(num_per_day):
                if attraction_idx >= total_attractions:
                    break
                p = attractions_raw[attraction_idx]
                attraction_idx += 1

                loc = p.get("location", {})
                try:
                    lng = float(loc.get("longitude", 0)) if loc else 0
                    lat = float(loc.get("latitude", 0)) if loc else 0
                except (ValueError, TypeError):
                    lng, lat = 0, 0

                try:
                    rating = float(p.get("rating", 0)) if p.get("rating") else None
                except (ValueError, TypeError):
                    rating = None

                ticket = p.get("_ticket", 0)

                day_attractions.append(Attraction(
                    name=p.get("name", "景点"),
                    address=p.get("address", ""),
                    location=Location(longitude=lng, latitude=lat),
                    visit_duration=120,
                    description="",
                    ticket_price=ticket,
                    rating=rating,
                    category="景点"
                ))

            if weather_data and i < len(weather_data):
                w = weather_data[i]
                weather_info.append(WeatherInfo(
                    date=w.get("date", day_date),
                    day_weather=w.get("day_weather", "晴"),
                    night_weather=w.get("night_weather", "晴"),
                    day_temp=_safe_int(w.get("day_temp", 25), 25),
                    night_temp=_safe_int(w.get("night_temp", 15), 15),
                    wind_direction=w.get("day_wind", "东南"),
                    wind_power=f"{w.get('day_power', '3')}级"
                ))
            else:
                weather_info.append(WeatherInfo(
                    date=day_date, day_weather="晴", night_weather="晴",
                    day_temp=25, night_temp=15, wind_direction="东南", wind_power="3级"
                ))

            if total_hotels > 0:
                h = hotels_raw[hotel_idx % total_hotels]
                hotel_idx += 1
                hotel_price = get_hotel_price(h, request.accommodation)
                day_hotel = Hotel(
                    name=h.get("name", f"{city}酒店"),
                    address=h.get("address", f"{city}"),
                    estimated_cost=hotel_price
                )
            else:
                hotel_price = get_hotel_price({}, request.accommodation)
                day_hotel = Hotel(
                    name=f"{city}{request.accommodation}",
                    address=f"{city}市区",
                    estimated_cost=hotel_price
                )

            # 餐饮：优先使用附近搜索到的真实餐厅
            day_meals = []
            meal_types = [
                ("breakfast", meals_data["bf"]["cost"]),
                ("lunch", meals_data["lc"]["cost"]),
                ("dinner", meals_data["dn"]["cost"]),
            ]
            for meal_type, default_cost in meal_types:
                if restaurant_idx < total_nearby_restaurants:
                    r = all_nearby_restaurants[restaurant_idx]
                    restaurant_idx += 1
                    # 使用真实餐厅名 + 城市参考菜品
                    city_ref = meals_data[{"breakfast": "bf", "lunch": "lc", "dinner": "dn"}[meal_type]]
                    meal_name = f"{r['name']}（{city_ref['name'].split('（')[0]}）"
                    # 尝试从高德数据获取价格，否则用默认
                    try:
                        meal_cost = int(float(r.get("price", 0) or 0)) or default_cost
                    except (ValueError, TypeError):
                        meal_cost = default_cost
                    day_meals.append(Meal(
                        type=meal_type,
                        name=meal_name,
                        address=r.get("address", ""),
                        estimated_cost=meal_cost
                    ))
                else:
                    # 附近餐厅用完，回退到城市餐饮参考
                    key = {"breakfast": "bf", "lunch": "lc", "dinner": "dn"}[meal_type]
                    day_meals.append(Meal(
                        type=meal_type,
                        name=meals_data[key]["name"],
                        estimated_cost=meals_data[key]["cost"]
                    ))

            attr_names = [a.name for a in day_attractions]
            if len(attr_names) >= 3:
                desc = f"第{i+1}天：上午游览{attr_names[0]}、{attr_names[1]}，下午游览{attr_names[2]}"
                if len(attr_names) > 3:
                    desc += f"、{attr_names[3]}"
            elif len(attr_names) == 2:
                desc = f"第{i+1}天：上午{attr_names[0]}，下午{attr_names[1]}"
            elif len(attr_names) == 1:
                desc = f"第{i+1}天：游览{attr_names[0]}"
            else:
                desc = f"第{i+1}天：市区自由活动"

            days_plan.append(DayPlan(
                date=day_date,
                day_index=i,
                description=desc,
                transportation=request.transportation,
                accommodation=request.accommodation,
                hotel=day_hotel,
                attractions=day_attractions,
                meals=day_meals
            ))

        total_attraction_price = sum(a.ticket_price for d in days_plan for a in d.attractions)
        hotel_total = sum(d.hotel.estimated_cost for d in days_plan)
        meal_total = sum(m.estimated_cost for d in days_plan for m in d.meals)
        transport_total = tc * days_count

        budget = Budget(
            total_attractions=total_attraction_price,
            total_hotels=hotel_total,
            total_meals=meal_total,
            total_transportation=transport_total,
            total=total_attraction_price + hotel_total + meal_total + transport_total
        )

        num_used = len(set(a.name for d in days_plan for a in d.attractions))
        suggestions = f"{request.start_date}出发，共安排 {num_used} 个景点。"
        if total_attractions == 0:
            suggestions += "（未能获取到景点数据）"
        suggestions += f" 住宿{request.accommodation}，交通：{request.transportation}。"

        return TripPlan(
            city=city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days_plan,
            weather_info=weather_info,
            overall_suggestions=suggestions,
            budget=budget
        )
