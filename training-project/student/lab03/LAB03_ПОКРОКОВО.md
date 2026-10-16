# Лабораторна 03 — готовий порядок виконання для exideys

Цей файл — інструкція виконання. Звіт для здачі буде створено окремо в `training-project/reports/lab03/REPORT.md`, а після перевірки — у `reports/lab03/submission/REPORT.md`.

Підготовлено для Taranenko Serhii, KH-1223B, Windows `lstar`, GitHub `exideys`. Команди виконуються в PowerShell, послідовно, в одному терміналі. Команд публікації до GitHub тут немає; пуш виконується самостійно.

## Що вже зроблено

- Створено локальну гілку `lab03/exideys` від `lab02/exideys`.
- Отримано та злито `upstream/main`; зміни курсу збережено локальним merge-комітом.
- Пройдено допуск Lab02: `Laboratory 02 verification passed.` Перевірявся тимчасовий каталог, оригінальний verification-report Lab02 не переписувався.
- Відновлено точні LF-байти `reports/lab02/semantic-review.yaml` із Git: Windows раніше перетворила їх на CRLF, порушивши відповідність контрольному хешу. Зміст розгляду та зовнішнє сховище не змінювалися.
- Перевірено тести Lab03: **37 тестів, OK**.
- Підготовлено `student/lab03/lab03_helper.py`: чернетка калібрування, створення B після A, протокол, введення сліпих оцінок і формування звіту з фактичних свідчень.

Живі виклики ще не виконувалися: у середовищі немає ключа OpenRouter. Скриншоти, відповіді моделі, оцінки held-out та фінальний результат не створювалися штучно. Відкладені матеріали для підготовки інструкції не відкривалися.

## 0. Відкрити термінал і задати змінні

```powershell
Set-Location 'F:\sobol\ai-systems-design-course'
git switch lab03/exideys
Set-Location .\training-project
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8
$student = 'exideys'
$vault = 'C:\Users\lstar\OneDrive\ai-systems-learning-vault'
$utf8 = New-Object Text.UTF8Encoding($false)
New-Item -ItemType Directory -Force .\reports\lab03\screenshots | Out-Null
```

Допоміжний файл має залишатися в `student/lab03/` поруч із цією інструкцією. Не копіюй початковий шаблон у `reports/lab03/REPORT.md`: наприкінці скрипт створить заповнений звіт і відмовиться перезаписувати наявний.

Допуск уже пройдено. Продовжуй із розділу 1. Не запускай `lab02 verify` у поточній гілці Lab03 після злиття нового `upstream/main`: перевірка порівнює файли курсу з версією, зареєстрованою під час Lab02, і відхиляє пізніші оновлення курсу.

Якщо потрібна повторна перевірка допуску, використовуй окрему тимчасову робочу копію завершеної гілки Lab02. Свідчення копіюються з наявного `reports/lab02` зі збереженням точних байтів; повторний checkout усіх свідчень може змінити переноси рядків та їхні хеші.

```powershell
$admission = Join-Path ([IO.Path]::GetTempPath()) ('lab02-admission-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath .\reports\lab02 -Destination $admission -Recurse
$admissionWorktree = Join-Path ([IO.Path]::GetTempPath()) ('lab02-admission-worktree-' + [guid]::NewGuid().ToString('N'))
git -c core.autocrlf=false worktree add --detach "$admissionWorktree" lab02/exideys
if ($LASTEXITCODE -ne 0) { throw 'Не вдалося створити тимчасову копію Lab02.' }
Push-Location (Join-Path $admissionWorktree 'training-project')
try {
    uv run --frozen learning-project lab02 verify --vault "$vault" --report-dir "$admission"
    $admissionExit = $LASTEXITCODE
} finally {
    Pop-Location
}
if ($admissionExit -ne 0) { throw "Допуск Lab02 не пройдено. Деталі: $admission\verification-report.json" }
```

Потрібний результат: `Laboratory 02 verification passed.` Основна гілка залишається `lab03/exideys`; тимчасова копія створюється без переключення основного каталогу. Її можна залишити до завершення роботи. Якщо після нового checkout знову з’явиться `Decision review changed.`, точні байти відновлюються так; запускай лише за відсутності власних нових змін до цього файлу:

```powershell
@'
from pathlib import Path
import subprocess
path = 'training-project/reports/lab02/semantic-review.yaml'
root = Path.cwd().parent
blob = subprocess.check_output(['git', '-C', str(root), 'show', f'HEAD:{path}'])
(root / path).write_bytes(blob)
'@ | uv run python -
```

Після цього перевір допуск ще раз на **новій** тимчасовій копії.

## 1. Калібрування: готові чотири судження

Спочатку ініціалізуй пакет:

