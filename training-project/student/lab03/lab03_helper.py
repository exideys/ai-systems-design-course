"""Student-side preparation and report formatting. Run from training-project.

Provider calls, assessments, and evidence records go through the course CLI.
This helper never reads reserve cases or calibration reviewed labels.
"""

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports/lab03"
STUDENT = ROOT / "student/lab03"
STUDENT_ID = "exideys"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def cli(*args):
    subprocess.run(
        [sys.executable, "-m", "learning_project.cli", "lab03", *args],
        cwd=ROOT, check=True,
    )


def comparison(freeze):
    if not freeze or Path(freeze).name != freeze or not freeze.startswith("cmp-"):
        raise ValueError("Use the complete cmp-... identifier printed by freeze.")
    path = REPORT / "comparisons" / freeze
    if not path.is_dir():
        raise ValueError(f"Comparison does not exist: {path}")
    return path


def calibration_draft():
    directory = REPORT / "calibration/calibration-a"
    if (directory / "calibration-result.json").exists():
        raise ValueError("Calibration is already submitted; labels must remain unchanged.")
    path = directory / "student-labels.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if any(item.get("category") or item.get("rationale") for item in data["labels"]):
        raise ValueError("Labels already contain judgments; refusing to overwrite them.")
    judgments = {
        "cal-a-1": ("S", "Завдання вимагає визначити, на який матеріал указує source baseline. "
                    "Джерело: 'A source baseline identifies the material against which a proposal is reviewed.' "
                    "Відповідь зберігає зв’язок матеріалу з розглядом пропозиції, не додає тверджень; правило S."),
        "cal-a-2": ("I", "Для завдання source-baseline-definition джерело пов’язує матеріал із розглядом "
                    "пропозиції: 'against which a proposal is reviewed'. Відповідь 'identifies material' "
                    "підкріплена, але пропускає цей необхідний зв’язок. Очікувана повнота не досягнута; правило I."),
        "cal-a-3": ("U", "У source-baseline-definition джерело описує лише матеріал для розгляду пропозиції. "
                    "Твердження 'automatically approves later changes' не має підкріплення. "
                    "Очікувана поведінка не містить автоматичного затвердження; додана вигадка визначає U для всієї відповіді."),
        "cal-a-4": ("Q", "Завдання retention-duration запитує строк зберігання. Джерело 'Review records are stored "
                    "in the knowledge system' не задає строку. Відповідь прямо вказує на відсутню інформацію, "
                    "відповідає очікуваній невизначеності та правилу Q."),
    }
    for item in data["labels"]:
        item["category"], item["rationale"] = judgments[item["output_id"]]
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Draft written: {path}. Review all four judgments before calibrate-submit.")


def prepare_b():
    schedule = read(REPORT / "development/schedule.json")
    a = [p for p in schedule["positions"] if p["variant"] == "a"]
    if len(a) != 2 or any(p["state"] not in {"returned", "failed"} for p in a):
        raise ValueError("Finish both A development positions first.")
    if not any(p["state"] == "returned" for p in a):
        raise ValueError("Both A positions failed: use honest-partial Step 3.")
    if any(p["state"] != "unstarted" for p in schedule["positions"] if p["variant"] == "b"):
        raise ValueError("B has already started; its instructions must remain unchanged.")
    original = (ROOT / "instructions/lab03/variant-a.txt").read_text(encoding="utf-8")
    addition = (
        "\nSource-evidence policy: Base every substantive claim only on the supplied source. "
        "Preserve all source-supported relationships required to answer the task. "
        "If the source does not establish a requested fact, explicitly state that the source "
        "does not specify it instead of inferring or inventing it.\n"
    )
    write_new(STUDENT / "variant-b.txt", original.rstrip() + "\n" + addition)
    declaration = {
        "changed_property": "source-evidence policy: implicit in A; explicit source-only grounding with bounded uncertainty in B",
        "mechanism": "A: лише 'Answer the task about the supplied source.' B: явно встановлено політику "
                     "підкріплення кожного твердження джерелом зі збереженням потрібних зв’язків і повідомленням "
                     "про відсутній факт. Очікується менше вигаданих тверджень без втрати повноти. "
                     "Змінено лише політику використання джерельних свідчень; завдання і JSON-контракт збережено.",
    }
    declaration["declared_factors"] = [declaration["changed_property"]]
    write_new(STUDENT / "change-declaration.yaml", yaml.safe_dump(declaration, allow_unicode=True, sort_keys=False))
    print("Variant B and its one-factor declaration are ready for review and record-variant-b.")


