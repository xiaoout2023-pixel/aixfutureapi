import os
import json
import httpx

APP_ENV = os.environ.get("APP_ENV", "dev")

DB_CONFIGS = {
    "dev": {
        "url": os.environ.get("TURSO_DEV_URL", "libsql://modelstemp2-xiaoout.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_DEV_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc0MTI2OTcsImlkIjoiMDE5ZGQ2MGQtNDUwMS03YTA0LWEwMzYtOTM2MzJiMGI1MDJlIiwicmlkIjoiYjYxZGM1MzEtYWZhNi00ODQzLTlkMTYtNjhkYTY3ZGY1MTdjIn0.HV3mUz8GH3BJ2lOGJvCnuQF0xqiPwIwLTq5DaAtKfOLzwqL6iLNZj8XCnEA8sbaN2mzpxvRUc7rLB9quqCIbCw"),
    },
    "uat": {
        "url": os.environ.get("TURSO_UAT_URL", "libsql://ai-models-db-xiaoout.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_UAT_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzcxMzk0NTcsImlkIjoiMDE5ZGM1YzMtYjEwMS03ZmI3LTk2MTktMjcxMTQ5MTc0NjMxIiwicmlkIjoiMWRiYjJmYmQtYzBiOS00MGVmLTk1OGYtODMxMDQ5OGI3MGEwIn0.ZJPCre8vUElMfKyEJITI6cdLcj9yDwjGxd49FmoXYBe5VlaVbs4LTKYffeTzbbKZGYOB8KCd-ubqrzjOs6mGCg"),
    },
    "prod": {
        "url": os.environ.get("TURSO_PROD_URL", "libsql://aixfutureprod-xiaoout.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_PROD_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc0MTEwNjMsImlkIjoiMDE5ZGQ1ZjItZWQwMS03MjIxLWExYTAtODkxYjYzMTE2MWI2IiwicmlkIjoiNGQxMWU5MGEtNzE2NC00MjIzLWE0OGMtNGVjYWQ0NjAzOWM4In0.tJJcjMjfiAewjYpblXM8S1NKcSDZT0UBsBSmwYXz7DsU6I3kQXlyVvyAI8-sgKsGE4y6LZpbIw2viWg70tkhDQ"),
    },
    "temp2": {
        "url": os.environ.get("TURSO_TEMP2_URL", "libsql://modelstemp2-xiaoout.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_TEMP2_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc0MTI2OTcsImlkIjoiMDE5ZGQ2MGQtNDUwMS03YTA0LWEwMzYtOTM2MzJiMGI1MDJlIiwicmlkIjoiYjYxZGM1MzEtYWZhNi00ODQzLTlkMTYtNjhkYTY3ZGY1MTdjIn0.HV3mUz8GH3BJ2lOGJvCnuQF0xqiPwIwLTq5DaAtKfOLzwqL6iLNZj8XCnEA8sbaN2mzpxvRUc7rLB9quqCIbCw"),
    },
}

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", DB_CONFIGS[APP_ENV]["url"])
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", DB_CONFIGS[APP_ENV]["token"])


class TursoDB:
    def __init__(self, url=None, token=None):
        self.url = (url or TURSO_DATABASE_URL).replace("libsql://", "https://")
        self.token = token or TURSO_AUTH_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _convert_value(self, value):
        if isinstance(value, dict):
            if value.get("type") == "null":
                return None
            if "value" in value:
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
            elif isinstance(p, float):
                args.append({"type": "text", "value": str(p)})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
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
