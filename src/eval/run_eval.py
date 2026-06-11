import json
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent

TEST_CASES_PATH = BASE_DIR / "test_cases.json"
REPORT_PATH = BASE_DIR / "report.json"

CHAT_ENDPOINT = "http://localhost:8000/chat"


def run_eval():

    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []

    passed = 0

    for case in test_cases:

        response = requests.post(
            CHAT_ENDPOINT,
            json={
                "query": case["query"],
                "session_id": case["id"]
            }
        )

        agent_result = response.json()

        # Chekk which tools were called by the agent
        actual_tools = set(agent_result.get("tool_calls", []))

        expected_tools = set(case["expected_tools"])

        tools_match = expected_tools.issubset(actual_tools)

        # Check if citations exist when they are expected
        citations_exist = len(
            agent_result.get("citations", [])
        ) > 0

        citations_match = (
            citations_exist
            == case["should_have_citations"]
        )

        # Check if a ticket draft was created when expected
        ticket_created = (
            agent_result
            .get("ticket_draft", {})
            .get("created", False)
        )

        ticket_match = (
            ticket_created
            == case["should_create_ticket"]
        )

        # Final test pass if all conditions match
        test_pass = (
            tools_match
            and citations_match
            and ticket_match
        )

        if test_pass:
            passed += 1

        results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "passed": test_pass,
                "tools_match": tools_match,
                "citations_match": citations_match,
                "ticket_match": ticket_match,
                "actual_tools": list(actual_tools),
                "expected_tools": list(expected_tools),
            }
        )

    report = {
        "total_tests": len(test_cases),
        "passed": passed,
        "failed": len(test_cases) - passed,
        "pass_rate": round(
            passed / len(test_cases),
            2
        ),
        "results": results,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            report,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("=" * 60)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Pass Rate: {report['pass_rate']}")
    print("=" * 60)


if __name__ == "__main__":
    run_eval()