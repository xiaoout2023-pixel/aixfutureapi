import httpx
import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

PROVIDER_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "meta-llama": "meta",
    "mistralai": "mistral",
    "cohere": "cohere",
    "deepseek": "deepseek",
    "alibaba": "aliyun",
    "qwen": "aliyun",
    "01-ai": "01ai",
    "perplexity": "perplexity",
    "x-ai": "xai",
    "microsoft": "microsoft",
    "nvidia": "nvidia",
    "databricks": "databricks",
    "snowflake": "snowflake",
    "amazon": "amazon",
    "zhipu": "zhipu",
    "minimax": "minimax",
    "moonshot": "moonshot",
}

SKIP_PATTERNS = [
    ":free", ":beta", ":nitro", ":floor", ":extended", ":self-moderated",
    "/embed", "/guard", "/instruct", "/chat", "/base", "/preview",
    "/vision", "/code", "/math", "/reasoning",
]


class OpenRouterCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="openrouter", base_url="https://openrouter.ai")
        self.api_url = "https://openrouter.ai/api/v1/models"

    async def fetch_models(self) -> Dict:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                    response = await client.get(self.api_url, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()
                    model_count = len(data.get("data", []))
                    logger.info(f"Fetched {model_count} models from OpenRouter")
                    return data
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for OpenRouter: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return {"data": []}

    def _parse_model(self, raw: Dict) -> Dict[str, Any]:
        model_id_raw = raw.get("id", "")
        name = raw.get("name", "")
        context_length = raw.get("context_length", 0)
        description = raw.get("description", "")
        arch = raw.get("architecture", {})
        pricing = raw.get("pricing", {})
        top_provider = raw.get("top_provider", {})
        supported_params = raw.get("supported_parameters", [])

        parts = model_id_raw.split("/")
        provider_key = parts[0] if len(parts) > 1 else "unknown"
        provider = PROVIDER_MAP.get(provider_key, provider_key)

        model_id = model_id_raw.replace("/", "-")

        modality = arch.get("modality", "text->text")
        input_modalities = arch.get("input_modalities", ["text"])
        output_modalities = arch.get("output_modalities", ["text"])

        has_vision = "image" in input_modalities or "file" in input_modalities
        has_audio = "audio" in input_modalities
        has_image_gen = "image" in output_modalities
        has_video = "video" in input_modalities or "video" in output_modalities
        has_tool_use = "tools" in supported_params
        has_structured_output = "structured_outputs" in supported_params or "response_format" in supported_params
        has_reasoning = "reasoning" in supported_params or "internal_reasoning" in supported_params
        has_code = any(kw in name.lower() for kw in ["code", "codestral", "devstral"])
        is_embedding = "embed" in model_id_raw.lower() or "embedding" in output_modalities

        prompt_price_per_token = float(pricing.get("prompt", "0"))
        completion_price_per_token = float(pricing.get("completion", "0"))
        image_price = float(pricing.get("image", "0"))
        request_price = float(pricing.get("request", "0"))
        cache_read_price = float(pricing.get("input_cache_read", "0"))
        cache_write_price = float(pricing.get("input_cache_write", "0"))
        reasoning_price = float(pricing.get("internal_reasoning", "0"))

        input_per_1m = prompt_price_per_token * 1_000_000
        output_per_1m = completion_price_per_token * 1_000_000
        image_per_1m = image_price * 1_000_000
        cache_read_per_1m = cache_read_price * 1_000_000
        cache_write_per_1m = cache_write_price * 1_000_000
        reasoning_per_1m = reasoning_price * 1_000_000

        is_free = input_per_1m == 0 and output_per_1m == 0

        max_output_tokens = top_provider.get("max_completion_tokens")
        if max_output_tokens is None:
            max_output_tokens = 4096

        reasoning_level = "high" if has_reasoning else ("medium" if "think" in name.lower() else "low")

        capabilities = {
            "text": True,
            "vision": has_vision,
            "audio": has_audio,
            "code": has_code,
            "reasoning": has_reasoning,
            "tool_use": has_tool_use,
            "function_calling": has_tool_use,
            "image_generation": has_image_gen,
            "video_understanding": has_video,
            "video_generation": False,
            "json_mode": has_structured_output,
            "structured_output": has_structured_output,
            "code_execution": False,
            "fine_tuning": False,
            "embedding": is_embedding,
            "context_length": context_length or 0,
            "max_output_tokens": max_output_tokens,
            "reasoning_level": reasoning_level,
        }

        pricing_data = {
            "input_per_1m_tokens": round(input_per_1m, 6),
            "output_per_1m_tokens": round(output_per_1m, 6),
            "cached_input_price": round(cache_read_per_1m, 6) if cache_read_per_1m > 0 else None,
            "batch_input_price": None,
            "batch_output_price": None,
            "price_per_image": round(image_per_1m, 6) if image_per_1m > 0 else None,
            "price_per_request": round(request_price * 1_000_000, 6) if float(request_price) > 0 else None,
            "reasoning_price_per_1m": round(reasoning_per_1m, 6) if reasoning_per_1m > 0 else None,
            "currency": "USD",
            "free_tier": is_free,
        }

        speed_score = 75 if context_length < 200000 else 60
        reasoning_score = {"high": 90, "medium": 70, "low": 50}[reasoning_level]
        coding_score = reasoning_score - 5 if has_code else reasoning_score - 15
        cost_efficiency = max(0, 100 - (input_per_1m + output_per_1m) * 2) if not is_free else 100
        overall_score = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)

        scores = {
            "reasoning_score": reasoning_score,
            "coding_score": coding_score,
            "speed_score": speed_score,
            "cost_efficiency_score": round(cost_efficiency, 1),
            "overall_score": overall_score,
            "latency_level": "low" if speed_score >= 75 else "medium",
            "throughput_level": "high" if speed_score >= 75 else "medium",
        }

        tags = self.generate_tags(capabilities, pricing_data)

        source = {
            "model_page": f"https://openrouter.ai/models/{model_id_raw}",
            "api_docs": "https://openrouter.ai/docs",
            "pricing_page": "https://openrouter.ai/pricing",
            "last_updated": time.strftime("%Y-%m-%d"),
            "source_type": "marketplace",
            "region_restriction": False,
            "enterprise_only": False,
            "openai_compatible": True,
            "sdk_support": True,
        }

        status = "active"
        if ":preview" in model_id_raw:
            status = "beta"
        elif ":deprecated" in model_id_raw:
            status = "deprecated"

        return {
            "model_id": model_id,
            "model_name": name,
            "provider": provider,
            "release_date": None,
            "status": status,
            "capabilities": json.dumps(capabilities, ensure_ascii=False),
            "pricing": json.dumps(pricing_data, ensure_ascii=False),
            "scores": json.dumps(scores, ensure_ascii=False),
            "tags": json.dumps(tags, ensure_ascii=False),
            "source": json.dumps(source, ensure_ascii=False),
            "last_updated": time.strftime("%Y-%m-%d"),
            "_raw_id": model_id_raw,
            "_provider_key": provider_key,
        }

    def _should_skip(self, raw: Dict) -> bool:
        model_id = raw.get("id", "")
        name = raw.get("name", "")
        modality = raw.get("architecture", {}).get("modality", "")
        output_modalities = raw.get("architecture", {}).get("output_modalities", [])

        if "embedding" in output_modalities:
            return True
        if any(p in model_id for p in [":free", ":nitro", ":floor", ":extended", ":self-moderated"]):
            return True
        if any(p in model_id for p in ["/embed", "/guard"]) and "instruct" not in model_id:
            return True

        return False

    async def crawl(self) -> List[Dict[str, Any]]:
        data = await self.fetch_models()
        raw_models = data.get("data", [])

        models = []
        seen_providers = set()

        for raw in raw_models:
            if self._should_skip(raw):
                continue

            model = self._parse_model(raw)
            provider_key = model.pop("_provider_key")
            seen_providers.add(provider_key)
            models.append(model)

        logger.info(f"Parsed {len(models)} models from {len(seen_providers)} providers")
        return models

    async def crawl_marketplace_data(self) -> List[Dict]:
        data = await self.fetch_models()
        raw_models = data.get("data", [])

        marketplace_entries = []
        for raw in raw_models:
            if self._should_skip(raw):
                continue

            model_id_raw = raw.get("id", "")
            model_id = model_id_raw.replace("/", "-")
            pricing = raw.get("pricing", {})

            prompt_price = float(pricing.get("prompt", "0")) * 1_000_000
            completion_price = float(pricing.get("completion", "0")) * 1_000_000

            marketplace_entries.append({
                "model_id": model_id,
                "marketplace": "openrouter",
                "marketplace_model_id": model_id_raw,
                "input_price": round(prompt_price, 6),
                "output_price": round(completion_price, 6),
                "latency_ms": None,
                "uptime": None,
                "availability": None,
            })

        logger.info(f"Collected {len(marketplace_entries)} marketplace entries from OpenRouter")
        return marketplace_entries
