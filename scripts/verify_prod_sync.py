import asyncio
import httpx
import sys
import os

sys.stdout.reconfigure(line_buffering=True)

UAT_URL = os.environ["UAT_DB_URL"]
UAT_TOKEN = os.environ["UAT_DB_TOKEN"]
PROD_URL = os.environ["PROD_DB_URL"]
PROD_TOKEN = os.environ["PROD_DB_TOKEN"]


def _url_to_http(url):
    return url.replace("libsql://", "https://")


async def query_count(url, token, table):
    http_url = _url_to_http(url)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{http_url}/v2/pipeline",
            json={"requests": [{"type": "execute", "stmt": {"sql": f"SELECT COUNT(*) as cnt FROM {table}"}}]},
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return -1
        result_data = results[0].get("response", {}).get("result", {})
        if not result_data:
            return -1
        rows = result_data.get("rows", [])
        if not rows:
            return -1
        val = rows[0][0]
        if isinstance(val, dict):
            return int(val.get("value", -1))
        return int(val)


async def main():
    print("=" * 60, flush=True)
    print("VERIFY: UAT vs PROD Database", flush=True)
    print("=" * 60, flush=True)

    tables = ["models", "leaderboards", "leaderboard", "model_marketplace", "price_history", "scenarios", "scenario_steps"]

    all_match = True
    for table in tables:
        try:
            uat_cnt = await query_count(UAT_URL, UAT_TOKEN, table)
            prod_cnt = await query_count(PROD_URL, PROD_TOKEN, table)
            match = "✓" if uat_cnt == prod_cnt else "✗"
            if uat_cnt != prod_cnt:
                all_match = False
            print(f"  {table}: UAT={uat_cnt}, PROD={prod_cnt} {match}", flush=True)
        except Exception as e:
            print(f"  {table}: ERROR - {e}", flush=True)
            all_match = False

    if all_match:
        print("\n✓ All tables match!", flush=True)
    else:
        print("\n✗ Some tables do not match!", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