```powershell
uv run learning-project lab03 calibrate --report-dir reports/lab03 --packet calibration-a --by "$student"
if ($LASTEXITCODE -ne 0) { throw 'Перевір причину; не перезапускай уже створений пакет.' }
```

Переглянь лише дозволені поля пакета:

```powershell
@'
import json
from pathlib import Path
p = json.loads(Path('cases/lab03/calibration/calibration-a/packet.json').read_text(encoding='utf-8'))
print(json.dumps({k: p[k] for k in ('tasks', 'authored_outputs')}, ensure_ascii=False, indent=2))
'@ | uv run python -
```

Підготовлені за джерелом та §2.3 судження:

| Фікстура | Категорія | Причина |
| --- | --- | --- |
| `cal-a-1` | `S` | Збережено повний зв’язок матеріалу з розглядом пропозиції. |
| `cal-a-2` | `I` | Матеріал названо, але його роль у розгляді пропозиції пропущено. |
| `cal-a-3` | `U` | Автоматичне затвердження подальших змін вигадане. |
| `cal-a-4` | `Q` | Джерело не встановлює строку зберігання; невизначеність доречна. |

Запиши чернетку з повними поясненнями та перевір її:

```powershell
uv run python .\student\lab03\lab03_helper.py calibration-draft
Get-Content -Encoding UTF8 .\reports\lab03\calibration\calibration-a\student-labels.yaml
```

Це підготовлені за допомогою Codex пояснення, а остаточні судження перевіряє студент. За потреби виправ їх **до подання**. До подання не відкривай `reviewed_labels` та інші ключі початкового пакета. Після перевірки всіх чотирьох суджень введи:

```powershell
uv run learning-project lab03 calibrate-submit --report-dir reports/lab03 --packet calibration-a --by "$student"
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

**СКРИНШОТ №1 зараз.** Має бути видно результат `Calibration complete: .../4`, акаунт і дату. `Win+Shift+S` → виділи термінал → збережи PNG:

`F:\sobol\ai-systems-design-course\training-project\reports\lab03\screenshots\01-calibration.png`

Після подання мітки не переписувати. Якщо є розбіжності, у фінальному звіті поясни кожну за правилом рубрики. Якщо розглянуті мітки `calibration-a` випадково побачено раніше, збережи цей пакет і один раз виконай оригінальний крок 2 для `calibration-b`; автоматична чернетка й генератор повного звіту тут розраховані на `calibration-a`, тому для B відповідні частини заповнюються вручну. Якщо обидва пакети розкрито завчасно — частковий шлях `Step 2`.

## 2. Приховано ввести ключ OpenRouter

Уведення відбувається локально, без відображення символів:

```powershell
$secure = Read-Host 'OpenRouter API key' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    Remove-Variable secure, bstr
}
```

Ключ не записується в Markdown. Не виводь значення змінної середовища. За відкриття нового термінала цей блок потрібно виконати знову.

## 3. Запуски A та огляд джерел

Оголоси функцію, яка пропускає завершені спроби та перевіряє кожну повернену відповідь:

```powershell
function Invoke-DevelopmentPosition([string]$position) {
    $schedulePath = '.\reports\lab03\development\schedule.json'
    $attempt = ".\reports\lab03\development\attempts\$position"
    $state = 'unstarted'
    if (Test-Path $schedulePath) {
        $schedule = Get-Content -Raw -Encoding UTF8 $schedulePath | ConvertFrom-Json
        $state = ($schedule.positions | Where-Object position_id -eq $position).state
    }
    if ($state -eq 'unstarted') {
        if (Test-Path "$attempt\request.json") { throw 'Є перерваний запит. Див. розділ про переривання.' }
        uv run learning-project lab03 dev-run --report-dir reports/lab03 --position-id "$position" --adapter openrouter --model-id openrouter/free --by "$student"
        if ($LASTEXITCODE -ne 0) { throw 'Помилка CLI; збережи стан і перевір причину.' }
    }
    $schedule = Get-Content -Raw -Encoding UTF8 $schedulePath | ConvertFrom-Json
    $state = ($schedule.positions | Where-Object position_id -eq $position).state
    if ($state -eq 'returned' -and -not (Test-Path "$attempt\structural-result.json")) {
        uv run learning-project lab03 dev-structural-check --report-dir reports/lab03 --position-id "$position"
    }
    Write-Host "$position : $state"
}

