# Field-QA baseline (механический, исчерпывающий)

> Один вердикт на КАЖДОЕ поле реестра (count==полей). Проверяется корректность, не правдоподобие. Это must-have baseline; независимая ре-деривация и official-review — отдельные слои.

| Форма | Поле | Вердикт | Причина |
|---|---|---|---|
| MI-T | Primer apellido | ✅ OK |  |
| MI-T | Segundo apellido | ✅ OK | пусто в профиле и корректно помечено |
| MI-T | Nombre | ✅ OK |  |
| MI-T | Sexo | ✅ OK |  |
| MI-T | Fecha de nacimiento | ✅ OK |  |
| MI-T | Lugar de nacimiento | ✅ OK |  |
| MI-T | País de nacimiento | ✅ OK |  |
| MI-T | Nacionalidad | ✅ OK |  |
| MI-T | Estado civil | ✅ OK |  |
| MI-T | N.I.E. | ✅ OK |  |
| MI-T | Nº pasaporte | ✅ OK |  |
| MI-T | Domicilio en España | ✅ OK |  |
| MI-T | Tipo de autorización: TELETRABAJADOR DE CARÁCTER INTERNACIONAL | ✅ OK |  |
| MI-T | INICIAL / RENOVADA | ✅ OK |  |
| MI-T | Correo a efectos de notificaciones | ✅ OK |  |
| MI-T | Teléfono | ✅ OK |  |
| MI-F | Primer apellido | ✅ OK |  |
| MI-F | Nombre | ✅ OK |  |
| MI-F | Sexo | ✅ OK |  |
| MI-F | Fecha de nacimiento | ✅ OK |  |
| MI-F | Nacionalidad | ✅ OK |  |
| MI-F | N.I.E. | ✅ OK |  |
| MI-F | Nº pasaporte | ✅ OK |  |
| MI-F | Parentesco con el titular | ✅ OK |  |
| MI-F | Nº de registro de la solicitud del titular | ⚠️ MISSING | обязательное поле пусто в профиле |
| MI-F | INICIAL / RENOVADA | ✅ OK |  |
| tasa-790-052 | Apellidos y nombre / Razón social | ✅ OK |  |
| tasa-790-052 | N.I.E. | ✅ OK |  |
| tasa-790-052 | Epígrafe / autoliquidación | ⚠️ MISSING | обязательное поле пусто в профиле |
| tasa-790-052 | Importe | ✅ OK | пусто в профиле и корректно помечено |
| tasa-790-012 | Apellidos y nombre | ✅ OK |  |
| tasa-790-012 | N.I.E. | ✅ OK |  |
| tasa-790-012 | Domicilio | ✅ OK |  |
| tasa-790-012 | Epígrafe / autoliquidación (TIE) | ⚠️ MISSING | обязательное поле пусто в профиле |
| tasa-790-012 | Importe (TIE) | ✅ OK | пусто в профиле и корректно помечено |
| EX-17 | Primer apellido | ✅ OK |  |
| EX-17 | Segundo apellido | ✅ OK | пусто в профиле и корректно помечено |
| EX-17 | Nombre | ✅ OK |  |
| EX-17 | Sexo | ✅ OK |  |
| EX-17 | Fecha de nacimiento | ✅ OK |  |
| EX-17 | Lugar de nacimiento | ✅ OK |  |
| EX-17 | País de nacimiento | ✅ OK |  |
| EX-17 | Nombre del padre | ✅ OK |  |
| EX-17 | Nombre de la madre | ✅ OK |  |
| EX-17 | Nacionalidad | ✅ OK |  |
| EX-17 | Estado civil | ✅ OK |  |
| EX-17 | N.I.E. | ✅ OK |  |
| EX-17 | Nº pasaporte | ✅ OK |  |
| EX-17 | Domicilio en España | ✅ OK |  |
| EX-17 | Teléfono | ✅ OK |  |
| EX-17 | Correo electrónico | ✅ OK |  |
| EX-17 | TIE: INICIAL / RENOVADA | ✅ OK |  |
| EX-17 | DIRIGIDA A (provincia / comisaría) | ✅ OK |  |
| EX-17-familiar | Primer apellido | ✅ OK |  |
| EX-17-familiar | Nombre | ✅ OK |  |
| EX-17-familiar | Sexo | ✅ OK |  |
| EX-17-familiar | Fecha de nacimiento | ✅ OK |  |
| EX-17-familiar | Lugar de nacimiento | ✅ OK |  |
| EX-17-familiar | País de nacimiento | ✅ OK |  |
| EX-17-familiar | Nombre del padre | ✅ OK |  |
| EX-17-familiar | Nombre de la madre | ✅ OK |  |
| EX-17-familiar | Nacionalidad | ✅ OK |  |
| EX-17-familiar | Estado civil | ✅ OK |  |
| EX-17-familiar | N.I.E. | ✅ OK |  |
| EX-17-familiar | Nº pasaporte | ✅ OK |  |
| EX-17-familiar | Domicilio en España | ✅ OK |  |
| EX-17-familiar | Teléfono | ✅ OK |  |
| EX-17-familiar | Correo electrónico | ✅ OK |  |
| EX-17-familiar | TIE: INICIAL / RENOVADA | ✅ OK |  |
| memoria | Основание (teletrabajo, Ley 14/2013) | ✅ OK |  |
| memoria | Описание работы и роли | ✅ OK |  |
| memoria | Обоснование дохода (gross, EUR-эквивалент) | ✅ OK |  |
| memoria | Работодатель/заказчик | ✅ OK |  |

## Сводка

| Вердикт | Кол-во |
|---|---|
| OK | 70 |
| WRONG | 0 |
| MISSING | 3 |
| UNCERTAIN | 0 |
| **Всего полей** | **73** |