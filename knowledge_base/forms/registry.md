# Реестр полей форм DNV (per-form field registry)

Машиночитаемая версия: **`registry.json`** (источник правды для генерации и
верификации). Этот файл — человекочитаемое зеркало.

> ⚠️ **Сверяйте ярлыки и эпиграфы с ТЕКУЩИМИ чистыми бланками** MI-T / MI-F /
> tasa (Modelo 790) — формы и суммы tasa меняются (R23, as-of 2026-06).
> `case_derived` = поле выведено из архетипа v1 (autónomo/контрактор + cónyuge);
> `generic` = применимо ко всем кейсам.

## Зачем нужен реестр

1. **Генерация** (`dnv-documents`): движок берёт значение по `profile_key`
   из `user/case-profile.json` и подставляет в форму. Значение поля = значение
   профиля; ничего не выдумывается.
2. **Исчерпывающая верификация** (`field-qa-reviewer`): по реестру перечисляется
   **каждое** поле, для каждого — вердикт. Out-of-domain ловится механически
   (контролируемый словарь).

## Канонический namespace ключей

`profile_key` — общий namespace со схемой профиля (U7). Инвариант: **каждый
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

## Tasa (Modelo 790)

| Форма | Поле | profile_key | Примечание |
|---|---|---|---|
| 790-052 (autorización) | Apellidos y nombre | applicant.full_name | плательщик = заявитель |
| 790-052 | N.I.E. | applicant.nie | |
| 790-052 | Epígrafe / Importe | tasa.epigrafe_052 / tasa.importe_052 | сумма меняется — проверить вживую |
| 790-012 (TIE, после concesión) | Apellidos y nombre / N.I.E. / Importe | applicant.full_name / applicant.nie / tasa.importe_012 | сумма меняется — проверить вживую |

## Memoria / carta explicativa (свободный текст)

Питается из `user/spec.md`: основание (Ley 14/2013, art. 74 bis–quinquies),
описание роли (согласовать с Certificate of services), обоснование дохода
(gross, €-эквивалент, выше порога), работодатель/заказчик (при смене названия —
пояснить amendment). Поля `work.*` + `applicant.permit_type`.
