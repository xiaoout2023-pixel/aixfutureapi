import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

MISTRAL_MODELS = [
    {"model_id": "mistral-large-latest", "model_name": "Mistral Large", "context_length": 128000,
     "input_price": 2.0, "output_price": 6.0, "reasoning_level": "high",
     "vision": False, "code": True, "reasoning": True, "tool_use": True},
    {"model_id": "mistral-medium-latest", "model_name": "Mistral Medium", "context_length": 128000,
     "input_price": 0.40, "output_price": 2.0, "reasoning_level": "medium",
     "vision": False, "code": True, "reasoning": False, "tool_use": True},
    {"model_id": "mistral-small-latest", "model_name": "Mistral Small", "context_length": 128000,
     "input_price": 0.20, "output_price": 0.60, "reasoning_level": "low",
     "vision": False, "code": False, "reasoning": False, "tool_use": True},
    {"model_id": "codestral-latest", "model_name": "Codestral", "context_length": 256000,
     "input_price": 0.30, "output_price": 0.90, "reasoning_level": "high",
     "vision": False, "code": True, "reasoning": False, "tool_use": False},
    {"model_id": "pixtral-large-latest", "model_name": "Pixtral Large", "context_length": 128000,
     "input_price": 2.0, "output_price": 6.0, "reasoning_level": "high",
     "vision": True, "code": True, "reasoning": True, "tool_use": True},
    {"model_id": "mistral-embed", "model_name": "Mistral Embed", "context_length": 32000,
     "input_price": 0.10, "output_price": 0.10, "reasoning_level": "low",
     "vision": False, "code": False, "reasoning": False, "tool_use": False},
]


class MistralCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="mistral", base_url="https://mistral.ai")

    async def crawl(self) -> List[Dict[str, Any]]:
        models = []
        for m in MISTRAL_MODELS:
            is_embedding = "embed" in m["model_id"]
            capabilities = {
                "text": True, "vision": m["vision"], "audio": False, "code": m["code"],
                "reasoning": m["reasoning"], "tool_use": m["tool_use"], "function_calling": m["tool_use"],
                "image_generation": False, "video_understanding": False, "video_generation": False,
                "json_mode": True, "structured_output": True, "code_execution": False,
                "fine_tuning": True, "embedding": is_embedding,
                "context_length": m["context_length"], "max_output_tokens": 8192,
                "reasoning_level": m["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": m["input_price"], "output_per_1m_tokens": m["output_price"],
                "cached_input_price": None, "batch_input_price": None, "batch_output_price": None,
                "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
                "currency": "USD", "free_tier": False,
            }
            scores = self._calc_scores(m["reasoning_level"], m["input_price"], m["output_price"], m["code"])
            tags = self.generate_tags(capabilities, pricing)
            source = {
                "model_page": "https://docs.mistral.ai/getting-started/models/models_overview/",
                "api_docs": "https://docs.mistral.ai/api/",
                "pricing_page": "https://mistral.ai/pricing/",
                "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
                "region_restriction": False, "enterprise_only": False,
                "openai_compatible": True, "sdk_support": True,
            }
            models.append({
                "model_id": m["model_id"], "model_name": m["model_name"], "provider": "mistral",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Collected {len(models)} Mistral models")
        return models

    def _calc_scores(self, reasoning_level, input_price, output_price, has_code):
        speed_score = 75
        reasoning_score = {"high": 90, "medium": 70, "low": 50}[reasoning_level]
        coding_score = reasoning_score - 5 if has_code else reasoning_score - 15
        cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
        overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
        return {
            "reasoning_score": reasoning_score, "coding_score": coding_score,
            "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
            "overall_score": overall, "latency_level": "medium", "throughput_level": "high",
        }
