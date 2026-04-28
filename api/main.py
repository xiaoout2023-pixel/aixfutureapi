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
    q: Optional[str] = Query(None, description="搜索关键词：模型名、厂商名、标签"),
    task: Optional[str] = Query(None, description="任务类型：text_classification/code_generation/translation/reasoning/summarization/multimodal"),
    provider: Optional[str] = Query(None, description="厂商筛选，逗号分隔，如 openai,anthropic"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    text_generation: Optional[bool] = Query(None),
    code_generation: Optional[bool] = Query(None),
    vision: Optional[bool] = Query(None),
    audio: Optional[bool] = Query(None),
    multimodal: Optional[bool] = Query(None),
    tool_calling: Optional[bool] = Query(None),
    reasoning_level: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
    min_input_price: Optional[float] = Query(None, description="输入价格下限"),
    max_input_price: Optional[float] = Query(None, description="输入价格上限"),
    min_output_price: Optional[float] = Query(None, description="输出价格下限"),
    max_output_price: Optional[float] = Query(None, description="输出价格上限"),
    sort_by: Optional[str] = Query("cost_efficiency_score", pattern="^(overall_score|cost_efficiency_score|input_price|output_price|context_length)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(20, ge=1, le=100)
):
    task_to_tags = {
        "text_classification": ["reasoning"],
        "code_generation": ["coding"],
        "translation": ["fast"],
        "reasoning": ["reasoning"],
        "summarization": ["fast"],
        "multimodal": ["multimodal"]
    }
    task_to_capability = {
        "text_classification": "text_generation",
        "code_generation": "code_generation",
        "translation": "text_generation",
        "reasoning": None,
        "summarization": "text_generation",
        "multimodal": "multimodal"
    }
    task_to_reasoning = {
        "reasoning": "high"
    }

    filters = {
        "has_vision": vision,
        "has_tool_calling": tool_calling,
        "text_generation": text_generation,
        "code_generation": code_generation,
        "audio": audio,
        "multimodal": multimodal,
        "reasoning_level": reasoning_level,
        "min_input_price": min_input_price,
        "max_input_price": max_input_price,
        "min_output_price": min_output_price,
        "max_output_price": max_output_price,
        "sort_by": sort_by,
        "sort_order": sort_order
    }

    if q:
        filters["q"] = q

    if task:
        filter_tags = task_to_tags.get(task, [])
        cap = task_to_capability.get(task)
        reason_level = task_to_reasoning.get(task)
        if filter_tags:
            filters["tags"] = filter_tags
        if cap and code_generation is None and text_generation is None:
            if cap == "code_generation":
                filters["code_generation"] = True
            elif cap == "text_generation":
                filters["text_generation"] = True
            elif cap == "multimodal":
                filters["multimodal"] = True
        if reason_level and not reasoning_level:
            filters["reasoning_level"] = reason_level

    if tags:
        existing_tags = filters.get("tags", [])
        new_tags = [t.strip() for t in tags.split(",")]
        filters["tags"] = existing_tags + new_tags

    models = await get_repo().search_models(filters)

    if provider:
        provider_list = [p.strip().lower() for p in provider.split(",")]
        models = [m for m in models if m.get("provider", "").lower() in provider_list]

    if not models and not q and not task:
        recommendations = await get_repo().get_recommendations()
        return {
            "code": 200,
            "message": "success",
            "data": [],
            "total": 0,
            "suggestions": recommendations,
            "empty_state": True
        }

    total = len(models)
    start = (page - 1) * page_size
    end = start + page_size
    models = models[start:end]

    result = {
        "code": 200,
        "message": "success",
        "data": models,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

    if not models and (q or task):
        suggestions = await get_repo().get_search_suggestions(q or task)
        result["suggestions"] = suggestions["suggestions"]

    return result

@app.get("/api/search/suggest")
async def search_suggest(q: str = Query(..., description="搜索关键词")):
    if len(q) < 1:
        return {"code": 200, "message": "success", "data": {"suggestions": [], "popular_tags": []}}
    
    suggestions = await get_repo().get_search_suggestions(q)
    
    all_models = await get_repo().get_all_models()
    tag_counts = {}
    for m in all_models:
        for tag in m.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "suggestions": suggestions["suggestions"],
            "popular_tags": [{"tag": t, "count": c} for t, c in popular_tags]
        }
    }

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
            "status": "/api/status",
            "scenarios": "/api/calculator/scenarios",
            "calculator_templates": "/api/calculator/templates",
            "leaderboard_categories": "/api/leaderboard/categories",
            "leaderboard": "/api/leaderboard/{category}",
            "model_marketplace": "/api/models/{model_id}/marketplace",
            "marketplace_compare": "/api/marketplace/compare?models=model1,model2"
        }
    }

