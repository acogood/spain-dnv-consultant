# Синтетический сквозной пример

Полностью **вымышленный** кейс, на котором можно посмотреть, что движок делает,
не подставляя свои данные. Один архетип v1 (autónomo/контрактор + cónyuge,
renovación). Реальных значений здесь нет.

## Кто такой синтетический заявитель

`case-profile.json` — Ivan Testovenko (вымышлен), удалённый контрактор на
зарубежную компанию (Acme Remote LLC), супруга Maria Testovenko (cónyuge),
продление. Все NIE/паспорта/даты/суммы — фиктивные.

Профиль заполнен и по полям **ветки `tie`** (имена родителей, провинция
отделения) — чтобы пример показывал и заливку EX-17. В живом кейсе их не
спрашивают в интейке: их добирает `/dnv-tie` уже после одобрения.

## Как прогнать пример: intake → draft → field-QA

`case-profile.json` представляет **результат интейка** (`/dnv-intake`) для этого
кейса. Дальше — две детерминированные команды (запускаются из корня репо).

> **Запуск.** `python` 3.8+ (если `python` не на PATH — укажите полный путь к
> интерпретатору). Команды ниже даны для bash (перенос строки `\`); в PowerShell
> используйте перенос `` ` `` и пишите команду одной строкой. На Windows-консоли
> для корректного вывода кириллицы задайте `PYTHONIOENCODING=utf-8` (bash:
> `export PYTHONIOENCODING=utf-8`; PowerShell: `$env:PYTHONIOENCODING="utf-8"`).

```bash
# 1) DRAFT: заполнить формы строго из профиля
python engine/scripts/fill_forms.py example/mvp-case/case-profile.json \
    knowledge_base/forms/registry.json --out-dir example/mvp-case/drafts --allowed-root example

# 2) FIELD-QA: исчерпывающий механический ревью чистого черновика
python engine/scripts/field_qa.py example/mvp-case/case-profile.json \
    knowledge_base/forms/registry.json example/mvp-case/drafts/drafts.json \
    --out-dir example/mvp-case/drafts --allowed-root example
```

Ожидаемо на ЧИСТОМ черновике — `fields=73 OK=70 WRONG=0 MISSING=3 UNCERTAIN=0`,
код возврата 0. Вердикт на 100% полей реестра; три `MISSING` — не ошибки:

| Поле | Почему пусто |
|---|---|
| MI-F · Nº de registro de la solicitud del titular | REGAGE титулара появляется **после** его подачи — выдумывать нельзя |
| tasa-790-052 · Epígrafe | ищется вживую на дату подачи (сумма меняется) |
| tasa-790-012 · Epígrafe | то же; и строки renovación / primera concesión — **разные** |

> Формы `EX-17`, `EX-17-familiar` и `tasa-790-012` относятся к этапу **после**
> одобрения (`/dnv-tie`, сдача отпечатков), но живут в том же реестре — поэтому
> в прогоне они присутствуют и получают вердикт наравне с остальными.

## Демонстрация: field-QA ловит посаженные ошибки

`planted-bug/drafts.json` — тот же черновик с **5** намеренными ошибками:

| Поле | Ошибка | Тип | Поймано как |
|---|---|---|---|
| MI-T Sexo | `Mujer` (профиль Hombre) | правдоподобная | WRONG (не совпадает) |
| MI-T N.I.E. | транспонированные цифры | правдоподобная | WRONG (не совпадает) |
| MI-F Sexo | `indefinido` | грубая (вне домена) | WRONG (домен) |
| MI-F Reg. titular | выдуманный номер (профиль пуст) | галлюцинация | WRONG (галлюцинация) |
| **EX-17 Nº pasaporte** | номер **устаревшего** паспорта при действующем в профиле | правдоподобная | WRONG (не совпадает) |

```bash
python engine/scripts/field_qa.py example/mvp-case/case-profile.json \
    knowledge_base/forms/registry.json example/mvp-case/planted-bug/drafts.json \
    --out-dir example/mvp-case/planted-bug --allowed-root example
# -> fields=73 OK=66 WRONG=5 MISSING=2, exit 1; см. planted-bug/field_qa_report.md
```

*(`MISSING` здесь 2, а не 3: поле REGAGE титулара теперь несёт выдуманное
значение и попадает в `WRONG`, а не в `MISSING`.)*

**Ключ:** правдоподобные ошибки (Mujer вместо Hombre, транспонированный NIE,
номер прошлого паспорта) прошли бы инспекцию «на глаз», но независимая
ре-деривация из профиля их ловит. Пятая — не выдуманная для примера: ровно эта
ошибка случилась в реальном прогоне и пережила первый аудит.

## Что демонстрирует пример

- Черновик заполняется **строго из профиля**; нет данных → `[ТРЕБУЕТСЯ]`, не
  выдумка.
- Field-QA даёт вердикт на **каждое** поле (count==полей реестра).
- Ловит и грубые, и правдоподобные-но-неверные ошибки.
