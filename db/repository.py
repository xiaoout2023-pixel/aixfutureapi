import json
from typing import List, Dict, Optional
from db.turso import TursoDB

MODEL_COLUMNS = """model_id, model_name, provider, release_date, status, last_updated,
    cap_text, cap_vision, cap_audio, cap_code, cap_reasoning, cap_tool_use,
    cap_function_calling, cap_image_generation, cap_video_understanding,
    cap_video_generation, cap_json_mode, cap_structured_output, cap_code_execution,
    cap_fine_tuning, cap_embedding, context_length, max_output_tokens, reasoning_level,
    price_input_per_1m, price_output_per_1m, price_cached_input, price_batch_input,
    price_batch_output, price_per_image, price_per_request, price_reasoning_per_1m,
    price_currency, price_free_tier,
    score_reasoning, score_coding, score_speed, score_cost_efficiency, score_overall,
    score_latency_level, score_throughput_level,
    tags, source_model_page, source_api_docs, source_pricing_page, source_type,
    source_region_restriction, source_enterprise_only, source_openai_compatible, source_sdk_support"""

MODEL_PARAMS = """?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?"""

MODEL_UPDATE = """model_name=excluded.model_name, provider=excluded.provider,
    release_date=excluded.release_date, status=excluded.status, last_updated=excluded.last_updated,
    cap_text=excluded.cap_text, cap_vision=excluded.cap_vision, cap_audio=excluded.cap_audio,
    cap_code=excluded.cap_code, cap_reasoning=excluded.cap_reasoning, cap_tool_use=excluded.cap_tool_use,
    cap_function_calling=excluded.cap_function_calling, cap_image_generation=excluded.cap_image_generation,
    cap_video_understanding=excluded.cap_video_understanding, cap_video_generation=excluded.cap_video_generation,
    cap_json_mode=excluded.cap_json_mode, cap_structured_output=excluded.cap_structured_output,
    cap_code_execution=excluded.cap_code_execution, cap_fine_tuning=excluded.cap_fine_tuning,
    cap_embedding=excluded.cap_embedding, context_length=excluded.context_length,
    max_output_tokens=excluded.max_output_tokens, reasoning_level=excluded.reasoning_level,
    price_input_per_1m=excluded.price_input_per_1m, price_output_per_1m=excluded.price_output_per_1m,
    price_cached_input=excluded.price_cached_input, price_batch_input=excluded.price_batch_input,
    price_batch_output=excluded.price_batch_output, price_per_image=excluded.price_per_image,
    price_per_request=excluded.price_per_request, price_reasoning_per_1m=excluded.price_reasoning_per_1m,
    price_currency=excluded.price_currency, price_free_tier=excluded.price_free_tier,
    score_reasoning=excluded.score_reasoning, score_coding=excluded.score_coding,
    score_speed=excluded.score_speed, score_cost_efficiency=excluded.score_cost_efficiency,
    score_overall=excluded.score_overall, score_latency_level=excluded.score_latency_level,
    score_throughput_level=excluded.score_throughput_level,
    tags=excluded.tags, source_model_page=excluded.source_model_page,
    source_api_docs=excluded.source_api_docs, source_pricing_page=excluded.source_pricing_page,
    source_type=excluded.source_type, source_region_restriction=excluded.source_region_restriction,
    source_enterprise_only=excluded.source_enterprise_only,
    source_openai_compatible=excluded.source_openai_compatible,
    source_sdk_support=excluded.source_sdk_support"""


