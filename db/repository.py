import asyncio
import json
from typing import List, Dict, Optional
from db.turso import TursoDB

class ModelRepository:
    def __init__(self, db: TursoDB):
        self.db = db

    async def save_model(self, model: Dict):
        sql = """
            INSERT INTO models (model_id, model_name, provider, release_date, status, 
                               capabilities, pricing, scores, tags, source, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model_id) DO UPDATE SET
                model_name=excluded.model_name,
                provider=excluded.provider,
                release_date=excluded.release_date,
                status=excluded.status,
                capabilities=excluded.capabilities,
                pricing=excluded.pricing,
                scores=excluded.scores,
                tags=excluded.tags,
                source=excluded.source,
                last_updated=excluded.last_updated
        """
        params = [
            model["model_id"],
            model["model_name"],
            model["provider"],
            model.get("release_date"),
            model.get("status", "active"),
            json.dumps(model.get("capabilities", {})),
            json.dumps(model.get("pricing", {})),
            json.dumps(model.get("scores", {})),
            json.dumps(model.get("tags", [])),
            json.dumps(model.get("source", {})),
            model.get("last_updated")
        ]
        await self.db.execute(sql, params)

    async def save_models(self, models: List[Dict]):
        statements = []
        for model in models:
            sql = """
                INSERT INTO models (model_id, model_name, provider, release_date, status, 
                                   capabilities, pricing, scores, tags, source, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_id) DO UPDATE SET
                    model_name=excluded.model_name,
                    provider=excluded.provider,
                    release_date=excluded.release_date,
                    status=excluded.status,
                    capabilities=excluded.capabilities,
                    pricing=excluded.pricing,
                    scores=excluded.scores,
                    tags=excluded.tags,
                    source=excluded.source,
                    last_updated=excluded.last_updated
            """
            params = [
                model["model_id"],
                model["model_name"],
                model["provider"],
                model.get("release_date"),
                model.get("status", "active"),
                json.dumps(model.get("capabilities", {})),
                json.dumps(model.get("pricing", {})),
                json.dumps(model.get("scores", {})),
                json.dumps(model.get("tags", [])),
                json.dumps(model.get("source", {})),
                model.get("last_updated")
            ]
            statements.append((sql, params))
        return await self.db.execute_batch(statements)

    async def get_all_models(self) -> List[Dict]:
        sql = "SELECT * FROM models ORDER BY provider, model_name"
        rows = await self.db.query_all(sql)
        return [self._parse_row(row) for row in rows]

    async def get_model(self, model_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM models WHERE model_id = ?"
        row = await self.db.query_one(sql, [model_id])
        return self._parse_row(row) if row else None

    async def get_models_by_provider(self, provider: str) -> List[Dict]:
        sql = "SELECT * FROM models WHERE provider = ? ORDER BY model_name"
        rows = await self.db.query_all(sql, [provider])
        return [self._parse_row(row) for row in rows]

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
            conditions.append("JSON_EXTRACT(capabilities, '$.context_length') >= ?")
            params.append(str(filters["min_context"]))
        
        if filters.get("max_input_price"):
            conditions.append("JSON_EXTRACT(pricing, '$.input_price_per_1m_tokens') <= ?")
            params.append(str(filters["max_input_price"]))
        
        if filters.get("max_output_price"):
            conditions.append("JSON_EXTRACT(pricing, '$.output_price_per_1m_tokens') <= ?")
            params.append(str(filters["max_output_price"]))

        if filters.get("min_input_price"):
            conditions.append("JSON_EXTRACT(pricing, '$.input_price_per_1m_tokens') >= ?")
            params.append(str(filters["min_input_price"]))

        if filters.get("min_output_price"):
            conditions.append("JSON_EXTRACT(pricing, '$.output_price_per_1m_tokens') >= ?")
            params.append(str(filters["min_output_price"]))
        
        if filters.get("has_vision") is not None:
            conditions.append("CAST(JSON_EXTRACT(capabilities, '$.vision') AS TEXT) = ?")
            params.append("true" if filters["has_vision"] else "false")
        
        if filters.get("has_tool_calling") is not None:
            conditions.append("CAST(JSON_EXTRACT(capabilities, '$.tool_calling') AS TEXT) = ?")
            params.append("true" if filters["has_tool_calling"] else "false")

        if filters.get("text_generation") is not None:
            conditions.append("CAST(JSON_EXTRACT(capabilities, '$.text_generation') AS TEXT) = ?")
            params.append("true" if filters["text_generation"] else "false")

        if filters.get("code_generation") is not None:
            conditions.append("CAST(JSON_EXTRACT(capabilities, '$.code_generation') AS TEXT) = ?")
            params.append("true" if filters["code_generation"] else "false")

        if filters.get("audio") is not None:
            conditions.append("CAST(JSON_EXTRACT(capabilities, '$.audio') AS TEXT) = ?")
            params.append("true" if filters["audio"] else "false")

        if filters.get("multimodal") is not None:
            conditions.append("CAST(JSON_EXTRACT(capabilities, '$.multimodal') AS TEXT) = ?")
            params.append("true" if filters["multimodal"] else "false")

        if filters.get("reasoning_level"):
            conditions.append("JSON_EXTRACT(capabilities, '$.reasoning_level') = ?")
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

        sql = f"SELECT * FROM models"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sort_by = filters.get("sort_by", "overall_score")
        sort_order = filters.get("sort_order", "desc")
        if sort_by in ["overall_score", "cost_efficiency_score"]:
            sql += f" ORDER BY JSON_EXTRACT(scores, '$.{sort_by}') {sort_order}"
        elif sort_by == "input_price":
            sql += f" ORDER BY JSON_EXTRACT(pricing, '$.input_price_per_1m_tokens') {sort_order}"
        elif sort_by == "output_price":
            sql += f" ORDER BY JSON_EXTRACT(pricing, '$.output_price_per_1m_tokens') {sort_order}"
        elif sort_by == "context_length":
            sql += f" ORDER BY JSON_EXTRACT(capabilities, '$.context_length') {sort_order}"
        
        rows = await self.db.query_all(sql, params)
        return [self._parse_row(row) for row in rows]

    async def get_providers(self) -> List[Dict]:
        sql = """
            SELECT provider, COUNT(*) as model_count 
            FROM models 
            GROUP BY provider 
            ORDER BY model_count DESC
        """
        return await self.db.query_all(sql)

    async def record_price(self, model_id: str, input_price: float, output_price: float):
        sql = """
            INSERT INTO price_history (model_id, input_price, output_price)
            VALUES (?, ?, ?)
        """
        await self.db.execute(sql, [model_id, input_price, output_price])

    def _parse_row(self, row: Dict) -> Dict:
        parsed = row.copy()
        for field in ["capabilities", "pricing", "scores", "tags", "source"]:
            if isinstance(parsed.get(field), str):
                try:
                    parsed[field] = json.loads(parsed[field])
                except:
                    parsed[field] = {} if field != "tags" else []
        return parsed

    async def get_recommendations(self) -> List[Dict]:
        sql = """
            SELECT * FROM models 
            WHERE status = 'active'
            ORDER BY JSON_EXTRACT(scores, '$.overall_score') DESC
            LIMIT 6
        """
        rows = await self.db.query_all(sql)
        return [self._parse_row(row) for row in rows]

    async def get_search_suggestions(self, q: str) -> Dict:
        models = await self.get_all_models()
        q_lower = q.lower()
        
        model_name_matches = []
        provider_matches = []
        tag_matches = []
        
        for m in models:
            if q_lower in m.get("model_id", "").lower() or q_lower in m.get("model_name", "").lower():
                model_name_matches.append(m)
            if q_lower in m.get("provider", "").lower():
                provider_matches.append(m)
            for tag in m.get("tags", []):
                if q_lower in tag.lower():
                    tag_matches.append(m)
                    break
        
        seen = set()
        result = []
        for m in model_name_matches + provider_matches + tag_matches:
            if m["model_id"] not in seen:
                seen.add(m["model_id"])
                result.append(m)
        
        return {"suggestions": result[:10]}

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
        row = await self.db.query_one(sql, [scenario_id])
        return row

    async def get_all_scenarios(self) -> List[Dict]:
        sql = "SELECT * FROM scenarios ORDER BY updated_at DESC"
        return await self.db.query_all(sql)

    async def update_scenario(self, scenario_id: str, name: str) -> Optional[Dict]:
        from datetime import datetime
        now = datetime.now().isoformat()
        sql = "UPDATE scenarios SET name = ?, updated_at = ? WHERE id = ?"
        await self.db.execute(sql, [name, now, scenario_id])
        row = await self.get_scenario(scenario_id)
        return row

    async def delete_scenario(self, scenario_id: str) -> bool:
        await self.db.execute("DELETE FROM scenario_steps WHERE scenario_id = ?", [scenario_id])
        await self.db.execute("DELETE FROM scenarios WHERE id = ?", [scenario_id])
        return True

    async def get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        sql = """
            SELECT s.*, m.model_name, m.pricing 
            FROM scenario_steps s 
            LEFT JOIN models m ON s.model_id = m.model_id
            WHERE s.scenario_id = ? 
            ORDER BY s.step_order
        """
        rows = await self.db.query_all(sql, [scenario_id])
        result = []
        for row in rows:
            row_dict = dict(row)
            if isinstance(row_dict.get("pricing"), str):
                try:
                    row_dict["pricing"] = json.loads(row_dict["pricing"])
                except:
                    row_dict["pricing"] = {}
            result.append(row_dict)
        return result

    async def add_step(self, step: Dict) -> Dict:
        import uuid
        step_id = str(uuid.uuid4())[:8]
        sql = """
            INSERT INTO scenario_steps (id, scenario_id, step_order, task_type, model_id, 
                                       input_tokens, output_tokens, daily_calls, cache_hit_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            step_id,
            step["scenario_id"],
            step.get("step_order", 0),
            step.get("task_type", ""),
            step.get("model_id", ""),
            step.get("input_tokens", 0),
            step.get("output_tokens", 0),
            step.get("daily_calls", 1),
            step.get("cache_hit_rate", 0.0)
        ]
        await self.db.execute(sql, params)
        return {"id": step_id, **step}

    async def update_step(self, step_id: str, step: Dict) -> Optional[Dict]:
        sql = """
            UPDATE scenario_steps SET 
                task_type = ?, model_id = ?, input_tokens = ?, output_tokens = ?,
                daily_calls = ?, cache_hit_rate = ?
            WHERE id = ?
        """
        params = [
            step.get("task_type", ""),
            step.get("model_id", ""),
            step.get("input_tokens", 0),
            step.get("output_tokens", 0),
            step.get("daily_calls", 1),
            step.get("cache_hit_rate", 0.0),
            step_id
        ]
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
            try:
                pricing = json.loads(pricing)
            except:
                pricing = {}
        
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
            "single_cost": round(single_cost, 6),
            "daily_cost": round(daily_cost, 4),
            "monthly_cost": round(monthly_cost, 2),
            "yearly_cost": round(yearly_cost, 2)
        }

    async def get_scenario_with_costs(self, scenario_id: str) -> Dict:
        scenario = await self.get_scenario(scenario_id)
        if not scenario:
            return None
        
        steps = await self.get_scenario_steps(scenario_id)
        
        total_daily = 0.0
        total_monthly = 0.0
        total_yearly = 0.0
        max_step = None
        max_cost = 0.0
        
        for step in steps:
            costs = self.calculate_step_cost(step)
            step["costs"] = costs
            total_daily += costs["daily_cost"]
            total_monthly += costs["monthly_cost"]
            total_yearly += costs["yearly_cost"]
            if costs["daily_cost"] > max_cost:
                max_cost = costs["daily_cost"]
                max_step = step
        
        return {
            **scenario,
            "steps": steps,
            "summary": {
                "total_daily_cost": round(total_daily, 4),
                "total_monthly_cost": round(total_monthly, 2),
                "total_yearly_cost": round(total_yearly, 2),
                "max_cost_step": max_step["task_type"] if max_step else None,
                "step_count": len(steps)
            }
        }

    async def get_templates(self) -> List[Dict]:
        return [
            {
                "name": "客服机器人",
                "description": "完整的客服场景成本计算",
                "steps": [
                    {"task_type": "意图识别", "input_tokens": 200, "output_tokens": 50, "daily_calls": 1000, "cache_hit_rate": 0},
                    {"task_type": "知识检索", "input_tokens": 500, "output_tokens": 200, "daily_calls": 800, "cache_hit_rate": 30},
                    {"task_type": "回复生成", "input_tokens": 300, "output_tokens": 500, "daily_calls": 800, "cache_hit_rate": 0}
                ]
            },
            {
                "name": "内容审核链路",
                "description": "多级内容审核流程",
                "steps": [
                    {"task_type": "初筛", "input_tokens": 1000, "output_tokens": 100, "daily_calls": 5000, "cache_hit_rate": 0},
                    {"task_type": "复审", "input_tokens": 500, "output_tokens": 200, "daily_calls": 500, "cache_hit_rate": 0},
                    {"task_type": "标签生成", "input_tokens": 500, "output_tokens": 50, "daily_calls": 500, "cache_hit_rate": 0}
                ]
            },
            {
                "name": "翻译流程",
                "description": "机器翻译+润色流程",
                "steps": [
                    {"task_type": "语言检测", "input_tokens": 500, "output_tokens": 20, "daily_calls": 2000, "cache_hit_rate": 50},
                    {"task_type": "机器翻译", "input_tokens": 1000, "output_tokens": 1000, "daily_calls": 2000, "cache_hit_rate": 0},
                    {"task_type": "润色优化", "input_tokens": 1000, "output_tokens": 800, "daily_calls": 2000, "cache_hit_rate": 0}
                ]
            },
            {
                "name": "代码助手",
                "description": "代码生成、审查、文档流程",
                "steps": [
                    {"task_type": "代码生成", "input_tokens": 500, "output_tokens": 2000, "daily_calls": 100, "cache_hit_rate": 0},
                    {"task_type": "代码审查", "input_tokens": 2000, "output_tokens": 500, "daily_calls": 100, "cache_hit_rate": 0},
                    {"task_type": "文档生成", "input_tokens": 2000, "output_tokens": 1000, "daily_calls": 50, "cache_hit_rate": 0}
                ]
            }
        ]

    # ========== Leaderboard Methods ==========

    async def save_leaderboard_entry(self, entry: Dict):
        sql = """
            INSERT INTO leaderboards (category, rank, model_name, organization, score,
                                      score_details, is_opensource, is_domestic, release_date, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(category, model_name) DO UPDATE SET
                rank=excluded.rank,
                organization=excluded.organization,
                score=excluded.score,
                score_details=excluded.score_details,
                is_opensource=excluded.is_opensource,
                is_domestic=excluded.is_domestic,
                release_date=excluded.release_date,
                updated_at=datetime('now')
        """
        params = [
            entry["category"],
            entry["rank"],
            entry["model_name"],
            entry["organization"],
            entry.get("score"),
            entry.get("score_details"),
            entry.get("is_opensource", 0),
            entry.get("is_domestic", 1),
            entry.get("release_date", ""),
        ]
        await self.db.execute(sql, params)

    async def save_leaderboard_entries(self, entries: List[Dict]):
        statements = []
        for entry in entries:
            sql = """
                INSERT INTO leaderboards (category, rank, model_name, organization, score,
                                          score_details, is_opensource, is_domestic, release_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(category, model_name) DO UPDATE SET
                    rank=excluded.rank,
                    organization=excluded.organization,
                    score=excluded.score,
                    score_details=excluded.score_details,
                    is_opensource=excluded.is_opensource,
                    is_domestic=excluded.is_domestic,
                    release_date=excluded.release_date,
                    updated_at=datetime('now')
            """
            params = [
                entry["category"],
                entry["rank"],
                entry["model_name"],
                entry["organization"],
                entry.get("score"),
                entry.get("score_details"),
                entry.get("is_opensource", 0),
                entry.get("is_domestic", 1),
                entry.get("release_date", ""),
            ]
            statements.append((sql, params))
        return await self.db.execute_batch(statements)

    async def get_leaderboard_categories(self) -> List[Dict]:
        sql = """
            SELECT category, COUNT(*) as model_count, MAX(updated_at) as updated_at
            FROM leaderboards
            GROUP BY category
            ORDER BY category
        """
        return await self.db.query_all(sql)

    async def get_leaderboard(self, category: str, opensource: Optional[str] = None,
                               domestic: Optional[str] = None, page: int = 1,
                               page_size: int = 50) -> Dict:
        conditions = ["category = ?"]
        params = [category]

        if opensource == "open":
            conditions.append("is_opensource = 1")
        elif opensource == "closed":
            conditions.append("is_opensource = 0")

        if domestic == "domestic":
            conditions.append("is_domestic = 1")
        elif domestic == "overseas":
            conditions.append("is_domestic = 0")

        where = " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) as total FROM leaderboards WHERE {where}"
        count_row = await self.db.query_one(count_sql, params)
        total = int(count_row.get("total", 0)) if count_row else 0

        sql = f"""
            SELECT * FROM leaderboards
            WHERE {where}
            ORDER BY rank ASC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, (page - 1) * page_size])
        rows = await self.db.query_all(sql, params)

        result = []
        for row in rows:
            entry = dict(row)
            if isinstance(entry.get("score_details"), str):
                try:
                    entry["score_details"] = json.loads(entry["score_details"])
                except:
                    entry["score_details"] = {}
            result.append(entry)

        return {
            "entries": result,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    async def get_leaderboard_detail(self, category: str) -> Optional[Dict]:
        sql = "SELECT * FROM leaderboards WHERE category = ? ORDER BY rank ASC LIMIT 1"
        row = await self.db.query_one(sql, [category])
        if not row:
            return None

        count_sql = "SELECT COUNT(*) as total FROM leaderboards WHERE category = ?"
        count_row = await self.db.query_one(count_sql, [category])
        total = int(count_row.get("total", 0)) if count_row else 0

        return {
            "category": category,
            "total_models": total,
            "updated_at": row.get("updated_at"),
        }
