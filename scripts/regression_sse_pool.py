"""Regression test: many concurrent SSE streams must not exhaust the DB pool.

Before the fix, `Depends(get_db)` on the SSE endpoint pinned one pooled
connection per open stream; the QueuePool (size 5 + overflow 10) was drained
after ~15 viewers and every REST endpoint began returning 500.
"""
import asyncio
import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"
STREAMS = 25


async def main() -> int:
    async with httpx.AsyncClient(base_url=BASE, timeout=20.0, trust_env=False) as c:
        discussions = (await c.get("/api/discussions")).json()
        if not discussions:
            print("no discussions to stream; run demo_smoke.py first")
            return 1
        did = discussions[0]["id"]
        print(f"streaming {STREAMS} concurrent SSE connections for {did}")

        opened = 0
        stop = asyncio.Event()

        async def hold_stream(i: int) -> None:
            nonlocal opened
            try:
                async with c.stream("GET", f"/api/discussions/{did}/events") as resp:
                    if resp.status_code != 200:
                        print(f"  stream {i}: HTTP {resp.status_code}")
                        return
                    opened += 1
                    async for _ in resp.aiter_lines():
                        if stop.is_set():
                            return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"  stream {i} error: {exc}")

        tasks = [asyncio.create_task(hold_stream(i)) for i in range(STREAMS)]
        await asyncio.sleep(6)
        print(f"  streams opened OK: {opened}/{STREAMS}")

        print("  probing REST endpoints while streams are held open...")
        failures = 0
        for path in ("/api/health", "/api/discussions", f"/api/discussions/{did}",
                     f"/api/discussions/{did}/transcript", f"/api/discussions/{did}/summary"):
            r = await c.get(path)
            tag = "OK " if r.status_code == 200 else "FAIL"
            if r.status_code != 200:
                failures += 1
            print(f"    {tag} {r.status_code}  {path}")

        stop.set()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        if opened < STREAMS:
            print(f"WARN: only {opened} streams opened")
        if failures or opened < STREAMS:
            print(f"RESULT: FAILED ({failures} REST failures, {opened} streams)")
            return 1
        print(f"RESULT: PASSED — {STREAMS} streams held, all REST endpoints healthy")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
