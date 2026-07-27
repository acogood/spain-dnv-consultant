# Ley 39/2015 — общая административная процедура (extract)

> **Акт:** Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de
> las Administraciones Públicas.
> **BOE:** BOE-A-2015-10565
> **Консолидированный текст:** https://www.boe.es/buscar/act.php?id=BOE-A-2015-10565
> **Дата извлечения:** 2026-07-27
> **Режим:** **extract** — пять статей, на которые движок якорится: 5 и 6
> (представительство и REA), 15 (язык), 21 (обязанность резолвить), 30 (счёт сроков).

Ley 39/2015 применяется к процедуре DNV **как общий закон**: Ley 14/2013 задаёт
специальные правила (20 дней, silencio positivo), а всё, чего она не говорит, идёт
отсюда. Инструкция conjunta ссылается на эту же Ley 39/2015 прямо — в Octava ¶ 1
(язык) и Séptima ¶ 1 (art. 28, оригиналы документов).

---

## Artículo 30. Cómputo de plazos.

> 1. Salvo que por Ley o en el Derecho de la Unión Europea se disponga otro cómputo,
> cuando los plazos se señalen por horas, se entiende que éstas son hábiles. Son
> hábiles todas las horas del día que formen parte de un día hábil.
>
> […]
>
> 2. **Siempre que por Ley o en el Derecho de la Unión Europea no se exprese otro
> cómputo, cuando los plazos se señalen por días, se entiende que éstos son hábiles,
> excluyéndose del cómputo los sábados, los domingos y los declarados festivos.**
>
> Cuando los plazos se hayan señalado por días naturales por declararlo así una ley o
> por el Derecho de la Unión Europea, se hará constar esta circunstancia en las
> correspondientes notificaciones.
>
> 3. Los plazos expresados en días se contarán a partir del día siguiente a aquel en
> que tenga lugar la notificación o publicación del acto de que se trate, o desde el
> siguiente a aquel en que se produzca la estimación o la desestimación por silencio
> administrativo.
>
> 4. Si el plazo se fija en meses o años, éstos se computarán a partir del día
> siguiente a aquel en que tenga lugar la notificación o publicación del acto de que se
> trate, o desde el siguiente a aquel en que se produzca la estimación o desestimación
> por silencio administrativo.
>
> El plazo concluirá el mismo día en que se produjo la notificación, publicación o
> silencio administrativo en el mes o el año de vencimiento. Si en el mes de
> vencimiento no hubiera día equivalente a aquel en que comienza el cómputo, se
> entenderá que el plazo expira el último día del mes.
>
> 5. Cuando el último día del plazo sea inhábil, se entenderá prorrogado al primer día
> hábil siguiente.
>
> 6. Cuando un día fuese hábil en el municipio o Comunidad Autónoma en que residiese el
> interesado, e inhábil en la sede del órgano administrativo, o a la inversa, se
> considerará inhábil en todo caso.
>
> 7. La Administración General del Estado y las Administraciones de las Comunidades
> Autónomas, con sujeción al calendario laboral oficial, fijarán, en su respectivo
> ámbito, el calendario de días inhábiles a efectos de cómputos de plazos. […]

**Это статья, снимающая неоднозначность «20 días» в art. 76 Ley 14/2013.**

| Формулировка в норме | Как считать | Почему |
|---|---|---|
| art. 76 Ley 14/2013: «veinte días» — **без** слова `naturales` | **20 días hábiles** | ¶ 2: если закон не сказал иного, дни — hábiles; суббота, воскресенье и праздники **исключаются** |
| art. 74 quater.3: «sesenta días **naturales**» | 60 календарных | сказано `naturales` прямо |
| art. 76.3: «noventa días posteriores» — без уточнения | ⚠️ формально hábiles по ¶ 2; на практике «хвост» считают календарными | расхождение реальное — **(проверить вживую)** |
| art. 209 RD 1155/2024: «plazo de un mes» | по ¶ 4 — «от дня, следующего за…», и заканчивается тем же числом следующего месяца | срок в месяцах, не в днях |

**Практические следствия для арифметики движка:**

- 20 días hábiles — это примерно **4 календарные недели**, а не 20 дней. Праздничные
  календари (¶ 7) публикуются заранее и **различаются по автономиям**; ¶ 6 добавляет:
  если день нерабочий либо у заявителя, либо у органа — он нерабочий **в любом
  случае**.
- ¶ 5: если последний день срока нерабочий — срок сдвигается на **первый следующий
  рабочий**. Никогда не «истекает в субботу».
- ¶ 3: отсчёт с **дня, следующего** за уведомлением, а не с самого дня.

