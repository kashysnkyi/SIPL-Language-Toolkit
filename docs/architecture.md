# Архітектура

Потік даних:

```text
SIPL source
    ↓ lexer/parser (Lark grammar)
Lark parse tree ──→ Text / JSON / DOT
    ↓ AST builder
typed AST + SourceSpan ──→ Text / JSON / DOT
    ├──→ interpreter ──→ state + execution events
    └──→ semantic builder ──→ semantic term
```

Мова визначається в одному місці - `grammar/sipl.lark`. `parser.py` перетворює конкретне дерево бібліотеки на стабільні AST-вузли з `ast.py`. Інтерпретатор, візуалізатори й семантичний модуль працюють лише з цими AST API, тому не дублюють парсер.

Стан виконання є словником `dict[str, int]`. Trace складається з типізованих подій зі `SourceSpan`, тому придатний для майбутнього debugger або IDE-клієнта. CLI серіалізує ті самі моделі в JSON зі стабільною версією схеми.

