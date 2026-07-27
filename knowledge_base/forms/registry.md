# Реестр полей форм DNV (per-form field registry)

Машиночитаемая версия: **`registry.json`** (источник правды для генерации и
верификации). Этот файл — человекочитаемое зеркало.

> ⚠️ **Сверяйте ярлыки и эпиграфы с ТЕКУЩИМИ чистыми бланками** MI-T / MI-F /
> EX-17 / tasa (Modelo 790) — формы и суммы tasa меняются (as-of 2026-07).
> `case_derived` = поле выведено из архетипа v1 (autónomo/контрактор + cónyuge);
> `generic` = применимо ко всем кейсам.

**Когда какая форма.** MI-T/MI-F, tasa 790-038 (+ `-familiar`) и memoria — на
подачу (`/dnv-documents`). EX-17 (+ `-familiar`) и tasa 790-012 (+ `-familiar`) —
уже **после** одобрения, на сдачу отпечатков (`/dnv-tie`): до concesión заполнять
их нечем и незачем.

**Рендер значения задаёт `type` поля.** Реестр не только называет `profile_key`,
но и говорит, **как** значение попадает в ячейку листа
(`engine/scripts/_fieldfmt.py`, одна общая функция для генератора и для
ре-деривации field-QA):

| `type` | Что делает | Пример |
|---|---|---|
| `date` | `AAAA-MM-DD` → **`DD/MM/AAAA`** (формат испанского бланка); нераспознанное проходит насквозь, поэтому повторный прогон ничего не сдвигает | `1990-01-15` → `15/01/1990` |
| `checkbox` + `domain: fixed_checked` | отметка **плюс** значение профиля | `☑ отметить — teletrabajador de carácter internacional` |
| `text`, `enum`, `number` | как есть (`number` в v1 намеренно не форматируется) | `X9999999R` |

⚠️ Правило завязано на **поле**, а не на `profile_key`: один ключ в разных формах
может рендериться по-разному. `applicant.permit_type` — ровно такой случай: в
`MI-T` это чекбокс, в `memoria` — обычный текст.

## `applies_when` — состояние кейса как машиночитаемое условие

| Форма | `applies_when` (все ключи по И) | Род условия |
|---|---|---|
| `EX-17` | `case.resolution_notified` | этап |
| `tasa-790-012` | `case.resolution_notified` | этап |
| `MI-F` | `family.present` | **состав** |
| `tasa-790-038-familiar` | `family.present` | **состав** |
| `EX-17-familiar` | `case.resolution_notified` + `family.present` | этап + состав |
| `tasa-790-012-familiar` | `case.resolution_notified` + `family.present` | этап + состав |
| остальные | нет — применяются всегда | — |

Форма применяется, когда **все** её ключи непусты (для булевых — истинны:
`family.present: false` это заполненный ответ «нет», он форму **не** включает).

**Два рода условий, и ключ их намеренно не различает.** «Этап» — форма применится
**позже** (`case.resolution_notified` появится после одобрения). «Состав» — у
этого заявителя форма не применится **никогда**: соло-кейс заявлен в объёме v1, и
семейного бланка у него нет вовсе. Механика одна, разной остаётся только
формулировка в листе и в отчёте.

> **MI-F гейтится с 2026-07.** До этого семейная форма подачи была единственной,
> у которой условия не было, — и профиль без блока `family` давал
> **десять** ложных MISSING (все поля MI-F). Пакет соло-кейса читался как
> наполовину незаполненный. Этот же документ уже утверждал, что «„семьи нет“
> выражено через `applies_when`» (см. ниже, MI-F/EX-17-familiar) — утверждение
> опережало реестр на одну форму. Теперь совпадает.

