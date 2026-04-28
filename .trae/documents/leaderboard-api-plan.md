# 排行榜 API 实施计划

## 需求理解

基于 SuperCLUE（<https://superclueai.com/homepage）数据源，提供通用榜和多模态榜的排行榜> API，供前端展示。

SuperCLUE 评测维度：

* **通用榜**：幻觉控制、数学推理、科学推理、精确指令遵循、代码生成、智能体(任务规划) 六大维度综合评分

* **多模态榜**：多模态能力评测排名

额外指标：生成耗时(秒)、模型综合价格(元/百万tokens)

***

## 一、数据库设计

新增 `leaderboard` 表：

```sql
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,           -- 模型ID（与models表关联）
    model_name TEXT NOT NULL,         -- 模型名称
    provider TEXT NOT NULL,           -- 厂商
    board_type TEXT NOT NULL,         -- 榜单类型：general(通用榜) / multimodal(多模态榜)
    rank INTEGER,                     -- 排名
    score REAL,                       -- 总分
    sub_scores TEXT,                  -- 子维度评分 JSON
    generation_time REAL,             -- 生成耗时(秒)
    input_price REAL,                 -- 输入价格(元/百万tokens)
    output_price REAL,                -- 输出价格(元/百万tokens)
    composite_price REAL,             -- 综合价格(元/百万tokens)
    is_reference INTEGER DEFAULT 0,   -- 是否仅参考(0/1，国外模型不参与排名)
    period TEXT,                      -- 评测周期，如 "2026-03"
    source TEXT DEFAULT 'SuperCLUE',  -- 数据来源
    last_updated TEXT,
    UNIQUE(model_id, board_type, period)
);
```

`sub_scores` JSON 示例（通用榜）：

```json
{
    "hallucination_control": 85.2,
    "math_reasoning": 78.5,
    "science_reasoning": 82.1,
    "instruction_following": 88.3,
    "code_generation": 76.9,
    "agent_planning": 72.4
}
```

***

## 二、新增文件

### 1. `crawler/superclue.py` — SuperCLUE 爬虫

继承 `BaseCrawler`，爬取 SuperCLUE 网站数据：

* 爬取通用榜和多模态榜

* 解析排名、评分、耗时、价格等

* 保存到 `leaderboard` 表

**策略**：先尝试爬取网页，失败则使用硬编码数据（与现有爬虫策略一致）

### 2. 修改 `db/init_db.py` — 添加 leaderboard 表初始化

### 3. 修改 `db/repository.py` — 添加排行榜数据访问方法

新增方法：

* `save_leaderboard(entries)` — 批量保存排行榜数据

* `get_leaderboard(board_type, period)` — 获取指定榜单

* `get_leaderboard_periods()` — 获取可用评测周期列表

### 4. 修改 `api/main.py` — 添加排行榜 API 路由

### 5. 修改 `crawler/run_all.py` — 集成 SuperCLUE 爬虫

***

## 三、API 设计

### 1. `GET /api/leaderboard` — 获取排行榜

**参数：**

| 参数          | 类型     | 必填 | 说明                                                        |
| ----------- | ------ | -- | --------------------------------------------------------- |
| board\_type | string | 是  | 榜单类型：general(通用榜) / multimodal(多模态榜)                      |
| period      | string | 否  | 评测周期，如 "2026-03"，默认最新                                     |
| provider    | string | 否  | 按厂商筛选                                                     |
| sort\_by    | string | 否  | 排序字段：rank/score/generation\_time/composite\_price，默认 rank |
| sort\_order | string | 否  | 排序方向：asc/desc，默认 asc                                      |
| page        | int    | 否  | 页码，默认 1                                                   |
| page\_size  | int    | 否  | 每页数量，默认 20                                                |

**响应：**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "model_id": "deepseek-r1",
            "model_name": "DeepSeek-R1",
            "provider": "deepseek",
            "rank": 1,
            "score": 89.5,
            "sub_scores": {
                "hallucination_control": 85.2,
                "math_reasoning": 92.1,
                "science_reasoning": 88.3,
                "instruction_following": 90.1,
                "code_generation": 89.7,
                "agent_planning": 86.5
            },
            "generation_time": 12.5,
            "input_price": 4.0,
            "output_price": 16.0,
            "composite_price": 7.0,
            "is_reference": false
        }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20,
    "period": "2026-03",
    "board_type": "general"
}
```

### 2. `GET /api/leaderboard/periods` — 获取可用评测周期

**响应：**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {"period": "2026-03", "board_types": ["general", "multimodal"]},
        {"period": "2026-02", "board_types": ["general"]}
    ]
}
```

### 3. `GET /api/leaderboard/summary` — 排行榜概览

返回通用榜和多模态榜的 Top5 摘要，供前端首页展示。

**响应：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "general": {
            "period": "2026-03",
            "top5": [...]
        },
        "multimodal": {
            "period": "2026-03",
            "top5": [...]
        }
    }
}
```

***

## 四、实施步骤

1. **修改** **`db/init_db.py`** — 添加 leaderboard 建表语句
2. **修改** **`db/repository.py`** — 添加排行榜相关的数据访问方法
3. **新建** **`crawler/superclue.py`** — SuperCLUE 数据爬虫（含硬编码初始数据）
4. **修改** **`crawler/run_all.py`** — 集成 SuperCLUE 爬虫
5. **修改** **`api/main.py`** — 添加 3 个排行榜 API 路由
6. **修改** **`api/docs.html`** — 更新接口文档
7. **本地测试** — 启动服务，测试每个接口
8. **提交代码**

***

## 五、风险与优化点

* **数据时效性**：SuperCLUE 每月更新，需通过 GitHub Actions 定时爬取

* **爬取稳定性**：SuperCLUE 网站可能反爬，需做好降级（硬编码数据兜底）

* **模型ID映射**：SuperCLUE 的模型名与本项目 model\_id 需要做映射对齐

* **后续优化**：可考虑增加更多数据源（如 Chatbot Arena、OpenCompass）