def _flatten_model(model: Dict) -> list:
    cap = model.get("capabilities", {})
    if isinstance(cap, str):
        cap = json.loads(cap)
    prc = model.get("pricing", {})
    if isinstance(prc, str):
        prc = json.loads(prc)
    scr = model.get("scores", {})
    if isinstance(scr, str):
        scr = json.loads(scr)
    src = model.get("source", {})
    if isinstance(src, str):
        src = json.loads(src)
    tags = model.get("tags", [])
    if isinstance(tags, str):
        tags = json.loads(tags)

    return [
        model["model_id"], model["model_name"], model["provider"],
        model.get("release_date"), model.get("status", "active"), model.get("last_updated"),
        int(cap.get("text", cap.get("text_generation", True))),
        int(cap.get("vision", False)), int(cap.get("audio", False)),
        int(cap.get("code", cap.get("code_generation", False))),
        int(cap.get("reasoning", False)),
        int(cap.get("tool_use", cap.get("tool_calling", False))),
        int(cap.get("function_calling", False)), int(cap.get("image_generation", False)),
        int(cap.get("video_understanding", False)), int(cap.get("video_generation", False)),
        int(cap.get("json_mode", False)), int(cap.get("structured_output", False)),
        int(cap.get("code_execution", False)), int(cap.get("fine_tuning", False)),
        int(cap.get("embedding", False)),
        cap.get("context_length", 0), cap.get("max_output_tokens", 4096),
        cap.get("reasoning_level", "low"),
        prc.get("input_per_1m_tokens", prc.get("input_price_per_1m_tokens", 0)),
        prc.get("output_per_1m_tokens", prc.get("output_price_per_1m_tokens", 0)),
        prc.get("cached_input_price"), prc.get("batch_input_price"),
        prc.get("batch_output_price"), prc.get("price_per_image"),
        prc.get("price_per_request"), prc.get("reasoning_price_per_1m"),
        prc.get("currency", "USD"), int(prc.get("free_tier", False)),
        scr.get("reasoning_score", 0), scr.get("coding_score", 0),
        scr.get("speed_score", 0), scr.get("cost_efficiency_score", 0),
        scr.get("overall_score", 0), scr.get("latency_level", "medium"),
        scr.get("throughput_level", "medium"),
        json.dumps(tags, ensure_ascii=False),
        src.get("model_page"), src.get("api_docs"), src.get("pricing_page"),
        src.get("source_type", "official"), int(src.get("region_restriction", False)),
        int(src.get("enterprise_only", False)), int(src.get("openai_compatible", False)),
        int(src.get("sdk_support", False)),
    ]


