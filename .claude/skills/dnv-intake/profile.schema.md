# Схема профиля кейса (человекочитаемая)

Источник правды — **`profile.schema.json`** (рядом). Профиль пишется в
`user/case-profile.json` (gitignored). Namespace **общий с реестром форм**
(`knowledge_base/forms/registry.json`); инвариант registry ⊆ schema проверяет
`engine/scripts/check_namespace.py`.

## Блоки и ветки

| Префикс | Что | Когда спрашивается |
|---|---|---|
| `case.*` | тип процесса, флаг архетипа | всегда |
| `applicant.*` | titular: identidad, разрешение, даты | всегда (часть — только renovación) |
| `work.*` | работа/доход (autónomo/контрактор) | всегда |
| `family.*` | член семьи (cónyuge/pareja) | если `family.present=true` |
| `tasa.*` | суммы/эпиграфы tasa | производные, проверять вживую |

**Ветки (`branch`):** `both` — всегда; `renovacion` — только продление
(`tie_expiry`, `first_approval_date`); `family` — только при члене семьи;
`initial` — только первичная; `tie` — **не спрашивается в интейке**, добирается
в `/dnv-tie` после одобрения, когда заполняется EX-17 (имена родителей,
провинция отделения, эпиграф tasa 012).

> Ветка `tie` существует, чтобы не удлинять первое интервью полями, которые
> понадобятся через месяцы. Все её поля `required: false`; до `/dnv-tie` они
> легитимно пусты, и черновик показывает по ним `[ТРЕБУЕТСЯ: …]`.

## Контролируемые словари

- `sexo` ∈ {**Hombre**, **Mujer**} — не пусто, не «indefinido».
- `estado_civil` ∈ {Soltero/a, Casado/a, Viudo/a, Divorciado/a, Separado/a}.
- `tipo_solicitud` ∈ {INICIAL, RENOVADA}.
- `parentesco` ∈ {Cónyuge, Pareja, Hijo/a, Ascendiente}.
- `process_type` ∈ {initial, renovacion}.

## Правила

- `required=true` (для активной ветки) обязательно к заполнению; неизвестное →
  `null` + пометка, **не выдумывать**.
- `derived=true` — вычисляется/ищется (full_name; tipo_solicitud; суммы tasa).
- `family.titular_regage` заполняется **после** подачи titular — не выдумывать.
- Значения профиля **не** дублируются в `CLAUDE.md`/память.

Структура файла — вложенный объект, эквивалентный dotted-ключам схемы. Пример
формы — `user/case-profile.json.example`.
