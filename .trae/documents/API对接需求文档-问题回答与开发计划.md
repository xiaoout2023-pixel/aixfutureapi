# API对接需求文档 - 问题回答与开发计划

## 一、问题回答（直接基于实际代码）

### 问题 1: `POST /api/cost/calculate` 的请求体格式是什么？

**已实现 ✅**

请求体示例：
```json
{
  "model_id": "gpt-4o",
  "input_tokens": 100000,
  "output_tokens": 50000
}
```

参数说明：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model_id` | string | 是 | - | 模型ID |
| `input_tokens` | int | 否 | 1000 | 输入token数量 |
| `output_tokens` | int | 否 | 1000 | 输出token数量 |

返回格式示例：
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
    "pricing": {
      "input_price_per_1m_tokens": 2.50,
      "output_price_per_1m_tokens": 10.00,
      "currency": "USD"
    },
    "cost_breakdown": {
      "input_cost": 0.25,
      "output_cost": 0.50,
      "total_cost": 0.75,
      "currency": "USD"
    }
  }
}
```

- ✅ 返回包含 USD 货币单位
- ❌ 不支持 `quantity`（调用次数）参数
- ❌ 不支持 `currency` 切换参数
- ❌ 不支持 `cached_tokens` 参数

---

### 问题 2: `POST /api/cost/compare` 的请求体格式是什么？

**已实现 ✅**

请求体示例：
```json
{
  "models": ["gpt-4o", "claude-3-opus", "qwen-max"],
  "input_tokens": 100000,
  "output_tokens": 50000
}
```

参数说明：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `models` | string[] | 是 | - | 模型ID数组 |
| `input_tokens` | int | 否 | 1000 | 输入token数量 |
| `output_tokens` | int | 否 | 1000 | 输出token数量 |

返回格式示例：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "model_id": "gpt-4o",
      "model_name": "GPT-4o",
      "provider": "openai",
      "input_cost": 0.25,
      "output_cost": 0.50,
      "total_cost": 0.75,
      "pricing": {...}
    }
  ],
  "meta": {
    "input_tokens": 100000,
    "output_tokens": 50000,
    "cheapest_model": "gpt-4o"
  }
}
```

- ✅ 按 total_cost 升序排列
- ✅ 包含最便宜模型标识 `cheapest_model`
- ✅ models 数组元素是 model_id

---

### 问题 3: `GET /api/models` 是否支持 `provider`、`type`、`access` 筛选参数？

**部分支持 ✅**

当前支持的查询参数：
| 参数 | 状态 | 说明 |
|------|------|------|
| `provider` | ✅ 支持 | 按供应商筛选 |
| `status` | ✅ 支持 | 按状态筛选 |
| `tags` | ✅ 支持 | 按标签筛选（逗号分隔） |
| `min_context` | ✅ 支持 | 最小上下文长度 |
| `max_input_price` | ✅ 支持 | 最大输入价格 |
| `max_output_price` | ✅ 支持 | 最大输出价格 |
| `has_vision` | ✅ 支持 | 是否支持视觉 |
| `has_tool_calling` | ✅ 支持 | 是否支持工具调用 |
| `sort_by` | ✅ 支持 | 排序字段 |
| `sort_order` | ✅ 支持 | 排序方向 |
| `type` | ❌ 不支持 | 模型类型（需新增） |
| `access` | ❌ 不支持 | 开源/闭源（需新增） |

---

### 问题 4: 是否有汇率数据？是否需要前端硬编码？

**❌ 当前无汇率接口**

建议：前端暂时硬编码汇率，后续新增 `GET /api/exchange-rate` 接口。

---

### 问题 5: 供应商数据能否补充完整？

**❌ 当前不完整**

当前只有爬虫已实现的供应商：openai, aliyun, anthropic（共3个）。

缺少：阿里巴巴（已有 aliyun 但需完善）、月之暗面、深度求索、智谱AI、Mistral AI、Stability AI 等。

---

### 问题 6: Swagger 文档页面加载失败（/openapi.json 404）

**❌ 需要确认**

需要验证 Vercel 部署后 `/openapi.json` 和 `/docs` 是否可访问。

---

## 二、需求提取

### 高优先级需求

1. **新增汇率接口** `GET /api/exchange-rate`
2. **增强模型列表筛选**：新增 `type`、`access` 筛选参数
3. **补充供应商数据**：扩展爬虫支持更多供应商
4. **修复 Swagger 文档**：确保 `/openapi.json` 和 `/docs` 可访问

### 中优先级需求

5. **新增模型能力字段**：在模型数据中增强 `capabilities` 结构
6. **新增模型分类接口** `GET /api/model-types`
7. **支持分页**：`/api/models` 增加 `page`/`pageSize` 参数

### 低优先级需求

8. **支持调用次数参数**：成本计算接口增加 `quantity`
9. **支持缓存token计算**：成本计算接口增加 `cached_tokens`
10. **支持货币切换**：成本计算接口增加 `currency` 参数
11. **补充供应商 Logo**
12. **排行榜接口** `GET /api/leaderboards`

---

## 三、实施计划

### Step 1: 验证并修复 Swagger 文档
- 检查 Vercel 上 `/openapi.json` 和 `/docs` 的访问情况
- 如果404，调整配置

### Step 2: 新增汇率接口 `GET /api/exchange-rate`
- 返回 USD ↔ CNY 汇率
- 支持固定汇率或第三方 API

### Step 3: 增强模型列表筛选参数
- `/api/models` 增加 `type` 参数
- `/api/models` 增加 `access` 参数

### Step 4: 新增模型分类接口 `GET /api/model-types`
- 返回可用的模型类型列表

### Step 5: 新增分页支持
- `/api/models` 增加 `page` 和 `pageSize` 参数
- 返回 `total`、`page`、`pageSize` 等分页元信息

### Step 6: 增强成本计算接口
- `POST /api/cost/calculate` 增加 `quantity` 参数
- `POST /api/cost/compare` 增加 `quantity` 参数
- 增加 `currency` 参数支持

### Step 7: 补充供应商数据
- 新增 Google (Gemini) 爬虫
- 新增 Zhipu (智谱AI) 爬虫
- 新增 Moonshot (月之暗面) 爬虫
- 完善现有供应商信息

### Step 8: 测试验证
- 本地测试所有新接口
- 推送后验证 Vercel 部署
