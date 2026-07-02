---
name: dnv-chat-mining
description: ЛОКАЛЬНО домалывает практику из свежих выгрузок Telegram-чатов DNV — merge → anonymize → filter → slice — в user/slices/ для верификации. Идемпотентно: дедуп по message-id, перекрывающийся ре-импорт даёт ноль новых, покрытие монотонно. Всё остаётся в user/ (gitignored); наружу ничего не публикует. Опциональный шаг; требует dnv-intake.
---

# dnv-chat-mining — локальная догрузка практики

Ты прогоняешь **свои свежие выгрузки** чатов через локальный пайплайн
(`merge → anonymize → filter → slice`) в `user/slices/`, чтобы `dnv-verify` мог
считать практику по **уникальным псевдонимам**. **Всё остаётся в `user/`**
(gitignored). Наружу (в дайджест) ничего не идёт — это делает мейнтейнер отдельно
(`build_digest.py`), не этот навык.

## Предусловие (KTD12 — см. `user/pipeline-state.schema.md`)

- Твёрдое: `dnv-intake` = `completed` (workspace/state существует).
- Нужны **свежие экспорты** Telegram (JSON, Telegram Desktop) в `user/`. Нет
  экспортов — скажи, как выгрузить (ниже), и остановись без ошибки.

Это **опциональный** шаг. Без него пайплайн работает — `dnv-synthesis`/`dnv-verify`
используют только опубликованный дайджест, помечая сниженную полноту.

## Шаг 1. Определи окно догрузки

- Прочитай `knowledge_base/practice/LAST_COVERED_DATE` (напр. `2026-06-17`) —
  докуда покрыт **опубликованный** дайджест.
- Скажи пользователю: **выгрузи чат от этой даты до сегодня** (Telegram Desktop →
  Export chat history → JSON). Перекрытие диапазонов не страшно — дедуп это
  снимет (Шаг 2).

## Шаг 2. Прогон локального пайплайна (всё под `user/`, path-containment)

Пути ввода/вывода — **аргументы**; вывод контейнится `--allowed-root user`.
Один экспорт — можно пропустить `merge` и сразу `anonymize`.

```bash
# a) merge (если экспортов ≥2): дедуп по message-id, сортировка по времени
python engine/scripts/chat/merge_chat_dumps.py user/dump_old.json user/dump_new.json user/merged.json --allowed-root user
# отчёт вида "in=… out=… dedup=…": dedup>0 при перекрытии — это и есть идемпотентность

# b) anonymize (ПРИВАТ-ГЕЙТ, U2): keep-allowlist полей, псевдоним = salted-hash from_id,
#    страйп имён/контактов. Салт стабильный (один файл) → стабильные псевдонимы между прогонами.
python engine/scripts/chat/anonymize_chat.py user/merged.json user/anon.json --salt-file user/.anon_salt --allowed-root user

# c) filter: теги DNV-тем + реконструкция reply-тредов (config-driven)
python engine/scripts/chat/filter_chat.py user/anon.json user/filtered.json --allowed-root user

# d) slice: по одному небольшому файлу на тему (для downstream Grep)
python engine/scripts/chat/slice_by_topic.py user/filtered.json user/slices all --allowed-root user
```

> **НИКОГДА** не подавай сырой (не-анонимизированный) экспорт в `filter`/`slice` —
> скрипты fail-closed это отвергнут, но и ты не делай. Порядок: anonymize → потом всё.

## Шаг 3. Идемпотентность (first-class)

- **Дедуп по стабильному `message-id`** в `merge` → перекрывающийся ре-импорт даёт
  **ноль новых** (см. `dedup=` в отчёте).
- **Стабильный салт** (`user/.anon_salt`, тот же файл) → один `from_id` всегда даёт
  **тот же псевдоним** → подсчёт *разных* людей в `dnv-verify` устойчив между
  прогонами.
- **Покрытие монотонно:** заметь максимальную дату сообщения в `user/filtered.json`
  и считай её новой «покрыто до». Повторная догрузка старого диапазона не
  откатывает покрытие и не плодит дублей.

## Шаг 4. Приватность

- `user/anon.json`, `user/filtered.json`, `user/slices/`, `user/.anon_salt`,
  сырые экспорты — **всё gitignored**, остаётся локально.
- В опубликованное дерево из этого навыка **ничего не уходит**. Псевдо-ключи и
  сырой текст не покидают `user/`.

## Шаг 5. Обнови состояние

`steps["dnv-chat-mining"] = {status:"completed", last_run:"<сегодня>",
output:"user/slices/"}`. Упомяни «покрыто до <max message date>».

## Выход

`user/slices/topic_*.json` (обезличенные) для `dnv-verify`. Следующий шаг:
`dnv-verify` (сверит claim'ы против slices + источников + web) или
`dnv-synthesis` (подтянет свежую практику). «Telegram = мнение, не закон.»
