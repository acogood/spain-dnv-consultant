# Реестр полей форм DNV (per-form field registry)

Машиночитаемая версия: **`registry.json`** (источник правды для генерации и
верификации). Этот файл — человекочитаемое зеркало.

> ⚠️ **Сверяйте ярлыки и эпиграфы с ТЕКУЩИМИ чистыми бланками** MI-T / MI-F /
> EX-17 / tasa (Modelo 790) — формы и суммы tasa меняются (as-of 2026-07).
> `case_derived` = поле выведено из архетипа v1 (autónomo/контрактор + cónyuge);
> `generic` = применимо ко всем кейсам.

**Когда какая форма.** MI-T/MI-F, tasa 790-052 и memoria — на подачу
(`/dnv-documents`). EX-17 и tasa 790-012 — уже **после** одобрения, на сдачу
отпечатков (`/dnv-tie`): до concesión заполнять их нечем и незачем.

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
| TELETRABAJADOR DE CARÁCTER INTERNACIONAL | checkbox | fixed | applicant.permit_type | alta | нужна именно эта галочка | case_derived |
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
| **Nombre del padre** | text | free | applicant.father_name | media | в MI-T поля не было → в профиле может быть пусто; добирается в `/dnv-tie` | generic |
| **Nombre de la madre** | text | free | applicant.mother_name | media | то же | generic |
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

Та же форма на члена семьи; заполняется, **только если он подавался**. Все поля
`media`: при `family.present=false` профиль по ним пуст, черновик ставит
`[ТРЕБУЕТСЯ]`, и field-QA считает это корректной пометкой, а не пропуском.

`family.last_name`, `family.first_name`, `family.sexo`, `family.birth_date`,
`family.birth_place`, `family.birth_country`, `family.father_name`,
`family.mother_name`, `family.nationality`, `family.marital_status`,
`family.nie`, `family.passport_number`, `family.address_full`, `family.phone`,
`family.email`, `family.tipo_solicitud`.

## Tasa (Modelo 790)

| Форма | Поле | profile_key | Примечание |
|---|---|---|---|
| 790-052 (autorización) | Apellidos y nombre | applicant.full_name | плательщик = заявитель |
| 790-052 | N.I.E. | applicant.nie | |
| 790-052 | Epígrafe / Importe | tasa.epigrafe_052 / tasa.importe_052 | сумма меняется — проверить вживую |
| 790-012 (TIE, после concesión) | Apellidos y nombre / N.I.E. / Domicilio | applicant.full_name / applicant.nie / applicant.address_full | какой адрес — практика расходится, сверить с отделением |
| 790-012 | **Epígrafe** | tasa.epigrafe_012 | **RENOVACIÓN и primera concesión — разные строки с разными суммами**; подставленная формой сумма это и проверяет |
| 790-012 | Importe | tasa.importe_012 | сумма меняется — проверить вживую |

## Memoria / carta explicativa (свободный текст)

Питается из `user/spec.md`: основание (Ley 14/2013, art. 74 bis–quinquies),
описание роли (согласовать с Certificate of services), обоснование дохода
(gross, €-эквивалент, выше порога), работодатель/заказчик (при смене названия —
пояснить amendment). Поля `work.*` + `applicant.permit_type`.
