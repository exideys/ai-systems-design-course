"""Show actual Lab04 evidence for screenshots and finish the local report."""
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "reports" / "lab04"
NAMES = (
    "01-boundary-selection.png", "02-embedding-index.png",
    "03-retrieval-comparison.png", "04-relevance-metrics.png",
    "05-operational-decision.png", "06-final-verification.png",
)
SHORT = {
    "lexical retrieval": "lexical",
    "embedding-based retrieval": "embedding",
    "hybrid retrieval": "hybrid",
    "lexical retrieval followed by embedding-based reranking": "reranking",
}


def read(relative):
    return json.loads((REPORT / relative).read_text(encoding="utf-8"))


def cli(*args):
    subprocess.run(
        [sys.executable, "-m", "learning_project.cli", "lab04", *args,
         "--report-dir", "reports/lab04"], cwd=ROOT, check=True,
    )


def identity():
    print(f"Windows account: {getpass.getuser()} | GitHub: exideys", flush=True)
    print("System date: " + datetime.now().astimezone().isoformat(timespec="seconds"), flush=True)


def metric(value):
    return f"{value['numerator']}/{value['denominator']} = {value['value']}"


def checkpoint(number):
    identity()
    if number == 1:
        import yaml
        decision = yaml.safe_load((REPORT / "stage-b/boundary-decision.yaml").read_text(encoding="utf-8"))
        print("Selected boundary: " + decision["selected chunking configuration"])
        for config in read("stage-b/boundary-comparison.json")["chunking_configuration_results"]:
            units = config["source_fragments"]
            print(config["chunking_configuration_id"] + ": " + ", ".join(u["stable_retrieval_identifier"] for u in units))
        print("Rationale: " + decision["rationale"], flush=True)
        cli("verify-stage-b")
    elif number == 2:
        manifest = read("stage-c1/index-manifest.json")
        print("Index: " + manifest["index version"])
        print("Units: " + ", ".join(manifest["indexed retrieval units"]) + " | dimension: 256")
        for version in ("v1", "v2"):
            check = read(f"stage-c1/binding-check-required-course-seed-{version}.json")
            print(check["required retrieval configuration id"] + ": " + check["outcome"])
            if check["outcome"] == "stale":
                print("Failed binding: " + check["failed binding"])
                print("Rebuild condition: " + check["rebuild condition"])
        sys.stdout.flush()
        cli("verify-stage-c1")
    elif number == 3:
        print("case | configuration | ranked candidate output (unit, score)")
        for path in sorted((REPORT / "stage-c2").glob("*.json")):
            item = json.loads(path.read_text(encoding="utf-8"))
            ranked = [(r["stable retrieval identifier"], round(r["score"], 8)) for r in item["ranked candidate output"]]
            print(f"{item['evaluation case']} | {SHORT[item['retrieval configuration']]} | {ranked}")
        print("Names: lexical = lexical retrieval; embedding = embedding-based retrieval;")
        print("hybrid = hybrid retrieval; reranking = lexical retrieval followed by embedding-based reranking.", flush=True)
        cli("verify-stage-c2", "--model-dir", "models/potion-base-8M")
    elif number == 4:
        for case in read("stage-c3/relevance-judgments.json")["judged evaluation cases"]:
            print(case["evaluation case"] + ":")
            for item in case["relevance judgments"]:
                print(item["stable retrieval identifier"] + ": " + item["relevance judgment"])
                print(item["rationale"])
        metrics = read("stage-c3/retrieval-metrics.json")
        print("case | configuration | precision@1 | recall@1")
        for item in metrics["per-case metrics"]:
            print(f"{item['evaluation case']} | {SHORT[item['retrieval configuration']]} | {metric(item['precision@1'])} | {metric(item['recall@1'])}")
        print("Aggregate across A+B:")
        for item in metrics["aggregate metrics"]:
            print(f"{SHORT[item['retrieval configuration']]} | P: {metric(item['precision@1'])} | R: {metric(item['recall@1'])}")
        print("Empty output: precision undefined (0/0); recall 0/1. Latency is excluded from metrics.")
    elif number == 5:
        operations = read("stage-c3/operational-evidence.json")
        print("Measured wall-clock seconds for BOTH queries, mean of 3 runs:")
        for item in operations["operational measurements"]:
            print(f"{SHORT[item['retrieval configuration']]}: {item['query latency']['measurement']} s | failures: {item['execution failures']['measurement']}")
        print("Index build: not re-measured; archived index reused. Query cost: encoder operations, no currency estimate.")
        print("Resources: local model and CPU; peak memory not instrumented; no network during retrieval.")
        decision = read("stage-c3/configuration-decision.json")
        print("Selected: " + decision["selected retrieval configuration"])
        print("Rationale: " + decision["rationale"])
        print("Decision boundary: " + decision["decision boundary"])
        print("Authority boundary: " + decision["authority boundary"], flush=True)
        cli("verify-stage-c3", "--model-dir", "models/potion-base-8M")
    elif number == 6:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        print("Exact final commit: " + commit, flush=True)
        cli("verify", "--final-commit", commit)
        verification = read("verification-report.json")
        print("Verification outcome: " + verification["outcome"])
        print("Verified commit: " + verification["final_commit"])
    identity()