> **Своя tasa на каждого заявителя — с 2026-07.** Тот же класс дефекта, ещё на
> двух формах. Sujeto pasivo пошлины — `los solicitantes de **cada**
> autorización`: 790-038 платится **отдельным бланком на каждого** заявителя,
> включая cónyuge, и то же на этапе TIE для 790-012. Реестр этого выразить не
> мог — одна форма с ключами `applicant.*`, множественности нет, — поэтому
> `fill_forms` второй бланк не создавал, `field_qa` не помечал его пропущенным, и
> человек приходил **с недоплатой**. Ниже (блок Tasa) этот документ уже писал
> «плательщик = каждый заявитель» — снова документация опережала реестр, теперь
> на две формы. Закрыто парами `tasa-790-038-familiar` и `tasa-790-012-familiar`
> по образцу MI-T/MI-F: кода это не потребовало.
>
> Эпиграф и сумма **переиспользуются** из ключей титуляра (`tasa.epigrafe_038` и
> т. д.): первичный источник говорит «на каждого заявителя», а это про **число
> платежей**, не про разные строки. Встречающееся в сообществе утверждение, что
> на renovación строки у титуляра и члена семьи разные, — `[практика — Telegram]`
> и вдобавок **вопрос, а не ответ**; апгрейд практики до нормы запрещён.
> Митигация — предупреждение «сверьте строку отдельно для каждого заявителя» в
> `common_errors` эпиграфа: оно доедет гарантированно, потому что эпиграф всегда
> пуст → всегда `MISSING` → `attach_hint` его покажет.

**Что это меняет в проверках:**

- форма **не применяется** → пустое поле, честно помеченное `[ТРЕБУЕТСЯ]`, даёт
  `OK`; `fill_forms.py` ставит на лист шапку «не применяется к вашему кейсу»;
- форма **применяется** → работает обычное правило: `alta` + пусто = `MISSING`;
- **проверка значений идёт в обоих случаях.** Значение из ниоткуда, выход из
  домена, расхождение с профилем — это `WRONG` независимо от этапа.
  Неприменимость снимает гейт **обязательности**, но не **корректности**.

> **Почему не критичностью.** Раньше «ещё не этот этап» кодировали занижением
> `criticality` до `media` у всех полей EX-17. Ложные `MISSING` это глушило —
> но заодно **маскировало настоящие**: при `family.present=true` пустой
> `family.passport_number` давал `OK`. `criticality` статична, а обязательность
> зависит от **состояния кейса**; смешивать их — значит терять одно из двух.
> Теперь критичность честная, а состояние решает `applies_when`.

> `case.resolution_notified` записывает `/dnv-tie` — он и так спрашивает дату
> уведомления, нового вопроса не появилось. Инвариант «ключ `applies_when`
> объявлен в схеме профиля» проверяет `engine/scripts/check_namespace.py`:
> гейт на необъявленном ключе не сработал бы никогда, и это хуже отсутствия
> гейта.

## Зачем нужен реестр

1. **Генерация** (`dnv-documents`): движок берёт значение по `profile_key`
   из `user/case-profile.json` и подставляет в форму. Значение поля = значение
   профиля; ничего не выдумывается.
2. **Исчерпывающая верификация** (`field-qa-reviewer`): по реестру перечисляется
   **каждое** поле, для каждого — вердикт. Out-of-domain ловится механически
   (контролируемый словарь).

## Канонический namespace ключей

`profile_key` — общий namespace со схемой профиля. Инвариант: **каждый
`profile_key` реестра существует в схеме профиля** (проверяется
`engine/scripts/check_namespace.py`).

Префиксы: `applicant.*` (titular), `family.*` (член семьи), `work.*`
(работа/доход), `tasa.*` (поля tasa, не персональные).

## Контролируемые словари (домены)

| Домен | Допустимые значения |
|---|---|
| `sexo` | **Hombre**, **Mujer** |
| `estado_civil` | Soltero/a, Casado/a, Viudo/a, Divorciado/a, Separado/a |
| `tipo_solicitud` | INICIAL, RENOVADA |
| `parentesco` | Cónyuge, Pareja, Hijo/a, Ascendiente |

> **Урок реального прогона:** поле `Sexo` было оставлено пустым / `indefinido`
> вместо `Hombre`. Поэтому `sexo` — контролируемый словарь, а field-QA обязана
> вынести вердикт по нему явно (молчание = бага ревью).

## MI-T (titular)

