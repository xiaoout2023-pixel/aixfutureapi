import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "context_length": 1048576, "max_output_tokens": 65536,
     "input_price": 1.25, "output_price": 10.0, "cached_input": 0.3125, "reasoning_level": "high",
     "vision": True, "audio": True, "code": True, "reasoning": True, "tool_use": True, "structured_output": True},
    {"model_id": "gemini-2.5-flash", "model_name": "Gemini 2.5 Flash", "context_length": 1048576, "max_output_tokens": 65536,
     "input_price": 0.15, "output_price": 0.60, "cached_input": 0.0375, "reasoning_level": "high",
     "vision": True, "audio": True, "code": True, "reasoning": True, "tool_use": True, "structured_output": True},
    {"model_id": "gemini-2.0-flash", "model_name": "Gemini 2.0 Flash", "context_length": 1048576, "max_output_tokens": 8192,
     "input_price": 0.10, "output_price": 0.40, "cached_input": 0.025, "reasoning_level": "medium",
     "vision": True, "audio": True, "code": True, "reasoning": False, "tool_use": True, "structured_output": True},
    {"model_id": "gemini-2.0-flash-lite", "model_name": "Gemini 2.0 Flash Lite", "context_length": 1048576, "max_output_tokens": 8192,
     "input_price": 0.075, "output_price": 0.30, "cached_input": 0.01875, "reasoning_level": "low",
     "vision": True, "audio": False, "code": False, "reasoning": False, "tool_use": True, "structured_output": False},
    {"model_id": "gemini-1.5-pro", "model_name": "Gemini 1.5 Pro", "context_length": 2097152, "max_output_tokens": 8192,
     "input_price": 1.25, "output_price": 5.0, "cached_input": 0.3125, "reasoning_level": "high",
     "vision": True, "audio": True, "code": True, "reasoning": False, "tool_use": True, "structured_output": True},
    {"model_id": "gemini-1.5-flash", "model_name": "Gemini 1.5 Flash", "context_length": 1048576, "max_output_tokens": 8192,
     "input_price": 0.075, "output_price": 0.30, "cached_input": 0.01875, "reasoning_level": "medium",
     "vision": True, "audio": True, "code": False, "reasoning": False, "tool_use": True, "structured_output": False},
]


class GeminiCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="google", base_url="https://ai.google.dev")

    async def crawl(self) -> List[Dict[str, Any]]:
        models = []
        for m in GEMINI_MODELS:
            capabilities = {
                "text": True, "vision": m["vision"], "audio": m["audio"], "code": m["code"],
                "reasoning": m["reasoning"], "tool_use": m["tool_use"], "function_calling": m["tool_use"],
                "image_generation": False, "video_understanding": m["vision"], "video_generation": False,
                "json_mode": m["structured_output"], "structured_output": m["structured_output"],
                "code_execution": True, "fine_tuning": False, "embedding": False,
                "context_length": m["context_length"], "max_output_tokens": m["max_output_tokens"],
                "reasoning_level": m["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": m["input_price"], "output_per_1m_tokens": m["output_price"],
                "cached_input_price": m.get("cached_input"), "batch_input_price": None,
                "batch_output_price": None, "price_per_image": None, "price_per_request": None,
                "reasoning_price_per_1m": None, "currency": "USD", "free_tier": False,
            }
            scores = self._calc_scores(m["reasoning_level"], m["input_price"], m["output_price"], m["code"])
            tags = self.generate_tags(capabilities, pricing)
            source = {
                "model_page": "https://ai.google.dev/gemini-api/docs/models",
                "api_docs": "https://ai.google.dev/api",
                "pricing_page": "https://ai.google.dev/pricing",
                "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
                "region_restriction": False, "enterprise_only": False,
                "openai_compatible": False, "sdk_support": True,
            }
            models.append({
                "model_id": m["model_id"], "model_name": m["model_name"], "provider": "google",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Collected {len(models)} Gemini models")
        return models

    def _calc_scores(self, reasoning_level, input_price, output_price, has_code):
        speed_score = 80
        reasoning_score = {"high": 90, "medium": 70, "low": 50}[reasoning_level]
        coding_score = reasoning_score - 5 if has_code else reasoning_score - 15
        cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
        overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
        return {
            "reasoning_score": reasoning_score, "coding_score": coding_score,
            "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
            "overall_score": overall, "latency_level": "low", "throughput_level": "high",
        }
