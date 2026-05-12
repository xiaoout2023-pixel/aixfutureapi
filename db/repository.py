import json
from typing import List, Dict, Optional
from db.turso import TursoDB


def _to_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _to_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _parse_json(val, default=None):
    if default is None:
        default = {}
    if val is None:
        return default
    if isinstance(val, dict) or isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default


def _parse_model_row(row: Dict) -> Dict:
    if not row:
        return None
    r = dict(row)
    r["capabilities"] = _parse_json(r.get("capabilities"), {})
    r["urls"] = _parse_json(r.get("urls"), {})
    r["tags"] = _parse_json(r.get("tags"), [])
    r["aliases"] = _parse_json(r.get("aliases"), [])
    r["regions"] = _parse_json(r.get("regions"), [])
    r["private_deployment"] = bool(_to_int(r.get("private_deployment")))
    r["openai_compatible"] = bool(_to_int(r.get("openai_compatible")))
    r["context_length"] = _to_int(r.get("context_length"))
    r["max_output_tokens"] = _to_int(r.get("max_output_tokens"))
    return r


def _parse_pricing_row(row: Dict) -> Dict:
    if not row:
        return None
    r = dict(row)
    r["reasoning_tokens_charged"] = bool(_to_int(r.get("reasoning_tokens_charged")))
    r["has_spot"] = bool(_to_int(r.get("has_spot")))
    r["tiers"] = _parse_json(r.get("tiers"))
    r["volume_discount"] = _parse_json(r.get("volume_discount"))
    return r


def _parse_eval_row(row: Dict) -> Dict:
    if not row:
        return None
    r = dict(row)
    r["other_benchmarks"] = _parse_json(r.get("other_benchmarks"), {})
    return r


_PRICING_SUBQUERY = """
    SELECT model_id, input_price_per_1m, output_price_per_1m,
           cache_read_price_per_1m, cache_write_price_per_1m,
           currency, free_tier_tokens, reasoning_tokens_charged
    FROM pricing
    WHERE channel = 'official' AND region = 'global'
      AND valid_from = (
          SELECT MAX(p2.valid_from) FROM pricing p2
          WHERE p2.model_id = pricing.model_id
            AND p2.channel = 'official' AND p2.region = 'global'
      )
"""

_AA_EVAL_SUBQUERY = """
    SELECT model_id, aa_intelligence_index, aa_coding_index, aa_math_index,
           tokens_per_second, ttft_ms, mmlu_pro, gpqa, hle, aime,
           livecodebench, scicode, ifbench, aa_lcr
    FROM evaluations
    WHERE source = 'https://artificialanalysis.ai'
      AND eval_date = (
          SELECT MAX(e2.eval_date) FROM evaluations e2
          WHERE e2.model_id = evaluations.model_id
            AND e2.source = 'https://artificialanalysis.ai'
      )
"""

_LMARENA_EVAL_SUBQUERY = """
    SELECT model_id, lmarena_elo, lmarena_coding, lmarena_math, lmarena_hard
    FROM evaluations
    WHERE source = 'https://lmarena.ai'
      AND eval_date = (
          SELECT MAX(e2.eval_date) FROM evaluations e2
          WHERE e2.model_id = evaluations.model_id
            AND e2.source = 'https://lmarena.ai'
      )
"""


