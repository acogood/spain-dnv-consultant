---
geometry:
- a4paper
- margin=2.5cm
---

<!--
  ШАБЛОН: memoria descriptiva / carta explicativa к заявлению на residencia para
  teletrabajador de carácter internacional (Ley 14/2013).

  ЧТО ЭТО. Связный рассказ о кейсе, который читает сотрудник UGE: кто заявитель,
  на каком основании подаёт, чем занимается, чем это подтверждается и почему
  условия выполнены. Формы MI-T/MI-F дают поля, memoria — повествование.

  ПРАВИЛА ЗАПОЛНЕНИЯ (те же, что у escritos):
  * {{ПЛЕЙСХОЛДЕРЫ}} подставляются ИЗ ПРОФИЛЯ (user/case-profile.json) и из
    user/spec.md. Значения не выдумываются.
  * Плейсхолдер, которого нет в профиле, остаётся как [ТРЕБУЕТСЯ: <что>] —
    не заменяется правдоподобным текстом.
  * Блоки, помеченные "УСЛОВНЫЙ", включаются только если условие выполнено.
    family.present = false -> секцию 6 целиком УДАЛИТЬ, а не оставить пустой.
  * Юридические утверждения берутся из knowledge_base/norms/ и user/spec.md.
    Ничего не утверждать о норме сверх того, что там есть. Суммы, пороги и
    ссылки на статьи проверяются вживую (as-of норм-файлов).
  * Memoria не заменяет документы: каждое утверждение здесь должно быть
    подкреплено приложением из перечня в конце.
-->

**MEMORIA DESCRIPTIVA DE LA ACTIVIDAD PROFESIONAL**
**Solicitud de autorización de residencia para teletrabajador de carácter internacional**
*(Ley 14/2013, de 27 de septiembre, artículos 74 bis y siguientes)*

**AL MINISTERIO DE INCLUSIÓN, SEGURIDAD SOCIAL Y MIGRACIONES**
**UNIDAD DE GRANDES EMPRESAS Y COLECTIVOS ESTRATÉGICOS (UGE-CE)**

**DATOS DE LA PERSONA SOLICITANTE**

D./Dña. **{{NOMBRE_COMPLETO}}**, de nacionalidad **{{NACIONALIDAD}}**,
con N.I.E. **{{NIE}}** y pasaporte **{{PASAPORTE}}**,
con domicilio en España en **{{DOMICILIO}}**,
correo a efectos de notificaciones **{{EMAIL}}**.

Tipo de solicitud: **{{TIPO_SOLICITUD}}** *(INICIAL / RENOVADA)*.

---

## 1. Objeto y fundamento

Que formulo la presente **{{TIPO_SOLICITUD_TEXTO}}** de autorización de
residencia para **teletrabajador de carácter internacional**, al amparo de la
**Ley 14/2013, de 27 de septiembre**, en su redacción vigente
*(artículos 74 bis y siguientes — [ТРЕБУЕТСЯ: сверить точные статьи с
knowledge_base/norms/marco-legal.md на дату подачи])*.

Ejerzo mi actividad profesional **en su totalidad a distancia**, por medios
exclusivamente telemáticos, para **{{EMPRESA_CLIENTE}}**, entidad radicada en
**{{PAIS_EMPRESA}}**, sin prestar servicios en el mercado laboral español.

<!-- УСЛОВНЫЙ (renovación): -->
*Para renovación:* la presente solicitud tiene por objeto la **renovación** de
la autorización concedida el **{{FECHA_PRIMERA_CONCESION}}**, cuya Tarjeta de
Identidad de Extranjero caduca el **{{FECHA_CADUCIDAD_TIE}}**. Se mantienen las
condiciones que fundamentaron la concesión inicial, según se acredita a
continuación.

## 2. Descripción de la actividad

- **Puesto / rol:** {{ROL}}
- **Entidad para la que trabajo:** {{EMPRESA_CLIENTE}} ({{PAIS_EMPRESA}})
- **Naturaleza de la relación:** {{TIPO_RELACION}} *(contratista independiente /
  autónomo — arquetipo v1 de este repositorio)*
- **Inicio de la relación:** {{FECHA_CONTRATO}}
- **Referencia del contrato:** {{NUM_CONTRATO}}

<!-- Опишите СВОИМИ СЛОВАМИ 3-6 предложениями: чем именно занимаетесь, какими
     инструментами, как организована удалённая работа, почему присутствие в
     офисе не требуется. Согласуйте формулировки с контрактом и с Certificate
     of services — расхождение между ними порождает дозапрос. -->

{{DESCRIPCION_ACTIVIDAD}}

## 3. Acreditación de la relación profesional

La relación con **{{EMPRESA_CLIENTE}}** se acredita mediante:

| Documento | Referencia | Observaciones |
|---|---|---|
| Contrato de prestación de servicios | {{NUM_CONTRATO}} ({{FECHA_CONTRATO}}) | {{OBS_CONTRATO}} |
| Certificado / carta de la entidad | {{REF_CERTIFICADO_SERVICIOS}} | confirma el carácter **remoto** de la prestación |
| Facturas emitidas | {{PERIODO_FACTURAS}} | vinculadas a los pagos recibidos |
| Documentación registral de la entidad | {{REF_REGISTRO_EMPRESA}} | antigüedad de la entidad |

