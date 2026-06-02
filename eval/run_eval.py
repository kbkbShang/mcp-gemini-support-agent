from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from support_agent.agent import SupportAgent

QUESTIONS_FILE = ROOT / "eval" / "questions.json"
REPORT_FILE = ROOT / "eval" / "report.json"


def main() -> None:
    agent = SupportAgent()
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))

    items = []
    passed = 0
    for i, q in enumerate(questions, start=1):
        result = agent.run(query=q["query"], session_id=f"eval-{i:03d}")
        kb_titles = [c["title"] for c in result.citations if c["source"] == "kb"]
        has_expected = any(q["expect_doc"].lower() in t.lower() for t in kb_titles)
        ok = bool(result.answer.strip()) and len(result.citations) > 0 and 0 <= result.confidence <= 1 and has_expected
        if ok:
            passed += 1
        items.append(
            {
                "id": i,
                "query": q["query"],
                "expected": q["expect_doc"],
                "top_kb_titles": kb_titles,
                "confidence": result.confidence,
                "pass": ok,
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(questions),
        "passed": passed,
        "pass_rate": round(passed / len(questions), 4) if questions else 0.0,
        "items": items,
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Eval complete: {passed}/{len(questions)} passed. Report -> {REPORT_FILE}")


if __name__ == "__main__":
    main()
