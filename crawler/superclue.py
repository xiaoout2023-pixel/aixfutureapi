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

ARENA_BOARD_NAMES = {
    "T2VBoard": {"key": "multimodal_t2v", "name": "SuperCLUE-T2V 文生视频", "group": "multimodal"},
    "I2VBoard": {"key": "multimodal_i2v", "name": "SuperCLUE-I2V 图生视频模型", "group": "multimodal"},
    "IEBoard": {"key": "multimodal_edit", "name": "SuperCLUE-Edit 图像编辑", "group": "multimodal"},
    "R2VBoard": {"key": "multimodal_r2v", "name": "SuperCLUE-R2V 参考生视频", "group": "multimodal"},
    "T2IBoard": {"key": "multimodal_image", "name": "SuperCLUE-Image 文生图", "group": "multimodal"},
    "TTSBoard": {"key": "multimodal_tts", "name": "SuperCLUE-TTS 语音合成", "group": "multimodal"},
}

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

    async def crawl_arena_boards(self) -> List[Dict]:
        logger.info("Crawling arena boards from JS bundle...")
        html = await self._fetch(self.base_url)
        js_files = re.findall(r'(?:src|href)="(/assets/[^"]+\.js)"', html)

        all_boards = []
        for js_file in js_files:
            full_url = self.base_url + js_file
            try:
                js_text = await self._fetch(full_url)
                if any(k in js_text for k in ["T2VBoard", "IEBoard", "rows:[{rank"]):
                    logger.info(f"  Found arena data in {js_file}")
                    boards = self._extract_arena_boards(js_text)
                    all_boards.extend(boards)
            except Exception as e:
                logger.warning(f"  Error processing {js_file}: {e}")

        return all_boards

    def _extract_arena_boards(self, js_text: str) -> List[Dict]:
        results = []
        for board_name, meta in ARENA_BOARD_NAMES.items():
            pattern = rf'{board_name}\s*[,=].*?data\s*\(\s*\)\s*\{{\s*return\s*\{{\s*rows:\s*\['
            match = re.search(pattern, js_text, re.DOTALL)
            if not match:
                pattern = rf'name:\s*["\']?{board_name}["\']?\s*,\s*data\s*\(\s*\)\s*\{{\s*return\s*\{{\s*rows:\s*\['
                match = re.search(pattern, js_text, re.DOTALL)

            if not match:
                logger.warning(f"Board {board_name} not found, skipping")
                continue

            start = match.end() - 1
            bracket_count = 0
            end = start
            for i in range(start, min(start + 50000, len(js_text))):
                if js_text[i] == '[':
                    bracket_count += 1
                elif js_text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break

            array_text = js_text[start:end]
            try:
                rows = json.loads(array_text)
            except json.JSONDecodeError:
                rows = self._parse_js_array(array_text)

            for row in rows:
                if "org" in row:
                    row["organization"] = normalize_provider_name(row.pop("org"))
                if "model" in row:
                    row["model_name"] = row.pop("model")
                if "date" in row:
                    row["release_date"] = row.pop("date")

            board_data = {
                "key": meta["key"],
                "name": meta["name"],
                "group": meta["group"],
                "source": "arena",
                "crawl_time": datetime.now().isoformat(),
                "rows": rows,
            }
            results.append(board_data)
            logger.info(f"  Board {board_name} ({meta['key']}): {len(rows)} entries")

        return results

    def _parse_js_array(self, text: str) -> List[Dict]:
        results = []
        obj_pattern = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        for obj_text in obj_pattern:
            try:
                obj = {}
                for kv in re.findall(r'(\w+)\s*:\s*([^,}\s]+|"[^"]*"|\'[^\']*\'|\[[^\]]*\])', obj_text):
                    key, value = kv
                    value = value.strip('"').strip("'")
                    try:
                        obj[key] = json.loads(value)
                    except:
                        obj[key] = value
                if obj:
                    results.append(obj)
            except:
                pass
        return results

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

            headers = [str(h).strip() if h else "" for h in rows_data[0]]

            entries = []
            for row_data in rows_data[1:]:
                if not row_data or not row_data[0]:
                    continue
                entry = {}
                for i, val in enumerate(row_data):
                    if i < len(headers) and headers[i]:
                        entry[headers[i]] = val
                if "机构" in entry:
                    entry["机构"] = normalize_provider_name(str(entry["机构"]))
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
        logger.info("Starting SuperCLUE leaderboard crawl (raw mode)...")

        arena_boards = await self.crawl_arena_boards()
        logger.info(f"Arena boards: {len(arena_boards)}")

        excel_boards = await self.crawl_excel_boards()
        logger.info(f"Excel boards: {len(excel_boards)}")

        all_boards = arena_boards + excel_boards
        logger.info(f"Total boards: {len(all_boards)}")
        return all_boards
