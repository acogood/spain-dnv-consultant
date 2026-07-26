# Схема `user/pipeline-state.json` — контракт возобновления

**Источник правды формы** — этот файл + `user/pipeline-state.json.example`.
Настоящий `user/pipeline-state.json` **gitignored** (живёт только локально).

В Claude Code **нет встроенного секвенсора** навыков. Порядок `dnv-*` — только
**конвенция**. Единый файл состояния делает набор навыков **возобновляемым
многосессионным пайплайном** и позволяет каждому навыку **проверять
предусловия** и останавливаться с инструкцией, а не догадываться.

## Форма файла

```json
{
  "schema_version": "1.0",
  "steps": {
    "<step-name>": { "status": "pending|completed", "last_run": "YYYY-MM-DD", "output": "<repo-relative path>" }
  }
}
```

- **`status`** ∈ `{pending, completed}` — гранулярность v1 (status-only; без
  content-hash staleness-propagation — это Open Question).
- **`last_run`** — дата последнего успешного прогона шага (`YYYY-MM-DD`); у
  `pending` может отсутствовать.
- **`output`** — путь к главному артефакту шага (для «продолжить с…» и для
  precondition-проверок downstream). У `pending` отсутствует.
- Неизвестные будущие ключи внутри записи шага — игнорировать (forward-compatible).

## Шаги и их предусловия (канонический граф)

| Шаг (step-name) | Главный выход | Твёрдое предусловие (hard) | Мягкое (soft, улучшает) |
|---|---|---|---|
| `dnv-intake` | `user/case-profile.json` | — (первый) | — |
| `dnv-research` | `user/research-notes.md` | `dnv-intake` completed | — |
| `dnv-chat-mining` | `user/slices/` (+ `user/anon.json`) | `dnv-intake` completed | свежие выгрузки в `user/` |
| `dnv-synthesis` | `user/spec.md` | `dnv-research` completed | `dnv-chat-mining` (для практики) |
| `dnv-verify` | `user/verification_report.md` | `dnv-synthesis` completed | `dnv-chat-mining` (локальные slices) |
| `dnv-documents` | `user/drafts/` | `dnv-intake` completed | — |
| `dnv-review` | `user/drafts/review_summary.md` | `dnv-documents` completed | `dnv-synthesis` (для official-reviewer) |
| `dnv-submission` | `user/drafts/submission_checklist.md` | `dnv-review` completed | `dnv-synthesis` (даты/риски) |

> **Твёрдое предусловие** — навык **останавливается**, если оно не `completed`.
> **Мягкое** — навык работает без него, но **флагует** снижение полноты (напр.
> синтез без chat-mining использует только опубликованный дайджест; помечает это).

> **Вне графа:** `dnv-status` (read-only консюмер состояния, ничего не пишет),
> `dnv-tracking` (повторяемый пост-подачный шаг; его состояние —
> `user/tracking.md`, а не запись в `steps`; предусловие `dnv-submission` он
> проверяет сам) и `dnv-tie` (последняя миля после одобрения; состояние —
> `user/tie-checklist.md`; предусловие — **факт**, о котором может сообщить
> только пользователь: пришла resolución или certificado de acto presunto, а не
> детерминированный переход по графу).
>
> Разделение ролей: `dnv-tracking` ведёт кейс **до** резолюции (сроки, силенсио,
> escritos), `dnv-tie` — **после** (huellas, EX-17, tasa 790-012, карта).

**Минимальный сквозной путь**: `dnv-intake → dnv-documents →
dnv-review` — минует research/synthesis/verify. Он валиден: у `dnv-documents`
твёрдое предусловие — только `dnv-intake`.

## Контракт каждого `dnv-*` навыка

**На входе (precondition-гард):**
1. Прочитай `user/pipeline-state.json` (если нет — только `dnv-intake` вправе его
   создать; остальные останавливаются с «Сначала `/dnv-intake`»).
2. Проверь, что все **твёрдые** предусловия шага = `completed`. Если нет —
   **остановись** и укажи, какой навык запустить (`/dnv-<step>`), не догадывайся.
3. Проверь **мягкие**: если не `completed`, продолжай, но пометь снижение полноты
   в своём выводе.

**На выходе:**
4. Обнови свою запись: `steps["<step-name>"] = {status:"completed",
   last_run:"<сегодня>", output:"<путь>"}`. Идемпотентно (перезапуск = перезапись
   своей записи, не дублирование).

**Возобновление (resume):** любой навык, прочитав состояние, может отрендерить
«сделано / следующий шаг» (что `completed`, что `pending`, что разблокировано).
Онбординг (`README`) использует это же состояние.

## Идемпотентность и порядок

- Повторный запуск шага **перезаписывает** свою запись (не плодит записи).
- Запуск **не по порядку** (напр. `/dnv-documents` до `/dnv-intake`) →
  **halt с инструкцией**, состояние не портится.
- Состояние — **только про статус**; актуальность содержимого (устарел ли
  `user/spec.md` после нового intake) в v1 **не** отслеживается автоматически —
  навык может предупредить по `last_run`, но staleness-propagation — future.

## Приватность

`pipeline-state.json` хранит **пути и статусы**, а не значения профиля. Не
записывай сюда NIE/имена/суммы (дата-минимизация).