def _to_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def _to_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _parse_row(row: Dict) -> Dict:
    if not row:
        return None
    r = dict(row)
    tags = r.get("tags", "[]")
    if isinstance(tags, str):
        try:
            r["tags"] = json.loads(tags)
        except:
            r["tags"] = []

    r["capabilities"] = {
        "text": bool(_to_int(r.get("cap_text"), 1)),
        "vision": bool(_to_int(r.get("cap_vision"))),
        "audio": bool(_to_int(r.get("cap_audio"))),
        "code": bool(_to_int(r.get("cap_code"))),
        "reasoning": bool(_to_int(r.get("cap_reasoning"))),
        "tool_use": bool(_to_int(r.get("cap_tool_use"))),
        "function_calling": bool(_to_int(r.get("cap_function_calling"))),
        "image_generation": bool(_to_int(r.get("cap_image_generation"))),
        "video_understanding": bool(_to_int(r.get("cap_video_understanding"))),
        "video_generation": bool(_to_int(r.get("cap_video_generation"))),
        "json_mode": bool(_to_int(r.get("cap_json_mode"))),
        "structured_output": bool(_to_int(r.get("cap_structured_output"))),
        "code_execution": bool(_to_int(r.get("cap_code_execution"))),
        "fine_tuning": bool(_to_int(r.get("cap_fine_tuning"))),
        "embedding": bool(_to_int(r.get("cap_embedding"))),
        "context_length": _to_int(r.get("context_length")),
        "max_output_tokens": _to_int(r.get("max_output_tokens"), 4096),
        "reasoning_level": r.get("reasoning_level") or "low",
    }
    r["pricing"] = {
        "input_per_1m_tokens": _to_float(r.get("price_input_per_1m")),
        "output_per_1m_tokens": _to_float(r.get("price_output_per_1m")),
        "cached_input_price": _to_float(r.get("price_cached_input")) if r.get("price_cached_input") is not None else None,
        "batch_input_price": _to_float(r.get("price_batch_input")) if r.get("price_batch_input") is not None else None,
        "batch_output_price": _to_float(r.get("price_batch_output")) if r.get("price_batch_output") is not None else None,
        "price_per_image": _to_float(r.get("price_per_image")) if r.get("price_per_image") is not None else None,
        "price_per_request": _to_float(r.get("price_per_request")) if r.get("price_per_request") is not None else None,
        "reasoning_price_per_1m": _to_float(r.get("price_reasoning_per_1m")) if r.get("price_reasoning_per_1m") is not None else None,
        "currency": r.get("price_currency") or "USD",
        "free_tier": bool(_to_int(r.get("price_free_tier"))),
    }
    r["scores"] = {
        "reasoning_score": _to_float(r.get("score_reasoning")),
        "coding_score": _to_float(r.get("score_coding")),
        "speed_score": _to_float(r.get("score_speed")),
        "cost_efficiency_score": _to_float(r.get("score_cost_efficiency")),
        "overall_score": _to_float(r.get("score_overall")),
        "latency_level": r.get("score_latency_level") or "medium",
        "throughput_level": r.get("score_throughput_level") or "medium",
    }
    r["source"] = {
        "model_page": r.get("source_model_page"),
        "api_docs": r.get("source_api_docs"),
        "pricing_page": r.get("source_pricing_page"),
        "source_type": r.get("source_type") or "official",
        "region_restriction": bool(_to_int(r.get("source_region_restriction"))),
        "enterprise_only": bool(_to_int(r.get("source_enterprise_only"))),
        "openai_compatible": bool(_to_int(r.get("source_openai_compatible"))),
        "sdk_support": bool(_to_int(r.get("source_sdk_support"))),
    }

    for key in ["cap_text","cap_vision","cap_audio","cap_code","cap_reasoning","cap_tool_use",
                "cap_function_calling","cap_image_generation","cap_video_understanding",
                "cap_video_generation","cap_json_mode","cap_structured_output","cap_code_execution",
                "cap_fine_tuning","cap_embedding","context_length","max_output_tokens","reasoning_level",
                "price_input_per_1m","price_output_per_1m","price_cached_input","price_batch_input",
                "price_batch_output","price_per_image","price_per_request","price_reasoning_per_1m",
                "price_currency","price_free_tier","score_reasoning","score_coding","score_speed",
                "score_cost_efficiency","score_overall","score_latency_level","score_throughput_level",
                "source_model_page","source_api_docs","source_pricing_page","source_type",
                "source_region_restriction","source_enterprise_only","source_openai_compatible","source_sdk_support"]:
        r.pop(key, None)

    return r