Invoke-DevelopmentPosition 'pos-dev-source-baseline-definition-a-1'
Invoke-DevelopmentPosition 'pos-dev-approval-authority-absent-a-1'
Get-Content -Encoding UTF8 .\cases\lab03\development\dev-common-inputs.json
Get-ChildItem .\reports\lab03\development\attempts\*-a-1\raw-response.txt | ForEach-Object {
    Write-Host $_.Directory.Name
    Get-Content -Encoding UTF8 $_.FullName
}
```

Перевір за джерелами: у першому випадку потрібен зв’язок матеріалу з розглядом пропозиції; у другому джерело не називає суб’єкта затвердження, тому відповідь має повідомити про відсутність цієї інформації. Коректний JSON ще не доводить правильності змісту. Запам’ятай конкретні виявлені пропуски/вигадки або відсутність таких дефектів для розділу діагнозу A у звіті.

Якщо **обидві** A мають `failed`, B не створюй: частковий шлях `Step 3`. Якщо хоча б одна A повернула відповідь, продовжуй; дефектні відповіді також зберігаються.

## 4. Створити B, оголосити фактор і виконати ще дві спроби

Після огляду A створюється готова кандидатна інструкція:

```powershell
uv run python .\student\lab03\lab03_helper.py prepare-b
Get-Content -Encoding UTF8 .\student\lab03\variant-b.txt
Get-Content -Encoding UTF8 .\student\lab03\change-declaration.yaml
```

Один фактор — політика використання джерельних свідчень: у A вона неявна, у B явно вимагається підкріплювати твердження джерелом і повідомляти про відсутній факт. Збереження повноти й доречна невизначеність є складовими цього режиму. Контракт JSON із `case_id` та `proposed_text` не змінюється. Окремі ефекти складових цієї політики експеримент не розділяє.

```powershell
uv run learning-project lab03 record-variant-b --report-dir reports/lab03 --text student/lab03/variant-b.txt --change student/lab03/change-declaration.yaml
if ($LASTEXITCODE -ne 0) { throw 'Варіант B не записано.' }
Invoke-DevelopmentPosition 'pos-dev-source-baseline-definition-b-1'
Invoke-DevelopmentPosition 'pos-dev-approval-authority-absent-b-1'
$dev = Get-Content -Raw -Encoding UTF8 .\reports\lab03\development\schedule.json | ConvertFrom-Json
$dev.order | ForEach-Object {
    $position = $_
    $dev.positions | Where-Object position_id -eq $position
} | Format-Table position_id, state
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

**СКРИНШОТ №2 зараз:** чотири спроби A, A, B, B та кінцеві стани, акаунт і дата. Зберегти як `reports/lab03/screenshots/02-development.png`.

Після перегляду результатів B не редагуй `variant-b.txt` і декларацію. Якщо обидві B завершилися відмовою **і обидва `error.json` визначають `route-wide`**, збережи чотири спроби та переходь до часткового шляху `Step 4`. Інші завершені відмови не видаляй.

## 5. Протокол перед розкриттям відкладених випадків

```powershell
uv run python .\student\lab03\lab03_helper.py protocol
Get-Content -Encoding UTF8 .\student\lab03\protocol-draft.yaml
```

Готові умови протоколу: для кожної конфігурації 8 спроб, усі повернені, структурно чинні та придатні до оцінювання; щонайменше 7/8 прийнятних (`S+Q`); жодного `U`; кожна повернена відповідь не довше 120 с. `X`, невідомий релевантний час або дефект свідчень ведуть до `seek-more-evidence`. Вартість і токени залишаються допоміжними невідомими, їхня перевага не стверджується.

Ці пороги обрано **до** перегляду held-out. Прочитай повний YAML; після freeze їх не змінюють під побачені результати.

```powershell
$freezeOutput = uv run learning-project lab03 freeze --report-dir reports/lab03 --protocol student/lab03/protocol-draft.yaml --by "$student"
$freezeExit = $LASTEXITCODE
$freezeOutput | Out-Host
if ($freezeExit -ne 0) { throw 'Freeze не виконано: якщо немає невикористаної родини — частковий шлях Step 5.' }
$freeze = [regex]::Match(($freezeOutput -join "`n"), 'cmp-[a-f0-9]+').Value
if (-not $freeze) { throw 'Не знайдено повний ідентифікатор freeze.' }
$cmp = ".\reports\lab03\comparisons\$freeze"
Write-Host "Freeze: $freeze"
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

**СКРИНШОТ №3 зараз:** успішний `Froze comparison cmp-...`, ідентифікатор, акаунт і дата. Зберегти як `reports/lab03/screenshots/03-freeze.png`.

## 6. Призначити родину й виконати 16 позицій

Тепер, після freeze:

```powershell
uv run learning-project lab03 select-family --report-dir reports/lab03 --freeze-id "$freeze" --by "$student"
if ($LASTEXITCODE -ne 0) { throw 'Зупинись: перевір наявний стан, не призначай родину повторно.' }
uv run learning-project lab03 list-positions --report-dir reports/lab03 --freeze-id "$freeze"
```

Визнач функцію виконання **наступної** спроби:

