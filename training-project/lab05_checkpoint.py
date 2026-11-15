"""Display recorded Lab 05 evidence for the six student screenshots."""

import argparse
import getpass
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "reports" / "lab05"
ROLES = ("experiment-baseline", "candidate-configuration")
CASES = ("ec-05-1", "ec-05-2", "ec-05-3")


def read(relative):
    return json.loads((REPORT / relative).read_text(encoding="utf-8"))


def verify(command):
    result = subprocess.run(
        [sys.executable, "-m", "learning_project.cli", "lab05", command,
         "--report-dir", "reports/lab05"], cwd=ROOT, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{command} failed; keep the diagnostic output.")


def display(step):
    print(f"Account: {getpass.getuser()} | GitHub: exideys", flush=True)
    print(f"System date: {datetime.now().astimezone().isoformat(timespec='seconds')}", flush=True)
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True,
    ).strip()
    print(f"Branch: {branch} | Laboratory 05 | Checkpoint {step}\n", flush=True)
    if step == 1:
        record = read("query-rewriting/query-rewriting-results.json")
        print(f"Rule: {record['query-rewriting rule']}")
        for case in record["cases"]:
            print(f"\n{case['case id']}: {case['outcome']}")
            if "meaning preservation" in case:
                for field, value in case["meaning preservation"].items():
                    print(f"  {field}: {value}")
                print(f"  rewritten retrieval input: {case['rewritten retrieval input']}")
            else:
                print(f"  missing identity: {case['missing identity']}")
                print("  rewritten retrieval input: absent")
            print(f"  next operation: {case['next operation']}")
        print("\nRanked candidate output: absent in both rewrite results.")
        sys.stdout.flush()
        verify("verify-query-rewriting")
    elif step == 2:
        record = read("retrieval-unit-selection/selection-record.json")
        print(f"Record: {record['selection record id']} | Criteria: {record['retrieval-unit admission criteria']}")
        print(f"Text query: {record['text query']}")
        print(f"Context budget: {record['context budget characters']} characters")
        for unit in record["ranked candidate output"]:
            print(f"Rank {unit['rank']}: {unit['retrieval unit id']} ({unit['text character count']} characters)")
        print("Admitted:", ", ".join(u["retrieval unit id"] for u in record["supplied source evidence"]))
        for excluded in record["exclusions"]:
            print(f"Excluded {excluded['retrieval unit id']}: {excluded['failed criterion']}")
            print("  evaluated criteria:", ", ".join(excluded["evaluated criteria"]))
        print(f"Remaining budget: {record['remaining context budget characters']} characters")
        sys.stdout.flush()
        verify("verify-retrieval-unit-selection")
    elif step == 3:
        record = read("context-construction/bounded-model-request.json")
        print(f"Bounded model request: {record['bounded model request id']}")
        fields = record["required fields"]
        print("Required fields:")
        print(f"  task instruction: {fields['task instruction']['task instruction id']}")
        print("  supplied source evidence:", ", ".join(u["retrieval unit id"] for u in fields["supplied source evidence"]))
        print(f"  output contract: {fields['output contract']['output contract id']}")
        print("Excluded request fields:")
        for field in record["excluded request fields"]:
            print(f"  {field}")
        print("Context budget:", json.dumps(record["context budget"]))
        print(f"Next operation: {record['next operation']}")
        sys.stdout.flush()
        verify("verify-context-construction")
    elif step == 4:
        protocol = read("generation/shared-experiment-protocol.json")
        print(f"Protocol: {protocol['shared experiment protocol id']}")
        for role, config in protocol["configuration roles"].items():
            print(f"{role}: {config['model id']} / {config['instruction profile']}")
        for role in ROLES:
            for case in CASES:
                outcome = read(f"generation/runs/{role}/{case}/raw-outcome.json")
                print(f"{role} / {case}: {outcome['outcome type']}")
                if case == "ec-05-3":
                    print("  blocking condition:", outcome["blocking condition"])
        sys.stdout.flush()
        verify("verify-generation-outputs")
    elif step == 5:
        review_input = read("human-review-input.json")
        if "review_seconds_by_role" in review_input or "review_seconds_per_output" in review_input:
            print("Review-time inputs: user-specified, unmeasured; shown separately for each role.")
        rates = read("evaluation/rubric-pass-rate.json")["rubric pass rates"]
        conditions = read("evaluation/acceptance-evaluation.json")["acceptance condition evaluation"]
        for role, rate in rates.items():
            numerator = rate["candidate concept definition passes"] + rate["refusal passes"]
            print(f"{role}: {numerator}/{rate['judged outputs']} = {rate['rubric pass rate']}")
            for name, value in conditions[role].items():
                print(f"  {name}: {value['result'] if isinstance(value, dict) else value}")
                if isinstance(value, dict) and "observed maximum review minutes" in value:
                    minutes, seconds = divmod(round(value["observed maximum review minutes"] * 60), 60)
                    duration = f"{minutes}m" + (f" {seconds}s" if seconds else "")
                    print(f"    review-time input: {duration} / limit {value['permitted maximum']}m")
                if isinstance(value, dict) and "observed maximum elapsed seconds" in value:
                    print(f"    elapsed seconds: {value['observed maximum elapsed seconds']} / limit {value['permitted maximum']}")
        decision = read("evaluation/configuration-decision.json")
        print("Decision:", decision["bounded configuration decision"])
        print("Scope:", decision["scope"])
        print("Authority boundary:", decision["authority boundary"])
        sys.stdout.flush()
        verify("verify-evaluation-outputs")
    else:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        print(f"Exact HEAD: {head}", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "learning_project.cli", "lab05", "verify",
             "--report-dir", "reports/lab05", "--final-commit", head], cwd=ROOT,
        )
        record = read("verification-report.json")
        print(f"Recorded verification: {record['outcome']} | {record['final_commit']}")
        if result.returncode:
            raise RuntimeError("Final verification failed; fix the reported checks before submission.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", type=int, choices=range(1, 7))
    args = parser.parse_args()
    try:
        display(args.step)
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        print(f"\nCheckpoint unavailable: {exc}", file=sys.stderr)
        sys.exit(1)