class ModelRepository:
    def __init__(self, db: TursoDB):
        self.db = db

    async def save_model(self, model: Dict):
        sql = f"""
            INSERT INTO models ({MODEL_COLUMNS})
            VALUES ({MODEL_PARAMS})
            ON CONFLICT(model_id) DO UPDATE SET {MODEL_UPDATE}
        """
        await self.db.execute(sql, _flatten_model(model))

    async def save_models(self, models: List[Dict]):
        statements = []
        for model in models:
            sql = f"""
                INSERT INTO models ({MODEL_COLUMNS})
                VALUES ({MODEL_PARAMS})
                ON CONFLICT(model_id) DO UPDATE SET {MODEL_UPDATE}
            """
            statements.append((sql, _flatten_model(model)))
        return await self.db.execute_batch(statements)

    async def get_all_models(self) -> List[Dict]:
        sql = f"SELECT {MODEL_COLUMNS} FROM models ORDER BY provider, model_name"
        rows = await self.db.query_all(sql)
        return [_parse_row(row) for row in rows]

    async def get_model(self, model_id: str) -> Optional[Dict]:
        sql = f"SELECT {MODEL_COLUMNS} FROM models WHERE model_id = ?"
        row = await self.db.query_one(sql, [model_id])
        return _parse_row(row) if row else None

    async def get_models_by_provider(self, provider: str) -> List[Dict]:
        sql = f"SELECT {MODEL_COLUMNS} FROM models WHERE provider = ? ORDER BY model_name"
        rows = await self.db.query_all(sql, [provider])
        return [_parse_row(row) for row in rows]

    async def search_models(self, filters: Dict) -> List[Dict]:
        conditions = []
        params = []
        
        if filters.get("provider"):
            conditions.append("provider = ?")
            params.append(filters["provider"])
        if filters.get("status"):
            conditions.append("status = ?")
            params.append(filters["status"])
        if filters.get("min_context"):
            conditions.append("context_length >= ?")
            params.append(filters["min_context"])
        if filters.get("max_input_price"):
            conditions.append("price_input_per_1m <= ?")
            params.append(filters["max_input_price"])
        if filters.get("max_output_price"):
            conditions.append("price_output_per_1m <= ?")
            params.append(filters["max_output_price"])
        if filters.get("min_input_price"):
            conditions.append("price_input_per_1m >= ?")
            params.append(filters["min_input_price"])
        if filters.get("min_output_price"):
            conditions.append("price_output_per_1m >= ?")
            params.append(filters["min_output_price"])
        if filters.get("has_vision") is not None:
            conditions.append("cap_vision = ?")
            params.append(1 if filters["has_vision"] else 0)
        if filters.get("has_tool_calling") is not None:
            conditions.append("cap_tool_use = ?")
            params.append(1 if filters["has_tool_calling"] else 0)
        if filters.get("text_generation") is not None:
            conditions.append("cap_text = ?")
            params.append(1 if filters["text_generation"] else 0)
        if filters.get("code_generation") is not None:
            conditions.append("cap_code = ?")
            params.append(1 if filters["code_generation"] else 0)
        if filters.get("audio") is not None:
            conditions.append("cap_audio = ?")
            params.append(1 if filters["audio"] else 0)
        if filters.get("multimodal") is not None:
            conditions.append("cap_vision = ?")
            params.append(1 if filters["multimodal"] else 0)
        if filters.get("reasoning_level"):
            conditions.append("reasoning_level = ?")
            params.append(filters["reasoning_level"])
        if filters.get("tags"):
            tags = filters["tags"]
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
        if filters.get("q"):
            q = filters["q"]
            conditions.append("(model_id LIKE ? OR model_name LIKE ? OR provider LIKE ? OR tags LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])

        sql = f"SELECT {MODEL_COLUMNS} FROM models"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sort_by = filters.get("sort_by", "score_overall")
        sort_order = filters.get("sort_order", "desc")
        sort_map = {
            "overall_score": "score_overall",
            "cost_efficiency_score": "score_cost_efficiency",
            "input_price": "price_input_per_1m",
            "output_price": "price_output_per_1m",
            "context_length": "context_length",
        }
        order_col = sort_map.get(sort_by, sort_by)
        sql += f" ORDER BY {order_col} {sort_order}"
        
        rows = await self.db.query_all(sql, params)
        return [_parse_row(row) for row in rows]

    async def get_providers(self) -> List[Dict]:
        sql = """
            SELECT provider, COUNT(*) as model_count 
            FROM models 
            GROUP BY provider 
            ORDER BY model_count DESC
        """
        return await self.db.query_all(sql)

    async def record_price(self, model_id: str, input_price: float, output_price: float):
        sql = "INSERT INTO price_history (model_id, input_price, output_price) VALUES (?, ?, ?)"
        await self.db.execute(sql, [model_id, input_price, output_price])

    async def get_recommendations(self) -> List[Dict]:
        sql = f"SELECT {MODEL_COLUMNS} FROM models WHERE status = 'active' ORDER BY score_overall DESC LIMIT 6"
        rows = await self.db.query_all(sql)
        return [_parse_row(row) for row in rows]

    async def get_search_suggestions(self, q: str) -> Dict:
        q_lower = q.lower()
        sql = f"SELECT {MODEL_COLUMNS} FROM models WHERE model_id LIKE ? OR model_name LIKE ? OR provider LIKE ? ORDER BY score_overall DESC LIMIT 10"
        params = [f"%{q_lower}%", f"%{q_lower}%", f"%{q_lower}%"]
        rows = await self.db.query_all(sql, params)
        return {"suggestions": [_parse_row(row) for row in rows]}

    # ========== Scenario Calculator Methods ==========

    async def create_scenario(self, name: str) -> Dict:
        import uuid
        from datetime import datetime
        scenario_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        sql = "INSERT INTO scenarios (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)"
        await self.db.execute(sql, [scenario_id, name, now, now])
        return {"id": scenario_id, "name": name, "created_at": now, "updated_at": now}

    async def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM scenarios WHERE id = ?"
        return await self.db.query_one(sql, [scenario_id])

    async def get_all_scenarios(self) -> List[Dict]:
        sql = "SELECT * FROM scenarios ORDER BY updated_at DESC"
        return await self.db.query_all(sql)

    async def update_scenario(self, scenario_id: str, name: str) -> Optional[Dict]:
        from datetime import datetime
        now = datetime.now().isoformat()
        sql = "UPDATE scenarios SET name = ?, updated_at = ? WHERE id = ?"
        await self.db.execute(sql, [name, now, scenario_id])
        return await self.get_scenario(scenario_id)

    async def delete_scenario(self, scenario_id: str) -> bool:
        await self.db.execute("DELETE FROM scenario_steps WHERE scenario_id = ?", [scenario_id])
        await self.db.execute("DELETE FROM scenarios WHERE id = ?", [scenario_id])
        return True

    async def get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        sql = """
            SELECT s.*, m.model_name, m.price_input_per_1m, m.price_output_per_1m, m.price_currency
            FROM scenario_steps s 
            LEFT JOIN models m ON s.model_id = m.model_id
            WHERE s.scenario_id = ? 
            ORDER BY s.step_order
        """
        rows = await self.db.query_all(sql, [scenario_id])
        result = []
        for row in rows:
            r = dict(row)
            r["pricing"] = {
                "input_price_per_1m_tokens": r.pop("price_input_per_1m", 0),
                "output_price_per_1m_tokens": r.pop("price_output_per_1m", 0),
                "currency": r.pop("price_currency", "USD"),
            }
            result.append(r)
        return result

    async def add_step(self, step: Dict) -> Dict:
        import uuid
        step_id = str(uuid.uuid4())[:8]
        sql = """
            INSERT INTO scenario_steps (id, scenario_id, step_order, task_type, model_id, 
                                       input_tokens, output_tokens, daily_calls, cache_hit_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [step_id, step["scenario_id"], step.get("step_order", 0),
                  step.get("task_type", ""), step.get("model_id", ""),
                  step.get("input_tokens", 0), step.get("output_tokens", 0),
                  step.get("daily_calls", 1), step.get("cache_hit_rate", 0.0)]
        await self.db.execute(sql, params)
        return {"id": step_id, **step}

    async def update_step(self, step_id: str, step: Dict) -> Optional[Dict]:
        sql = """UPDATE scenario_steps SET task_type=?, model_id=?, input_tokens=?, 
                 output_tokens=?, daily_calls=?, cache_hit_rate=? WHERE id=?"""
        params = [step.get("task_type",""), step.get("model_id",""), step.get("input_tokens",0),
                  step.get("output_tokens",0), step.get("daily_calls",1), step.get("cache_hit_rate",0.0), step_id]
        await self.db.execute(sql, params)
        return await self.get_step(step_id)

    async def get_step(self, step_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM scenario_steps WHERE id = ?"
        return await self.db.query_one(sql, [step_id])

    async def delete_step(self, step_id: str) -> bool:
        await self.db.execute("DELETE FROM scenario_steps WHERE id = ?", [step_id])
        return True

    async def reorder_steps(self, scenario_id: str, step_orders: List[Dict]) -> List[Dict]:
        statements = []
        for item in step_orders:
            sql = "UPDATE scenario_steps SET step_order = ? WHERE id = ? AND scenario_id = ?"
            statements.append((sql, [item["step_order"], item["id"], scenario_id]))
        await self.db.execute_batch(statements)
        return await self.get_scenario_steps(scenario_id)

    def calculate_step_cost(self, step: Dict) -> Dict:
        pricing = step.get("pricing", {})
        if isinstance(pricing, str):
            try: pricing = json.loads(pricing)
            except: pricing = {}
        input_price_per_m = float(pricing.get("input_price_per_1m_tokens", 0))
        output_price_per_m = float(pricing.get("output_price_per_1m_tokens", 0))
        input_tokens = int(step.get("input_tokens", 0))
        output_tokens = int(step.get("output_tokens", 0))
        daily_calls = int(step.get("daily_calls", 1))
        cache_hit_rate = float(step.get("cache_hit_rate", 0)) / 100.0
        single_cost = (input_tokens * input_price_per_m + output_tokens * output_price_per_m) / 1_000_000
        daily_cost = single_cost * daily_calls * (1 - cache_hit_rate)
        monthly_cost = daily_cost * 30
        yearly_cost = monthly_cost * 12
        return {
            "single_cost": round(single_cost, 6), "daily_cost": round(daily_cost, 4),
            "monthly_cost": round(monthly_cost, 2), "yearly_cost": round(yearly_cost, 2)
        }

    async def get_scenario_with_costs(self, scenario_id: str) -> Dict:
        scenario = await self.get_scenario(scenario_id)
        if not scenario: return None
        steps = await self.get_scenario_steps(scenario_id)
        total_daily, total_monthly, total_yearly = 0.0, 0.0, 0.0
        max_step, max_cost = None, 0.0
        for step in steps:
            costs = self.calculate_step_cost(step)
            step["costs"] = costs
            total_daily += costs["daily_cost"]
            total_monthly += costs["monthly_cost"]
            total_yearly += costs["yearly_cost"]
            if costs["daily_cost"] > max_cost:
                max_cost = costs["daily_cost"]
                max_step = step
        return {**scenario, "steps": steps, "summary": {
            "total_daily_cost": round(total_daily, 4), "total_monthly_cost": round(total_monthly, 2),
            "total_yearly_cost": round(total_yearly, 2), "max_cost_step": max_step["task_type"] if max_step else None,
            "step_count": len(steps)}}

    async def get_templates(self) -> List[Dict]:
        return [
            {"name": "客服机器人", "description": "完整的客服场景成本计算", "steps": [
                {"task_type": "意图识别", "input_tokens": 200, "output_tokens": 50, "daily_calls": 1000, "cache_hit_rate": 0},
                {"task_type": "知识检索", "input_tokens": 500, "output_tokens": 200, "daily_calls": 800, "cache_hit_rate": 30},
                {"task_type": "回复生成", "input_tokens": 300, "output_tokens": 500, "daily_calls": 800, "cache_hit_rate": 0}]},
            {"name": "内容审核链路", "description": "多级内容审核流程", "steps": [
                {"task_type": "初筛", "input_tokens": 1000, "output_tokens": 100, "daily_calls": 5000, "cache_hit_rate": 0},
                {"task_type": "复审", "input_tokens": 500, "output_tokens": 200, "daily_calls": 500, "cache_hit_rate": 0},
                {"task_type": "标签生成", "input_tokens": 500, "output_tokens": 50, "daily_calls": 500, "cache_hit_rate": 0}]},
            {"name": "翻译流程", "description": "机器翻译+润色流程", "steps": [
                {"task_type": "语言检测", "input_tokens": 500, "output_tokens": 20, "daily_calls": 2000, "cache_hit_rate": 50},
                {"task_type": "机器翻译", "input_tokens": 1000, "output_tokens": 1000, "daily_calls": 2000, "cache_hit_rate": 0},
                {"task_type": "润色优化", "input_tokens": 1000, "output_tokens": 800, "daily_calls": 2000, "cache_hit_rate": 0}]},
            {"name": "代码助手", "description": "代码生成、审查、文档流程", "steps": [
                {"task_type": "代码生成", "input_tokens": 500, "output_tokens": 2000, "daily_calls": 100, "cache_hit_rate": 0},
                {"task_type": "代码审查", "input_tokens": 2000, "output_tokens": 500, "daily_calls": 100, "cache_hit_rate": 0},
                {"task_type": "文档生成", "input_tokens": 2000, "output_tokens": 1000, "daily_calls": 50, "cache_hit_rate": 0}]},
        ]

    # ========== Leaderboard Methods ==========

    async def save_leaderboard_entry(self, entry: Dict):
        sql = """INSERT INTO leaderboards (category, rank, model_name, organization, score,
                 score_details, is_opensource, is_domestic, release_date, usage_type, is_reasoning, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                 ON CONFLICT(category, model_name) DO UPDATE SET
                 rank=excluded.rank, organization=excluded.organization, score=excluded.score,
                 score_details=excluded.score_details, is_opensource=excluded.is_opensource,
                 is_domestic=excluded.is_domestic, release_date=excluded.release_date,
                 usage_type=excluded.usage_type, is_reasoning=excluded.is_reasoning, updated_at=datetime('now')"""
        await self.db.execute(sql, [entry["category"], entry["rank"], entry["model_name"],
            entry["organization"], entry.get("score"), entry.get("score_details"),
            entry.get("is_opensource", 0), entry.get("is_domestic", 1), entry.get("release_date", ""),
            entry.get("usage_type", "api"), entry.get("is_reasoning", 0)])

    async def save_leaderboard_entries(self, entries: List[Dict]):
        statements = []
        for entry in entries:
            sql = """INSERT INTO leaderboards (category, rank, model_name, organization, score,
                     score_details, is_opensource, is_domestic, release_date, usage_type, is_reasoning, updated_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                     ON CONFLICT(category, model_name) DO UPDATE SET
                     rank=excluded.rank, organization=excluded.organization, score=excluded.score,
                     score_details=excluded.score_details, is_opensource=excluded.is_opensource,
                     is_domestic=excluded.is_domestic, release_date=excluded.release_date,
                     usage_type=excluded.usage_type, is_reasoning=excluded.is_reasoning, updated_at=datetime('now')"""
            statements.append((sql, [entry["category"], entry["rank"], entry["model_name"],
                entry["organization"], entry.get("score"), entry.get("score_details"),
                entry.get("is_opensource", 0), entry.get("is_domestic", 1), entry.get("release_date", ""),
                entry.get("usage_type", "api"), entry.get("is_reasoning", 0)]))
        return await self.db.execute_batch(statements)

    async def get_leaderboard_categories(self) -> List[Dict]:
        sql = "SELECT category, COUNT(*) as model_count, MAX(updated_at) as updated_at FROM leaderboards GROUP BY category ORDER BY category"
        return await self.db.query_all(sql)

    async def get_leaderboard(self, category: str, opensource: Optional[str] = None,
                               domestic: Optional[str] = None, page: int = 1, page_size: int = 50,
                               is_reasoning: Optional[bool] = None) -> Dict:
        conditions = ["category = ?"]
        params = [category]
        if opensource == "open": conditions.append("is_opensource = 1")
        elif opensource == "closed": conditions.append("is_opensource = 0")
        if domestic == "domestic": conditions.append("is_domestic = 1")
        elif domestic == "overseas": conditions.append("is_domestic = 0")
        if is_reasoning is not None: conditions.append("is_reasoning = ?"); params.append(1 if is_reasoning else 0)
        where = " AND ".join(conditions)
        count_row = await self.db.query_one(f"SELECT COUNT(*) as total FROM leaderboards WHERE {where}", params)
        total = int(count_row.get("total", 0)) if count_row else 0
        sql = f"SELECT * FROM leaderboards WHERE {where} ORDER BY rank ASC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        rows = await self.db.query_all(sql, params)
        result = []
        for row in rows:
            entry = dict(row)
            if isinstance(entry.get("score_details"), str):
                try: entry["score_details"] = json.loads(entry["score_details"])
                except: entry["score_details"] = {}
            entry["is_opensource"] = bool(_to_int(entry.get("is_opensource")))
            entry["is_domestic"] = bool(_to_int(entry.get("is_domestic")))
            entry["is_reasoning"] = bool(_to_int(entry.get("is_reasoning"), 0))
            result.append(entry)
        return {"entries": result, "total": total, "page": page, "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0}

    async def get_leaderboard_detail(self, category: str) -> Optional[Dict]:
        row = await self.db.query_one("SELECT * FROM leaderboards WHERE category = ? ORDER BY rank ASC LIMIT 1", [category])
        if not row: return None
        count_row = await self.db.query_one("SELECT COUNT(*) as total FROM leaderboards WHERE category = ?", [category])
        total = int(count_row.get("total", 0)) if count_row else 0
        return {"category": category, "total_models": total, "updated_at": row.get("updated_at")}

    # ========== Marketplace Methods ==========

    async def save_marketplace_entry(self, entry: Dict):
        sql = """INSERT INTO model_marketplace (model_id, marketplace, marketplace_model_id,
                 input_price, output_price, latency_ms, uptime, availability, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                 ON CONFLICT(model_id, marketplace) DO UPDATE SET
                 marketplace_model_id=excluded.marketplace_model_id, input_price=excluded.input_price,
                 output_price=excluded.output_price, latency_ms=excluded.latency_ms,
                 uptime=excluded.uptime, availability=excluded.availability, updated_at=datetime('now')"""
        await self.db.execute(sql, [entry["model_id"], entry["marketplace"], entry.get("marketplace_model_id"),
            entry.get("input_price"), entry.get("output_price"), entry.get("latency_ms"),
            entry.get("uptime"), entry.get("availability")])

    async def save_marketplace_entries(self, entries: List[Dict]):
        statements = []
        for entry in entries:
            sql = """INSERT INTO model_marketplace (model_id, marketplace, marketplace_model_id,
                     input_price, output_price, latency_ms, uptime, availability, updated_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                     ON CONFLICT(model_id, marketplace) DO UPDATE SET
                     marketplace_model_id=excluded.marketplace_model_id, input_price=excluded.input_price,
                     output_price=excluded.output_price, latency_ms=excluded.latency_ms,
                     uptime=excluded.uptime, availability=excluded.availability, updated_at=datetime('now')"""
            statements.append((sql, [entry["model_id"], entry["marketplace"], entry.get("marketplace_model_id"),
                entry.get("input_price"), entry.get("output_price"), entry.get("latency_ms"),
                entry.get("uptime"), entry.get("availability")]))
        return await self.db.execute_batch(statements)

    async def get_model_marketplace(self, model_id: str) -> List[Dict]:
        return await self.db.query_all("SELECT * FROM model_marketplace WHERE model_id = ? ORDER BY marketplace", [model_id])

    async def get_marketplace_compare(self, model_ids: List[str]) -> Dict:
        if not model_ids: return {"models": [], "comparison": {}}
        placeholders = ",".join(["?"] * len(model_ids))
        rows = await self.db.query_all(f"SELECT * FROM model_marketplace WHERE model_id IN ({placeholders}) ORDER BY model_id, marketplace", model_ids)
        result = {}
        for row in rows:
            mid = row["model_id"]
            if mid not in result: result[mid] = []
            result[mid].append(dict(row))
        cheapest_input = cheapest_output = best_latency = best_uptime = None
        for mid, entries in result.items():
            for e in entries:
                if e.get("input_price") is not None:
                    if cheapest_input is None or e["input_price"] < cheapest_input["price"]:
                        cheapest_input = {"model_id": mid, "marketplace": e["marketplace"], "price": e["input_price"]}
                if e.get("output_price") is not None:
                    if cheapest_output is None or e["output_price"] < cheapest_output["price"]:
                        cheapest_output = {"model_id": mid, "marketplace": e["marketplace"], "price": e["output_price"]}
                if e.get("latency_ms") is not None:
                    if best_latency is None or e["latency_ms"] < best_latency["latency_ms"]:
                        best_latency = {"model_id": mid, "marketplace": e["marketplace"], "latency_ms": e["latency_ms"]}
                if e.get("uptime") is not None:
                    if best_uptime is None or e["uptime"] > best_uptime["uptime"]:
                        best_uptime = {"model_id": mid, "marketplace": e["marketplace"], "uptime": e["uptime"]}
        return {"models": result, "comparison": {
            "cheapest_input": cheapest_input, "cheapest_output": cheapest_output,
            "best_latency": best_latency, "best_uptime": best_uptime}}