# ========== Calculator Pro: Scenario Cost Simulator ==========

class ScenarioCreate(BaseModel):
    name: str

class ScenarioUpdate(BaseModel):
    name: str

class StepCreate(BaseModel):
    scenario_id: str
    task_type: Optional[str] = ""
    model_id: Optional[str] = ""
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    daily_calls: Optional[int] = 1
    cache_hit_rate: Optional[float] = 0.0

class StepUpdate(BaseModel):
    task_type: Optional[str] = ""
    model_id: Optional[str] = ""
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    daily_calls: Optional[int] = 1
    cache_hit_rate: Optional[float] = 0.0

class StepReorder(BaseModel):
    id: str
    step_order: int

@app.post("/api/calculator/scenarios")
async def create_scenario(data: ScenarioCreate):
    scenario = await get_repo().create_scenario(data.name)
    return {"code": 200, "message": "success", "data": scenario}

@app.get("/api/calculator/scenarios")
async def list_scenarios():
    scenarios = await get_repo().get_all_scenarios()
    return {"code": 200, "message": "success", "data": scenarios, "total": len(scenarios)}

@app.get("/api/calculator/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    scenario = await get_repo().get_scenario_with_costs(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"code": 200, "message": "success", "data": scenario}

@app.put("/api/calculator/scenarios/{scenario_id}")
async def update_scenario(scenario_id: str, data: ScenarioUpdate):
    scenario = await get_repo().update_scenario(scenario_id, data.name)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"code": 200, "message": "success", "data": scenario}

@app.delete("/api/calculator/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str):
    await get_repo().delete_scenario(scenario_id)
    return {"code": 200, "message": "success"}

@app.post("/api/calculator/scenarios/{scenario_id}/steps")
async def add_step(scenario_id: str, data: StepCreate):
    step_data = data.dict()
    step_data["scenario_id"] = scenario_id
    existing_steps = await get_repo().get_scenario_steps(scenario_id)
    step_data["step_order"] = len(existing_steps)
    step = await get_repo().add_step(step_data)
    return {"code": 200, "message": "success", "data": step}

@app.get("/api/calculator/scenarios/{scenario_id}/steps")
async def list_steps(scenario_id: str):
    steps = await get_repo().get_scenario_steps(scenario_id)
    return {"code": 200, "message": "success", "data": steps, "total": len(steps)}

@app.put("/api/calculator/steps/{step_id}")
async def update_step(step_id: str, data: StepUpdate):
    step = await get_repo().update_step(step_id, data.dict())
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"code": 200, "message": "success", "data": step}

@app.delete("/api/calculator/steps/{step_id}")
async def delete_step(step_id: str):
    await get_repo().delete_step(step_id)
    return {"code": 200, "message": "success"}

@app.post("/api/calculator/scenarios/{scenario_id}/reorder")
async def reorder_steps(scenario_id: str, data: List[StepReorder]):
    steps = await get_repo().reorder_steps(scenario_id, [s.dict() for s in data])
    return {"code": 200, "message": "success", "data": steps}

