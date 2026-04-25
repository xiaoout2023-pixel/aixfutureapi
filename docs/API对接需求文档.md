# AI Model Pricing API 接口文档

API 地址：`https://aixfutureapi.vercel.app`

---

## 接口总览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 模型列表 |
| GET | `/api/models/{model_id}` | 单个模型详情 |
| GET | `/api/compare` | 模型对比 |
| GET | `/api/providers` | 供应商列表 |
| GET | `/api/search` | 搜索模型 |
| GET | `/api/status` | 服务状态 |
| GET | `/api/exchange-rate` | 汇率 |
| GET | `/api/model-types` | 模型分类 |
| POST | `/api/cost/calculate` | 单个模型成本计算 |
| POST | `/api/cost/compare` | 多模型成本对比 |

---

## 数据模型

每个模型对象包含以下字段：

```
model_id: 唯一标识（string，如 gpt-4o）
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
  cached_input_price_per_1m_tokens: 缓存输入价格
  currency: 货币（默认USD）

scores: 评分
  overall_score: 综合评分（0-100）
  cost_efficiency_score: 性价比评分（0-100）

tags: 标签数组
source: 来源信息
```

---

## GET /api/models

模型列表。

**参数：**

```
provider: 按厂商筛选，如 openai
status: 按状态筛选，如 active
tags: 按标签筛选，逗号分隔，如 vision,coding
type: 按类型筛选，llm/multimodal/vision/audio/code
access: 按开源类型筛选，open/closed
min_context: 最小上下文长度
max_input_price: 最大输入价格
max_output_price: 最大输出价格
has_vision: 是否支持视觉，true/false
has_tool_calling: 是否支持工具调用，true/false
sort_by: 排序字段，overall_score/cost_efficiency_score/input_price/output_price/context_length
sort_order: 排序方向，asc/desc，默认desc
page: 页码，默认1
page_size: 每页数量，默认20，最大100
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": [模型对象数组],
  "total": 总数量,
  "page": 当前页码,
  "page_size": 每页数量,
  "total_pages": 总页数
}
```

**示例：**
- `/api/models?provider=openai` - OpenAI 的模型
- `/api/models?type=multimodal` - 多模态模型
- `/api/models?access=closed` - 闭源模型
- `/api/models?page=1&page_size=10` - 第一页，10条

---

## GET /api/models/{model_id}

单个模型详情。

**参数：**
- `model_id`：路径参数，模型ID

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": 模型对象
}
```

---

## GET /api/compare

模型对比。

**参数：**
- `models`：模型ID，逗号分隔，如 `gpt-4o,claude-3-opus`

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": [模型对象数组],
  "meta": {
    "cheapest_input": 最便宜输入的模型ID,
    "cheapest_output": 最便宜输出的模型ID,
    "longest_context": 最长上下文的模型ID,
    "best_overall": 综合评分最高的模型ID
  }
}
```

---

## GET /api/providers

供应商列表。

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "provider": "openai",
      "model_count": 8
    }
  ]
}
```

---

## GET /api/search

搜索模型。

**参数：**

```
tags: 标签筛选，逗号分隔
text_generation: 文本生成，true/false
code_generation: 代码生成，true/false
vision: 视觉，true/false
audio: 音频，true/false
multimodal: 多模态，true/false
tool_calling: 工具调用，true/false
reasoning_level: 推理等级，low/medium/high
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": [模型对象数组],
  "total": 数量
}
```

---

## GET /api/status

服务状态。

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_models": 模型总数,
    "providers": 供应商数量,
    "provider_list": ["openai", "aliyun", "anthropic"]
  }
}
```

---

## GET /api/exchange-rate

汇率。

**响应：**

```json
{
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
```

---

## GET /api/model-types

模型分类。

**响应：**

```json
{
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
```

---

## POST /api/cost/calculate

单个模型成本计算。

**请求体：**

```json
{
  "model_id": "gpt-4o",
  "input_tokens": 100000,
  "output_tokens": 50000,
  "quantity": 10,
  "currency": "CNY"
}
```

**参数：**

```
model_id: 模型ID（必填）
input_tokens: 输入token数量（默认1000）
output_tokens: 输出token数量（默认1000）
quantity: 调用次数（默认1）
currency: 货币，USD/CNY/EUR/JPY/GBP（默认USD）
```

**响应：**

```json
{
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
      "currency_symbol": "¥",
      "exchange_rate": 7.25
    }
  }
}
```

---

## POST /api/cost/compare

多模型成本对比。

**请求体：**

```json
{
  "models": ["gpt-4o", "claude-3-opus", "qwen-max"],
  "input_tokens": 100000,
  "output_tokens": 50000,
  "quantity": 10,
  "currency": "CNY"
}
```

**参数：**

```
models: 模型ID数组（必填）
input_tokens: 输入token数量（默认1000）
output_tokens: 输出token数量（默认1000）
quantity: 调用次数（默认1）
currency: 货币，USD/CNY/EUR/JPY/GBP（默认USD）
```

**响应：**

```json
{
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
}
```
