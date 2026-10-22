import sys
import xml.etree.ElementTree as ET

ENDPOINTS = {
    "test_endpoints": "GET /api/staff-workload/profiles and /alerts (database faked)",
    "test_live_endpoints": "GET /api/staff-workload/profiles and /alerts (running containers)",
    "test_multi_agent_mode": "Multi-Agent routes (switch and Student 3 boundary)",
}


def outcome(case):
    if case.find("failure") is not None or case.find("error") is not None:
        return "FAIL"
    if case.find("skipped") is not None:
        return "SKIP"
    return "PASS"


def main(path):
    # The file is the JUnit report pytest wrote earlier in the same CI job, not outside input.
    root = ET.parse(path).getroot()  # noqa: S314
    cases = list(root.iter("testcase"))
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    rows = []
    for case in cases:
        result = outcome(case)
        counts[result] += 1
        module = case.get("classname", "").split(".")[-1]
        rows.append(f"| {ENDPOINTS.get(module, module)} | `{case.get('name')}` | {result} | {float(case.get('time', 0)):.3f}s |")

    print("# Student 3 Post-Commit Endpoint Test Report\n")
    print(f"**{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped** ({len(cases)} tests)\n")
    print("| Endpoint function | Test | Result | Time |")
    print("| --- | --- | --- | --- |")
    print("\n".join(rows))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