@app.post("/api/calculator/scenarios/{scenario_id}/duplicate")
async def duplicate_scenario(scenario_id: str):
    scenario = await get_repo().get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    from datetime import datetime
    now = datetime.now().isoformat()
    new_name = f"{scenario['name']} (副本)"
    new_scenario = await get_repo().create_scenario(new_name)
    
    steps = await get_repo().get_scenario_steps(scenario_id)
    for i, step in enumerate(steps):
        step_data = {
            "scenario_id": new_scenario["id"],
            "step_order": i,
            "task_type": step.get("task_type", ""),
            "model_id": step.get("model_id", ""),
            "input_tokens": step.get("input_tokens", 0),
            "output_tokens": step.get("output_tokens", 0),
            "daily_calls": step.get("daily_calls", 1),
            "cache_hit_rate": step.get("cache_hit_rate", 0.0)
        }
        await get_repo().add_step(step_data)
    
    result = await get_repo().get_scenario_with_costs(new_scenario["id"])
    return {"code": 200, "message": "success", "data": result}

@app.get("/api/calculator/templates")
async def get_templates():
    templates = await get_repo().get_templates()
    return {"code": 200, "message": "success", "data": templates}

@app.post("/api/calculator/templates/{template_name}/apply")
async def apply_template(template_name: str):
    templates = await get_repo().get_templates()
    template = None
    for t in templates:
        if t["name"] == template_name:
            template = t
            break
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    scenario = await get_repo().create_scenario(template["name"])
    
    for i, step_data in enumerate(template["steps"]):
        step_data["scenario_id"] = scenario["id"]
        step_data["step_order"] = i
        await get_repo().add_step(step_data)
    
    result = await get_repo().get_scenario_with_costs(scenario["id"])
    return {"code": 200, "message": "success", "data": result}

@app.post("/api/calculator/compare")
async def compare_scenarios(scenario_ids: List[str]):
    results = []
    for sid in scenario_ids:
        scenario = await get_repo().get_scenario_with_costs(sid)
        if scenario:
            results.append({
                "id": scenario["id"],
                "name": scenario["name"],
                "summary": scenario["summary"]
            })
    
    if len(results) < 2:
        return {"code": 200, "message": "success", "data": {"scenarios": results, "comparison": None}}
    
    comparison = {
        "daily_cost_diff": round(results[0]["summary"]["total_daily_cost"] - results[1]["summary"]["total_daily_cost"], 4),
        "monthly_cost_diff": round(results[0]["summary"]["total_monthly_cost"] - results[1]["summary"]["total_monthly_cost"], 2),
        "yearly_cost_diff": round(results[0]["summary"]["total_yearly_cost"] - results[1]["summary"]["total_yearly_cost"], 2)
    }
    
    return {"code": 200, "message": "success", "data": {"scenarios": results, "comparison": comparison}}

# ========== Leaderboard: SuperCLUE Rankings ==========

LEADERBOARD_CATEGORY_META = {
    "general_overall": {"name": "总排行榜", "group": "general", "description": "SuperCLUE通用榜综合能力排名"},
    "general_reasoning": {"name": "推理模型总排行榜", "group": "general", "description": "推理类模型综合排名"},
    "general_base": {"name": "基础模型总排行榜", "group": "general", "description": "基础/非推理模型综合排名"},
    "general_reasoning_task": {"name": "推理任务总排行榜", "group": "general", "description": "按推理任务维度排名"},
    "general_opensource": {"name": "开源排行榜", "group": "general", "description": "开源模型综合排名"},
    "multimodal_vlm": {"name": "SuperCLUE-VLM 多模态视觉语言模型", "group": "multimodal", "description": "多模态视觉语言模型评测"},
    "multimodal_image": {"name": "SuperCLUE-Image 文生图", "group": "multimodal", "description": "文生图模型竞技场排名"},
    "multimodal_comicshorts": {"name": "SuperCLUE-ComicShorts AI漫剧大模型", "group": "multimodal", "description": "AI漫剧大模型评测"},
    "multimodal_r2v": {"name": "SuperCLUE-R2V 参考生视频", "group": "multimodal", "description": "参考生视频模型评测"},
    "multimodal_i2v": {"name": "SuperCLUE-I2V 图生视频模型", "group": "multimodal", "description": "图生视频模型竞技场排名"},
    "multimodal_edit": {"name": "SuperCLUE-Edit 图像编辑", "group": "multimodal", "description": "图像编辑模型评测"},
    "multimodal_t2v": {"name": "SuperCLUE-T2V 文生视频", "group": "multimodal", "description": "文生视频模型竞技场排名"},
    "multimodal_world": {"name": "SuperCLUE-World 世界模型", "group": "multimodal", "description": "世界模型评测"},
    "multimodal_voice_av": {"name": "SuperCLUE-Voice 实时音视频", "group": "multimodal", "description": "实时音视频模型评测"},
    "multimodal_voice_chat": {"name": "SuperCLUE-Voice 实时语音交互", "group": "multimodal", "description": "实时语音交互模型评测"},
    "multimodal_tts": {"name": "SuperCLUE-TTS 语音合成", "group": "multimodal", "description": "语音合成模型评测"},
    "multimodal_v": {"name": "SuperCLUE-V 多模态理解", "group": "multimodal", "description": "多模态理解模型评测"},
    "multimodal_vlr": {"name": "SuperCLUE-VLR 视觉推理", "group": "multimodal", "description": "视觉推理模型评测"},
}