> ⚠️ Движок **не считает** праздничные календари сам — он не знает автономию и год
> публикации календаря. Поэтому любая дата silencio, посчитанная как «подача + 20
> календарных», в `user/tracking.md` помечается как **ориентир**, а точную дату
> заявитель сверяет по календарю inhábiles своей автономии. См.
> `../../norms/plazos-silencio.md`.

## Artículo 21. Obligación de resolver (извлечение).

> 1. La Administración está obligada a dictar resolución expresa y a notificarla en
> todos los procedimientos cualquiera que sea su forma de iniciación.
>
> […]
>
> 2. El plazo máximo en el que debe notificarse la resolución expresa será el fijado por
> la norma reguladora del correspondiente procedimiento.
>
> Este plazo no podrá exceder de seis meses salvo que una norma con rango de Ley
> establezca uno mayor o así venga previsto en el Derecho de la Unión Europea.
>
> 3. Cuando las normas reguladoras de los procedimientos no fijen el plazo máximo, éste
> será de tres meses. Este plazo y los previstos en el apartado anterior se contarán:
>
> a) En los procedimientos iniciados de oficio, desde la fecha del acuerdo de
> iniciación.
>
> b) **En los iniciados a solicitud del interesado, desde la fecha en que la solicitud
> haya tenido entrada en el registro electrónico de la Administración u Organismo
> competente para su tramitación.**

**¶ 3.b — точка отсчёта.** Срок тикает с **даты входа заявления в электронный
реестр компетентного органа**. Для DNV это ровно та дата, которая стоит в
**REGAGE**-квитанции; art. 76 Ley 14/2013 говорит то же своими словами («desde la
presentación electrónica de la solicitud en el órgano competente»). Поэтому
`dnv-tracking` считает срок от даты REGAGE, а не от даты отправки документов.
`[норма]`

## Artículo 15. Lengua de los procedimientos (извлечение).

> 1. La lengua de los procedimientos tramitados por la Administración General del
> Estado será el castellano. No obstante lo anterior, los interesados que se dirijan a
> los órganos de la Administración General del Estado con sede en el territorio de una
> Comunidad Autónoma podrán utilizar también la lengua que sea cooficial en ella.
>
> […]
>
> 3. La Administración Pública instructora deberá traducir al castellano los
> documentos, expedientes o partes de los mismos que deban surtir efecto fuera del
> territorio de la Comunidad Autónoma y los documentos dirigidos a los interesados que
> así lo soliciten expresamente. […]

Это статья, на которую ссылается инструкция Octava ¶ 1. UGE-CE — орган **AGE**
(Administración General del Estado), поэтому язык процедуры — **castellano**.
Отсюда требование перевода иностранных документов; вид перевода (traducción jurada)
эта статья не задаёт — он идёт из практики органа, см.
`../../norms/documentacion-y-forma.md`. `[норма]` (для языка) /
`[официальное разъяснение]` (для формы перевода)

---

## Artículo 5. Representación.

> 1. Los interesados con capacidad de obrar podrán actuar por medio de representante,
> entendiéndose con éste las actuaciones administrativas, salvo manifestación expresa
> en contra del interesado.
>
> 2. Las personas físicas con capacidad de obrar y las personas jurídicas, siempre que
> ello esté previsto en sus Estatutos, podrán actuar en representación de otras ante
> las Administraciones Públicas.
>
> 3. Para formular solicitudes, presentar declaraciones responsables o comunicaciones,
> interponer recursos, desistir de acciones y renunciar a derechos en nombre de otra
> persona, deberá acreditarse la representación. Para los actos y gestiones de mero
> trámite se presumirá aquella representación.
>
> 4. La representación podrá acreditarse mediante cualquier medio válido en Derecho que
> deje constancia fidedigna de su existencia.
>
> A estos efectos, se entenderá acreditada la representación realizada mediante
> **apoderamiento apud acta** efectuado por comparecencia personal o comparecencia
> electrónica en la correspondiente sede electrónica, o a través de la acreditación de
> su inscripción en el **registro electrónico de apoderamientos** de la Administración
> Pública competente.
>
> 5. El órgano competente para la tramitación del procedimiento deberá incorporar al
> expediente administrativo acreditación de la condición de representante y de los
> poderes que tiene reconocidos en dicho momento. El documento electrónico que acredite
> el resultado de la consulta al registro electrónico de apoderamientos correspondiente
> tendrá la condición de acreditación a estos efectos.
>
> 6. La falta o insuficiente acreditación de la representación no impedirá que se tenga
> por realizado el acto de que se trate, siempre que se aporte aquélla o se subsane el
> defecto dentro del plazo de diez días que deberá conceder al efecto el órgano
> administrativo, o de un plazo superior cuando las circunstancias del caso así lo
> requieran.
>
> 7. Las Administraciones Públicas podrán habilitar con carácter general o específico a
> personas físicas o jurídicas autorizadas para la realización de determinadas
> transacciones electrónicas en representación de los interesados. […] No obstante,
> siempre podrá comparecer el interesado por sí mismo en el procedimiento.