```powershell
function Invoke-NextHeldOut {
    $schedule = Get-Content -Raw -Encoding UTF8 "$cmp\schedule.json" | ConvertFrom-Json
    $next = $null
    foreach ($position in $schedule.order) {
        $entry = $schedule.positions | Where-Object position_id -eq $position
        if ($entry.state -eq 'unstarted') { $next = $position; break }
    }
    if (-not $next) { Write-Host 'Нерозпочатих позицій немає.'; return }
    if (Test-Path "$cmp\route-stop.json") {
        $stop = Get-Content -Raw -Encoding UTF8 "$cmp\route-stop.json" | ConvertFrom-Json
        if (-not $stop.resume_succeeded) { throw 'Маршрут зупинено. Див. розділ відновлення.' }
    }
    if (Test-Path "$cmp\attempts\$next\request.json") { throw 'Запит уже є: потрібен record-interrupted, а не повтор.' }
    uv run learning-project lab03 run --report-dir reports/lab03 --freeze-id "$freeze" --position-id "$next" --adapter openrouter --model-id openrouter/free --by "$student"
    if ($LASTEXITCODE -ne 0) { throw 'Помилка CLI. Перевір lab03 status.' }
    $schedule = Get-Content -Raw -Encoding UTF8 "$cmp\schedule.json" | ConvertFrom-Json
    $entry = $schedule.positions | Where-Object position_id -eq $next
    if ($entry.state -eq 'returned') {
        uv run learning-project lab03 structural-check --report-dir reports/lab03 --freeze-id "$freeze" --position-id "$next"
    }
    if (Test-Path "$cmp\route-stop.json") {
        $stop = Get-Content -Raw -Encoding UTF8 "$cmp\route-stop.json" | ConvertFrom-Json
        if (-not $stop.resume_succeeded) { throw 'Зафіксовано зупинку маршруту. Використай гілку відновлення.' }
    }
}

for ($i = 0; $i -lt 16; $i++) { Invoke-NextHeldOut }
```

Виклики виконуються послідовно в порядку CLI. `invalid` означає збережену структурно некоректну відповідь, а не дозвіл на повтор. `failed` без відповіді також зберігається. Функція зупиняє цикл за проблеми маршруту.

Після завершення:

```powershell
uv run learning-project lab03 list-positions --report-dir reports/lab03 --freeze-id "$freeze"
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

**СКРИНШОТ №4 зараз:** усі 16 позицій із `returned`/`failed`, акаунт і дата. Зберегти як `reports/lab03/screenshots/04-held-out-execution.png`.

### Якщо термінал закрито, процес перервано або маршрут недоступний

Повернися до каталогу `training-project`, виконай початкові присвоєння `$student`, `$utf8`, приховане введення ключа та:

```powershell
uv run learning-project lab03 status --report-dir reports/lab03
$comparisons = @(Get-ChildItem .\reports\lab03\comparisons -Directory -Filter 'cmp-*')
if ($comparisons.Count -ne 1) { throw 'Є кілька порівнянь: вибери активний повний cmp-id зі status вручну.' }
$freeze = $comparisons[0].Name
$cmp = ".\reports\lab03\comparisons\$freeze"
```

Не виконуй `freeze`, `select-family`, `build-scoring` та незмінні записи повторно. Спочатку перевір, що вже існує.

Якщо є `request.json`, але немає кінцевого результату, запиши переривання. У наступних командах `$position` потрібно присвоїти **саме ідентифікатор перерваної позиції** зі свого `status`/розкладу:

```powershell
$position = Read-Host 'Повний position-id перерваної спроби'
# Для розробницької спроби:
uv run learning-project lab03 dev-record-interrupted --report-dir reports/lab03 --position-id "$position" --reason 'process ended before terminal evidence was recorded' --by "$student"
# Для held-out виконай натомість цю команду, а не обидві:
# uv run learning-project lab03 record-interrupted --report-dir reports/lab03 --freeze-id "$freeze" --position-id "$position" --reason 'process ended before terminal evidence was recorded' --by "$student"
```

Після `failure_class: route-wide` дозволено одну пробу на **наступній нерозпочатій** позиції в межах 48 годин від freeze:

```powershell
$schedule = Get-Content -Raw -Encoding UTF8 "$cmp\schedule.json" | ConvertFrom-Json
$next = $null
foreach ($position in $schedule.order) {
    if (($schedule.positions | Where-Object position_id -eq $position).state -eq 'unstarted') { $next = $position; break }
}
if (-not $next) { throw 'Немає наступної нерозпочатої позиції; перевір кінцеві стани.' }
uv run learning-project lab03 run --report-dir reports/lab03 --freeze-id "$freeze" --position-id "$next" --adapter openrouter --model-id openrouter/free --resume-probe --by "$student"
```

Якщо проба повернула відповідь, виконай structural-check для `$next`, повторно оголоси функцію `Invoke-NextHeldOut` та продовжуй цикл для решти позицій. Якщо проба підтвердила недоступність маршруту:

```powershell
uv run learning-project lab03 close-unstarted --report-dir reports/lab03 --freeze-id "$freeze" --reason 'route unavailable after the permitted probe' --by "$student"
```

Переходь до часткового шляху `Step 6`; оцінювання, рекомендацію та регресію не створюй. Якщо проблема сталася вже на останній позиції, усі 16 спроб є кінцевими, тому перевір можливість повного шляху. За пропущеного вікна відновлення збережи точний стан і помилку CLI; не підмінюй час або історію.

## 7. Сліпе оцінювання реальних відповідей

```powershell
uv run learning-project lab03 build-scoring --report-dir reports/lab03 --freeze-id "$freeze"
if ($LASTEXITCODE -ne 0) { throw 'Перевір, чи всі позиції завершені та чи scoring ще не створено.' }
uv run python .\student\lab03\lab03_helper.py score --freeze "$freeze"
```

Скрипт показує тільки публічні поля `blind-id`, завдання, джерело, очікувану поведінку та відповідь. Для кожного елемента введи:

1. Одну категорію `S`, `I`, `U`, `Q`, `R` або `X`.
2. Дослівний фрагмент `supplied_source`, на який спирається оцінка; для `X` — точне місце дефекту свідчень.
3. Обґрунтування: яке твердження відповіді підтримане/пропущене/вигадане, як це узгоджується з `expected_behavior` і чому застосовано цю категорію.
4. `так`, лише коли перевірено незмінний запис.

| Категорія | Коли вводити |
| --- | --- |
| `S` | Усі твердження підкріплені й потрібний зміст збережено. |
| `I` | Вигадок немає, але потрібний зміст пропущено. |
| `U` | Є хоча б одне непідкріплене твердження, навіть поряд із правильним. |
| `Q` | Джерело не дає запитаного факту; відповідь конкретно повідомляє про цю прогалину. |
| `R` | Відповідь відмовляється або без потреби ухиляється, хоча джерела достатньо. |
| `X` | Структурно чинний текст або необхідні свідчення не дозволяють семантичного оцінювання. |

Готових міток для ще не отриманих відповідей немає. Очікувана поведінка не передається генератору. Під час оцінювання користуйся лише `scoring-view.json`: не відкривай `scoring/_join-map.json`, `_internal` або сирі спроби для визначення варіанта. Повторний запуск `score` пропускає вже збережені судження.

## 8. Підрахунки та обмежене рішення

```powershell
uv run learning-project lab03 aggregate --report-dir reports/lab03 --freeze-id "$freeze"
if ($LASTEXITCODE -ne 0) { throw 'Агрегування не завершено.' }
$agg = Get-Content -Raw -Encoding UTF8 "$cmp\scoring\aggregate.json" | ConvertFrom-Json
$agg.nested_counts | ConvertTo-Json -Depth 8
$agg.critical_unsupported_counts | ConvertTo-Json
$agg.observed_latency | ConvertTo-Json -Depth 8
$agg.observed_models | ConvertTo-Json -Depth 8
```

П’ять вкладених підрахунків: `attempted ≥ returned ≥ structurally_valid ≥ assessable ≥ rubric_acceptable`. Для прийнятності за обраним протоколом потрібні перші чотири по 8, останній не менше 7, `U=0`, кожна повернена відповідь ≤120 с, відомий невід’ємний час. Невдалу спробу не включай до latency повернених відповідей.

Вибери результат за **замороженим**, а не новим правилом:

- `recommend-b`: B прийнятний і A неприйнятний або B має строго більше `S+Q`; релевантних невідомих немає.
- `retain-a`: A прийнятний, а B не обґрунтовує зміни; релевантних невідомих немає.
- `reject-both`: в обох є блокувальне `U`; немає дефекту свідчень, який спочатку потребує уточнення.
- `seek-more-evidence`: є `X`, невідомий релевантний час, дефект свідчень або інші правила не дають рішення.

За невідомої вартості не стверджуй економічної переваги. Порівнюй категорії/тексти повторних спроб безпосередньо: різні `blind-id` ще не означають різного змісту.

```powershell
uv run learning-project lab03 select-comparison --report-dir reports/lab03 --comparison-id "$freeze" --by "$student"
$outcome = Read-Host 'recommend-b / retain-a / reject-both / seek-more-evidence'
$reason = Read-Host 'Обґрунтування українською: фактичні підрахунки A і B, U, часовий поріг, відповідність замороженому правилу та невідомі'
uv run learning-project lab03 recommend --report-dir reports/lab03 --freeze-id "$freeze" --outcome "$outcome" --rationale "$reason" --limitations 'small designed set;four cases with two attempts per configuration;one human assessor;openrouter/free may resolve to different models;cost and token usage unknown' --by "$student"
if ($LASTEXITCODE -ne 0) { throw 'Рекомендацію не записано; перевір причину.' }
$agg.nested_counts | ConvertTo-Json -Depth 8
$agg.critical_unsupported_counts | ConvertTo-Json
Get-Content -Encoding UTF8 "$cmp\recommendation.yaml"
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

