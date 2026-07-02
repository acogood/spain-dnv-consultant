# Field-QA baseline (механический, исчерпывающий)

> Один вердикт на КАЖДОЕ поле реестра (count==полей). Проверяется корректность, не правдоподобие. Это must-have baseline; независимая ре-деривация и official-review — отдельные слои.

| Форма | Поле | Вердикт | Причина |
|---|---|---|---|
| MI-T | Primer apellido | ✅ OK |  |
| MI-T | Segundo apellido | ✅ OK | пусто в профиле и корректно помечено |
| MI-T | Nombre | ✅ OK |  |
| MI-T | Sexo | ❌ WRONG | не совпадает: черновик 'Mujer' ≠ профиль 'Hombre' |
| MI-T | Fecha de nacimiento | ✅ OK |  |
| MI-T | Lugar de nacimiento | ✅ OK |  |
| MI-T | País de nacimiento | ✅ OK |  |
| MI-T | Nacionalidad | ✅ OK |  |
| MI-T | Estado civil | ✅ OK |  |
| MI-T | N.I.E. | ❌ WRONG | не совпадает: черновик 'X9099999R' ≠ профиль 'X9999999R' |
| MI-T | Nº pasaporte | ✅ OK |  |
| MI-T | Domicilio en España | ✅ OK |  |
| MI-T | Tipo de autorización: TELETRABAJADOR DE CARÁCTER INTERNACIONAL | ✅ OK |  |
| MI-T | INICIAL / RENOVADA | ✅ OK |  |
| MI-T | Correo a efectos de notificaciones | ✅ OK |  |
| MI-T | Teléfono | ✅ OK |  |
| MI-F | Primer apellido | ✅ OK |  |
| MI-F | Nombre | ✅ OK |  |
| MI-F | Sexo | ❌ WRONG | вне домена sexo: 'indefinido' ∉ ['Hombre', 'Mujer'] |
| MI-F | Fecha de nacimiento | ✅ OK |  |
| MI-F | Nacionalidad | ✅ OK |  |
| MI-F | N.I.E. | ✅ OK |  |
| MI-F | Nº pasaporte | ✅ OK |  |
| MI-F | Parentesco con el titular | ✅ OK |  |
| MI-F | Nº de registro de la solicitud del titular | ❌ WRONG | профиль пуст, но в черновике значение 'ВЫДУМАННЫЙ-НОМЕР-000' (галлюцинация) |
| MI-F | INICIAL / RENOVADA | ✅ OK |  |
| tasa-790-052 | Apellidos y nombre / Razón social | ✅ OK |  |
| tasa-790-052 | N.I.E. | ✅ OK |  |
| tasa-790-052 | Epígrafe / autoliquidación | ⚠️ MISSING | обязательное поле пусто в профиле |
| tasa-790-052 | Importe | ✅ OK | пусто в профиле и корректно помечено |
| tasa-790-012 | Apellidos y nombre | ✅ OK |  |
| tasa-790-012 | N.I.E. | ✅ OK |  |
| tasa-790-012 | Importe (TIE) | ✅ OK | пусто в профиле и корректно помечено |
| memoria | Основание (teletrabajo, Ley 14/2013) | ✅ OK |  |
| memoria | Описание работы и роли | ✅ OK |  |
| memoria | Обоснование дохода (gross, EUR-эквивалент) | ✅ OK |  |
| memoria | Работодатель/заказчик | ✅ OK |  |

## Сводка

| Вердикт | Кол-во |
|---|---|
| OK | 32 |
| WRONG | 4 |
| MISSING | 1 |
| UNCERTAIN | 0 |
| **Всего полей** | **37** |