# Lógica de negocio

## Principios

- `DECIDIDO`: las prioridades y transiciones son reglas puras, independientes del hardware.
- `DECIDIDO`: un mensaje recibido no se convierte en evento hasta ser validado.
- `DECIDIDO`: toda orden de Paro genera auditoría.
- `PROPUESTO`: los modelos siguientes son conceptuales; campos y tipos definitivos permanecen abiertos.

## Estado de implementación

`VALIDADO` en simulación: existen `SystemState`, el subconjunto inicial de `EventType`, `StateTransition` y `AuditRecord`, junto con reglas puras y fakes. El resto de los modelos de este documento continúa `PENDIENTE`.

`VALIDADO` mediante pruebas: el intérprete semántico de botones separa identidad física, política de activación y comando. Paro se emite siempre al presionar; Simulacro y Evacuación admiten políticas inmediatas o de retención sin generar repeticiones.

## Modelos conceptuales

### `SystemState`

- **Propósito:** estado operativo único de la máquina.
- **Campos sugeridos:** `kind`, `entered_at`, `reason`, `active_event_id`.
- **Invariantes:** un solo estado principal; entrada fechada; evento asociado cuando aplique.
- **Origen / consumidores:** máquina de estados / casos de uso, UI, auditoría y diagnóstico.
- **Pregunta:** ¿las fallas son estados exclusivos o condiciones paralelas?

### `EventType`

- **Propósito:** clasificar EQW, evacuación, simulacro, RWT y órdenes técnicas.
- **Campos sugeridos:** valor estable y prioridad.
- **Invariantes:** la prioridad no depende del adaptador que originó el evento.
- **Origen / consumidores:** mensajes y botones / política de prioridad.
- **Pregunta:** ¿Paro es tipo de evento, comando o ambos?

### `ReceivedMessage`

- **Propósito:** evidencia inmutable de una recepción aún no validada.
- **Campos sugeridos:** `id`, `received_at`, `raw_payload`, `channel`, métricas de recepción y `source`.
- **Invariantes:** conserva el contenido original y su instante de recepción.
- **Origen / consumidores:** decodificador AFSK / validador y bitácora técnica.
- **Preguntas:** formato, codificación, límites y manejo de datos sensibles.

### `ValidatedEvent`

- **Propósito:** evento confiable aceptado por reglas de validación.
- **Campos sugeridos:** `id`, `type`, `issued_at`, `received_message_id`, vigencia y resultado de validación.
- **Invariantes:** trazable a recepción; tipo admitido; no expirado.
- **Origen / consumidores:** validador / prioridades y máquina de estados.
- **Preguntas:** autenticidad, duplicados, caducidad y reloj tolerado.

### `ReceiverStatus`

- **Propósito:** estado semántico del receptor, no bytes ni pines crudos.
- **Campos sugeridos:** disponibilidad, canal, sincronización/configuración, señal, falla y `observed_at`.
- **Invariantes:** canal C1–C7 cuando está configurado; falla con código diagnóstico.
- **Origen / consumidores:** `ReceiverPort` / supervisión, UI y auditoría.
- **Pregunta:** métricas comparables disponibles en ambos módulos.

### `PowerStatus`

- **Propósito:** vista funcional de alimentación y batería.
- **Campos sugeridos:** red presente, batería conectada, batería baja, batería llena, descarga y calidad de datos.
- **Invariantes:** cada campo admite desconocido mientras falten señales o validación.
- **Origen / consumidores:** `PowerMonitorPort` / reglas, UI, diagnóstico.
- **Pregunta:** combinaciones físicamente imposibles y tiempos de estabilización.

### `ButtonEvent`

- **Propósito:** representar interacción ya filtrada eléctricamente.
- **Campos sugeridos:** botón, gesto (`PRESS`, `RELEASE`, `SHORT`, `LONG`, combinación), tiempo y duración.
- **Invariantes:** orden temporal; duración no negativa.
- **Origen / consumidores:** `ButtonInputPort` / casos de uso normal y técnico.
- **Pregunta:** umbrales de rebote, pulsación larga y combinación.

### `ChannelConfiguration`

- **Propósito:** selección persistente de C1–C7.
- **Campos sugeridos:** canal, frecuencia derivada, squelch, fecha y origen del cambio.
- **Invariantes:** canal válido; frecuencia calculada, nunca almacenada como verdad independiente.
- **Origen / consumidores:** modo técnico y repositorio / receptor y UI.
- **Pregunta:** rangos de squelch comunes y estrategia de rollback.

### `HardwareIdentity`

- **Propósito:** identificar unidad y revisiones para trazabilidad.
- **Campos sugeridos:** equipo, carrier, receptor, números de serie y lote.
- **Invariantes:** identificadores estables una vez provisionados.
- **Origen / consumidores:** EEPROM/configuración / diagnóstico, auditoría y soporte.
- **Pregunta:** esquema de identidad y campos obligatorios.

### `DiagnosticEvent`

- **Propósito:** observación técnica accionable.
- **Campos sugeridos:** código, severidad, componente, instante, contexto y estado de recuperación.
- **Invariantes:** código estable y fecha; contexto estructurado y acotado.
- **Origen / consumidores:** supervisores y adaptadores / UI, logging y mantenimiento.
- **Pregunta:** catálogo, severidades, deduplicación y rate limiting.

### `AuditRecord`

- **Propósito:** evidencia durable de decisiones y acciones relevantes.
- **Campos sugeridos:** id, instante, actor/origen, acción, estado anterior/posterior y referencias.
- **Invariantes:** append-only; ordenable; trazable a eventos relacionados.
- **Origen / consumidores:** aplicación / operadores, diagnóstico y certificación.
- **Pregunta:** retención, integridad, exportación y política ante almacenamiento lleno.

## Relacionados

[Estados](05-maquina-de-estados.md), [prioridades](06-eventos-y-prioridades.md), [interfaces](07-interfaces-de-hardware.md) y [logging](10-logging-y-diagnostico.md).
