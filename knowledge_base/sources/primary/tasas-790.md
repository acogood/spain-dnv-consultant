# Modelo 790 — карта кодов tasa (038 / 052 / 012)

> **Что это:** карта кодов tasa Modelo 790, релевантных процессу DNV, каждый со
> своим официальным якорем: **кто резолвит трамит** → **какой код** → **где
> платится**.
> **Источники (официальные страницы, не вторичные):**
> · 038 — https://sede.inclusion.gob.es/w/autorizaciones-de-trabajo-y-residencia-tasa-038
> · 052 — https://sede.administracionespublicas.gob.es/pagina/index/directorio/tasa052
> · 012 — https://sede.policia.gob.es/portalCiudadano/_es/tramites_extranjeria_tasas.php
> **Дата извлечения:** 2026-07-27
> **Режим:** справка по официальным страницам (не verbatim-текст нормы).

> ⚠️ **Сумм здесь нет намеренно.** Правило базы: цифры tasa не переносятся сюда
> даже из сходящихся между собой вторичных источников — вторичные источники
> переписывают друг друга, и согласие между ними ничего не подтверждает. Размеры установлены **Orden
> PJC/617/2025, de 13 de junio** (BOE-A-2025-12056, в силе с 16.06.2025, заменила
> Orden PRE/1803/2011) — действующую редакцию смотреть на BOE. Практичнее: выбрать
> эпиграф в бланке и **прочитать сумму, которую бланк подставит сам**; подставленная
> сумма — ещё и способ проверить, что выбрана нужная строка.

---

## Правило, по которому различаются коды

Код tasa определяется **не типом разрешения, а тем, какой орган трамитирует**.
Именно поэтому 038 и 052 легко перепутать: разрешения похожие, органы разные.

| Код | Кто трамитирует | Какое министерство | Где платится |
|---|---|---|---|
| **038** | **UGE-CE** (Unidad de Grandes Empresas y Colectivos Estratégicos) и Secretaría de Estado de Migraciones | Inclusión, Seguridad Social y Migraciones | `sede.inclusion.gob.es` → `expinterweb.inclusion.gob.es/Tasa038/` |
| **052** | **Oficinas de Extranjería** / Delegaciones y Subdelegaciones del Gobierno | Política Territorial | `sede.administracionespublicas.gob.es` |
| **012** | **Policía Nacional** (комиссарии) | Interior | `sede.policia.gob.es` |

---

## 790-038 — авторизация по Ley 14/2013 (movilidad internacional)

**Это код первичной подачи и продления DNV.** `[официальное разъяснение]`

Дословно со страницы `sede.inclusion.gob.es`:

> En este enlace puede rellenar y pagar electrónicamente el impreso de tasa 038,
> correspondiente a la tramitación de autorizaciones de residencia y trabajo para
> ciudadanos extranjeros resueltas por el Ministerio de Inclusión, Seguridad Social y
> Migraciones, así como sus **prórrogas, modificaciones y renovaciones**. En
> particular:
>
> - **Autorizaciones tramitadas por la Unidad de Grandes Empresas y Colectivos
>   Estratégicos**
> - Autorizaciones por circunstancias excepcionales resueltas por la Secretaría de
>   Estado de Migraciones
>
> Para autorizaciones tramitadas y resueltas por las oficinas de extranjería, debe
> obtener su tasa en la sede electrónica del Ministerio de Política Territorial y
> Función Pública […]
>
> Sujetos pasivos: Serán sujetos pasivos de las tasas las personas a cuyo favor se
> solicite la autorización de residencia (trabajador o su familiar) o de trabajo
> (empleador o empresario) según el artículo 46 de la Ley Orgánica 4/2000, de 11 de
> enero. **En autorizaciones de movilidad internacional, tendrán la consideración de
> sujetos pasivos los solicitantes de cada autorización conforme lo establecido en la
> Ley 14/2013, de 27 de septiembre, de apoyo a los emprendedores y su
> internacionalización.**

**Три вещи, которые эта страница решает:**

1. **Ley 14/2013 названа прямо** — режим teletrabajo идёт по 038, не по 052.
2. **Плательщик** = *el solicitante de cada autorización*. То есть при подаче с
   cónyuge — **своя tasa на каждого заявителя**, включая члена семьи (он «persona a
   cuyo favor se solicita»). `[официальное разъяснение]`
