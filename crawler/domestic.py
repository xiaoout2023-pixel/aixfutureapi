import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

CNY_TO_USD = 7.25

DEEPSEEK_MODELS = [
    {"model_id": "deepseek-chat", "model_name": "DeepSeek V3", "context_length": 65536,
     "input_price_cny": 0.002, "output_price_cny": 0.008, "cached_input_cny": 0.0005,
     "reasoning_level": "high", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    {"model_id": "deepseek-reasoner", "model_name": "DeepSeek R1", "context_length": 65536,
     "input_price_cny": 0.004, "output_price_cny": 0.016, "cached_input_cny": 0.001,
     "reasoning_level": "high", "vision": False, "code": True, "reasoning": True, "tool_use": False},
]

MOONSHOT_MODELS = [
    {"model_id": "moonshot-v1-auto", "model_name": "Moonshot V1 Auto", "context_length": 128000,
     "input_price_cny": 0.012, "output_price_cny": 0.012, "reasoning_level": "medium",
     "vision": False, "code": True, "reasoning": False, "tool_use": True},
    {"model_id": "moonshot-v1-8k", "model_name": "Moonshot V1 8K", "context_length": 8192,
     "input_price_cny": 0.012, "output_price_cny": 0.012, "reasoning_level": "medium",
     "vision": False, "code": True, "reasoning": False, "tool_use": True},
    {"model_id": "moonshot-v1-32k", "model_name": "Moonshot V1 32K", "context_length": 32768,
     "input_price_cny": 0.012, "output_price_cny": 0.012, "reasoning_level": "medium",
     "vision": False, "code": True, "reasoning": False, "tool_use": True},
]

MINIMAX_MODELS = [
    {"model_id": "minimax-text-01", "model_name": "MiniMax Text 01", "context_length": 1048576,
     "input_price_cny": 0.001, "output_price_cny": 0.002, "reasoning_level": "medium",
     "vision": False, "code": True, "reasoning": False, "tool_use": True},
    {"model_id": "minimax-vl-01", "model_name": "MiniMax VL 01", "context_length": 1048576,
     "input_price_cny": 0.001, "output_price_cny": 0.002, "reasoning_level": "medium",
     "vision": True, "code": True, "reasoning": False, "tool_use": True},
]


def _cny_to_usd_per_1m(cny_per_1k):
    return round(cny_per_1k / CNY_TO_USD * 1000, 6)


def _build_model(m, provider, source_info):
    input_usd = _cny_to_usd_per_1m(m.get("input_price_cny", 0))
    output_usd = _cny_to_usd_per_1m(m.get("output_price_cny", 0))
    cached_usd = _cny_to_usd_per_1m(m["cached_input_cny"]) if "cached_input_cny" in m else None
    capabilities = {
        "text": True, "vision": m.get("vision", False), "audio": False, "code": m.get("code", False),
        "reasoning": m.get("reasoning", False), "tool_use": m.get("tool_use", False),
        "function_calling": m.get("tool_use", False), "image_generation": False,
        "video_understanding": False, "video_generation": False,
        "json_mode": True, "structured_output": False, "code_execution": False,
        "fine_tuning": False, "embedding": False,
        "context_length": m["context_length"], "max_output_tokens": 4096,
        "reasoning_level": m["reasoning_level"],
    }
    pricing = {
        "input_per_1m_tokens": input_usd, "output_per_1m_tokens": output_usd,
        "cached_input_price": cached_usd, "batch_input_price": None, "batch_output_price": None,
        "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
        "currency": "USD", "free_tier": False,
    }
    speed_score = 70
    reasoning_score = {"high": 90, "medium": 70, "low": 50}[m["reasoning_level"]]
    coding_score = reasoning_score - 5 if m.get("code") else reasoning_score - 15
    cost_efficiency = max(0, 100 - (input_usd + output_usd) * 2)
    overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
    scores = {
        "reasoning_score": reasoning_score, "coding_score": coding_score,
        "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
        "overall_score": overall, "latency_level": "medium", "throughput_level": "medium",
    }
    tags = []
    if capabilities["vision"]: tags.append("vision")
    if capabilities["code"]: tags.append("coding")
    if capabilities["tool_use"]: tags.append("tool_use")
    if capabilities["reasoning"]: tags.append("reasoning")
    if input_usd <= 1: tags.append("cheap")
    if input_usd >= 10: tags.append("premium")
    if m["context_length"] >= 1000000: tags.append("long_context")
    source = {
        **source_info,
        "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
        "region_restriction": True, "enterprise_only": False,
        "openai_compatible": True, "sdk_support": True,
    }
    return {
        "model_id": m["model_id"], "model_name": m["model_name"], "provider": provider,
        "release_date": None, "status": "active",
        "capabilities": json.dumps(capabilities, ensure_ascii=False),
        "pricing": json.dumps(pricing, ensure_ascii=False),
        "scores": json.dumps(scores, ensure_ascii=False),
        "tags": json.dumps(tags, ensure_ascii=False),
        "source": json.dumps(source, ensure_ascii=False),
        "last_updated": time.strftime("%Y-%m-%d"),
    }


class DeepSeekCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="deepseek", base_url="https://api.deepseek.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        source_info = {
            "model_page": "https://api-docs.deepseek.com/zh-cn/",
            "api_docs": "https://api-docs.deepseek.com/",
            "pricing_page": "https://api-docs.deepseek.com/zh-cn/quick_start/pricing",
        }
        models = [_build_model(m, "deepseek", source_info) for m in DEEPSEEK_MODELS]
        logger.info(f"Collected {len(models)} DeepSeek models")
        return models


class MoonshotCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="moonshot", base_url="https://api.moonshot.cn")

    async def crawl(self) -> List[Dict[str, Any]]:
        source_info = {
            "model_page": "https://platform.moonshot.cn/docs/intro",
            "api_docs": "https://platform.moonshot.cn/docs/api/chat",
            "pricing_page": "https://platform.moonshot.cn/docs/pricing/chat",
        }
        models = [_build_model(m, "moonshot", source_info) for m in MOONSHOT_MODELS]
        logger.info(f"Collected {len(models)} Moonshot models")
        return models


class MiniMaxCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="minimax", base_url="https://www.minimaxi.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        source_info = {
            "model_page": "https://www.minimaxi.com/document/guides/chat-model/chat",
            "api_docs": "https://www.minimaxi.com/document/guides/chat-model/chat/api",
            "pricing_page": "https://www.minimaxi.com/document/guides/chat-model/chat/price",
        }
        models = [_build_model(m, "minimax", source_info) for m in MINIMAX_MODELS]
        logger.info(f"Collected {len(models)} MiniMax models")
        return models
