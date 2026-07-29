# Схема `user/pipeline-state.json` — опциональный файл состояния

**Источник правды формы** — этот файл + `user/pipeline-state.json.example`.
Настоящий `user/pipeline-state.json` **gitignored** (живёт только локально).

Файл состояния — **необязательный** инструмент учёта. Он помогает консультанту
отслеживать прогресс **между сессиями** и понимать, какие этапы уже пройдены.
Если файла нет — консультант работает без него, ориентируясь на содержимое `user/`.

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

## Этапы и их предусловия (канонический граф)

| Этап (step-name) | Главный выход | Твёрдое предусловие (hard) | Мягкое (soft, улучшает) |
|---|---|---|---|
| `dnv-intake` | `user/case-profile.json` | — (первый) | — |
| `dnv-research` | `user/research-notes.md` | `dnv-intake` completed | — |
| `dnv-chat-mining` | `user/slices/` (+ `user/anon.json`) | `dnv-intake` completed | свежие выгрузки в `user/` |
| `dnv-synthesis` | `user/spec.md` | `dnv-research` completed | `dnv-chat-mining` (для практики) |
| `dnv-verify` | `user/verification_report.md` | `dnv-synthesis` completed | `dnv-chat-mining` (локальные slices) |
| `dnv-documents` | `user/drafts/` | `dnv-intake` completed | — |
| `dnv-review` | `user/drafts/review_summary.md` | `dnv-documents` completed | `dnv-synthesis` (для official-reviewer) |
| `dnv-submission` | `user/drafts/submission_checklist.md` | `dnv-review` completed | `dnv-synthesis` (даты/риски) |

> **Твёрдое предусловие** — если оно не `completed`, стоит сначала завершить
> предыдущий этап. **Мягкое** — можно работать без него, но **пометить**
> снижение полноты (напр. синтез без chat-mining использует только
> опубликованный дайджест; помечает это).

> **Вне графа:** статус (read-only, ничего не пишет в состояние),
> трекинг (повторяемый пост-подачный этап; его состояние —
> `user/tracking.md`, а не запись в `steps`) и TIE (последняя миля после
> одобрения; состояние — `user/tie-checklist.md`; предусловие — **факт**,
> о котором может сообщить только пользователь: пришла resolución или
> certificado de acto presunto, а не детерминированный переход по графу).
>
> Разделение ролей: трекинг ведёт кейс **до** резолюции (сроки, силенсио,
> escritos), TIE — **после** (huellas, EX-17, tasa 790-012, карта).

**Минимальный сквозной путь**: `dnv-intake → dnv-documents →
dnv-review` — минует research/synthesis/verify. Он валиден: у `dnv-documents`
твёрдое предусловие — только `dnv-intake`.

## Работа с состоянием

**На входе:**
1. Прочитай `user/pipeline-state.json` (если есть). Если файла нет —
   ориентируйся на содержимое `user/` и контекст разговора.
2. Проверь **твёрдые** предусловия: если нужный этап не `completed`, уточни
   у пользователя, прежде чем продолжать.
3. Проверь **мягкие**: если не `completed`, продолжай, но пометь снижение полноты
   в своём выводе.

**На выходе:**
4. Обнови запись: `steps["<step-name>"] = {status:"completed",
   last_run:"<сегодня>", output:"<путь>"}`. Идемпотентно (перезапуск = перезапись
   своей записи, не дублирование).

**Возобновление (resume):** прочитав состояние, консультант может показать
«что сделано» (что `completed`, что `pending`, что разблокировано).
Онбординг (`README`) использует это же состояние.

## Идемпотентность

- Повторный запуск этапа **перезаписывает** свою запись (не плодит записи).
- Состояние — **только про статус**; актуальность содержимого (устарел ли
  `user/spec.md` после нового intake) в v1 **не** отслеживается автоматически —
  можно предупредить по `last_run`, но staleness-propagation — future.

## Приватность

`pipeline-state.json` хранит **пути и статусы**, а не значения профиля. Не
записывай сюда NIE/имена/суммы (дата-минимизация).