**СКРИНШОТ №5 зараз:** підрахунки, критичні відмови, обраний результат і пояснення, акаунт і дата. Зберегти як `reports/lab03/screenshots/05-scoring-recommendation.png`.

## 9. Регресійний запис

Спочатку досліди несприятливі оцінки. За підтвердженого дефекту конфігурації збережи **реальні** ідентифікатори:

Після завершення всіх оцінок та агрегування зв’язок `blind_id` → `position_id` можна переглянути у `$cmp\scoring\_join-map.json`. Запит, відповідь і structural-result містяться в `$cmp\attempts\<position_id>\`; джерело та очікувана поведінка — у збереженому scoring-view. Саме тепер зістав ці дані для діагностики, не змінюючи початкових оцінок.

```powershell
$position = Read-Host 'position-id підтвердженої відмови після дослідження'
$blind = Read-Host 'Відповідний blind-id'
$diagnosis = Read-Host 'Діагноз: джерело, очікування, запит, фактична відповідь, structural-result та правило рубрики'
$expectedReview = Read-Host 'Чому початкова очікувана поведінка правильна за джерелом і дефект належить конфігурації'
$env:LAB03_POSITION = $position
$env:LAB03_BLIND = $blind
$env:LAB03_DIAGNOSIS = $diagnosis
$env:LAB03_EXPECTED = $expectedReview
@'
import os, yaml
from pathlib import Path
record = dict(regression_id='observed-source-boundary', source_kind='observed-failure',
    position_id=os.environ['LAB03_POSITION'], blind_id=os.environ['LAB03_BLIND'],
    diagnosis=os.environ['LAB03_DIAGNOSIS'], expected_behavior_review=os.environ['LAB03_EXPECTED'], reviewed_by='exideys')
with Path('student/lab03/regression.yaml').open('x', encoding='utf-8', newline='\n') as f:
    yaml.safe_dump(record, f, allow_unicode=True, sort_keys=False)
'@ | uv run python -
Remove-Item Env:LAB03_POSITION,Env:LAB03_BLIND,Env:LAB03_DIAGNOSIS,Env:LAB03_EXPECTED
```

Якщо **немає придатної підтвердженої відмови** або місце дефекту лишається нерозв’язаним, виконай **замість попереднього блока** готову гілку авторської фікстури:

```powershell
Get-Content -Encoding UTF8 .\cases\lab03\authored-failure\authored-failure.json
$regression = @'
regression_id: authored-supported-plus-invented
source_kind: authored-fixture
fixture_id: authored-failure-supported-plus-invented
model_authorship_claim: none
diagnosis: >-
  Джерело пов’язує source baseline з матеріалом, за яким перевіряють пропозицію.
  Авторська відповідь додає автоматичне архівування всіх відхилених пропозицій.
  Джерело не містить такого правила, тому вся відповідь має категорію U.
expected_behavior_review: >-
  Потрібно зберегти зв’язок базового стану з джерелом для перевірки пропозиції
  без додавання архівних або затверджувальних функцій. Це прямо відповідає
  наданому джерелу та очікуваній поведінці фікстури. Відповідь авторська;
  модель її не генерувала, поточну поведінку A або B вона не вимірює.
reviewed_by: exideys
'@
if (Test-Path .\student\lab03\regression.yaml) { throw 'Регресійний вхід уже існує; не перезаписуй його.' }
[IO.File]::WriteAllText((Join-Path $PWD 'student\lab03\regression.yaml'), $regression, $utf8)
```

Після **однієї** з гілок:

```powershell
uv run learning-project lab03 record-regression --report-dir reports/lab03 --record student/lab03/regression.yaml
Get-Content -Encoding UTF8 .\student\lab03\regression.yaml
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

**СКРИНШОТ №6 зараз:** успішний запис, тип походження й діагноз, акаунт і дата. Зберегти як `reports/lab03/screenshots/06-regression.png`.

## 10. Створити заповнений звіт і запис завершення

```powershell
uv run python .\student\lab03\lab03_helper.py report --freeze "$freeze"
if ($LASTEXITCODE -ne 0) { throw 'Звіт не створено. Перевір повідомлення й наявність попередніх свідчень.' }
```

Відкрий `reports/lab03/REPORT.md`. Скрипт зберігає всі заголовки курсу, вставляє фактичні відповіді, оцінювання, підрахунки, протокол і рішення українською. До фінального коміту:

