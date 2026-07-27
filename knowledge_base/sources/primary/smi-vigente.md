# SMI действующий — RD 126/2026 (extract)

> **Акт:** Real Decreto 126/2026, de 18 de febrero, por el que se fija el salario
> mínimo interprofesional para 2026.
> **BOE:** BOE-A-2026-3815 · «BOE» núm. 44, de 19 de febrero de 2026
> **ELI:** https://www.boe.es/eli/es/rd/2026/02/18/126
> **Консолидированный текст:** https://www.boe.es/buscar/act.php?id=BOE-A-2026-3815
> **В силе с:** 20.02.2026 · estatus derogación: N
> **Дата извлечения:** 2026-07-27
> **Режим:** **extract** — art. 1 и art. 3.1 дословно (те, что нужны для порога).
> Полный текст RD — по ссылке; там же arts. 2, 4 (комплементы, срочные договоры,
> домработники) — к порогу DNV отношения не имеют.

> ⚠️ **SMI меняется ежегодно** — как правило в первом квартале, с обратной силой
> или без. RD 126/2026 подписан 18.02.2026, опубликован 19.02.2026 (это и есть та
> дата «19 февраля», которую называет публичный консультант в
> `../youtube-consultant/vyros-trebuemyj-dohod.md`). **Перед подачей — проверить,
> не вышел ли RD на следующий год.** Формула порога (200 / 75 / 25 %) при этом не
> меняется: она в `instruccion-conjunta-2023.md`, инструкция Tercera.

---

## Artículo 1. Cuantía del salario mínimo interprofesional.

> El salario mínimo para cualesquiera actividades en la agricultura, en la industria
> y en los servicios, sin distinción de sexo ni edad de las personas trabajadoras,
> queda fijado en 40,70 euros/día o 1 221 euros/mes, según el salario esté fijado
> por días o por meses.
>
> En el salario mínimo se computa únicamente la retribución en dinero, sin que el
> salario en especie pueda, en ningún caso, dar lugar a la minoración de la cuantía
> íntegra en dinero de aquel.
>
> Este salario se entiende referido a la jornada legal de trabajo en cada actividad,
> sin incluir en el caso del salario diario la parte proporcional de los domingos y
> festivos. Si se realizase jornada inferior se percibirá a prorrata.
>
> **Para la aplicación en cómputo anual del salario mínimo se tendrán en cuenta las
> reglas sobre compensación que se establecen en los artículos siguientes.**

## Artículo 3.1. Compensación y absorción (годовая величина).

> 1. La revisión del salario mínimo interprofesional establecida en este real decreto
> no afectará a la estructura ni a la cuantía de los salarios profesionales que
> viniesen percibiendo las personas trabajadoras cuando tales salarios en su conjunto
> y en cómputo anual fuesen superiores a dicho salario mínimo.
>
> A tales efectos, el salario mínimo en cómputo anual que se tomará como término de
> comparación será el resultado de adicionar al salario mínimo fijado en el artículo
> 1 de este real decreto los devengos a que se refiere el artículo 2, **sin que en
> ningún caso pueda considerarse una cuantía anual inferior a 17 094 euros**.

**Две цифры, и обе из нормы:**

| Величина | Значение | Где в акте | Тег |
|---|---|---|---|
| SMI месячный (при оплате по месяцам) | **1.221 €/мес** | art. 1 | `[норма]` |
| SMI **годовой** (минимум для годового расчёта) | **17.094 €/год** | art. 3.1 | `[норма]` |

> 17.094 = 1.221 × 14 — это **14 выплат** (12 месячных + 2 pagas
> extraordinarias). Годовая цифра **стоит в самом акте**, её не нужно выводить
> умножением: art. 3.1 называет её прямо.

---

## Производная таблица: порог дохода DNV

> ⚠️ **Эта таблица — производная, не норма.** Норма — две цифры выше (art. 1,
> art. 3.1) и проценты из `instruccion-conjunta-2023.md` (Tercera). Всё, что
> ниже, — арифметика над ними.

**Шаг, который решает всё:** какую месячную величину SMI подставлять в «200 %».
Инструкция говорит «cantidad que represente **mensualmente** el 200% del SMI» и
величину не уточняет. Применяется **годовой SMI ÷ 12**:

```
17 094 € / год  ÷  12  =  1 424,50 € / мес   ← месячная база порога
```

| Категория | Расчёт | Порог |
|---|---|---|
| Титуляр (200 %) | 1 424,50 × 2 | **2 849,00 €/мес** |
| + второй человек (+75 %) | 1 424,50 × 0,75 = 1 068,375 | **+1 068,38 €/мес** |
| **Итого семья из двоих** | 2 849,00 + 1 068,375 = 3 917,375 | **3 917,38 €/мес** |
| + каждый следующий (+25 %) | 1 424,50 × 0,25 = 356,125 | **+356,13 €/мес** |
| Семья из трёх (для сверки) | 3 917,375 + 356,125 = 4 273,50 | **4 273,50 €/мес** |

**Независимое подтверждение.** Публичный консультант на 30.03.2026 называет
**2.850 / 3.920 / +356 / 4.275** (`../youtube-consultant/vyros-trebuemyj-dohod.md`,
раздел с суммами) — это те же величины, округлённые вверх до десятков. Совпадение
подтверждает выбор базы (годовой ÷ 12), а не месячной цифры art. 1.
`[практика — консультант]`

> ⚠️ **Почему НЕ 1.221 × 200 % = 2.442.** Если подставить месячную цифру art. 1
> напрямую, получается 2.442 €/мес и 3.357,75 € на двоих — и это **та ошибка,
> которая жила в `../../norms/umbral-ingresos.md` до 2026-07**. 1.221 — это
> месячная ставка при **14** выплатах; чтобы получить месячный эквивалент
> годового минимума, годовую сумму делят на **12**, а не берут 14-паговую
> месячную. Разница — 407 €/мес на титуляра и ~560 €/мес на семью из двоих:
> достаточно, чтобы кейс, поданный по заниженному порогу, получил requerimiento
> или отказ.

**Уровни датированности разные — и это принципиально:**

| Слой | Стабильность | Тег |
|---|---|---|
| Проценты 200 / 75 / 25 | стабильны с 2023 (Instrucción, Tercera) | `[официальное разъяснение]` |
| Годовой ÷ 12 как база | применение UGE; в тексте инструкции не прописано | `[официальное разъяснение]` / `[практика — консультант]` |
| Сумма SMI (1.221 / 17.094) | **меняется ежегодно** — as-of 2026-02 | `[норма]` (проверить вживую) |
| Итоговые 2.849 / 3.917,38 / 356,13 | производные от строки выше | производное (проверить вживую) |

Разбор для пользователя — `../../norms/umbral-ingresos.md`.
