# Field-QA baseline (механический, исчерпывающий)

> Один вердикт на КАЖДОЕ поле реестра (count==полей). Проверяется корректность, не правдоподобие. Это must-have baseline; независимая ре-деривация и official-review — отдельные слои.

> **Как читать «Причина».** До «· реестр:» — вывод механической проверки. После — подсказка из реестра полей (`common_errors`), то есть **контекст, а не находка**: она объясняет, почему поле бывает пустым или что в нём путают. `MISSING` рядом с такой подсказкой может быть **корректным состоянием кейса** (например, `N.I.E.` на первичной подаче: требования предъявить NIE норма не устанавливает, а подачу подписывает представитель — art. 5 Ley 39/2015). Выдумывать значение нельзя ни в каком случае.

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
| MI-F | Nº de registro de la solicitud del titular | ⚠️ MISSING | обязательное поле пусто в профиле · реестр: связка дел: вписать REGAGE titular после его подачи; НЕ выдумывать |
| MI-F | INICIAL / RENOVADA | ✅ OK |  |
| tasa-790-038 | Apellidos y nombre / Razón social | ✅ OK |  |
| tasa-790-038 | N.I.E. | ✅ OK |  |
| tasa-790-038 | Epígrafe / autoliquidación | ⚠️ MISSING | обязательное поле пусто в профиле · реестр: выбрать верный эпиграф; сумма меняется — проверить вживую. Код 038 (НЕ 052): авторизацию по Ley 14/2013 резолвит UGE-CE. СВЕРЬТЕ СТРОКУ ОТДЕЛЬНО ДЛЯ КАЖДОГО ЗАЯВИТЕЛЯ: бланк на титуляра и бланк на члена семьи заполняются каждый сам по себе, и совпадение эпиграфа надо подтвердить, а не предположить |
| tasa-790-038 | Importe | ✅ OK | пусто в профиле и корректно помечено |
| tasa-790-038-familiar | Apellidos y nombre / Razón social | ✅ OK |  |
| tasa-790-038-familiar | N.I.E. | ✅ OK |  |
| tasa-790-038-familiar | Epígrafe / autoliquidación | ⚠️ MISSING | обязательное поле пусто в профиле · реестр: СВЕРЬТЕ СТРОКУ ОТДЕЛЬНО ДЛЯ КАЖДОГО ЗАЯВИТЕЛЯ. Реестр подставляет сюда тот же эпиграф, что и титуляру, потому что дословный источник различия не устанавливает; если на бланке видите, что для члена семьи строка своя — берите её, а не подставленную |
| tasa-790-038-familiar | Importe | ✅ OK | пусто в профиле и корректно помечено |
| tasa-790-012 | Apellidos y nombre | ✅ OK |  |
| tasa-790-012 | N.I.E. | ✅ OK |  |
| tasa-790-012 | Domicilio | ✅ OK |  |
| tasa-790-012 | Epígrafe / autoliquidación (TIE) | ⚠️ MISSING | обязательное поле пусто в профиле · реестр: RENOVACIÓN и primera concesión — РАЗНЫЕ строки с разными суммами; подставленная формой сумма — способ проверить, что выбрана нужная строка. СВЕРЬТЕ СТРОКУ ОТДЕЛЬНО ДЛЯ КАЖДОГО ЗАЯВИТЕЛЯ |
| tasa-790-012 | Importe (TIE) | ✅ OK | пусто в профиле и корректно помечено |
| tasa-790-012-familiar | Apellidos y nombre | ✅ OK |  |
| tasa-790-012-familiar | N.I.E. | ✅ OK |  |
| tasa-790-012-familiar | Domicilio | ✅ OK |  |
| tasa-790-012-familiar | Epígrafe / autoliquidación (TIE) | ⚠️ MISSING | обязательное поле пусто в профиле · реестр: СВЕРЬТЕ СТРОКУ ОТДЕЛЬНО ДЛЯ КАЖДОГО ЗАЯВИТЕЛЯ. Реестр подставляет ту же строку, что и титуляру; если на бланке для члена семьи строка своя — берите её |
| tasa-790-012-familiar | Importe (TIE) | ✅ OK | пусто в профиле и корректно помечено |
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
| OK | 77 |
| WRONG | 0 |
| MISSING | 5 |
| UNCERTAIN | 0 |
| **Всего полей** | **82** |