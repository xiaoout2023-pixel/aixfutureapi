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

DOCS_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Model Pricing API - 接口文档</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #f5f5f5; color: #333; }
.api-base { background: #1a1a2e; color: #fff; padding: 20px 40px; border-bottom: 2px solid #16213e; }
.api-base h1 { font-size: 22px; margin-bottom: 4px; }
.api-base p { color: #aaa; font-size: 14px; }
.api-base a { color: #7ec8e3; }
.container { display: flex; min-height: calc(100vh - 80px); }
.sidebar { width: 220px; background: #fff; border-right: 1px solid #ddd; padding: 16px 0; position: fixed; top: 0; bottom: 0; overflow-y: auto; }
.sidebar h3 { padding: 0 16px 8px; font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #eee; margin-bottom: 8px; }
.sidebar a { display: block; padding: 6px 16px; color: #555; text-decoration: none; font-size: 13px; border-left: 3px solid transparent; }
.sidebar a:hover { background: #f0f7ff; color: #1a73e8; }
.sidebar a .method { display: inline-block; width: 42px; font-size: 11px; font-weight: bold; text-align: center; border-radius: 3px; margin-right: 4px; }
.sidebar a .method.get { background: #61affe; color: #fff; }
.sidebar a .method.post { background: #49cc90; color: #fff; }
.main { margin-left: 220px; flex: 1; padding: 32px 40px; max-width: 900px; }
.endpoint { margin-bottom: 40px; }
.endpoint h2 { font-size: 18px; margin-bottom: 4px; }
.endpoint h2 .method { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 13px; font-weight: bold; margin-right: 8px; }
.endpoint h2 .method.get { background: #61affe; color: #fff; }
.endpoint h2 .method.post { background: #49cc90; color: #fff; }
.endpoint .desc { color: #666; margin-bottom: 12px; font-size: 14px; }
.endpoint h3 { font-size: 14px; margin: 12px 0 6px; color: #444; }
.endpoint table { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 13px; }
.endpoint th, .endpoint td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
.endpoint th { background: #f9f9f9; font-weight: 600; }
.endpoint code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
pre { background: #282c34; color: #abb2bf; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 12px; line-height: 1.5; margin-bottom: 12px; }
pre .comment { color: #5c6370; }
.section-title { font-size: 15px; font-weight: bold; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #1a1a2e; }
</style>
</head>
<body>
<div class="api-base">
<h1>AI Model Pricing API</h1>
<p>AI模型价格采集与对比系统 v0.3.0 &mdash; <a href="/">https://aixfutureapi.vercel.app</a></p>
</div>
<div class="container">
<div class="sidebar">
<h3>目录</h3>
<a href="#data-model"><span>数据模型</span></a>
<a href="#list-models"><span class="method get">GET</span> /api/models</a>
<a href="#get-model"><span class="method get">GET</span> /api/models/:id</a>
<a href="#compare"><span class="method get">GET</span> /api/compare</a>
<a href="#providers"><span class="method get">GET</span> /api/providers</a>
<a href="#search"><span class="method get">GET</span> /api/search</a>
<a href="#status"><span class="method get">GET</span> /api/status</a>
<a href="#exchange-rate"><span class="method get">GET</span> /api/exchange-rate</a>
<a href="#model-types"><span class="method get">GET</span> /api/model-types</a>
<a href="#cost-calc"><span class="method post">POST</span> /api/cost/calculate</a>
<a href="#cost-compare"><span class="method post">POST</span> /api/cost/compare</a>
</div>
<div class="main">

<div class="endpoint" id="data-model">
<h2>数据模型</h2>
<p class="desc">每个模型对象包含以下字段：</p>
<pre>model_id: 唯一标识（string，如 gpt-4o）
model_name: 模型名称（string，如 GPT-4o）
provider: 厂商（string，如 openai / aliyun / anthropic）
release_date: 发布时间（YYYY-MM-DD）
status: 状态（active / beta / deprecated）

capabilities: 能力
  text_generation: 文本生成（true/false）
  code_generation: 代码生成（true/false）
  vision: 图像理解（true/false）
  audio: 音频能力（true/false）
  multimodal: 多模态（true/false）
  tool_calling: 工具调用（true/false）
  context_length: 最大上下文长度（数字）
  reasoning_level: 推理等级（low/medium/high）

pricing: 定价
  input_price_per_1m_tokens: 输入价格（每100万token，USD）
  output_price_per_1m_tokens: 输出价格（每100万token，USD）
  currency: 货币（默认USD）

scores: 评分
  overall_score: 综合评分（0-100）
  cost_efficiency_score: 性价比评分（0-100）

tags: 标签数组（如 ["多模态", "coding", "vision"]）
source: 来源信息</pre>
</div>

<div class="endpoint" id="list-models">
<h2><span class="method get">GET</span> /api/models</h2>
<p class="desc">模型列表。</p>
<h3>参数</h3>
<table>
<tr><th>参数</th><th>类型</th><th>说明</th></tr>
<tr><td>provider</td><td>string</td><td>按厂商筛选，如 openai</td></tr>
<tr><td>status</td><td>string</td><td>按状态筛选，如 active</td></tr>
<tr><td>tags</td><td>string</td><td>按标签筛选，逗号分隔，如 vision,coding</td></tr>
<tr><td>type</td><td>string</td><td>按类型筛选，llm/multimodal/vision/audio/code</td></tr>
<tr><td>access</td><td>string</td><td>按开源类型筛选，open/closed</td></tr>
<tr><td>min_context</td><td>int</td><td>最小上下文长度</td></tr>
<tr><td>max_input_price</td><td>float</td><td>最大输入价格（每百万tokens）</td></tr>
<tr><td>max_output_price</td><td>float</td><td>最大输出价格（每百万tokens）</td></tr>
<tr><td>has_vision</td><td>bool</td><td>是否支持视觉，true/false</td></tr>
<tr><td>has_tool_calling</td><td>bool</td><td>是否支持工具调用，true/false</td></tr>
<tr><td>sort_by</td><td>string</td><td>排序字段：overall_score/cost_efficiency_score/input_price/output_price/context_length</td></tr>
<tr><td>sort_order</td><td>string</td><td>排序方向：asc/desc，默认 desc</td></tr>
<tr><td>page</td><td>int</td><td>页码，默认 1</td></tr>
<tr><td>page_size</td><td>int</td><td>每页数量，默认 20，最大 100</td></tr>
</table>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": [模型对象数组],
  "total": 总数量,
  "page": 当前页码,
  "page_size": 每页数量,
  "total_pages": 总页数
}</pre>
<h3>示例</h3>
<pre>/api/models?provider=openai
/api/models?type=multimodal
/api/models?access=closed
/api/models?page=1&amp;page_size=10</pre>
</div>

<div class="endpoint" id="get-model">
<h2><span class="method get">GET</span> /api/models/{model_id}</h2>
<p class="desc">单个模型详情。</p>
<h3>参数</h3>
<table>
<tr><th>参数</th><th>说明</th></tr>
<tr><td>model_id</td><td>路径参数，模型ID</td></tr>
</table>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": 模型对象
}</pre>
</div>

<div class="endpoint" id="compare">
<h2><span class="method get">GET</span> /api/compare</h2>
<p class="desc">模型对比。</p>
<h3>参数</h3>
<table>
<tr><th>参数</th><th>说明</th></tr>
<tr><td>models</td><td>模型ID，逗号分隔，如 gpt-4o,claude-3-opus</td></tr>
</table>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": [模型对象数组],
  "meta": {
    "cheapest_input": "最便宜输入的模型ID",
    "cheapest_output": "最便宜输出的模型ID",
    "longest_context": "最长上下文的模型ID",
    "best_overall": "综合评分最高的模型ID"
  }
}</pre>
</div>

<div class="endpoint" id="providers">
<h2><span class="method get">GET</span> /api/providers</h2>
<p class="desc">供应商列表。</p>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": [
    {
      "provider": "openai",
      "model_count": 8
    }
  ]
}</pre>
</div>

<div class="endpoint" id="search">
<h2><span class="method get">GET</span> /api/search</h2>
<p class="desc">搜索模型。</p>
<h3>参数</h3>
<table>
<tr><th>参数</th><th>类型</th><th>说明</th></tr>
<tr><td>tags</td><td>string</td><td>标签筛选，逗号分隔</td></tr>
<tr><td>text_generation</td><td>bool</td><td>文本生成，true/false</td></tr>
<tr><td>code_generation</td><td>bool</td><td>代码生成，true/false</td></tr>
<tr><td>vision</td><td>bool</td><td>视觉，true/false</td></tr>
<tr><td>audio</td><td>bool</td><td>音频，true/false</td></tr>
<tr><td>multimodal</td><td>bool</td><td>多模态，true/false</td></tr>
<tr><td>tool_calling</td><td>bool</td><td>工具调用，true/false</td></tr>
<tr><td>reasoning_level</td><td>string</td><td>推理等级，low/medium/high</td></tr>
</table>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": [模型对象数组],
  "total": 数量
}</pre>
</div>

<div class="endpoint" id="status">
<h2><span class="method get">GET</span> /api/status</h2>
<p class="desc">服务状态。</p>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": {
    "total_models": 17,
    "providers": 3,
    "provider_list": ["openai", "aliyun", "anthropic"]
  }
}</pre>
</div>

<div class="endpoint" id="exchange-rate">
<h2><span class="method get">GET</span> /api/exchange-rate</h2>
<p class="desc">汇率。</p>
<h3>响应</h3>
<pre>{
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
}</pre>
</div>

<div class="endpoint" id="model-types">
<h2><span class="method get">GET</span> /api/model-types</h2>
<p class="desc">模型分类。</p>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": [
    {"key": "llm", "name": "大语言模型", "description": "文本生成、对话等"},
    {"key": "multimodal", "name": "多模态", "description": "支持图文音视频等多种模态"},
    {"key": "vision", "name": "视觉", "description": "图像理解、生成"},
    {"key": "audio", "name": "音频", "description": "语音识别、合成"},
    {"key": "code", "name": "代码", "description": "代码生成、补全"}
  ]
}</pre>
</div>

<div class="endpoint" id="cost-calc">
<h2><span class="method post">POST</span> /api/cost/calculate</h2>
<p class="desc">单个模型成本计算。</p>
<h3>请求体</h3>
<pre>{
  "model_id": "gpt-4o",
  "input_tokens": 100000,
  "output_tokens": 50000,
  "quantity": 10,
  "currency": "CNY"
}</pre>
<h3>参数</h3>
<table>
<tr><th>参数</th><th>类型</th><th>必填</th><th>说明</th></tr>
<tr><td>model_id</td><td>string</td><td>是</td><td>模型ID</td></tr>
<tr><td>input_tokens</td><td>int</td><td>否</td><td>输入token数量，默认1000</td></tr>
<tr><td>output_tokens</td><td>int</td><td>否</td><td>输出token数量，默认1000</td></tr>
<tr><td>quantity</td><td>int</td><td>否</td><td>调用次数，默认1</td></tr>
<tr><td>currency</td><td>string</td><td>否</td><td>货币 USD/CNY/EUR/JPY/GBP，默认USD</td></tr>
</table>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": {
    "model_id": "gpt-4o",
    "model_name": "GPT-4o",
    "provider": "openai",
    "input_tokens": 100000,
    "output_tokens": 50000,
    "quantity": 10,
    "pricing": {定价信息},
    "cost_breakdown": {
      "input_cost": 1.8125,
      "output_cost": 3.625,
      "total_cost": 5.4375,
      "currency": "CNY",
      "currency_symbol": "￥",
      "exchange_rate": 7.25
    }
  }
}</pre>
</div>

<div class="endpoint" id="cost-compare">
<h2><span class="method post">POST</span> /api/cost/compare</h2>
<p class="desc">多模型成本对比。</p>
<h3>请求体</h3>
<pre>{
  "models": ["gpt-4o", "claude-3-opus", "qwen-max"],
  "input_tokens": 100000,
  "output_tokens": 50000,
  "quantity": 10,
  "currency": "CNY"
}</pre>
<h3>参数</h3>
<table>
<tr><th>参数</th><th>类型</th><th>必填</th><th>说明</th></tr>
<tr><td>models</td><td>string[]</td><td>是</td><td>模型ID数组</td></tr>
<tr><td>input_tokens</td><td>int</td><td>否</td><td>输入token数量，默认1000</td></tr>
<tr><td>output_tokens</td><td>int</td><td>否</td><td>输出token数量，默认1000</td></tr>
<tr><td>quantity</td><td>int</td><td>否</td><td>调用次数，默认1</td></tr>
<tr><td>currency</td><td>string</td><td>否</td><td>货币 USD/CNY/EUR/JPY/GBP，默认USD</td></tr>
</table>
<h3>响应</h3>
<pre>{
  "code": 200,
  "message": "success",
  "data": [
    {
      "model_id": "gpt-4o",
      "model_name": "GPT-4o",
      "provider": "openai",
      "input_cost": 1.8125,
      "output_cost": 3.625,
      "total_cost": 5.4375,
      "pricing": {定价信息},
      "quantity": 10
    }
  ],
  "meta": {
    "input_tokens": 100000,
    "output_tokens": 50000,
    "quantity": 10,
    "currency": "CNY",
    "cheapest_model": "gpt-4o"
  }
}</pre>
</div>

</div>
</div>
</body>
</html>"""

app = FastAPI(
    title="AI Model Pricing API",
    description="AI模型价格采集与对比系统",
    version="0.3.0"
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
