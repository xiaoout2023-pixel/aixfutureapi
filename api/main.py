from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import json

_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    with open(_env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                if key and key not in os.environ:
                    os.environ[key] = value

from db.turso import TursoDB
from db.repository import ModelRepository

DOCS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs.html')
with open(DOCS_PATH, 'r', encoding='utf-8') as f:
    DOCS_HTML = f.read()

app = FastAPI(
    title="AI Model Pricing API",
    description="AI模型价格采集与对比系统",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db = None
_repo = None

def get_repo() -> ModelRepository:
    global _db, _repo
    if _repo is None:
        _db = TursoDB()
        _repo = ModelRepository(_db)
    return _repo


class CostCalcRequest(BaseModel):
    model_id: str
    input_tokens: int = 1000
    output_tokens: int = 1000
    quantity: int = 1
    currency: Optional[str] = "USD"

class CostCompareRequest(BaseModel):
    models: List[str]
    input_tokens: int = 1000
    output_tokens: int = 1000
    quantity: int = 1
    currency: Optional[str] = "USD"


@app.get("/")
async def root():
    return {
        "name": "AI Model Pricing API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "models": "/api/models",
            "model_detail": "/api/models/{model_id}",
            "model_pricing": "/api/models/{model_id}/pricing",
            "model_evaluations": "/api/models/{model_id}/evaluations",
            "providers": "/api/providers",
            "search": "/api/search?q=gpt",
            "leaderboard": "/api/leaderboard?metric=aa_intelligence_index",
            "compare": "/api/compare?models=openai/gpt-4o-2024-08-06,anthropic/claude-opus-4-7",
            "cost_calculate": "POST /api/cost/calculate",
            "cost_compare": "POST /api/cost/compare",
            "exchange_rate": "/api/exchange-rate",
            "status": "/api/status",
            "superclue_categories": "/api/leaderboard/categories",
            "superclue_data": "/api/leaderboard/superclue/{category}",
        }
    }


@app.get("/api/status")
async def get_status():
    status = await get_repo().get_status()
    return {"code": 200, "message": "success", "data": status}


@app.get("/api/models")
async def list_models(
    provider: Optional[str] = Query(None),
    provider_type: Optional[str] = Query(None, description="open_source or closed"),
    capability: Optional[str] = Query(None, description="text/code/reasoning/vision/image_gen/audio/audio_gen/video/tool_use/structured_output/streaming/batch/fine_tuning/embedding"),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: Optional[str] = Query("aa_intelligence_index", description="排序字段: aa_intelligence_index/lmarena_elo/input_price/output_price/context_length/tokens_per_second"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    min_input_price: Optional[float] = Query(None),
    max_input_price: Optional[float] = Query(None),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(20, ge=1, le=100),
):
    result = await get_repo().get_models(
        page=page, page_size=page_size,
        provider=provider, capability=capability,
        provider_type=provider_type, status=status, q=q,
        sort_by=sort_by, sort_order=sort_order,
        min_input_price=min_input_price, max_input_price=max_input_price,
    )
    return {"code": 200, "message": "success", **result}


@app.get("/api/models/{model_id:path}/pricing")
async def get_model_pricing(
    model_id: str,
    channel: Optional[str] = Query(None, description="official/marketplace/reseller"),
    region: Optional[str] = Query(None, description="global/us/eu/ap"),
):
    pricing = await get_repo().get_model_pricing(model_id, channel=channel, region=region)
    if not pricing:
        raise HTTPException(status_code=404, detail=f"No pricing data for '{model_id}'")
    return {"code": 200, "message": "success", "data": pricing, "total": len(pricing)}


@app.get("/api/models/{model_id:path}/evaluations")
async def get_model_evaluations(model_id: str):
    evaluations = await get_repo().get_model_evaluations(model_id)
    if not evaluations:
        raise HTTPException(status_code=404, detail=f"No evaluation data for '{model_id}'")
    return {"code": 200, "message": "success", "data": evaluations, "total": len(evaluations)}


@app.get("/api/models/{model_id:path}")
async def get_model(model_id: str):
    model = await get_repo().get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return {"code": 200, "message": "success", "data": model}


@app.get("/api/providers")
async def list_providers():
    providers = await get_repo().get_providers()
    return {"code": 200, "message": "success", "data": providers}


@app.get("/api/leaderboard")
async def get_leaderboard(
    metric: Optional[str] = Query("aa_intelligence_index", description="排名指标: aa_intelligence_index/aa_coding_index/aa_math_index/lmarena_elo/lmarena_coding/lmarena_math/lmarena_hard/tokens_per_second"),
    provider_type: Optional[str] = Query(None, description="open_source or closed"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=200),
):
    result = await get_repo().get_leaderboard(
        metric=metric, page=page, page_size=page_size,
        provider_type=provider_type,
    )
    return {"code": 200, "message": "success", **result}


@app.get("/api/compare")
async def compare_models(
    models: str = Query(..., description="逗号分隔的模型ID列表，如 openai/gpt-4o-2024-08-06,anthropic/claude-opus-4-7"),
):
    model_ids = [m.strip() for m in models.split(",") if m.strip()]
    if not model_ids:
        raise HTTPException(status_code=400, detail="请提供至少一个模型ID")
    if len(model_ids) > 10:
        raise HTTPException(status_code=400, detail="最多对比10个模型")

    results = []
    for model_id in model_ids:
        model = await get_repo().get_model(model_id)
        if model:
            results.append(model)

    if not results:
        raise HTTPException(status_code=404, detail="未找到任何模型")

    meta = {}
    pricing_models = [(r.get("model_id", ""), r.get("pricing", {})) for r in results if r.get("pricing")]
    if pricing_models:
        cheapest_input = min(pricing_models, key=lambda x: x[1].get("input_per_1m_tokens", float("inf")))
        cheapest_output = min(pricing_models, key=lambda x: x[1].get("output_per_1m_tokens", float("inf")))
        meta["cheapest_input"] = cheapest_input[0]
        meta["cheapest_output"] = cheapest_output[0]

    eval_models = [(r.get("model_id", ""), r.get("evaluation", {})) for r in results if r.get("evaluation")]
    if eval_models:
        best_intelligence = max(
            eval_models,
            key=lambda x: x[1].get("aa_intelligence_index") or 0
        )
        meta["best_intelligence"] = best_intelligence[0]

    context_models = [(r.get("model_id", ""), r.get("context_length", 0)) for r in results]
    if context_models:
        longest_context = max(context_models, key=lambda x: x[1] or 0)
        meta["longest_context"] = longest_context[0]

    return {
        "code": 200,
        "message": "success",
        "data": results,
        "meta": meta,
    }


@app.get("/api/search")
async def search_models(
    q: str = Query(..., description="搜索关键词"),
    limit: Optional[int] = Query(10, ge=1, le=50),
):
    result = await get_repo().search_models(q=q, limit=limit)
    return {"code": 200, "message": "success", **result}


@app.post("/api/cost/calculate")
async def calculate_cost(request: CostCalcRequest):
    model = await get_repo().get_model(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{request.model_id}' not found")

    pricing = model.get("pricing") or {}
    input_price = pricing.get("input_per_1m_tokens", 0)
    output_price = pricing.get("output_per_1m_tokens", 0)

    input_cost = (request.input_tokens / 1000000) * input_price * request.quantity
    output_cost = (request.output_tokens / 1000000) * output_price * request.quantity
    total_cost = input_cost + output_cost

    currency = request.currency.upper()
    exchange_rates = {"USD": 1.0, "CNY": 7.25, "EUR": 0.92, "JPY": 149.5, "GBP": 0.79}
    rate = exchange_rates.get(currency, 1.0)
    currency_symbol = {"USD": "$", "CNY": "¥", "EUR": "€", "JPY": "¥", "GBP": "£"}.get(currency, currency)

    return {
        "code": 200, "message": "success",
        "data": {
            "model_id": request.model_id,
            "model_name": model.get("model_name"),
            "provider": model.get("provider"),
            "input_tokens": request.input_tokens,
            "output_tokens": request.output_tokens,
            "quantity": request.quantity,
            "pricing": pricing,
            "cost_breakdown": {
                "input_cost": round(input_cost * rate, 6),
                "output_cost": round(output_cost * rate, 6),
                "total_cost": round(total_cost * rate, 6),
                "currency": currency,
                "currency_symbol": currency_symbol,
                "exchange_rate": rate if currency != "USD" else None,
            }
        }
    }


@app.post("/api/cost/compare")
async def compare_cost(request: CostCompareRequest):
    results = []
    for model_id in request.models:
        model = await get_repo().get_model(model_id)
        if not model:
            continue
        pricing = model.get("pricing") or {}
        input_price = pricing.get("input_per_1m_tokens", 0)
        output_price = pricing.get("output_per_1m_tokens", 0)
        input_cost = (request.input_tokens / 1000000) * input_price * request.quantity
        output_cost = (request.output_tokens / 1000000) * output_price * request.quantity

        currency = request.currency.upper()
        exchange_rates = {"USD": 1.0, "CNY": 7.25, "EUR": 0.92, "JPY": 149.5, "GBP": 0.79}
        rate = exchange_rates.get(currency, 1.0)

        results.append({
            "model_id": model_id,
            "model_name": model.get("model_name"),
            "provider": model.get("provider"),
            "input_cost": round(input_cost * rate, 6),
            "output_cost": round(output_cost * rate, 6),
            "total_cost": round((input_cost + output_cost) * rate, 6),
            "pricing": pricing,
            "quantity": request.quantity,
        })

    results.sort(key=lambda x: x["total_cost"])
    cheapest = results[0]["model_id"] if results else None

    return {
        "code": 200, "message": "success",
        "data": results,
        "meta": {
            "input_tokens": request.input_tokens,
            "output_tokens": request.output_tokens,
            "quantity": request.quantity,
            "currency": currency,
            "cheapest_model": cheapest,
        }
    }


@app.get("/api/exchange-rate")
async def get_exchange_rate():
    return {
        "code": 200, "message": "success",
        "data": {
            "base": "USD",
            "rates": {"CNY": 7.25, "EUR": 0.92, "JPY": 149.5, "GBP": 0.79, "USD": 1.0},
            "updated_at": "2026-04-26",
        }
    }


@app.get("/docs")
async def custom_docs():
    return Response(content=DOCS_HTML, media_type="text/html; charset=utf-8")


LEADERBOARD_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "leaderboard")
if not os.path.exists(LEADERBOARD_DATA_DIR):
    LEADERBOARD_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "leaderboard")

def _load_leaderboard_json(filename: str):
    file_path = os.path.join(LEADERBOARD_DATA_DIR, filename)
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/leaderboard/categories")
async def get_leaderboard_categories():
    index = _load_leaderboard_json("index.json")
    if not index:
        return {"code": 200, "message": "success", "data": {"general": [], "multimodal": []}}
    general = []
    multimodal = []
    for item in index:
        if item.get("group") == "general":
            general.append(item)
        else:
            multimodal.append(item)
    return {"code": 200, "message": "success", "data": {"general": general, "multimodal": multimodal}}

@app.get("/api/leaderboard/superclue/{category}")
async def get_superclue_leaderboard(
    category: str,
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=200),
):
    data = _load_leaderboard_json(f"{category}.json")
    if not data:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    rows = data.get("rows", [])
    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]
    return {
        "code": 200, "message": "success",
        "data": {
            "key": data.get("key", category),
            "name": data.get("name", ""),
            "group": data.get("group", ""),
            "source": data.get("source", ""),
            "source_date": data.get("source_date", ""),
            "headers": data.get("headers", []),
            "crawl_time": data.get("crawl_time", ""),
            "rows": page_rows,
            "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
    }