| Поле | Тип | Домен | profile_key | Крит. | Частые ошибки | Origin |
|---|---|---|---|---|---|---|
| Primer apellido | text | free | applicant.last_name | alta | совпадение с паспортом | generic |
| Segundo apellido | text | free | applicant.second_last_name | media | нет второй фамилии → пусто | generic |
| Nombre | text | free | applicant.first_name | alta | совпадение с паспортом | generic |
| **Sexo** | enum | **sexo** | applicant.sexo | alta | **пусто/indefinido — ошибка; Hombre/Mujer** | generic |
| Fecha de nacimiento | date | free | applicant.birth_date | alta | формат DD/MM/AAAA | generic |
| Lugar de nacimiento | text | free | applicant.birth_place | media | город как в паспорте | generic |
| País de nacimiento | text | free | applicant.birth_country | media | | generic |
| Nacionalidad | text | free | applicant.nationality | alta | | generic |
| Estado civil | enum | estado_civil | applicant.marital_status | media | Casado/a при cónyuge | generic |
| N.I.E. | text | free | applicant.nie | alta | формат [XYZ]NNNNNNN[L]; транспозиция цифр | generic |
| Nº pasaporte | text | free | applicant.passport_number | alta | | generic |
| Domicilio en España | text | free | applicant.address_full | alta | совпадение с empadronamiento | generic |
| TELETRABAJADOR DE CARÁCTER INTERNACIONAL | checkbox | **fixed_checked** | applicant.permit_type | alta | нужна именно эта галочка; в лист идёт `☑ отметить — <значение>` | case_derived |
| INICIAL / RENOVADA | enum | tipo_solicitud | applicant.tipo_solicitud | alta | продление → RENOVADA | generic |
| Correo notificaciones | text | free | applicant.email | media | | generic |
| Teléfono | text | free | applicant.phone | baja | | generic |

## MI-F (familiar)

| Поле | Тип | Домен | profile_key | Крит. | Частые ошибки | Origin |
|---|---|---|---|---|---|---|
| Primer apellido | text | free | family.last_name | alta | | generic |
| Nombre | text | free | family.first_name | alta | | generic |
| **Sexo** | enum | **sexo** | family.sexo | alta | не пусто; Hombre/Mujer | generic |
| Fecha de nacimiento | date | free | family.birth_date | alta | DD/MM/AAAA | generic |
| Nacionalidad | text | free | family.nationality | alta | | generic |
| N.I.E. | text | free | family.nie | alta | | generic |
| Nº pasaporte | text | free | family.passport_number | alta | | generic |
| Parentesco con el titular | enum | parentesco | family.relationship | alta | Cónyuge vs Pareja — по актуальному статусу | case_derived |
| Nº registro solicitud del titular | text | free | family.titular_regage | alta | вписать REGAGE titular после подачи; НЕ выдумывать | case_derived |
| INICIAL / RENOVADA | enum | tipo_solicitud | family.tipo_solicitud | alta | | generic |

## EX-17 (TIE — titular; заполняется ПОСЛЕ concesión)

Форма последней мили: с ней идут сдавать отпечатки. Заполняется не в
`/dnv-documents`, а в `/dnv-tie`, когда одобрение уже получено.

> `applies_when: case.resolution_notified` — до резолюции форма не применяется.

> **Практика расходится: EX-17 или MI-TIE.** Часть отделений берёт EX-17, и
> распространённый совет в сообществе — принести обе. Движок фиксирует
> расхождение как расхождение и не выбирает за пользователя; см.
> `../norms/tie-huellas.md`.

