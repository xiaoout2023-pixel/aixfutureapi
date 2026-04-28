import httpx
import json
import re
import logging
import time
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

LEADERBOARD_CATEGORIES = {
    "general_overall": {"name": "总排行榜", "group": "general", "url": "https://www.superclueai.com/generalpage"},
    "general_reasoning": {"name": "推理模型总排行榜", "group": "general", "url": "https://www.superclueai.com/generalpage"},
    "general_base": {"name": "基础模型总排行榜", "group": "general", "url": "https://www.superclueai.com/generalpage"},
    "general_reasoning_task": {"name": "推理任务总排行榜", "group": "general", "url": "https://www.superclueai.com/generalpage"},
    "general_opensource": {"name": "开源排行榜", "group": "general", "url": "https://www.superclueai.com/generalpage"},
    "multimodal_vlm": {"name": "SuperCLUE-VLM 多模态视觉语言模型", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_image": {"name": "SuperCLUE-Image 文生图", "group": "multimodal", "url": "https://www.superclueai.com/arena?tab=t2iboard&type=image"},
    "multimodal_comicshorts": {"name": "SuperCLUE-ComicShorts AI漫剧大模型", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_r2v": {"name": "SuperCLUE-R2V 参考生视频", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_i2v": {"name": "SuperCLUE-I2V 图生视频模型", "group": "multimodal", "url": "https://www.superclueai.com/arena?tab=t2iboard&type=i2v"},
    "multimodal_edit": {"name": "SuperCLUE-Edit 图像编辑", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_t2v": {"name": "SuperCLUE-T2V 文生视频", "group": "multimodal", "url": "https://www.superclueai.com/arena?tab=t2iboard&type=video"},
    "multimodal_world": {"name": "SuperCLUE-World 世界模型", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_voice_av": {"name": "SuperCLUE-Voice 实时音视频", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_voice_chat": {"name": "SuperCLUE-Voice 实时语音交互", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_tts": {"name": "SuperCLUE-TTS 语音合成", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_v": {"name": "SuperCLUE-V 多模态理解", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
    "multimodal_vlr": {"name": "SuperCLUE-VLR 视觉推理", "group": "multimodal", "url": "https://www.superclueai.com/multimodalpage"},
}


class SuperCLUECrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="superclue", base_url="https://www.superclueai.com")

    async def fetch_page_with_render(self, url: str) -> str:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    logger.info(f"Fetched {url}, length: {len(response.text)}")
                    return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return ""

    def parse_html_table(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        results = []

        for table in tables:
            headers = []
            header_row = table.find("tr")
            if header_row:
                ths = header_row.find_all(["th", "td"])
                headers = [th.get_text(strip=True) for th in ths]

            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                row_data = {}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    row_data[key] = cell.get_text(strip=True)
                if row_data:
                    results.append(row_data)

        return results

    def parse_arena_table(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        results = []

        for table in tables:
            headers = []
            header_row = table.find("tr")
            if header_row:
                ths = header_row.find_all(["th", "td"])
                headers = [th.get_text(strip=True) for th in ths]

            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                row_data = {}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    row_data[key] = cell.get_text(strip=True)
                if row_data:
                    results.append(row_data)

        return results

    async def crawl_general_leaderboard(self) -> List[Dict]:
        logger.info("Crawling general leaderboard from SuperCLUE...")
        all_entries = []

        try:
            html = await self.fetch_page_with_render("https://www.superclueai.com/generalpage")
            table_data = self.parse_html_table(html)

            if table_data:
                for row in table_data:
                    rank = self._safe_int(row.get("排名", row.get("rank", 0)))
                    model_name = row.get("模型名称", row.get("model_name", ""))
                    org = row.get("机构", row.get("organization", ""))
                    score = self._safe_float(row.get("总分", row.get("score", row.get("总得分", 0))))
                    open_source = row.get("开/闭源", row.get("opensource", ""))
                    is_opensource = 1 if "开源" in str(open_source) else 0

                    if model_name:
                        all_entries.append({
                            "category": "general_overall",
                            "rank": rank,
                            "model_name": model_name,
                            "organization": org,
                            "score": score,
                            "score_details": json.dumps(row, ensure_ascii=False),
                            "is_opensource": is_opensource,
                            "is_domestic": 1 if self._is_domestic_org(org) else 0,
                            "release_date": row.get("发布时间", ""),
                        })
        except Exception as e:
            logger.error(f"Error crawling general leaderboard: {e}")

        return all_entries

    async def crawl_arena_leaderboard(self, arena_type: str = "video") -> List[Dict]:
        logger.info(f"Crawling arena leaderboard ({arena_type}) from SuperCLUE...")
        all_entries = []

        try:
            url = f"https://www.superclueai.com/arena?tab=t2iboard&type={arena_type}"
            html = await self.fetch_page_with_render(url)
            table_data = self.parse_arena_table(html)

            if table_data:
                for row in table_data:
                    rank = self._safe_int(row.get("排名", row.get("rank", 0)))
                    model_name = row.get("模型名称", row.get("model_name", ""))
                    org = row.get("机构", row.get("organization", ""))
                    score = self._safe_float(row.get("排位分", row.get("score", row.get("rating", 0))))
                    release_date = row.get("发布时间", "")

                    if model_name:
                        category_map = {
                            "video": "multimodal_t2v",
                            "image": "multimodal_image",
                            "i2v": "multimodal_i2v",
                        }
                        all_entries.append({
                            "category": category_map.get(arena_type, f"multimodal_{arena_type}"),
                            "rank": rank,
                            "model_name": model_name,
                            "organization": org,
                            "score": score,
                            "score_details": json.dumps(row, ensure_ascii=False),
                            "is_opensource": 0,
                            "is_domestic": 1 if self._is_domestic_org(org) else 0,
                            "release_date": release_date,
                        })
        except Exception as e:
            logger.error(f"Error crawling arena leaderboard ({arena_type}): {e}")

        return all_entries

    async def crawl(self) -> List[Dict[str, Any]]:
        all_entries = []

        general_entries = await self.crawl_general_leaderboard()
        all_entries.extend(general_entries)

        for arena_type in ["video", "image", "i2v"]:
            arena_entries = await self.crawl_arena_leaderboard(arena_type)
            all_entries.extend(arena_entries)

        logger.info(f"Total leaderboard entries collected: {len(all_entries)}")
        return all_entries

    @staticmethod
    def _safe_int(val) -> int:
        try:
            return int(float(str(val).replace(",", "")))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _safe_float(val) -> float:
        try:
            return float(str(val).replace(",", "").replace("+", "").split("-")[0].strip())
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _is_domestic_org(org: str) -> bool:
        domestic_keywords = [
            "字节跳动", "百度", "阿里", "腾讯", "智谱", "商汤", "快手", "讯飞",
            "深度求索", "DeepSeek", "零一万物", "百川", "MiniMax", "月之暗面",
            "生数", "潞晨", "爱诗", "小米", "华为", "Baidu", "Alibaba",
            "Tencent", "Zhipu", "SenseTime", "ByteDance", "Kuaishou",
            "iFlytek", "01.AI", "Baichuan", "Moonshot"
        ]
        org_lower = org.lower()
        for kw in domestic_keywords:
            if kw.lower() in org_lower:
                return True
        return False
