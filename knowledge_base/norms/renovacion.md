# Продление (renovación) — требования

> as-of: **2026-07** · охват: renovación teletrabajador internacional · `generic`
> с `case-derived` уточнениями.
> Якорь: `../sources/primary/ley-14-2013-teletrabajo.md` (arts. 74 quinquies.3, 76.3).
> Первичная подача — **отдельный файл: `solicitud-inicial.md`**.
>
> 🔎 **Переякоривание (2026-07).** Базовый принцип сверен с дословным текстом.
> Формулировка «art. 74 quinquies регулирует продление» уточнена: продление — это
> его **¶ 3**, а ¶ 1 той же статьи — про **первичную подачу изнутри Испании**.
> Таблица «initial vs renovación» переехала в `solicitud-inicial.md` §7 — она
> перестала жить только на стороне продления. Перечень документов по-прежнему
> сверять вживую.

## Базовый принцип

Продление стоит в **art. 74 quinquies.3** и **art. 76.3** Ley 14/2013, дословно:

> **74 quinquies.3.** Los titulares de esta autorización podrán solicitar su
> **renovación por períodos de dos años** siempre y cuando se mantengan las
> condiciones que generaron el derecho.

> **76.3.** Los titulares de una autorización regulada en esta sección podrán
> solicitar su renovación por periodos de dos años siempre y cuando mantengan las
> condiciones que generaron el derecho […] La Dirección General de Migraciones podrá
> **recabar los informes necesarios** para pronunciarse sobre el mantenimiento de
> las condiciones que generaron el derecho.

Разрешение продлевается, если **сохраняются условия**, дававшие право на первичное
разрешение (реальная удалённая деятельность на иностранного заказчика, достаточный
доход, отсутствие оснований для отказа). `[норма]`

Проверка со стороны Instrucción — одна строка (octava ¶ 5): *«Para la renovación de
las autorizaciones contempladas en la ley, se comprobará el mantenimiento de las
condiciones que justificaron la concesión»*. `[официальное разъяснение]`

> ⚠️ **Весь наблюдаемый перечень документов на продление — внеинструкционный.**
> В Instrucción его нет; он живёт в **недатированной** сводке UGE-CE на сайте и
> меняется без объявления. Пример: обновление 2026-06 сделало обязательными копии
> налоговых деклараций в испанскую налоговую за два периода, а через неделю орган
> стал прописывать в дозапросах именно **годовые** декларации, тогда как до этого
> проходили квартальные. `[практика — консультант]` — разбор в
> `../sources/reports/2026-07-aplicacion-practica.md` §3.7 и §11.
>
> Практический вывод: **отсутствие документа в списке обязательных не означает, что
> его не дозапросят.** В прежнем перечне не было ни банковских выписок, ни справки
> об отсутствии налоговых долгов — дозапросы по ним приходили.
> `[практика — консультант]`

> Это одна из **первых волн продлений** (первичные разрешения ~2023). Устойчивой
> административной практики мало — опираться на **текст нормы + свежий рисёрч**, не
> на единичные анекдоты. `[практика — Telegram]` (осторожно)

## Что доказывается на продлении

| Условие | Как подтверждается | Тег | Метка |
|---|---|---|---|
| Продолжение удалённой деятельности | контракт/Contractor Agreement (действующий), инвойсы/facturas за период | `[норма]` | `case-derived` (autónomo/контрактор) |
| Достаточный доход | банковские выписки (3 мес.) + расчёт EUR-эквивалента; порог — см. `umbral-ingresos.md` | `[норма]` | `generic` |
| Реальность работодателя/заказчика | корпоративные документы (Good Standing; при смене названия — Certificate of Amendment) | `[официальное разъяснение]` | `case-derived` |
| Налоговая/социальная исправность | certificado estar al corriente (Hacienda + Seguridad Social); alta RETA если autónomo | `[норма]` | `case-derived` |
| Пребывание/адрес | empadronamiento; отсутствие длительных отлучек сверх допустимого | `[норма]` | `generic` (проверить вживую лимиты отсутствия) |

## initial vs renovación (отличия для интейка)

Таблица переехала в **`solicitud-inicial.md` §7** и расширена (окно подачи, NIE,
certificado digital, налоговые декларации, нормативная причина карве-аута по
несудимости). Здесь не дублируется, чтобы не разъезжались две копии.

Коротко, что меняется на стороне продления: отметка на форме — **RENOVADA**;
нужны `tie_expiry` и `first_approval_date` (арифметика окна); справка о несудимости
как правило **не требуется** — не «по практике», а по **Instrucción cuarta ¶ 2**
(карве-аут для держателя разрешения > 6 месяцев), с оговоркой о сужении этого
карве-аута в сводке UGE-CE. `[официальное разъяснение]` (проверить вживую)

## Частые точки риска на продлении (каталог → см. spec §4)

- Несовпадение наименования контрактующего/инвойсящего лица (смена названия
  компании) → Certificate of Amendment + Addendum + Certificate of services.
  `case-derived`
- Доход через личный платёжный сервис (напр. Wise Personal) в иностранной валюте
  → выписки + сопроводительное с курсами и EUR-эквивалентом. `case-derived`
- Единственный заказчик → риск «falso autónomo»; подчеркнуть independent
  contractor + список duties + indefinite term. `case-derived`

> Значения и стратегии — в `templates/spec_renewal.template.md` §4 (generic
> каталог) и в дайджесте практики `../practice/`.