def protocol():
    data = {
        "engineering_decision": "Чи має B замінити A для оцінюваної операції пропозиції поняття?",
        "hypothesis": "Явна політика джерельного підкріплення зменшить U і збереже повноту S та доречну невизначеність Q.",
        "semantic_acceptance": "Окремо для кожної конфігурації: attempted=returned=structurally_valid=assessable=8; "
                               "rubric_acceptable/assessable >= 7/8, де чисельник є кількістю S+Q; U=0. "
                               "Покриття потрібних зв’язків перевіряється категорією S; пропуски I не приймаються. "
                               "X означає нерозв’язану невизначеність і потребує seek-more-evidence.",
        "blocking_failures": "Будь-яке U у відкладених відповідях блокує відповідну конфігурацію, незалежно від інших підрахунків.",
        "operational_acceptance": "Для кожної з 8 повернених відповідей конфігурації затримка від started_at до finished_at "
                                  "не перевищує 120 секунд. Відсутня або від’ємна затримка є невідомою і не доводить "
                                  "операційної прийнятності. Дані невдалих спроб не трактуються як затримка відповіді. "
                                  "Вартість, токени та квота можуть залишатися unknown: вони не є критеріями цього "
                                  "обмеженого рішення і не дозволяють тверджень про перевагу за вартістю.",
        "tradeoff_rule": "B може замінити A, якщо B семантично й операційно прийнятний, не має U, і A неприйнятний "
                         "або B має строго більше S+Q. За рівних S+Q і прийнятного A зберігається A. "
                         "Невідомі релевантні величини означають seek-more-evidence; невідомі витрати не порівнюються.",
        "decision_rule": {
            "recommend-b": "B задовольняє всі умови; A неприйнятний або B має строго більше S+Q; немає нерозв’язаної релевантної невизначеності.",
            "retain-a": "A задовольняє всі умови, а B не обґрунтовує зміни за tradeoff_rule; немає нерозв’язаної релевантної невизначеності.",
            "reject-both": "В обох конфігурацій є U, що порушує блокувальну умову; X або дефект свідчень спочатку потребує seek-more-evidence.",
            "seek-more-evidence": "Є X, невідоме релевантне вимірювання, дефект джерела/рубрики або жодна інша гілка не підтверджена.",
        },
        "attempt_budget": 16,
        "timing_boundary": "started_at -> finished_at: від початку запланованої спроби до отримання відповіді; однакова межа для A та B",
        "route": {"adapter": "openrouter", "model_id": "openrouter/free"},
    }
    write_new(STUDENT / "protocol-draft.yaml", yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    print("Protocol draft written. Read it before freezing; do not adjust after seeing held-out material.")


def score(freeze):
    directory = comparison(freeze)
    view = read(directory / "scoring/scoring-view.json")
    for item in view["items"]:
        if (directory / "scoring/assessments" / f"{item['blind_id']}.yaml").exists():
            continue
        print(json.dumps(item, ensure_ascii=False, indent=2))
        category = input("Категорія S/I/U/Q/R/X: ").strip().upper()
        if category not in {"S", "I", "U", "Q", "R", "X"}:
            raise ValueError("Unknown category; nothing recorded for this item.")
        pointer = input("Точний фрагмент supplied_source (для X — місце дефекту): ").strip()
        rationale = input("Обґрунтування: джерело + expected_behavior + твердження відповіді + правило: ").strip()
        if not pointer or not rationale:
            raise ValueError("Both source pointer and rationale are required.")
        print(f"{item['blind_id']}: {category}\n{pointer}\n{rationale}")
        if input("Записати це незмінне оцінювання? Введи так: ").strip().lower() != "так":
            print("Not recorded. Restart score to continue from the same item.")
            return
        cli("assess", "--report-dir", "reports/lab03", "--freeze-id", freeze,
            "--blind-id", item["blind_id"], "--category", category,
            "--source-pointer", pointer, "--rationale", rationale, "--by", STUDENT_ID)
    print("All public scoring items have assessments.")


def table(headers, rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(map(cell, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(map(cell, row)) + " |" for row in rows),
    ])


def report(freeze):
    directory = comparison(freeze)
    aggregate = read(directory / "scoring/aggregate.json")
    manifest = read(directory / "freeze-manifest.json")
    recommendation = yaml.safe_load((directory / "recommendation.yaml").read_text(encoding="utf-8"))
    regression_input = yaml.safe_load((STUDENT / "regression.yaml").read_text(encoding="utf-8"))
    regression = yaml.safe_load((REPORT / "regression" / f"{regression_input['regression_id']}.yaml").read_text(encoding="utf-8"))
    calibration = read(REPORT / "calibration/calibration-a/calibration-result.json")
    development = read(REPORT / "development/schedule.json")
    schedule = read(directory / "schedule.json")
    revealed = read(directory / "revealed-family.json")
    assessment_paths = sorted((directory / "scoring/assessments").glob("*.yaml"))
    assessments = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in assessment_paths]
    view = read(directory / "scoring/scoring-view.json")
    if len(assessments) != len(view["items"]):
        raise ValueError("Some blind items are not assessed.")
    if len(schedule["positions"]) != 16 or any(p["state"] not in {"returned", "failed"} for p in schedule["positions"]):
        raise ValueError("Complete report requires sixteen returned/failed positions; use the partial path otherwise.")
    counts = aggregate["nested_counts"]
    sections = []

    def add(title, text):
        sections.append(f"## {title}\n\n{text.strip()}\n")

    def picture(name, caption):
        return f"\n\n![{caption}](screenshots/{name})\n\nРисунок — `{name}`."

    add("Ідентифікація подання", "- Автор: Taranenko Serhii, група KH-1223B.\n"
        "- GitHub: `exideys`; Windows: `lstar`.\n"
        "- URL форку: https://github.com/exideys/ai-systems-design-course\n"
        "- Назва особистої гілки: `lab03/exideys`.\n"
        "- Статус завершення: `complete`.\n\n"
        "Повний хеш остаточного коміту й результат його перевірки належать до окремого `verification-report.json` після коміту.")
    add("Мета роботи", "Отримати відтворювані свідчення для обмеженого рішення, чи має кандидатна конфігурація B "
        "замінити базову A в оцінюваній операції пропозиції поняття з використанням моделі.")
    add("Початковий стан і межа лабораторної роботи 02", "Гілку `lab03/exideys` створено від завершеної `lab02/exideys`. "
        "Допуск Lab02 перевірено на одноразовій копії звіту: `Laboratory 02 verification passed.` "
        "Під час підготовки виявлено перетворення LF на CRLF у робочій копії `semantic-review.yaml`; "
        "відновлення точних байтів із Git повернуло відповідність хешу рішення. "
        "Стан публікації `upstream/main` злито локально. Lab03 не виконує записів у зовнішнє сховище та не змінює "
        "прийнятого поняття `Structured Output`, рішення чи аудиторського ланцюга.")
    cal_rows = [(i["output_id"], i["student_category"], i["reviewed_category"], i["agrees"], i["reviewed_rationale"])
                for i in calibration["comparison"]]
    add("Калібрування оцінювача", f"Активний пакет — `calibration-a`; збіг {calibration['agreement']}/{calibration['total']}. "
        "Чернетку обґрунтувань підготовлено за допомогою Codex; перед поданням студент перевіряє кожне судження за завданням, "
        "джерелом і §2.3. Початкові мітки збережено після подання. Авторські приклади готують оцінювача "
        "та не є свідченнями поведінки живої моделі.\n\n" + table(
            ["Фікстура", "Мітка студента", "Розглянута мітка", "Збіг", "Правило розглянутої мітки"], cal_rows)
        + "\n\nДля кожної розбіжності наведене правило визначає межу, яку потрібно уточнити; початкова оцінка не переписується."
        + picture("01-calibration.png", "Калібрування рубрики"))
    add("Розробницькі випадки", "Курс надав два випадки: `dev-source-baseline-definition` перевіряє збереження зв’язку "
        "базового стану з матеріалом для розгляду; `dev-approval-authority-absent` перевіряє доречне повідомлення про "
        "відсутність названого суб’єкта затвердження. Джерела та очікувана поведінка походять із матеріалів курсу.")
    dev_details = []
    for position in development["positions"]:
        attempt = REPORT / "development/attempts" / position["position_id"]
        text = (attempt / "raw-response.txt").read_text(encoding="utf-8") if position["state"] == "returned" else (attempt / "error.json").read_text(encoding="utf-8")
        structural = read(attempt / "structural-result.json") if (attempt / "structural-result.json").exists() else {}
        dev_details.append(f"### {position['position_id']}\n\nСтан: `{position['state']}`; structural valid: `{structural.get('valid', 'не застосовується')}`.\n\n```text\n{text}\n```\n")
    add("Розробницькі запуски й діагноз варіанта A", "Порядок — дві спроби A, потім дві B. Сирі результати наведено нижче; "
        "вони є свідченнями розроблення. Гіпотеза стосується ризику домислювання за неявної політики джерела, "
        "а конкретний дефект A можна встановити лише за наведеним текстом та відповідним джерелом. "
        "Успішна структура не доводить семантичної правильності.\n\n" + "\n".join(dev_details)
        + picture("02-development.png", "Чотири розробницькі спроби"))
    declaration = yaml.safe_load((STUDENT / "change-declaration.yaml").read_text(encoding="utf-8"))
    add("Єдина зміна у варіанті B", f"Змінена властивість: {declaration['changed_property']}.\n\n{declaration['mechanism']} "
        "Варіант B містить початковий текст A та явну source-evidence policy. Контракт `case_id` і `proposed_text`, "
        "завдання, джерела, маршрут, рубрика й кількість спроб однакові. Політика повноти та невизначеності "
        "є складовими одного оголошеного режиму використання свідчень; їхні окремі ефекти це порівняння не вимірює.")
    add("Заморожений протокол", f"Ідентифікатор: `{freeze}`. Заморожено: `{manifest['frozen_at']}`. "
        "Точні інструкції, декларація, протокол, маршрут, розробницький розклад і контракти зв’язані хешами. "
        "Зміна під тим самим ідентифікатором не допускається. Дві спроби на випадок і конфігурацію, нуль повторних спроб. "
        "CLI призначає збалансований порядок та 48-годинне вікно відновлення.\n\n```yaml\n"
        + yaml.safe_dump(manifest["protocol"], allow_unicode=True, sort_keys=False) + "```"
        + picture("03-freeze.png", "Фіксація протоколу до розкриття родини"))
    add("Вибір відкладеної родини та виконання", f"Призначена родина: `{revealed['family']['family_id']}`. "
        "Її розкриття фіксує `exposure-ledger.json`; призначення відбулося через `select-family` після freeze. "
        "Збережено всі 16 позицій; кінцеві відмови не замінювалися.\n\n"
        + table(["Позиція", "Варіант", "Спроба", "Стан"], [(p["position_id"], p["variant"], p["attempt"], p["state"]) for p in schedule["positions"]])
        + "\n\nВідомості про переривання та відновлення, якщо вони були, зберігаються в метаданих спроб і route-stop.json."
        + picture("04-held-out-execution.png", "Кінцеві стани відкладених спроб"))
    add("Сліпе семантичне оцінювання", "Оцінювання виконувалося за `scoring-view.json`, що приховує варіант і порядок. "
        "Кожній структурно чинній відповіді призначено одну категорію. S означає повну підкріплену відповідь; I — пропуск; "
        "U — непідкріплене твердження; Q — обґрунтовану невизначеність; R — непотрібну відмову; X — неможливість "
        "семантичного оцінювання. Невдалі та структурно некоректні спроби не отримують міток. X виключено з assessable.\n\n"
        + table(["Анонімна мітка", "Категорія", "Фрагмент джерела", "Обґрунтування"],
                [(a["blind_id"], a["category"], a["source_pointer"], a["rationale"]) for a in assessments]))
    fields = ["attempted", "returned", "structurally_valid", "assessable", "rubric_acceptable"]
    operational = {key: aggregate[key] for key in ["failure_counts", "unstarted_counts", "critical_unsupported_counts", "slices", "observed_models", "unknown_values"]}
    latencies = []
    for variant in ("a", "b"):
        values = [i["seconds"] for i in aggregate["observed_latency"][variant] if i["seconds"] is not None]
        latencies.append((variant.upper(), len(values), statistics.median(values) if values else "unknown", max(values) if values else "unknown"))
    add("Агрегати, зрізи й операційні свідчення", table(["Варіант", *fields], [(v.upper(), *(counts[v][f] for f in fields)) for v in ("a", "b")])
        + "\n\nПрийнятні категорії — S та Q; кожен наступний підрахунок є підмножиною попереднього. "
        "Рівень прийнятності — rubric_acceptable/assessable; за нульового знаменника частка невизначена. "
        "Операційний поріг застосовується лише до повернених відповідей за їхніми метаданими; час невдалої спроби "
        "не є часом отримання відповіді.\n\n" + table(["Варіант", "Виміряні спроби, включно з відмовами", "Медіана, с", "Максимум, с"], latencies)
        + "\n\n```json\n" + json.dumps(operational, ensure_ascii=False, indent=2) + "\n```\n\n"
        "Поля repeated_attempt_differences з агрегату перевіряються за категоріями: різні blind-id самі собою "
        "не доводять відмінності генерації. Різні категорії або тексти двох спроб показують мінливість генерації; "
        "один оцінювач не вимірює мінливості оцінювачів.")
    add("Обмежене рішення щодо конфігурації", "```yaml\n" + yaml.safe_dump(recommendation, allow_unicode=True, sort_keys=False)
        + "```\n\nРішення застосовує зафіксовані умови й не дозволяє розгортання або запис до прийнятого стану знань. "
        "Непідкріплене U не компенсується більшою кількістю прийнятних відповідей."
        + picture("05-scoring-recommendation.png", "Підрахунки й обмежене рішення"))
    add("Регресійний запис", "```yaml\n" + yaml.safe_dump(regression, allow_unicode=True, sort_keys=False)
        + "```\n\nДля observed-failure діагноз має простежувати джерело, очікувану поведінку, запит, відповідь, "
        "структурну перевірку та правило рубрики. Для authored-fixture авторство моделі не стверджується. "
        "Після огляду відомий випадок є матеріалом регресії та розроблення, тому не є свіжим відкладеним свідченням."
        + picture("06-regression.png", "Розглянутий регресійний випадок"))
    add("Обмеження й статус завершення", "Статус пакета — complete за наявності всіх необхідних записів; це не означає "
        "переваги B. Чотири спроєктовані випадки та дві спроби на пару не встановлюють загальної частоти помилок. "
        "Маршрут openrouter/free може обирати різні фактичні моделі; ідентифікатор маршруту фіксований, "
        "спостережені моделі наведено окремо. Вартість, токени та використання квоти залишаються unknown. "
        "Не доведено статистичної значущості, переваги за витратами чи придатності до розгортання. "
        "Перед фінальним комітом належить перевірити індивідуальні пояснення та результат публічних тестів.")
    add("Остаточна перевірка", "Базовий коміт курсу визначає походження контрактів; фінальний студентський коміт "
        "ідентифікує пакет свідчень. Після остаточного коміту `lab03 verify --final-commit` записує точний хеш і "
        "`passed-complete` або `passed-partial` до окремого `verification-report.json`. "
        "Студентські свідчення після цього коміту не змінюються; післякомітними є лише дозволені похідні файли."
        + picture("07-final-verification.png", "Перевірка точного фінального HEAD"))
    add("Висновки", f"Збережено калібрування, чотири розробницькі спроби, один фактор і заморожений протокол, "
        f"16 відкладених спроб, абсолютні оцінювання та регресійний запис. "
        f"Отримано рішення `{recommendation['outcome']}`. Для A прийнятно {counts['a']['rubric_acceptable']} "
        f"із {counts['a']['assessable']} придатних до оцінювання відповідей; для B — {counts['b']['rubric_acceptable']} "
        f"із {counts['b']['assessable']}. Мету отримання свідчень для обмеженого рішення досягнуто повністю "
        "за умови підтвердження остаточного пакета післякомітною перевіркою. "
        "Остаточна готовність до подання визначається результатом цієї перевірки та публічними тестами.")
    text = "# Лабораторна робота 03\n\n" + "\n".join(sections)
    template = (ROOT / "fixtures/lab03/REPORT.md").read_text(encoding="utf-8")
    expected = [line for line in template.splitlines() if line.startswith("## ")]
    actual = [line for line in text.splitlines() if line.startswith("## ")]
    if actual != expected:
        raise ValueError("Course report headings changed; inspect the current template before writing.")
    write_new(REPORT / "REPORT.md", text)
    print("REPORT.md generated from recorded evidence. Review it before committing.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["calibration-draft", "prepare-b", "protocol", "score", "report", "partial-report"])
    parser.add_argument("--freeze")
    parser.add_argument("--step", choices=["Step 2", "Step 3", "Step 4", "Step 5", "Step 6"])
    parser.add_argument("--limitation")
    args = parser.parse_args()
    if args.action == "partial-report":
        if not args.step or not args.limitation:
            raise ValueError("partial-report requires --step and --limitation.")
        template = (ROOT / "fixtures/lab03/REPORT.md").read_text(encoding="utf-8")
        headings = [line[3:] for line in template.splitlines() if line.startswith("## ")]
        contents = {
            "Ідентифікація подання": "Автор: Taranenko Serhii, KH-1223B. Форк: https://github.com/exideys/ai-systems-design-course. "
                                    "Гілка: `lab03/exideys`. Статус: `honest-partial`. Хеш фінального коміту зберігається окремо у verification-report.json.",
            "Мета роботи": "Отримати свідчення для обмеженого рішення, чи має B замінити A в операції пропозиції поняття.",
            "Початковий стан і межа лабораторної роботи 02": "Допуск Lab02 пройдено на одноразовій копії звіту після відновлення "
                "точних LF-байтів semantic-review.yaml із Git. Lab03 не змінювала зовнішнього сховища та прийнятого Structured Output.",
            "Обмежене рішення щодо конфігурації": "Обмежене рішення не записувалося: поточний неповний пакет не обґрунтовує вибору конфігурації.",
            "Регресійний запис": "Регресійний етап не досягнуто; вигаданий регресійний запис не створювався.",
            "Обмеження й статус завершення": f"Зупинка: {args.step}. Обмеження: {args.limitation}. "
                "Збережено фактично створені student/lab03/ та reports/lab03/. Наявні записи не замінювалися.",
            "Остаточна перевірка": "Після фінального коміту перевіряється точний HEAD; результат passed-partial і хеш "
                "мають бути підтверджені окремим verification-report.json. Студентські свідчення після коміту не змінюються.",
            "Висновки": f"Мету досягнуто частково. Роботу зупинено на {args.step}: {args.limitation}. "
                "Не отримано повного відкладеного порівняння та обмеженого рішення. "
                "Збережені матеріали підтверджують лише фактично досягнуті етапи; passed-partial не означає завершення повної лабораторної.",
        }
        mappings = {
            "Калібрування оцінювача": "01-calibration.png",
            "Розробницькі запуски й діагноз варіанта A": "02-development.png",
            "Заморожений протокол": "03-freeze.png",
            "Вибір відкладеної родини та виконання": "04-held-out-execution.png",
            "Остаточна перевірка": "07-final-verification.png",
        }
        evidence = [str(p.relative_to(REPORT)).replace("\\", "/") for p in sorted(REPORT.rglob("*")) if p.is_file()]
        inventory = "Фактично збережені артефакти пакета:\n\n" + "\n".join(f"- `{p}`" for p in evidence)
        result = ["# Лабораторна робота 03\n"]
        for heading in headings:
            body = contents.get(heading, f"Стан цього етапу обмежений зупинкою на {args.step}. "
                                "Зміст доступних артефактів наведено в інвентарі; результатів наступних етапів не стверджується.")
            if heading == "Калібрування оцінювача":
                body += " Авторські фікстури є підготовкою оцінювача, а не живими відповідями моделі.\n\n" + inventory
            image_name = mappings.get(heading)
            if image_name and (image_name.startswith("07-") or (REPORT / "screenshots" / image_name).exists()):
                body += f"\n\n![{heading}](screenshots/{image_name})\n\nРисунок — `{image_name}`."
            result.append(f"## {heading}\n\n{body}\n")
        write_new(REPORT / "REPORT.md", "\n".join(result))
        print("Partial report draft written. Describe the reached stages and exact recovery facts before committing.")
    elif args.action in {"score", "report"}:
        {"score": score, "report": report}[args.action](args.freeze)
    else:
        {"calibration-draft": calibration_draft, "prepare-b": prepare_b, "protocol": protocol}[args.action]()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        sys.exit(f"Stopped without replacing evidence: {exc}")