## Artículo 6. Registros electrónicos de apoderamientos (извлечение).

*redacción vigente: BOE-A-2018-8574 (STC 55/2018 отменила второй абзац ¶ 4)*

> 1. La Administración General del Estado, las Comunidades Autónomas y las Entidades
> Locales dispondrán de un registro electrónico general de apoderamientos, en el que
> deberán inscribirse, al menos, los de carácter general otorgados apud acta,
> presencial o electrónicamente, por quien ostente la condición de interesado en un
> procedimiento administrativo a favor de representante, para actuar en su nombre ante
> las Administraciones Públicas. También deberá constar el bastanteo realizado del
> poder.
>
> **En el ámbito estatal, este registro será el Registro Electrónico de Apoderamientos
> de la Administración General del Estado.**
>
> […]
>
> 3. Los asientos que se realicen en los registros electrónicos generales y particulares
> de apoderamientos deberán contener, al menos, la siguiente información:
>
> a) Nombre y apellidos o la denominación o razón social, documento nacional de
> identidad, número de identificación fiscal **o documento equivalente** del poderdante.
>
> b) Nombre y apellidos o la denominación o razón social, documento nacional de
> identidad, número de identificación fiscal o documento equivalente del apoderado.
>
> c) Fecha de inscripción.
>
> d) Período de tiempo por el cual se otorga el poder.
>
> e) Tipo de poder según las facultades que otorgue.
>
> 4. Los poderes que se inscriban […] deberán corresponder a alguna de las siguientes
> tipologías:
>
> a) Un poder general para que el apoderado pueda actuar en nombre del poderdante en
> cualquier actuación administrativa y ante cualquier Administración.
>
> b) Un poder para que el apoderado pueda actuar en nombre del poderdante en cualquier
> actuación administrativa ante una Administración u Organismo concreto.
>
> c) Un poder para que el apoderado pueda actuar en nombre del poderdante únicamente
> para la realización de determinados trámites especificados en el poder.
>
> 5. El apoderamiento «apud acta» se otorgará mediante comparecencia electrónica en la
> correspondiente sede electrónica haciendo uso de los sistemas de firma electrónica
> previstos en esta Ley, o bien mediante **comparecencia personal en las oficinas de
> asistencia en materia de registros**.
>
> 6. Los poderes inscritos en el registro tendrán una validez determinada máxima de
> cinco años a contar desde la fecha de inscripción. […]

**Это нормативная развязка тупика «нет NIE → нет certificado digital → нечем
подписать».** Логика по шагам, вся `[норма]`:

1. Подача по режиму DNV — **только электронная** с электронной подписью
   (art. 76.1 Ley 14/2013: `a través de medios telemáticos`).
2. Заявитель на первичной подаче **может не иметь NIE**: требования предъявить
   его норма не устанавливает. (art. 76.5 Ley 14/2013 говорит о **соцстрахе** —
   паспорт достаточен `para darse de alta en la Seguridad Social`, в том числе
   когда NIE нет; о подаче заявления он не говорит и якорем здесь не является,
   но показывает, что режим заявителя без NIE **предполагает**.)
3. Значит, подписывать может **представитель** — art. 5.1: «podrán actuar por medio
   de representante»; art. 5.3 требует, чтобы представительство было
   **acreditada** (подача заявления — не «mero trámite»).
4. Чем доказывается: **любым надёжным способом** (art. 5.4) — и прямо названы
   **apoderamiento apud acta** и запись в **REA**.
5. У поручителя (`poderdante`) в записи REA достаточно **«documento equivalente»**
   (art. 6.3.a) — то есть NIE/DNI не обязателен, паспорт подходит.
6. Ошибка в оформлении представительства **не фатальна**: даётся **10 дней** на
   исправление (art. 5.6).

> ⚠️ Что эти статьи **не** говорят: что представитель обязан быть abogado или
> gestor. Формально нет — представителем может быть любое дееспособное физлицо со
> своим сертификатом (art. 5.2). Практика UGE-CE и то, что реально проходит, —
> `../reports/2026-07-aplicacion-practica.md`. Разбор для пользователя —
> `../../norms/solicitud-inicial.md`.