def tests():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    log = REPORT / "public-tests-final.log"
    with log.open("wb") as stream:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests/public", "-v"],
            cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, env=env,
        )
    output = log.read_text(encoding="utf-8", errors="replace")
    for line in output.splitlines():
        if line.startswith(("Ran ", "OK", "FAILED", "ERROR:", "FAIL:")):
            print(line)
    (REPORT / "public-tests-result.json").write_text(json.dumps({
        "returncode": result.returncode,
        "command": "uv run python -m unittest discover -s tests/public -v",
        "generated_at": datetime.now().astimezone().isoformat(),
        "log": log.name,
    }, indent=2) + "\n", encoding="utf-8")
    print("Full log: " + str(log))
    return result.returncode


def finalize():
    from PIL import Image
    if read("public-tests-result.json")["returncode"] != 0:
        raise RuntimeError("Public tests have not passed.")
    for name in NAMES[:5]:
        with Image.open(REPORT / "screenshots" / name) as screenshot:
            if screenshot.format != "PNG":
                raise RuntimeError("Expected a real PNG screenshot: " + name)
            screenshot.verify()
    cli("verify-stage-c3", "--model-dir", "models/potion-base-8M")
    path = REPORT / "REPORT.md"
    body = path.read_text(encoding="utf-8")
    body = body.replace("Статус завершення: `honest-partial`", "Статус завершення: `complete`")
    body = body.replace(
        "Завершення подання очікується: потрібно переглянути судження, зберегти п’ять початкових знімків, успішно повторити публічні тести та виконати локальну перевірку остаточного коміту.",
        "Студент переглянув підготовлені за допомогою Codex судження та рішення; п’ять початкових знімків збережено, повторний запуск публічних тестів успішний. Остаточний статус і повний хеш локального коміту фіксуються окремо командою verify після коміту.",
    )
    body = body.replace(
        "Мету експерименту досягнуто; оформлення подання виконано частково через відсутність власних знімків, успішного повного запуску публічних тестів та остаточної перевірки коміту.",
        "Мету роботи досягнуто повністю в оголошеній межі порівняння: свідчення дозволяють відхилити заміну базової конфігурації. Нульова повнота пошуку вимагає подальшої роботи над якістю; збереження базової конфігурації не означає придатності для виробничого використання.",
    )
    path.write_text(body, encoding="utf-8", newline="\n")
    cli("validate-report")
    print("Report prepared for a LOCAL commit. No push was performed.")


def main():
    os.chdir(ROOT)
    if len(sys.argv) != 2:
        raise SystemExit("Usage: uv run python lab04_checkpoint.py {1|2|3|4|5|6|tests|finalize}")
    action = sys.argv[1]
    if action in {str(i) for i in range(1, 7)}:
        checkpoint(int(action))
    elif action == "tests":
        return tests()
    elif action == "finalize":
        finalize()
    else:
        raise SystemExit("Unknown action: " + action)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("Stopped: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