| Поле | Тип | Домен | profile_key | Крит. | Частые ошибки | Origin |
|---|---|---|---|---|---|---|
| Primer apellido | text | free | applicant.last_name | alta | совпадение с паспортом и с поданной MI-T | generic |
| Segundo apellido | text | free | applicant.second_last_name | media | нет второй фамилии → пусто | generic |
| Nombre | text | free | applicant.first_name | alta | | generic |
| **Sexo** | enum | **sexo** | applicant.sexo | alta | галочка есть в данных, но не рисуется частью просмотрщиков PDF | generic |
| Fecha de nacimiento | date | free | applicant.birth_date | alta | DD/MM/AAAA | generic |
| Lugar de nacimiento | text | free | applicant.birth_place | media | **реальная ошибка прогона: вписан телефон** — соседнее поле бланка | generic |
| País de nacimiento | text | free | applicant.birth_country | media | | generic |
| **Nombre del padre** | text | free | applicant.father_name | **alta** | в MI-T поля не было → в профиле может быть пусто; добирается в `/dnv-tie`. Пусто до резолюции не штрафуется (`applies_when`), после — штрафуется | generic |
| **Nombre de la madre** | text | free | applicant.mother_name | **alta** | то же | generic |
| Nacionalidad | text | free | applicant.nationality | alta | форма страны vs форма гражданства — держать одинаково во всех формах пакета | generic |
| Estado civil | enum | estado_civil | applicant.marital_status | media | см. Sexo (отрисовка галочки) | generic |
| N.I.E. | text | free | applicant.nie | alta | транспозиция цифр | generic |
| Nº pasaporte | text | free | applicant.passport_number | alta | **реальная ошибка прогона: номер устаревшего паспорта** | generic |
| Domicilio en España | text | free | applicant.address_full | alta | отпечатки не в провинции адреса заявки → сверить с отделением; иногда просят падрон | generic |
| Teléfono | text | free | applicant.phone | baja | | generic |
| Correo electrónico | text | free | applicant.email | media | | generic |
| TIE: INICIAL / RENOVADA | enum | tipo_solicitud | applicant.tipo_solicitud | alta | связано с выбором эпиграфа tasa 790-012 | generic |
| **DIRIGIDA A (provincia/comisaría)** | text | free | applicant.comisaria_provincia | alta | отделение, где реально взята запись — не обязательно провинция домициля | case_derived |

## EX-17-familiar (TIE — член семьи)

Та же форма на члена семьи; заполняется, **только если он подавался**.

> `applies_when: case.resolution_notified` **+** `family.present` — нужны оба.

| Поле | profile_key | Крит. |
|---|---|---|
| Primer apellido | `family.last_name` | alta |
| Nombre | `family.first_name` | alta |
| Sexo | `family.sexo` | alta |
| Fecha de nacimiento | `family.birth_date` | alta |
| Lugar de nacimiento | `family.birth_place` | media |
| País de nacimiento | `family.birth_country` | media |
| Nombre del padre | `family.father_name` | alta |
| Nombre de la madre | `family.mother_name` | alta |
| Nacionalidad | `family.nationality` | alta |
| Estado civil | `family.marital_status` | media |
| N.I.E. | `family.nie` | alta |
| **Nº pasaporte** | `family.passport_number` | **alta** |
| Domicilio en España | `family.address_full` | alta |
| Teléfono | `family.phone` | baja |
| Correo electrónico | `family.email` | media |
| TIE: INICIAL / RENOVADA | `family.tipo_solicitud` | alta |

> **Здесь была найденная ревью маскировка.** Раньше *все* поля этой формы стояли
> `media` — чтобы пустая семейная ветка не сыпала ложными `MISSING`. Побочный
> эффект: при `family.present=true` **настоящий** пропуск (пустой
> `family.passport_number`) тоже давал `OK`. Теперь критичность парная MI-F и
> EX-17 титулара, а «ещё не этот этап» / «семьи нет» выражено через
> `applies_when` — у **обеих** семейных форм, MI-F с 2026-07 (см. выше).

## Tasa (Modelo 790)

> **Четыре формы, а не две.** Пошлина платится **отдельным бланком на каждого
> заявителя** (sujeto pasivo — `los solicitantes de cada autorización`), поэтому
> у 790-038 и 790-012 есть парные `-familiar`, гейтованные `family.present`.
> Соло-заявителю парные формы не применяются никогда.

### `tasa-790-038` — титуляр (на подачу)

