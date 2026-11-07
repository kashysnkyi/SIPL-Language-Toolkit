# SIPL Language Toolkit

Курсовий проєкт із дисципліни «Теорія програмування». Toolkit реалізує формальну граматику, парсер, власне типізоване AST, інтерпретатор, подієвий trace, CLI, візуалізацію parse tree/AST і автоматичну побудову семантичного терму SIPL.

## Заявлені завдання

| ID | Зміст | Бали |
|---|---|---:|
| CORE-01 | Машинозчитувана граматика та позитивні/негативні приклади | 0.5 |
| CORE-02 | Парсер і типізоване AST із `SourceSpan` | 1.5 |
| CORE-03 | Інтерпретатор SIPL із лімітом кроків | 2.0 |
| CORE-04 | Подієва модель виконання і JSON trace | 1.0 |
| CORE-05 | CLI `parse/check/run/trace` і JSON-режим | 1.0 |
| VIS-01 | Parse tree у Text/JSON/DOT | 1.5 |
| VIS-02 | AST у Text/JSON/DOT та порівняння Parse Tree ↔ AST | 1.0 |
| SEM-01 | Побудова семантичного терму в нотації курсу | 2.0 |

Заявлена сума - 10.5 бала; відповідно до умов проєкту підсумкова оцінка обмежується 10 балами.

## Можливості

- арифметичні вирази: `+`, `-`, `*`, `div`, `mod`, унарний мінус;
- умови: `=`, `!=`, `<`, `<=`, `>`, `>=`, `not`, `and`, `or`, `true`, `false`;
- оператори: присвоювання, послідовність, `if`, `while`, `begin/end`, `skip`;
- точні позиції AST-вузлів у вихідному тексті;
- зрозумілі синтаксичні та runtime-діагностики;
- ліміт кроків для захисту від нескінченних циклів;
- події `BeforeStatement`, `AfterStatement`, `VariableChanged`, `ConditionEvaluated`, `ProgramFinished`;
- представлення parse tree та AST у тексті, JSON і Graphviz DOT;
- семантичні терми `AS`, `IF`, `WH`, суперпозиція `S^n`, розіменування `X^⇒` та послідовна композиція `·`.

## Встановлення

```powershell
cd SIPL_Course_Project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Швидкий запуск

```powershell
sipl check examples\parity.sipl
sipl parse examples\power.sipl --json
sipl run examples\power.sipl --state X=2 --state Y=5
sipl trace examples\parity.sipl --state N=5 --json
sipl semantic examples\parity.sipl
sipl tree examples\gcd.sipl --format dot --output gcd-tree.dot
sipl ast examples\gcd.sipl --format json
sipl compare examples\gcd.sipl
```

## Локальний сайт

Після встановлення запустіть:

```powershell
sipl-web
```

Браузер автоматично відкриє `http://127.0.0.1:8000`. На сторінці можна:

- вибрати готовий приклад або вставити власний SIPL-код;
- задати початковий стан, наприклад `N=5` або `X=2,Y=5`;
- перевірити синтаксис і переглянути AST;
- побудувати семантичний терм;
- виконати програму та переглянути кінцевий стан і trace.

Додаткові параметри:

```powershell
sipl-web --port 8080
sipl-web --no-browser
```

Замість встановленої команди можна використовувати `python -m sipl.cli`.

## CLI та коди завершення

| Код | Значення |
|---:|---|
| 0 | успішне виконання |
| 2 | синтаксична помилка або неправильні аргументи |
| 3 | помилка виконання SIPL |

Команди `parse`, `run`, `trace`, `semantic`, `tree`, `ast`, `compare` підтримують машинозчитуваний JSON там, де це доречно. JSON-контракти містять поле `schema_version: "1.0"`.

## Тести

```powershell
pytest
pytest --cov=sipl --cov-report=term-missing
```

Тести включають щонайменше 10 коректних і 10 некоректних програм, перевірки AST і `SourceSpan`, виконання, помилок, trace, семантичних термів та візуалізаторів.

## Структура

```text
src/sipl/
  grammar/sipl.lark     формальна граматика
  ast.py                типізовані AST-вузли
  parser.py             Lark parse tree -> власне AST
  interpreter.py        runtime, state, trace
  semantics.py          семантичний терм
  visualization.py      Text/JSON/DOT
  cli.py                команди користувача
  webapp.py             локальний HTTP API
  webui/index.html      локальний вебінтерфейс
examples/               SIPL-приклади
tests/                  автоматичні тести
docs/                   архітектура та звіт
```

## Обмеження

- SIPL використовує цілі числа без статичної системи типів.
- `div` округлює частку до нуля; ділення на нуль є runtime-помилкою.
- Інструмент не виконує символічне доведення коректності програм.
- DOT генерується без вбудованого рендерера; SVG можна отримати зовнішньою командою `dot -Tsvg tree.dot -o tree.svg`.

