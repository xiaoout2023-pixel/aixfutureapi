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
            conditions.append("JSON_EXTRACT(capabilities, '$.vision') = ?")
            params.append("true" if filters["has_vision"] else "false")
        
        if filters.get("has_tool_calling") is not None:
            conditions.append("JSON_EXTRACT(capabilities, '$.tool_calling') = ?")
            params.append("true" if filters["has_tool_calling"] else "false")

        if filters.get("text_generation") is not None:
            conditions.append("JSON_EXTRACT(capabilities, '$.text_generation') = ?")
            params.append("true" if filters["text_generation"] else "false")

        if filters.get("code_generation") is not None:
            conditions.append("JSON_EXTRACT(capabilities, '$.code_generation') = ?")
            params.append("true" if filters["code_generation"] else "false")

        if filters.get("audio") is not None:
            conditions.append("JSON_EXTRACT(capabilities, '$.audio') = ?")
            params.append("true" if filters["audio"] else "false")

        if filters.get("multimodal") is not None:
            conditions.append("JSON_EXTRACT(capabilities, '$.multimodal') = ?")
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
