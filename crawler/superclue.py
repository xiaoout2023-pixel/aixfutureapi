import httpx
import json
import re
import logging
import time
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from crawler.base import BaseCrawler, normalize_provider_name

logger = logging.getLogger(__name__)

BASE_DIR = "data/leaderboard"

EXCEL_SHEET_MAPPING = {
    "总排行榜": {"key": "general_overall", "name": "总排行榜", "group": "general"},
    "推理模型总排行榜": {"key": "general_reasoning", "name": "推理模型总排行榜", "group": "general"},
    "基础模型总排行榜": {"key": "general_base", "name": "基础模型总排行榜", "group": "general"},
    "推理任务总排行榜": {"key": "general_reasoning_task", "name": "推理任务总排行榜", "group": "general"},
    "开源排行榜": {"key": "general_opensource", "name": "开源排行榜", "group": "general"},
    "小模型10B榜": {"key": "general_small_10b", "name": "小模型10B榜", "group": "general"},
    "小模型5B榜": {"key": "general_small_5b", "name": "小模型5B榜", "group": "general"},
}

EXCEL_DATA_PATHS = {
    "general": "/data/generalboard/",
    "multimodal_vlm": "/data/multimodal_list/VLM/",
    "multimodal_image": "/data/multimodal_list/Image/",
    "multimodal_t2v": "/data/multimodal_list/T2V/",
    "multimodal_i2v": "/data/multimodal_list/I2V/",
    "multimodal_edit": "/data/multimodal_list/Edit/",
    "multimodal_r2v": "/data/multimodal_list/R2V/",
    "multimodal_comicshorts": "/data/multimodal_list/comic/",
    "multimodal_world": "/data/multimodal_list/World/",
    "multimodal_voice_av": "/data/multimodal_list/VoiceAV/",
    "multimodal_voice_chat": "/data/multimodal_list/VoiceChat/",
    "multimodal_tts": "/data/multimodal_list/TTS/",
    "multimodal_v": "/data/multimodal_list/V/",
    "multimodal_vlr": "/data/multimodal_list/VLR/",
}

AVAILABLE_DATES = [
    "2026年3月", "2025年度测评", "2025年11月", "2025年9月",
    "2025年7月", "2025年5月", "2025年3月", "2024年12月",
    "2024年10月", "2024年8月", "2024年6月", "2024年4月",
    "2024年2月", "2023年12月", "2023年11月", "2023年10月", "2023年9月",
]

COLUMN_NAME_ALIASES = {
    "模型": "模型名称",
    "分数": "总分",
    "机构": "机构",
}


def clean_column_name(name: str) -> str:
    name = name.replace("\n", "").replace("\r", "").replace("\t", "")
    name = re.sub(r"\s+", "", name)
    name = name.strip()
    if name in COLUMN_NAME_ALIASES:
        name = COLUMN_NAME_ALIASES[name]
    return name


class SuperCLUELeaderboardCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="superclue", base_url="https://www.superclueai.com")

    async def _fetch(self, url: str, binary: bool = False) -> Any:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    if binary:
                        return response.content
                    return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return b"" if binary else ""

    async def crawl_excel_boards(self) -> List[Dict]:
        logger.info("Crawling Excel-based boards...")
        all_boards = []
        date = AVAILABLE_DATES[0]
        logger.info(f"Using date: {date}")

        for board_key, data_path in EXCEL_DATA_PATHS.items():
            xlsx_url = self.base_url + data_path + date + ".xlsx"
            try:
                content = await self._fetch(xlsx_url, binary=True)
                if not content or len(content) < 100:
                    logger.warning(f"  {board_key}: empty or too small response")
                    continue

                boards = self._parse_excel(content, board_key, date)
                all_boards.extend(boards)
                logger.info(f"  {board_key}: {sum(len(b['rows']) for b in boards)} entries from Excel")

            except Exception as e:
                logger.warning(f"  {board_key}: error - {e}")

        return all_boards

    def _parse_excel(self, content: bytes, default_key: str, date: str) -> List[Dict]:
        try:
            import openpyxl
        except ImportError:
            logger.error("openpyxl not installed. Run: pip install openpyxl")
            return []

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        results = []
        sheet_index = 0

        for sheet_name in wb.sheetnames:
            sheet_meta = EXCEL_SHEET_MAPPING.get(sheet_name, None)
            ws = wb[sheet_name]

            rows_data = list(ws.iter_rows(values_only=True))
            if len(rows_data) < 2:
                continue

            raw_headers = [str(h).strip() if h else "" for h in rows_data[0]]
            headers = [clean_column_name(h) for h in raw_headers]
            headers = [h for h in headers if h]

            entries = []
            for row_data in rows_data[1:]:
                if not row_data or not row_data[0]:
                    continue
                entry = {}
                col_idx = 0
                for i, val in enumerate(row_data):
                    if i < len(raw_headers):
                        col_name = clean_column_name(raw_headers[i])
                        if col_name:
                            entry[col_name] = val
                if "机构" in entry:
                    entry["机构"] = normalize_provider_name(str(entry["机构"]))
                if entry:
                    entries.append(entry)

            if sheet_meta:
                key = sheet_meta["key"]
                name = sheet_meta["name"]
                group = sheet_meta["group"]
            else:
                key = f"{default_key}_{sheet_index}" if sheet_index > 0 else default_key
                name = sheet_name
                group = "multimodal"

            board_data = {
                "key": key,
                "name": name,
                "group": group,
                "source": "excel",
                "source_date": date,
                "source_file": f"/data/{default_key}/{date}.xlsx",
                "sheet_name": sheet_name,
                "headers": headers,
                "crawl_time": datetime.now().isoformat(),
                "rows": entries,
            }
            results.append(board_data)
            sheet_index += 1

        wb.close()
        return results

    async def crawl_all(self) -> List[Dict]:
        logger.info("Starting SuperCLUE leaderboard crawl (Excel only)...")

        excel_boards = await self.crawl_excel_boards()
        logger.info(f"Excel boards: {len(excel_boards)}")

        logger.info(f"Total boards: {len(excel_boards)}")
        return excel_boards