class ModelRepository:
    def __init__(self, db: TursoDB):
        self.db = db

    async def get_models(self, page: int = 1, page_size: int = 20,
                         provider: Optional[str] = None,
                         capability: Optional[str] = None,
                         provider_type: Optional[str] = None,
                         status: Optional[str] = None,
                         q: Optional[str] = None,
                         sort_by: str = "aa_intelligence_index",
                         sort_order: str = "desc",
                         min_input_price: Optional[float] = None,
                         max_input_price: Optional[float] = None) -> Dict:
        conditions = ["m.status = 'active'"]
        params = []

        if provider:
            conditions.append("m.provider = ?")
            params.append(provider)
        if provider_type:
            conditions.append("m.provider_type = ?")
            params.append(provider_type)
        if status:
            conditions.append("m.status = ?")
            params.append(status)
        if q:
            conditions.append("(m.model_id LIKE ? OR m.model_name LIKE ? OR m.provider LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        if capability:
            conditions.append("m.capabilities LIKE ?")
            params.append(f'%"{capability}":true%')
        if min_input_price is not None:
            conditions.append("p_official.input_price_per_1m >= ?")
            params.append(min_input_price)
        if max_input_price is not None:
            conditions.append("p_official.input_price_per_1m <= ?")
            params.append(max_input_price)

        where = " AND ".join(conditions)

        sort_map = {
            "aa_intelligence_index": "eval_aa.aa_intelligence_index",
            "lmarena_elo": "eval_lmarena.lmarena_elo",
            "input_price": "p_official.input_price_per_1m",
            "output_price": "p_official.output_price_per_1m",
            "context_length": "m.context_length",
            "tokens_per_second": "eval_aa.tokens_per_second",
            "model_name": "m.model_name",
        }
        order_col = sort_map.get(sort_by, "eval_aa.aa_intelligence_index")
        nulls = "DESC NULLS LAST" if sort_order.upper() == "DESC" else "ASC NULLS LAST"

        count_sql = f"""
            SELECT COUNT(*) as total FROM models m
            LEFT JOIN ({_PRICING_SUBQUERY}) p_official ON m.model_id = p_official.model_id
            LEFT JOIN ({_AA_EVAL_SUBQUERY}) eval_aa ON m.model_id = eval_aa.model_id
            LEFT JOIN ({_LMARENA_EVAL_SUBQUERY}) eval_lmarena ON m.model_id = eval_lmarena.model_id
            WHERE {where}
        """
        count_row = await self.db.query_one(count_sql, params)
        total = _to_int(count_row.get("total", 0)) if count_row else 0

        data_sql = f"""
            SELECT m.*,
                p_official.input_price_per_1m as official_input_price,
                p_official.output_price_per_1m as official_output_price,
                p_official.cache_read_price_per_1m as official_cache_read_price,
                p_official.cache_write_price_per_1m as official_cache_write_price,
                p_official.currency as official_currency,
                p_official.free_tier_tokens as official_free_tier_tokens,
                p_official.reasoning_tokens_charged as official_reasoning_charged,
                eval_aa.aa_intelligence_index,
                eval_aa.aa_coding_index,
                eval_aa.aa_math_index,
                eval_aa.tokens_per_second,
                eval_aa.ttft_ms,
                eval_lmarena.lmarena_elo,
                eval_lmarena.lmarena_coding,
                eval_lmarena.lmarena_math,
                eval_lmarena.lmarena_hard
            FROM models m
            LEFT JOIN ({_PRICING_SUBQUERY}) p_official ON m.model_id = p_official.model_id
            LEFT JOIN ({_AA_EVAL_SUBQUERY}) eval_aa ON m.model_id = eval_aa.model_id
            LEFT JOIN ({_LMARENA_EVAL_SUBQUERY}) eval_lmarena ON m.model_id = eval_lmarena.model_id
            WHERE {where}
            ORDER BY {order_col} {nulls}
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, (page - 1) * page_size])
        rows = await self.db.query(data_sql, params)
        models = [_parse_model_row(row) for row in rows]

        for m in models:
            _cr = m.pop("official_cache_read_price", None)
            _cw = m.pop("official_cache_write_price", None)
            m["pricing"] = {
                "input_per_1m_tokens": _to_float(m.pop("official_input_price", None)),
                "output_per_1m_tokens": _to_float(m.pop("official_output_price", None)),
                "cache_read_per_1m": _to_float(_cr) if _cr is not None else None,
                "cache_write_per_1m": _to_float(_cw) if _cw is not None else None,
                "currency": m.pop("official_currency", "USD") or "USD",
                "free_tier_tokens": m.pop("official_free_tier_tokens", None),
                "reasoning_tokens_charged": bool(_to_int(m.pop("official_reasoning_charged", 0))),
            }
            _aii = m.pop("aa_intelligence_index", None)
            _aci = m.pop("aa_coding_index", None)
            _ami = m.pop("aa_math_index", None)
            _tps = m.pop("tokens_per_second", None)
            _ttft = m.pop("ttft_ms", None)
            _le = m.pop("lmarena_elo", None)
            _lc = m.pop("lmarena_coding", None)
            _lm = m.pop("lmarena_math", None)
            _lh = m.pop("lmarena_hard", None)
            m["evaluation"] = {
                "aa_intelligence_index": _to_float(_aii) if _aii is not None else None,
                "aa_coding_index": _to_float(_aci) if _aci is not None else None,
                "aa_math_index": _to_float(_ami) if _ami is not None else None,
                "tokens_per_second": _to_int(_tps) if _tps is not None else None,
                "ttft_ms": _to_int(_ttft) if _ttft is not None else None,
                "lmarena_elo": _to_float(_le) if _le is not None else None,
                "lmarena_coding": _to_float(_lc) if _lc is not None else None,
                "lmarena_math": _to_float(_lm) if _lm is not None else None,
                "lmarena_hard": _to_float(_lh) if _lh is not None else None,
            }

        return {
            "data": models,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    async def get_model(self, model_id: str) -> Optional[Dict]:
        row = await self.db.query_one("SELECT * FROM models WHERE model_id = ?", [model_id])
        if not row:
            return None
        model = _parse_model_row(row)

        pricing_rows = await self.db.query(
            "SELECT * FROM pricing WHERE model_id = ? ORDER BY channel, region, valid_from DESC",
            [model_id])
        model["pricing_list"] = [_parse_pricing_row(p) for p in pricing_rows]

        official = [p for p in pricing_rows if p.get("channel") == "official" and p.get("region") == "global"]
        if official:
            o = official[0]
            model["pricing"] = {
                "input_per_1m_tokens": _to_float(o.get("input_price_per_1m")),
                "output_per_1m_tokens": _to_float(o.get("output_price_per_1m")),
                "cache_read_per_1m": _to_float(o.get("cache_read_price_per_1m")) if o.get("cache_read_price_per_1m") is not None else None,
                "cache_write_per_1m": _to_float(o.get("cache_write_price_per_1m")) if o.get("cache_write_price_per_1m") is not None else None,
                "currency": o.get("currency", "USD") or "USD",
                "free_tier_tokens": o.get("free_tier_tokens"),
                "reasoning_tokens_charged": bool(_to_int(o.get("reasoning_tokens_charged", 0))),
            }
        else:
            model["pricing"] = None

        eval_rows = await self.db.query(
            "SELECT * FROM evaluations WHERE model_id = ? ORDER BY eval_date DESC, source",
            [model_id])
        model["evaluations"] = [_parse_eval_row(e) for e in eval_rows]

        eval_aa = [e for e in eval_rows if e.get("source") == "https://artificialanalysis.ai"]
        eval_lmarena = [e for e in eval_rows if e.get("source") == "https://lmarena.ai"]
        if eval_aa:
            aa = eval_aa[0]
            model["evaluation"] = {
                "aa_intelligence_index": aa.get("aa_intelligence_index"),
                "aa_coding_index": aa.get("aa_coding_index"),
                "aa_math_index": aa.get("aa_math_index"),
                "tokens_per_second": aa.get("tokens_per_second"),
                "ttft_ms": aa.get("ttft_ms"),
                "mmlu_pro": aa.get("mmlu_pro"),
                "gpqa": aa.get("gpqa"),
                "hle": aa.get("hle"),
                "aime": aa.get("aime"),
                "livecodebench": aa.get("livecodebench"),
                "ifbench": aa.get("ifbench"),
                "aa_lcr": aa.get("aa_lcr"),
            }
        if eval_lmarena:
            lm = eval_lmarena[0]
            if "evaluation" not in model:
                model["evaluation"] = {}
            model["evaluation"].update({
                "lmarena_elo": lm.get("lmarena_elo"),
                "lmarena_coding": lm.get("lmarena_coding"),
                "lmarena_math": lm.get("lmarena_math"),
                "lmarena_hard": lm.get("lmarena_hard"),
            })

        return model

    async def get_providers(self) -> List[Dict]:
        rows = await self.db.query("""
            SELECT provider, provider_type, COUNT(*) as model_count
            FROM models
            WHERE status = 'active'
            GROUP BY provider
            ORDER BY model_count DESC
        """)
        priority = [
            "openai", "anthropic", "google", "deepseek", "meta",
            "mistralai", "xai", "alibaba", "qwen", "zhipu",
            "moonshot", "minimax", "baidu", "bytedance", "nvidia",
        ]
        result_priority = []
        result_others = []
        for row in rows:
            if row["provider"] in priority:
                result_priority.append(row)
            else:
                result_others.append(row)
        result_priority.sort(key=lambda x: priority.index(x["provider"]) if x["provider"] in priority else 999)
        return result_priority + result_others

    async def get_leaderboard(self, metric: str = "aa_intelligence_index",
                               page: int = 1, page_size: int = 50,
                               provider_type: Optional[str] = None) -> Dict:
        metric_map = {
            "aa_intelligence_index": ("eval_aa.aa_intelligence_index", "https://artificialanalysis.ai"),
            "aa_coding_index": ("eval_aa.aa_coding_index", "https://artificialanalysis.ai"),
            "aa_math_index": ("eval_aa.aa_math_index", "https://artificialanalysis.ai"),
            "lmarena_elo": ("eval_lmarena.lmarena_elo", "https://lmarena.ai"),
            "lmarena_coding": ("eval_lmarena.lmarena_coding", "https://lmarena.ai"),
            "lmarena_math": ("eval_lmarena.lmarena_math", "https://lmarena.ai"),
            "lmarena_hard": ("eval_lmarena.lmarena_hard", "https://lmarena.ai"),
            "tokens_per_second": ("eval_aa.tokens_per_second", "https://artificialanalysis.ai"),
        }
        if metric not in metric_map:
            metric = "aa_intelligence_index"

        col, source = metric_map[metric]

        conditions = ["m.status = 'active'", f"{col} IS NOT NULL"]
        params = []
        if provider_type:
            conditions.append("m.provider_type = ?")
            params.append(provider_type)
        where = " AND ".join(conditions)

        count_sql = f"""
            SELECT COUNT(*) as total
            FROM models m
            LEFT JOIN ({_AA_EVAL_SUBQUERY}) eval_aa ON m.model_id = eval_aa.model_id
            LEFT JOIN ({_LMARENA_EVAL_SUBQUERY}) eval_lmarena ON m.model_id = eval_lmarena.model_id
            WHERE {where}
        """
        count_row = await self.db.query_one(count_sql, params)
        total = _to_int(count_row.get("total", 0)) if count_row else 0

        data_sql = f"""
            SELECT m.model_id, m.model_name, m.provider, m.provider_type,
                m.capabilities, m.context_length, m.tags,
                p_official.input_price_per_1m, p_official.output_price_per_1m, p_official.currency,
                eval_aa.aa_intelligence_index, eval_aa.aa_coding_index, eval_aa.aa_math_index,
                eval_aa.tokens_per_second, eval_aa.ttft_ms,
                eval_lmarena.lmarena_elo, eval_lmarena.lmarena_coding,
                eval_lmarena.lmarena_math, eval_lmarena.lmarena_hard,
                {col} as rank_score
            FROM models m
            LEFT JOIN ({_PRICING_SUBQUERY}) p_official ON m.model_id = p_official.model_id
            LEFT JOIN ({_AA_EVAL_SUBQUERY}) eval_aa ON m.model_id = eval_aa.model_id
            LEFT JOIN ({_LMARENA_EVAL_SUBQUERY}) eval_lmarena ON m.model_id = eval_lmarena.model_id
            WHERE {where}
            ORDER BY rank_score DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, (page - 1) * page_size])
        rows = await self.db.query(data_sql, params)

        entries = []
        for idx, row in enumerate(rows):
            entry = _parse_model_row(row)
            entry["rank"] = (page - 1) * page_size + idx + 1
            entry["rank_score"] = _to_float(row.get("rank_score"))
            _ip = entry.pop("input_price_per_1m", None)
            _op = entry.pop("output_price_per_1m", None)
            _cur = entry.pop("currency", None)
            entry["pricing"] = {
                "input_per_1m_tokens": _to_float(_ip) if _ip is not None else None,
                "output_per_1m_tokens": _to_float(_op) if _op is not None else None,
                "currency": _cur or "USD",
            }
            _aii = entry.pop("aa_intelligence_index", None)
            _aci = entry.pop("aa_coding_index", None)
            _ami = entry.pop("aa_math_index", None)
            _tps = entry.pop("tokens_per_second", None)
            _ttft = entry.pop("ttft_ms", None)
            _le = entry.pop("lmarena_elo", None)
            _lc = entry.pop("lmarena_coding", None)
            _lm = entry.pop("lmarena_math", None)
            _lh = entry.pop("lmarena_hard", None)
            entry["evaluation"] = {
                "aa_intelligence_index": _to_float(_aii) if _aii is not None else None,
                "aa_coding_index": _to_float(_aci) if _aci is not None else None,
                "aa_math_index": _to_float(_ami) if _ami is not None else None,
                "tokens_per_second": _to_int(_tps) if _tps is not None else None,
                "ttft_ms": _to_int(_ttft) if _ttft is not None else None,
                "lmarena_elo": _to_float(_le) if _le is not None else None,
                "lmarena_coding": _to_float(_lc) if _lc is not None else None,
                "lmarena_math": _to_float(_lm) if _lm is not None else None,
                "lmarena_hard": _to_float(_lh) if _lh is not None else None,
            }
            entries.append(entry)

        return {
            "metric": metric,
            "source": source,
            "data": entries,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    async def search_models(self, q: str, limit: int = 10) -> Dict:
        sql = f"""
            SELECT m.model_id, m.model_name, m.provider, m.provider_type,
                eval_aa.aa_intelligence_index
            FROM models m
            LEFT JOIN ({_AA_EVAL_SUBQUERY}) eval_aa ON m.model_id = eval_aa.model_id
            WHERE m.status = 'active'
              AND (m.model_id LIKE ? OR m.model_name LIKE ? OR m.provider LIKE ?)
            ORDER BY eval_aa.aa_intelligence_index DESC NULLS LAST
            LIMIT ?
        """
        params = [f"%{q}%", f"%{q}%", f"%{q}%", limit]
        rows = await self.db.query(sql, params)
        return {"suggestions": [_parse_model_row(row) for row in rows]}

    async def get_model_pricing(self, model_id: str,
                                 channel: Optional[str] = None,
                                 region: Optional[str] = None) -> List[Dict]:
        conditions = ["model_id = ?"]
        params = [model_id]
        if channel:
            conditions.append("channel = ?")
            params.append(channel)
        if region:
            conditions.append("region = ?")
            params.append(region)
        where = " AND ".join(conditions)
        rows = await self.db.query(
            f"SELECT * FROM pricing WHERE {where} ORDER BY channel, region, valid_from DESC",
            params)
        return [_parse_pricing_row(p) for p in rows]

    async def get_model_evaluations(self, model_id: str) -> List[Dict]:
        rows = await self.db.query(
            "SELECT * FROM evaluations WHERE model_id = ? ORDER BY eval_date DESC, source",
            [model_id])
        return [_parse_eval_row(e) for e in rows]

    async def get_status(self) -> Dict:
        models_cnt = await self.db.query_one("SELECT COUNT(*) as cnt FROM models WHERE status = 'active'")
        providers_cnt = await self.db.query_one("SELECT COUNT(DISTINCT provider) as cnt FROM models WHERE status = 'active'")
        pricing_cnt = await self.db.query_one("SELECT COUNT(*) as cnt FROM pricing")
        eval_cnt = await self.db.query_one("SELECT COUNT(*) as cnt FROM evaluations")
        return {
            "total_models": _to_int(models_cnt.get("cnt", 0)) if models_cnt else 0,
            "total_providers": _to_int(providers_cnt.get("cnt", 0)) if providers_cnt else 0,
            "total_pricing_records": _to_int(pricing_cnt.get("cnt", 0)) if pricing_cnt else 0,
            "total_evaluations": _to_int(eval_cnt.get("cnt", 0)) if eval_cnt else 0,
        }
