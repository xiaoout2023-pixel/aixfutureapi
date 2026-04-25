from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys

# Resolve project root for Vercel Serverless environment
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from db.turso import TursoDB
from db.repository import ModelRepository

DOCS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs.html')
with open(DOCS_PATH, 'r', encoding='utf-8') as f:
    DOCS_HTML = f.read()

app = FastAPI(
    title="AI Model Pricing API",
    description="AI模型价格采集与对比系统",
    version="0.3.0",
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

# Lazy initialization for Serverless environment
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

@app.get("/api/models")
async def list_models(
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    min_context: Optional[int] = Query(None),
    max_input_price: Optional[float] = Query(None),
    max_output_price: Optional[float] = Query(None),
    has_vision: Optional[bool] = Query(None),
    has_tool_calling: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="模型类型：llm(大语言模型)/multimodal(多模态)/vision(视觉)/audio(音频)/code(代码)"),
    access: Optional[str] = Query(None, description="开源类型：open(开源)/closed(闭源)"),
    sort_by: Optional[str] = Query("overall_score", pattern="^(overall_score|cost_efficiency_score|input_price|output_price|context_length)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(20, ge=1, le=100)
):
    filters = {
        "provider": provider,
        "status": status,
        "min_context": min_context,
        "max_input_price": max_input_price,
        "max_output_price": max_output_price,
        "has_vision": has_vision,
        "has_tool_calling": has_tool_calling,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    if tags:
        filters["tags"] = [t.strip() for t in tags.split(",")]
    
    models = await get_repo().search_models(filters)
    
    # Apply type filter
    if type:
        type_map = {
            "llm": lambda m: m.get("capabilities", {}).get("text_generation") and not m.get("capabilities", {}).get("multimodal"),
            "multimodal": lambda m: m.get("capabilities", {}).get("multimodal"),
            "vision": lambda m: m.get("capabilities", {}).get("vision") and not m.get("capabilities", {}).get("multimodal"),
            "audio": lambda m: m.get("capabilities", {}).get("audio"),
            "code": lambda m: m.get("capabilities", {}).get("code_generation")
        }
        filter_fn = type_map.get(type)
        if filter_fn:
            models = [m for m in models if filter_fn(m)]
    
    # Apply access filter
    if access:
        open_source_providers = {"openai", "anthropic", "google", "mistral"}
        if access == "open":
            models = [m for m in models if m.get("provider") not in open_source_providers]
        elif access == "closed":
            models = [m for m in models if m.get("provider") in open_source_providers]
    
    # Pagination
    total = len(models)
    start = (page - 1) * page_size
    end = start + page_size
    models = models[start:end]
    
    return {
        "code": 200,
        "message": "success",
        "data": models,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    model = await get_repo().get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return {"code": 200, "message": "success", "data": model}

@app.get("/api/compare")
async def compare_models(
    models: str = Query(..., description="模型ID，逗号分隔")
):
    model_ids = [m.strip() for m in models.split(",")]
    
    result = []
    for model_id in model_ids:
        model = await get_repo().get_model(model_id)
        if model:
            result.append(model)
    
    if not result:
        raise HTTPException(status_code=404, detail="No models found")
    
    meta = {}
    if result:
        cheapest_input = min(result, key=lambda x: x.get("pricing", {}).get("input_price_per_1m_tokens", float("inf")))
        cheapest_output = min(result, key=lambda x: x.get("pricing", {}).get("output_price_per_1m_tokens", float("inf")))
        longest_context = max(result, key=lambda x: x.get("capabilities", {}).get("context_length", 0))
        best_overall = max(result, key=lambda x: x.get("scores", {}).get("overall_score", 0))
        
        meta = {
            "cheapest_input": cheapest_input.get("model_id"),
            "cheapest_output": cheapest_output.get("model_id"),
            "longest_context": longest_context.get("model_id"),
            "best_overall": best_overall.get("model_id")
        }
    
    return {"code": 200, "message": "success", "data": result, "meta": meta}

@app.get("/api/providers")
async def list_providers():
    providers = await get_repo().get_providers()
    return {"code": 200, "message": "success", "data": providers}

@app.post("/api/cost/calculate")
async def calculate_cost(request: CostCalcRequest):
    model = await get_repo().get_model(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")
    
    pricing = model.get("pricing", {})
    input_price = pricing.get("input_price_per_1m_tokens", 0)
    output_price = pricing.get("output_price_per_1m_tokens", 0)
    
    input_cost = (request.input_tokens / 1000000) * input_price * request.quantity
    output_cost = (request.output_tokens / 1000000) * output_price * request.quantity
    total_cost = input_cost + output_cost
    
    # Currency conversion
    currency = request.currency.upper()
    exchange_rates = {
        "USD": 1.0,
        "CNY": 7.25,
        "EUR": 0.92,
        "JPY": 149.5,
        "GBP": 0.79
    }
    rate = exchange_rates.get(currency, 1.0)
    currency_symbol = {"USD": "$", "CNY": "¥", "EUR": "€", "JPY": "¥", "GBP": "£"}.get(currency, currency)
    
    return {
        "code": 200,
        "message": "success",
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
                "exchange_rate": rate if currency != "USD" else None
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
        
        pricing = model.get("pricing", {})
        input_price = pricing.get("input_price_per_1m_tokens", 0)
        output_price = pricing.get("output_price_per_1m_tokens", 0)
        
        input_cost = (request.input_tokens / 1000000) * input_price * request.quantity
        output_cost = (request.output_tokens / 1000000) * output_price * request.quantity
        
        currency = request.currency.upper()
        exchange_rates = {
            "USD": 1.0,
            "CNY": 7.25,
            "EUR": 0.92,
            "JPY": 149.5,
            "GBP": 0.79
        }
        rate = exchange_rates.get(currency, 1.0)
        
        results.append({
            "model_id": model_id,
            "model_name": model.get("model_name"),
            "provider": model.get("provider"),
            "input_cost": round(input_cost * rate, 6),
            "output_cost": round(output_cost * rate, 6),
            "total_cost": round((input_cost + output_cost) * rate, 6),
            "pricing": pricing,
            "quantity": request.quantity
        })
    
    results.sort(key=lambda x: x["total_cost"])
    
    cheapest = results[0]["model_id"] if results else None
    
    return {
        "code": 200,
        "message": "success",
        "data": results,
        "meta": {
            "input_tokens": request.input_tokens,
            "output_tokens": request.output_tokens,
            "quantity": request.quantity,
            "currency": currency,
            "cheapest_model": cheapest
        }
    }

@app.get("/api/exchange-rate")
async def get_exchange_rate():
    return {
        "code": 200,
        "message": "success",
        "data": {
            "base": "USD",
            "rates": {
                "CNY": 7.25,
                "EUR": 0.92,
                "JPY": 149.5,
                "GBP": 0.79,
                "USD": 1.0
            },
            "updated_at": "2026-04-26"
        }
    }

@app.get("/api/model-types")
async def get_model_types():
    return {
        "code": 200,
        "message": "success",
        "data": [
            {"key": "llm", "name": "大语言模型", "description": "文本生成、对话等"},
            {"key": "multimodal", "name": "多模态", "description": "支持图文音视频等多种模态"},
            {"key": "vision", "name": "视觉", "description": "图像理解、生成"},
            {"key": "audio", "name": "音频", "description": "语音识别、合成"},
            {"key": "code", "name": "代码", "description": "代码生成、补全"}
        ]
    }

@app.get("/api/search")
async def search_models(
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    text_generation: Optional[bool] = Query(None),
    code_generation: Optional[bool] = Query(None),
    vision: Optional[bool] = Query(None),
    audio: Optional[bool] = Query(None),
    multimodal: Optional[bool] = Query(None),
    tool_calling: Optional[bool] = Query(None),
    reasoning_level: Optional[str] = Query(None, pattern="^(low|medium|high)$")
):
    filters = {
        "has_vision": vision,
        "has_tool_calling": tool_calling
    }
    if tags:
        filters["tags"] = [t.strip() for t in tags.split(",")]
    
    models = await get_repo().search_models(filters)
    
    if code_generation is not None:
        models = [m for m in models if m.get("capabilities", {}).get("code_generation") == code_generation]
    if text_generation is not None:
        models = [m for m in models if m.get("capabilities", {}).get("text_generation") == text_generation]
    if audio is not None:
        models = [m for m in models if m.get("capabilities", {}).get("audio") == audio]
    if multimodal is not None:
        models = [m for m in models if m.get("capabilities", {}).get("multimodal") == multimodal]
    if reasoning_level:
        models = [m for m in models if m.get("capabilities", {}).get("reasoning_level") == reasoning_level]
    
    return {"code": 200, "message": "success", "data": models, "total": len(models)}

@app.get("/api/status")
async def get_status():
    models = await get_repo().get_all_models()
    providers = await get_repo().get_providers()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_models": len(models),
            "providers": len(providers),
            "provider_list": [p["provider"] for p in providers]
        }
    }

@app.get("/docs")
async def custom_docs():
    return Response(content=DOCS_HTML, media_type="text/html; charset=utf-8")

@app.get("/")
async def root():
    return {
        "name": "AI Model Pricing API",
        "version": "0.3.0",
        "docs": "/docs",
        "endpoints": {
            "models": "/api/models",
            "model_detail": "/api/models/{model_id}",
            "compare": "/api/compare?models=gpt-4o,claude-3-opus",
            "providers": "/api/providers",
            "search": "/api/search?tags=vision,coding",
            "cost_calculate": "POST /api/cost/calculate",
            "cost_compare": "POST /api/cost/compare",
            "exchange_rate": "/api/exchange-rate",
            "model_types": "/api/model-types",
            "status": "/api/status"
        }
    }
