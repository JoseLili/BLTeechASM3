# ADR-014 — Cambios Mean Well como eventos diagnósticos estabilizados

## Estado

Aceptado e implementado en software; validación LAD-120A real pendiente.

## Contexto

Las cinco entradas PC817 ya tienen traducción eléctrica semántica, pero un
snapshot manual no avisa al operador, no conserva evidencia y puede amplificar
un rebote. Además, la tabla de verdad funcional de la LAD-120A aún no se ha
validado extremo a extremo.

## Decisión

- Establecer silenciosamente el primer snapshot como línea base.
- Estabilizar cada señal de forma independiente durante 250 ms.
- Publicar un registro por transición estable con estado anterior y actual.
- Agrupar en un solo aviso OLED los cambios publicados en el mismo ciclo.
- Persistir JSONL append-only con `fsync` después de cada registro.
- Mantener estos cambios separados de la auditoría de máquina de estados.
- No entrar automáticamente a `POWER_FAULT` hasta congelar la tabla de verdad y
  severidades mediante pruebas con la fuente real.

## Consecuencias

El operador recibe avisos automáticos y existe evidencia durable sin convertir
una señal todavía ambigua en una alarma funcional. El costo inicial es un
`fsync` por transición, aceptable porque estos cambios deben ser poco frecuentes.

## Pendiente

Validar los 250 ms, el significado de cada combinación, el reloj RTC, rotación,
retención, comportamiento ante disco lleno y restauración temporizada de la
pantalla previa después de un aviso.