3. **Renovación тоже 038**: «así como sus prórrogas, modificaciones y renovaciones».

Служебные реквизиты: Unidad de Gestión — Dirección General de Migraciones;
Código SIA **201361**. Доступ к оплате — DNIe / certificado electrónico / Cl@ve.
Ссылка «Forma y lugar de pago» с этой же страницы ведёт на **BOE-A-2022-9028**.

> Функциональный адрес для вопросов по movilidad internacional указан на самой
> странице `sede.inclusion.gob.es` — здесь он не воспроизводится: правило репо
> требует, чтобы любой email в трекаемом файле был из зарезервированного диапазона
> RFC 2606, и институционального исключения из него нет.

## 790-052 — общая экстранхерия (в т. ч. autorización de regreso)

**Это НЕ код авторизации DNV.** `[официальное разъяснение]`

Дословно со страницы `sede.administracionespublicas.gob.es`:

> **Tasa 052:** Tramitación de autorizaciones de residencia y otra documentación a
> ciudadanos extranjeros.
>
> **ÓRGANO RESPONSABLE:** Delegaciones y Subdelegaciones del Gobierno

Бланк 790-052 содержит эпиграфы общей экстранхерии, среди них — **`i) Autorización
de regreso`**.

**Где 052 в процессе DNV встречается легитимно:** только на **autorización de
regreso**, потому что её выдаёт не UGE-CE, а Delegación/Subdelegación del Gobierno
или полиция (art. 5.4 RD 1155/2024 — см. `rd-1155-2024-extractos.md`).

> ⚠️ **И там код зависит от органа.** art. 5.4 перечисляет **несколько** выдающих
> органов, поэтому у regreso нет одного кода на все случаи: через **Oficina de
> Extranjería / Delegación** — **790-052**, через **Comisaría** — **790-012**.
> Практика различается по провинции: сверять, куда именно вы идёте, **до** оплаты —
> оплаченная не та tasa не возвращается. `[официальное разъяснение]`
> (проверить вживую). Разбор — `../../norms/tie-huellas.md`, на этапе TIE.

> ⚠️ **Исторический дефект базы.** До 2026-07 база называла tasa авторизации
> **790-052**. Это было неверно: авторизацию по Ley 14/2013 резолвит UGE-CE, значит
> код **038**. Все четыре AI-отчёта в `../reports/` называли 038 правильно —
> ошибка натекла в дистиллят, а не из отчётов. Ключи профиля переименованы
> `tasa.epigrafe_052` / `tasa.importe_052` → `…_038` (ломающее переименование, без
> алиаса). Употребление 790-052 для **regreso** при этом верно и оставлено как есть.

## 790-012 — выпуск TIE (после concesión)

**Код за физический выпуск карты**, платится перед сдачей отпечатков.
`[официальное разъяснение]`

- Орган — **Policía Nacional**; платится через `sede.policia.gob.es`.
- Эпиграфы **`RENOVACIÓN`** и **`primera concesión`** — **разные строки с разными
  суммами**. Выбор не косметический: подставленная бланком сумма — способ проверить,
  что взята нужная строка.
- Разбор этапа — `../../norms/tie-huellas.md`, на этапе TIE.

---

## Сводка для чеклиста

| Этап процесса | Код | Кому |
|---|---|---|
| Первичная подача (autorización, art. 74 quinquies) | **790-038** | на каждого заявителя, включая cónyuge |
| Продление (renovación) | **790-038** | на каждого заявителя |
| Выпуск TIE после concesión | **790-012** | на каждого, кому выпускается карта |
| Autorización de regreso (выезд во время рассмотрения) | **790-052** через Oficina de Extranjería / Delegación del Gobierno; **790-012**, если трамит идёт через Comisaría | на того, кто выезжает |

Профильные ключи (`knowledge_base/forms/registry.json`): `tasa.epigrafe_038` /
`tasa.importe_038`, `tasa.epigrafe_012` / `tasa.importe_012`. Оба помечены
`derived` + «(проверить вживую)» — движок их **не выдумывает**, оставляет
`[ТРЕБУЕТСЯ: …]`, пока пользователь не прочитает сумму с бланка.
