# ADR-015 — Prioridad estricta y origen de eventos locales

## Estado

Aceptado e implementado para la rebanada operativa inicial.

## Contexto

Simulacro, Evacuación y Paro ya existen como comandos de botones, pero no
estaban conectados a una máquina que también pudiera representar RWT y EQW. La
auditoría tampoco distinguía una acción local de un evento de radio. Ejecutar
efectos de OLED desde callbacks GPIO además permitiría carreras con la
supervisión de energía.

## Decisión

- Centralizar `EQW > Evacuación > Simulacro > RWT` en valores de prioridad.
- Aceptar únicamente preempción estrictamente ascendente.
- Rechazar y auditar eventos iguales o inferiores sin ponerlos en cola.
- Permitir Paro para RWT, simulacro y evacuación; rechazarlo durante EQW.
- Guardar `EventSource` en cada decisión auditada.
- Traducir comandos del panel a eventos con origen `LOCAL_PANEL`.
- Encolar callbacks GPIO y ejecutar estado, OLED, LEDs y logs en un único ciclo.

## Consecuencias

Las prioridades pueden probarse sin hardware, cada decisión conserva su origen
y ninguna hebra de gpiozero dibuja directamente sobre la OLED. `STOPPED` no
regresa aún a `IDLE`, y todavía no existe entrada real para RWT/EQW.

## Pendiente

Definir deduplicación por identidad de mensaje, vigencia, reconocimiento de
`STOPPED`, política autorizada para finalizar EQW y estados de salud concurrentes.