| Поле | profile_key | Крит. | Примечание |
|---|---|---|---|
| Apellidos y nombre / Razón social | applicant.full_name | alta | плательщик = сам заявитель, а не тот, кто фактически платит картой |
| N.I.E. | applicant.nie | alta | на первичной подаче NIE может отсутствовать → `[ТРЕБУЕТСЯ]`, не выдумка |
| Epígrafe / autoliquidación | tasa.epigrafe_038 | alta | **сверить строку отдельно для каждого заявителя**; сумма меняется — вживую |
| Importe | tasa.importe_038 | media | меняется ежегодно |

### `tasa-790-038-familiar` — член семьи (`applies_when: family.present`)

| Поле | profile_key | Крит. | Примечание |
|---|---|---|---|
| Apellidos y nombre / Razón social | **family.full_name** | alta | ⚠️ плательщик = **член семьи**, НЕ титуляр. Оба бланка на титуляра — типовая ошибка, один платёж не засчитывается |
| N.I.E. | **family.nie** | alta | свой NIE члена семьи |
| Epígrafe / autoliquidación | tasa.epigrafe_038 | alta | подставляется та же строка, что титуляру (различия дословный источник не устанавливает) — **проверить на бланке** |
| Importe | tasa.importe_038 | media | **второй платёж**, а не половина общего |

### `tasa-790-012` — титуляр (TIE, после concesión)

| Поле | profile_key | Крит. | Примечание |
|---|---|---|---|
| Apellidos y nombre | applicant.full_name | alta | плательщик = тот, на кого выдаётся карта |
| N.I.E. | applicant.nie | alta | к этому этапу NIE уже присвоен резолюцией — пусто здесь это настоящий пропуск |
| Domicilio | applicant.address_full | media | адрес заявки vs падрона — практика расходится, сверить с отделением |
| **Epígrafe** | tasa.epigrafe_012 | alta | **RENOVACIÓN и primera concesión — разные строки с разными суммами**; подставленная сумма это и проверяет |
| Importe | tasa.importe_012 | media | меняется — вживую |

### `tasa-790-012-familiar` — член семьи (`applies_when: case.resolution_notified + family.present`)

| Поле | profile_key | Крит. | Примечание |
|---|---|---|---|
| Apellidos y nombre | **family.full_name** | alta | карту выдают ему — бланк на титуляра не засчитается |
| N.I.E. | **family.nie** | alta | NIE, присвоенный **его** резолюцией |
| Domicilio | **family.address_full** | media | обычно совпадает с адресом титуляра |
| **Epígrafe** | tasa.epigrafe_012 | alta | та же строка, что титуляру — **проверить на бланке** |
| Importe | tasa.importe_012 | media | второй платёж |

> ⚠️ **038, а не 052 — и это не опечатка.** Код tasa определяется тем, **какой
> орган трамитирует**, а не типом разрешения. Авторизацию по **Ley 14/2013**
> (movilidad internacional) резолвит **UGE-CE** → код **790-038**, платится через
> `sede.inclusion.gob.es`. Код **790-052** — общая экстранхерия через **Oficinas de
> Extranjería / Delegaciones del Gobierno**; в этом пайплайне он легитимен **только
> для `autorización de regreso`** (см. `../norms/tie-huellas.md`). Карта кодов с
> официальными якорями — `../sources/primary/tasas-790.md`.
>
> До 2026-07 реестр называл авторизационную tasa `790-052`. Это было неверно.
> Ключи профиля переименованы `tasa.epigrafe_052` / `tasa.importe_052` →
> **`tasa.epigrafe_038` / `tasa.importe_038`** — **ломающее переименование без
> алиаса**: если у вас есть заполненный `user/case-profile.json` прежней версии,
> переименуйте эти два ключа руками, иначе `dnv-documents` не найдёт значения.

## Memoria / carta explicativa (свободный текст)

Питается из `user/spec.md`: основание (Ley 14/2013, art. 74 bis–quinquies),
описание роли (согласовать с Certificate of services), обоснование дохода
(gross, €-эквивалент, выше порога), работодатель/заказчик (при смене названия —
пояснить amendment). Поля `work.*` + `applicant.permit_type`.