1. У розділі діагнозу A додай конкретний висновок за двома розробницькими відповідями: які дефекти дійсно спостерігалися або що дефектів не виявлено. Гіпотеза про ризик — окремо від спостереження.
2. Поясни кожну розбіжність калібрування, якщо вона є; початкових міток не змінюй.
3. Зафіксуй фактичне використання проби відновлення/переривань, якщо вони були, а також відмінності текстів чи категорій двох спроб одного випадку.
4. Перевір, що рішення справді відповідає замороженим порогам. Додай числову частку прийнятності A та B, якщо вона визначена.
5. Залиши всі посилання на PNG 01–07. Файл 07 з’явиться після коміту.
6. У звіті використовуй безособовий виклад; не залишай інструктивних підказок. Опиши допомогу Codex без приписування авторських прикладів живій моделі.

Потім:

```powershell
$completion = @'
stopped_at_step: "Step 10"
limitation: "none; student-authored evidence is ready for commit-first verification"
preserved_evidence: |
  reports/lab03/
  student/lab03/
'@
if (Test-Path .\student\lab03\completion-detail.yaml) { throw 'Completion detail уже існує; перевір стан.' }
[IO.File]::WriteAllText((Join-Path $PWD 'student\lab03\completion-detail.yaml'), $completion, $utf8)
uv run learning-project lab03 record-completion --report-dir reports/lab03 --status complete --detail student/lab03/completion-detail.yaml --by "$student"
Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
```

### Частковий шлях за реальною умовою зупинки

Виконуй цей розділ **замість** повного кроку 10, лише якщо настала одна з визначених у лабораторній умов: `Step 2`, `Step 3`, `Step 4`, `Step 5` або `Step 6`. Відсутність введеного ключа сама собою не є записаною відмовою маршруту.

```powershell
$stopped = Read-Host 'Точний крок: Step 2 / Step 3 / Step 4 / Step 5 / Step 6'
$limitation = Read-Host 'Фактичне обмеження: що сталося та якими записами підтверджується'
uv run python .\student\lab03\lab03_helper.py partial-report --step "$stopped" --limitation "$limitation"
$detail = [ordered]@{
    stopped_at_step = $stopped
    limitation = $limitation
    preserved_evidence = "reports/lab03/`nstudent/lab03/"
} | ConvertTo-Json
if (Test-Path .\student\lab03\completion-detail.yaml) { throw 'Completion detail уже існує; збережи попередні свідчення.' }
[IO.File]::WriteAllText((Join-Path $PWD 'student\lab03\completion-detail.yaml'), $detail, $utf8)
uv run learning-project lab03 record-completion --report-dir reports/lab03 --status honest-partial --detail student/lab03/completion-detail.yaml --by "$student"
Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
```

JSON у `completion-detail.yaml` є коректним YAML-входом для PyYAML. Перед комітом доповни частковий звіт точними результатами досягнутих етапів та використаною межею відновлення. Скрипт залишає лише посилання на наявні знімки та обов’язковий 07. Не створюй freeze, оцінювання, рішення чи регресію за недосягнуті етапи. Продовжуй із кроку 11. `passed-partial` не дорівнює повністю виконаній лабораторній.

## 11. Тести, локальний коміт і перевірка точного HEAD

```powershell
uv run --extra lab04 python -m unittest discover -s tests/public -v *> .\reports\lab03\public-tests.log
$testExit = $LASTEXITCODE
Get-Content .\reports\lab03\public-tests.log -Tail 35
Write-Host "Public tests exit code: $testExit"
```

Під час підготовки актуального upstream отримано: **198 тестів, 1 failure, 4 errors, 3 skipped**. Чотири помилки — `WinError 1314` у тестах Lab04 на символічні посилання; один failure — відсутній `huggingface_hub` з optional extra Lab04. Це не успішний загальний прогін. Окремо всі **37 тестів Lab03 пройшли**. Тести й платформу курсу не змінено.

Після першого фактичного загального прогону залежності встановлено командою `uv sync --locked --extra lab04`; окремий набір Stage C1 після цього пройшов: 23 тести, OK (skipped=1). Початковий невдалий загальний лог збережено також у `public-tests-before-environment-fix.log`.

Для чотирьох `WinError 1314` відкрий PowerShell від імені адміністратора, перейди до `F:\sobol\ai-systems-design-course\training-project` і повтори загальний прогін із явним `--extra lab04`. Це потрібно для створення символічних посилань у тестових тимчасових каталогах; файли тестів не змінюються. За невирішених збоїв збережи лог, прямо опиши їх у звіті та не називай весь набір успішним: за правилами лабораторної це лишається обмеженням готовності до демонстрації, навіть якщо `lab03 verify` прийме артефакти.

Фактичний повтор від адміністратора: 198 тестів, `FAILED (failures=2, skipped=3)`, код 1. Дві невдачі — `test_prepare_refuses_symlink_without_modifying_target` і `test_decision_refuses_dangling_symlink_without_modifying_target`: наданий код Lab04 Stage B не відхилив символічне посилання з відсутньою ціллю. Це вже не помилка прав або залежностей. Повторний набір Lab03 пройшов: 37 тестів, OK, код 0, лог `lab03-tests.log`. Результати внесено до REPORT.md без зміни тестів чи платформи. Післякомітний verify може підтвердити узгодженість пакета Lab03, але не скасовує цих двох невдач і вимоги успішного загального прогону.

Для окремої перевірки Lab03:

```powershell
uv run python -m unittest discover -s tests/public -p test_lab03_workflow.py -v
```

Перевір скриншоти 01–06, звіт і дані до коміту. Після перевірки тексту звіту:

```powershell
git status --short
git diff --check
git add student/lab03 reports/lab03
git diff --cached --check
git diff --cached --stat
git commit -m "feat(lab03): evaluate one instruction change"
if ($LASTEXITCODE -ne 0) { throw 'Фінальний коміт не створено.' }
$finalCommit = git rev-parse HEAD
uv run learning-project lab03 verify --report-dir reports/lab03 --final-commit "$finalCommit"
if ($LASTEXITCODE -ne 0) {
    Get-Content -Encoding UTF8 .\reports\lab03\verification-report.json
    throw 'Перевірка не пройшла. Усунь причину, створи новий фінальний коміт і перевір новий HEAD.'
}
Write-Host "Final commit: $finalCommit"
whoami
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

