# Синтетический сквозной пример

Полностью **вымышленный** кейс, на котором можно посмотреть, что движок делает,
не подставляя свои данные. Один архетип v1 (autónomo/контрактор + cónyuge,
renovación). Реальных значений здесь нет.

## Кто такой синтетический заявитель

`case-profile.json` — Ivan Testovenko (вымышлен), удалённый контрактор на
зарубежную компанию (Acme Remote LLC), супруга Maria Testovenko (cónyuge),
продление. Все NIE/паспорта/даты/суммы — фиктивные.

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

Ожидаемо на ЧИСТОМ черновике: `WRONG=0`, вердикт на 100% полей; пара `MISSING` —
это поля, заполняемые ПОСЛЕ подачи (`titular_regage`) или ищущиеся вживую
(эпиграф tasa), не ошибки.

## Демонстрация: field-QA ловит посаженные ошибки

`planted-bug/drafts.json` — тот же черновик с 4 намеренными ошибками:

| Поле | Ошибка | Тип | Поймано как |
|---|---|---|---|
| MI-T Sexo | `Mujer` (профиль Hombre) | правдоподобная | WRONG (не совпадает) |
| MI-T N.I.E. | транспонированные цифры | правдоподобная | WRONG (не совпадает) |
| MI-F Sexo | `indefinido` | грубая (вне домена) | WRONG (домен) |
| MI-F Reg. titular | выдуманный номер (профиль пуст) | галлюцинация | WRONG (галлюцинация) |

```bash
python engine/scripts/field_qa.py example/mvp-case/case-profile.json \
    knowledge_base/forms/registry.json example/mvp-case/planted-bug/drafts.json \
    --out-dir example/mvp-case/planted-bug --allowed-root example
# -> WRONG=4, exit 1; см. planted-bug/field_qa_report.md
```

**Ключ:** правдоподобные ошибки (Mujer вместо Hombre, транспонированный NIE)
прошли бы инспекцию «на глаз», но независимая ре-деривация из профиля их ловит.

## Что демонстрирует пример

- Черновик заполняется **строго из профиля**; нет данных → `[ТРЕБУЕТСЯ]`, не
  выдумка.
- Field-QA даёт вердикт на **каждое** поле (count==полей реестра).
- Ловит и грубые, и правдоподобные-но-неверные ошибки.