@app.get("/api/leaderboard/categories")
async def get_leaderboard_categories():
    db_categories = await get_repo().get_leaderboard_categories()
    db_map = {c["category"]: c for c in db_categories}

    general = []
    multimodal = []
    for key, meta in LEADERBOARD_CATEGORY_META.items():
        db_info = db_map.get(key, {})
        item = {
            "key": key,
            "name": meta["name"],
            "description": meta["description"],
            "model_count": db_info.get("model_count", 0),
            "updated_at": db_info.get("updated_at"),
        }
        if meta["group"] == "general":
            general.append(item)
        else:
            multimodal.append(item)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "general": general,
            "multimodal": multimodal
        }
    }

@app.get("/api/leaderboard/{category}")
async def get_leaderboard(
    category: str,
    opensource: Optional[str] = Query(None, description="开源类型筛选: open/closed"),
    domestic: Optional[str] = Query(None, description="地域筛选: domestic/overseas"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=100)
):
    if category not in LEADERBOARD_CATEGORY_META:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found. Available: {list(LEADERBOARD_CATEGORY_META.keys())}")

    result = await get_repo().get_leaderboard(category, opensource, domestic, page, page_size)
    meta = LEADERBOARD_CATEGORY_META[category]

    return {
        "code": 200,
        "message": "success",
        "data": {
            "category": category,
            "name": meta["name"],
            "description": meta["description"],
            "group": meta["group"],
            "entries": result["entries"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"],
        }
    }

@app.get("/api/leaderboard/{category}/detail")
async def get_leaderboard_detail(category: str):
    if category not in LEADERBOARD_CATEGORY_META:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    detail = await get_repo().get_leaderboard_detail(category)
    if not detail:
        raise HTTPException(status_code=404, detail=f"No data found for category '{category}'")

    meta = LEADERBOARD_CATEGORY_META[category]
    return {
        "code": 200,
        "message": "success",
        "data": {
            **detail,
            "name": meta["name"],
            "description": meta["description"],
            "group": meta["group"],
        }
    }

# ========== Marketplace: Multi-Provider Price Comparison ==========

@app.get("/api/models/{model_id}/marketplace")
async def get_model_marketplace(model_id: str):
    repo = get_repo()
    model = await repo.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    marketplace_data = await repo.get_model_marketplace(model_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "model_id": model_id,
            "model_name": model.get("model_name"),
            "provider": model.get("provider"),
            "official_pricing": model.get("pricing"),
            "marketplace": marketplace_data,
            "marketplace_count": len(marketplace_data),
        }
    }

@app.get("/api/marketplace/compare")
async def marketplace_compare(models: str = Query(..., description="逗号分隔的模型ID列表")):
    model_ids = [m.strip() for m in models.split(",") if m.strip()]
    if not model_ids:
        raise HTTPException(status_code=400, detail="At least one model_id required")
    if len(model_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 models per comparison")
    result = await get_repo().get_marketplace_compare(model_ids)
    return {
        "code": 200,
        "message": "success",
        "data": result,
        "meta": {
            "model_count": len(model_ids),
            "models_compared": model_ids
        }
    }
