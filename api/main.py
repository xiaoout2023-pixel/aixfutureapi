from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys

# 添加项目根目录到路径，以便能导入db模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.turso import TursoDB
from db.repository import ModelRepository

app = FastAPI(
    title="AI Model Pricing API",
    description="AI模型价格采集与对比系统",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = None
repo = None

@app.on_event("startup")
async def startup():
    global db, repo
    db = TursoDB()
    repo = ModelRepository(db)

class CostCalcRequest(BaseModel):
    model_id: str
    input_tokens: int = 1000
    output_tokens: int = 1000

class CostCompareRequest(BaseModel):
    models: List[str]
    input_tokens: int = 1000
    output_tokens: int = 1000

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
    sort_by: Optional[str] = Query("overall_score", pattern="^(overall_score|cost_efficiency_score|input_price|output_price|context_length)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$")
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
    
    models = await repo.search_models(filters)
    return {"code": 200, "message": "success", "data": models, "total": len(models)}

@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    model = await repo.get_model(model_id)
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
        model = await repo.get_model(model_id)
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
    providers = await repo.get_providers()
    return {"code": 200, "message": "success", "data": providers}

@app.post("/api/cost/calculate")
async def calculate_cost(request: CostCalcRequest):
    model = await repo.get_model(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")
    
    pricing = model.get("pricing", {})
    input_price = pricing.get("input_price_per_1m_tokens", 0)
    output_price = pricing.get("output_price_per_1m_tokens", 0)
    
    input_cost = (request.input_tokens / 1000000) * input_price
    output_cost = (request.output_tokens / 1000000) * output_price
    total_cost = input_cost + output_cost
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "model_id": request.model_id,
            "model_name": model.get("model_name"),
            "provider": model.get("provider"),
            "input_tokens": request.input_tokens,
            "output_tokens": request.output_tokens,
            "pricing": pricing,
            "cost_breakdown": {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
                "currency": pricing.get("currency", "USD")
            }
        }
    }

@app.post("/api/cost/compare")
async def compare_cost(request: CostCompareRequest):
    results = []
    for model_id in request.models:
        model = await repo.get_model(model_id)
        if not model:
            continue
        
        pricing = model.get("pricing", {})
        input_price = pricing.get("input_price_per_1m_tokens", 0)
        output_price = pricing.get("output_price_per_1m_tokens", 0)
        
        input_cost = (request.input_tokens / 1000000) * input_price
        output_cost = (request.output_tokens / 1000000) * output_price
        
        results.append({
            "model_id": model_id,
            "model_name": model.get("model_name"),
            "provider": model.get("provider"),
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
            "pricing": pricing
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
            "cheapest_model": cheapest
        }
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
    
    models = await repo.search_models(filters)
    
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
    models = await repo.get_all_models()
    providers = await repo.get_providers()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_models": len(models),
            "providers": len(providers),
            "provider_list": [p["provider"] for p in providers]
        }
    }

@app.get("/")
async def root():
    return {
        "name": "AI Model Pricing API",
        "version": "0.2.0",
        "docs": "/docs",
        "endpoints": {
            "models": "/api/models",
            "model_detail": "/api/models/{model_id}",
            "compare": "/api/compare?models=gpt-4o,claude-3-opus",
            "providers": "/api/providers",
            "search": "/api/search?tags=vision,coding",
            "cost_calculate": "POST /api/cost/calculate",
            "cost_compare": "POST /api/cost/compare",
            "status": "/api/status"
        }
    }
