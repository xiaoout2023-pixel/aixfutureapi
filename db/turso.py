import os
import json
import httpx

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "libsql://ai-models-db-xiaoout.aws-us-west-2.turso.io")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzcxMzk0NTcsImlkIjoiMDE5ZGM1YzMtYjEwMS03ZmI3LTk2MTktMjcxMTQ5MTc0NjMxIiwicmlkIjoiMWRiYjJmYmQtYzBiOS00MGVmLTk1OGYtODMxMDQ5OGI3MGEwIn0.ZJPCre8vUElMfKyEJITI6cdLcj9yDwjGxd49FmoXYBe5VlaVbs4LTKYffeTzbbKZGYOB8KCd-ubqrzjOs6mGCg")

class TursoDB:
    def __init__(self, url=None, token=None):
        self.url = (url or TURSO_DATABASE_URL).replace("libsql://", "https://")
        self.token = token or TURSO_AUTH_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _convert_value(self, value):
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

    def _format_args(self, params):
        if not params:
            return None
        args = []
        for p in params:
            if p is None:
                args.append({"type": "null"})
            elif isinstance(p, bool):
                args.append({"type": "text", "value": "1" if p else "0"})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": str(p)})
            else:
                args.append({"type": "text", "value": str(p)})
        return args

    async def execute(self, sql, params=None):
        stmt = {"sql": sql}
        formatted_args = self._format_args(params)
        if formatted_args:
            stmt["args"] = formatted_args
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.url}/v2/pipeline", json={"requests": [{"type": "execute", "stmt": stmt}]}, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def execute_batch(self, statements):
        requests = []
        for sql, params in statements:
            stmt = {"sql": sql}
            formatted_args = self._format_args(params)
            if formatted_args:
                stmt["args"] = formatted_args
            requests.append({"type": "execute", "stmt": stmt})
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.url}/v2/pipeline", json={"requests": requests}, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def query(self, sql, params=None):
        result = await self.execute(sql, params)
        results = result.get("results", [])
        if not results:
            return []
        result_data = results[0].get("response", {}).get("result", {})
        if not result_data:
            return []
        cols = [c.get("name", "") for c in result_data.get("cols", [])]
        rows = []
        for row in result_data.get("rows", []):
            rows.append({cols[i]: self._convert_value(row[i]) for i in range(len(cols))})
        return rows

    async def query_one(self, sql, params=None):
        results = await self.query(sql, params)
        return results[0] if results else None

    async def query_all(self, sql, params=None):
        return await self.query(sql, params)
