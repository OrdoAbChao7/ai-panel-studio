"""End-to-end smoke demo against a running AI Panel Studio backend."""
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None


def main():
    print("[1] health")
    print("   ", json.dumps(call("GET", "/api/health"), ensure_ascii=False))

    topic = "AI 会取代初级程序员吗？"
    print("\n[2] generate roster ->", topic)
    roster = call("POST", "/api/discussions/roster/generate", {"topic": topic, "participant_count": 4})
    experts = roster.get("experts") or []
    for e in experts:
        print(f"    - {e['name']} | {e['occupation']}")
        print(f"      立场: {e['stance']}")

    print("\n[3] create discussion")
    participants = [
        {"name": e["name"], "occupation": e["occupation"], "stance": e["stance"],
         "perspective": e["perspective"], "color_hex": e["color_hex"]}
        for e in experts
    ]
    d = call("POST", "/api/discussions",
             {"topic": topic, "max_rounds": 3, "participants": participants})
    did = d["id"]
    print("    id =", did, "| status =", d.get("status"))

    print("\n[4] start debate")
    print("   ", json.dumps(call("POST", f"/api/discussions/{did}/start"), ensure_ascii=False))

    print("\n[5] watch progress")
    for i in range(24):
        time.sleep(5)
        st = call("GET", f"/api/discussions/{did}")
        turns = st.get("turns") or []
        print(f"    t+{(i+1)*5:>3}s  status={st.get('status'):<10} round={st.get('current_round')} turns={len(turns)}")
        if st.get("status") in ("completed", "terminated", "finished", "concluded"):
            break

    print("\n[6] transcript")
    tr = call("GET", f"/api/discussions/{did}/transcript")
    items = tr.get("turns") if isinstance(tr, dict) else tr
    for t in (items or [])[:6]:
        speaker = t.get("speaker_name") or t.get("speaker_id")
        content = (t.get("content") or "").replace("\n", " ")
        print(f"    [{speaker}] {content[:150]}...")

    print("\n[7] summary")
    try:
        s = call("GET", f"/api/discussions/{did}/summary")
        print("   ", json.dumps(s, ensure_ascii=False)[:900])
    except Exception as exc:
        print("    summary unavailable:", exc)

    print("\nDISCUSSION_ID=", did)


if __name__ == "__main__":
    sys.exit(main())