Потрібний результат: `Laboratory 03 verification passed-complete.` або, для дозволеної зупинки, `passed-partial.`

**СКРИНШОТ №7 зараз, після успішної перевірки.** Має бути видно результат, повний хеш, акаунт і дату. Зберегти як `reports/lab03/screenshots/07-final-verification.png`.

Після цього:

```powershell
uv run learning-project prepare-report .\reports\lab03\REPORT.md
if ($LASTEXITCODE -ne 0) { throw 'Подання не підготовлено. Перевір, що всі потрібні PNG існують.' }
git status --short
```

Не редагуй студентські свідчення й не роби amend після успішної фінальної перевірки. Якщо зміни необхідні, потрібні новий фінальний коміт, повторний verify і новий знімок 07. Після коміту дозволені лише похідні `verification-report.json`, `07-final-verification.png` та `submission/REPORT.md`.

## 12. Що саме здати

Після самостійного пушу фінальної гілки додай у Teams **окремими файлами**:

1. `training-project/reports/lab03/submission/REPORT.md` — зі вбудованими зображеннями.
2. `training-project/reports/lab03/verification-report.json`.
3. `training-project/reports/lab03/screenshots/07-final-verification.png`.

Супровідний текст:

```text
Taranenko Serhii, KH-1223B. Лабораторна робота 03.
Форк: https://github.com/exideys/ai-systems-design-course
Гілка: lab03/exideys
Фінальний коміт: [сюди скопіювати повний $finalCommit]
Результат перевірки: [фактичний passed-complete або passed-partial]
```

Не здавай цю покрокову інструкцію замість REPORT.md. Архів і PDF не потрібні.

## Коли робити кожен скриншот

На кожному мають бути видимі акаунт (`whoami`) та системна дата (`Get-Date`). Усі імена точні; формат PNG.

| № | Момент | Назва у `reports/lab03/screenshots/` |
| --- | --- | --- |
| 1 | Після `calibrate-submit` | `01-calibration.png` |
| 2 | Після чотирьох development-спроб та перевірок повернених відповідей | `02-development.png` |
| 3 | Після `freeze`, до `select-family` | `03-freeze.png` |
| 4 | Після 16 кінцевих held-out позицій | `04-held-out-execution.png` |
| 5 | Після `aggregate` та `recommend` | `05-scoring-recommendation.png` |
| 6 | Після `record-regression` | `06-regression.png` |
| 7 | Після коміту та успішного `verify`, до `prepare-report` | `07-final-verification.png` |

## Короткі відповіді для захисту

1. Калібрування вимірює застосування рубрики оцінювачем до авторських прикладів; поточна модель їх не генерувала.
2. Однакові випадки й протокол дозволяють пов’язувати різницю з оголошеним фактором, ураховуючи мінливість генерації та маршрутизації.
3. П’ять підрахунків відділяють виклики, відповіді, структурну чинність, можливість семантичного судження та прийнятність. Відмови не зникають зі знаменника спроб.
4. `U` порушує заздалегідь визначену блокувальну умову; додаткові `S` і `Q` не скасовують порушення.
5. Відомий регресійний випадок уже використано для діагностики, тому він не є свіжим незалежним матеріалом для нового фінального порівняння.
6. Оцінювач класифікує відповіді; інженерна команда обирає конфігурацію. Це не надає повноважень на розгортання чи запис прийнятих знань.
