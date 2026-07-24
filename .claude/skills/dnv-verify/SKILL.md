---
name: dnv-verify
description: Верифицирует claim'ы из user/spec.md против курируемых источников, обезличенного дайджеста, локальных slices и web через агента devils-advocate. Считает разных псевдо-пользователей (не объём сообщений), выдаёт per-claim вердикты; claim без источника → UNVERIFIABLE; «Telegram = мнение, не закон». Пишет user/verification_report.md. Требует dnv-synthesis.
---

# dnv-verify — верификация claim'ов (devils-advocate)

Ты запускаешь **адверсариальную верификацию** каждого claim'а в `user/spec.md`
через субагента `devils-advocate` и собираешь `user/verification_report.md`.
Вывод поддерживает **черновик**, требующий независимой экспертной проверки:
верификация покрывает **трассируемость** claim'ов и **механику полей**, не
юридическую правильность (R21).

## Предусловие (KTD12 — см. `user/pipeline-state.schema.md`)

- Твёрдое: `dnv-synthesis` = `completed` (есть `user/spec.md`). Нет —
  **остановись**: «Сначала `/dnv-synthesis`».
- Мягкое: `dnv-chat-mining`. Если `user/slices/` есть — они войдут в проверку
  практики (Grep). Если нет — практика проверяется только по опубликованному
  дайджесту; **пометь** сниженную полноту практики в отчёте.

## Шаг 1. Извлеки claim'ы

```bash
python engine/scripts/extract_claims.py user/spec.md user/claims.json
```
`user/claims.json` — тегированные claim'ы (с уровнем достоверности, ссылками,
секцией). Идемпотентно перегенерируется при изменении spec.

## Шаг 2. Запусти devils-advocate

Вызови субагента **`devils-advocate`** (`.claude/agents/devils-advocate.md`). Он:
- сам пре-загружает источники (`knowledge_base/norms|sources|practice`),
  локальные `user/slices/` (Grep-only, не Read целиком), и web;
- проверяет по стратегии на тег: `[норма]`→BOE/WebSearch; `[практика — Telegram]`
  → **Grep дайджеста/slices, счёт РАЗНЫХ псевдонимов** (один человек ×5 ≠ 5);
  `[не подтверждено]` → UNVERIFIABLE + конкретная внешняя проверка;
- выдаёт вердикты (CONFIRMED / WEAKLY SUPPORTED / CONTRADICTED / UNVERIFIABLE /
  OUTDATED / TAG TOO HIGH/LOW) и пишет `user/verification_report.md`.

**Ключевые инварианты** (агент их держит, проверь на выходе):
- `[практика — Telegram]` **никогда** не апгрейдится до `[норма]` количеством
  сообщений — только текст закона/офиц. разъяснение меняет уровень.
- **Приватные консультантские чаты — не источник** ни в каком виде.
- Claim без найденного источника → **UNVERIFIABLE** + пункт в «список внешних
  проверок», не «похоже на правду».
- as-of: источник старше текущего года на процедурном → **OUTDATED** + живая сверка.

Если запускаешь частично — передай агенту номер секции (он поддерживает partial).

## Шаг 3. Обнови состояние

`steps["dnv-verify"] = {status:"completed", last_run:"<сегодня>",
output:"user/verification_report.md"}`.

## Выход

`user/verification_report.md` — **явный вердикт на каждый claim** + сводка +
«список внешних проверок (вручную)» + проверка актуальности дат/порогов. Если
`dnv-chat-mining` не запускался — отчёт помечает сниженную полноту практики.
Следующий шаг: `dnv-documents` → `dnv-review` → `dnv-submission`.

> Отчёт — вход для **экспертной/официальной** проверки, не замена её. Движок не
> подаёт.