<!-- Если название заказчика менялось (amendment, смена юрлица) — объясните это
     здесь ЯВНО, одним абзацем, со ссылкой на подтверждающий документ. Молчание
     об этом читается как несостыковка. -->

## 4. Medios económicos

- **Ingresos declarados:** {{INGRESO_MENSUAL}} {{MONEDA}} al mes
  ({{INGRESO_EUR}} EUR equivalentes).
- **Umbral aplicable:** [ТРЕБУЕТСЯ: порог года из
  knowledge_base/norms/umbral-ingresos.md — сверить вживую на дату подачи].
- **Relación con el umbral:** {{RELACION_UMBRAL}}.

<!-- УСЛОВНЫЙ (доход в валюте, отличной от EUR): укажите источник курса и
     приведите €-эквивалент ПО КАЖДОМУ платежу отдельно, а не общей суммой.
     Из практики: UGE сверяет договор с назначением платежей в выписке, поэтому
     из выписки должно быть видно, ОТ КОГО и ПО КАКОМУ договору пришли деньги. -->

Los ingresos se perciben en **{{BANCO}}** y se acreditan mediante los extractos
bancarios aportados, en los que consta el ordenante y el concepto de cada pago,
en correspondencia con las facturas relacionadas en el apartado 3.

## 5. Vinculación con España

- **Domicilio:** {{DOMICILIO}}
- **Empadronamiento:** {{REF_PADRON}}
- **Seguro / cobertura sanitaria:** {{REF_SEGURO}}

<!-- УСЛОВНЫЙ БЛОК — включать, только если family.present = true.
     При family.present = false УДАЛИТЬ секцию 6 целиком. -->

## 6. Unidad familiar

Solicita conjuntamente **{{NOMBRE_FAMILIAR}}**, N.I.E. **{{NIE_FAMILIAR}}**,
pasaporte **{{PASAPORTE_FAMILIAR}}**, en calidad de **{{PARENTESCO}}**, vínculo
acreditado mediante **{{REF_DOC_VINCULO}}** ({{FECHA_VINCULO}}).

La solicitud del familiar se vincula al expediente del titular
nº **{{REGAGE_TITULAR}}**
<!-- REGAGE появляется ТОЛЬКО после подачи титулара. До этого — [ТРЕБУЕТСЯ],
     не выдумывать номер. -->

Los medios económicos acreditados en el apartado 4 corresponden al **titular** y
se consideran suficientes para la unidad familiar conforme al umbral aplicable.

## 7. Relación de documentos aportados

<!-- Перечень должен совпадать с тем, что реально приложено. Каждое утверждение
     из разделов выше должно иметь здесь свою строку. -->

1. {{DOC_1}}
2. {{DOC_2}}
3. {{DOC_3}}
4. {{DOC_4}}
5. {{DOC_5}}

---

Por lo expuesto, **SOLICITO** que se tenga por presentada esta memoria junto con
la documentación relacionada y se acuerde la concesión de la autorización de
residencia para teletrabajador de carácter internacional interesada.

En **{{CIUDAD}}**, a **{{FECHA}}**.

Fdo.: **{{NOMBRE_COMPLETO}}** — N.I.E. {{NIE}}
*(firma electrónica)*

<!-- ═══════════════════════════════════════════════════════════════════════
     ПОДПИСЬ — РАЗВЕСТИ ДВЕ РАЗНЫЕ ВЕЩИ. Инструкция синтезу/documents.

     1) ДОКУМЕНТ подписывает САМ ЗАЯВИТЕЛЬ. Instrucción Octava ¶ 2, п. 3.º:
        `Formulario de solicitud firmado por la persona teletrabajadora`.
        Представитель подписать документ ЗА заявителя не может — он подписывает
        ОТПРАВКУ (электронную подачу своим сертификатом, art. 5 Ley 39/2015).
        Это два разных действия, и путать их нельзя: подача представителем НЕ
        означает, что под memoria и под MI-T стоит его имя.

     2) БЕЗ NIE — блок выше НЕ ГОДИТСЯ: строка `N.I.E. {{NIE}}` даст либо
        пустое место, либо [ТРЕБУЕТСЯ] в подписи. На первичной подаче NIE
        законно может не быть. ЗАМЕНИТЬ блок подписи на вариант Б:

        Fdo.: **{{NOMBRE_COMPLETO}}** — pasaporte **{{PASAPORTE}}**
        *(firma manuscrita; documento presentado telemáticamente por
        representante — art. 5 Ley 39/2015)*

        Идентифицируйте себя ПАСПОРТОМ: он у заявителя есть всегда, а art. 76.5
        прямо называет паспорт `documento acreditativo suficiente` в ситуации
        без NIE (пусть и применительно к соцстраху).

     3) ЕСЛИ ПОДАЁТ ПРЕДСТАВИТЕЛЬ — добавить ПОСЛЕ подписи заявителя отдельный
        блок, не вместо неё:

        Presentado telemáticamente por **{{NOMBRE_REPRESENTANTE}}**,
        N.I.E./D.N.I. **{{NIE_REPRESENTANTE}}**, en representación de la persona
        solicitante, acreditada mediante **{{poder notarial / consular / apud
        acta / REA}}** — art. 5 Ley 39/2015.
     ═══════════════════════════════════════════════════════════════════════ -->
