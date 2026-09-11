# Eventos y prioridades

## Orden funcional

`DECIDIDO` como referencia inicial:

```text
EQW > Evacuación > Simulacro > RWT > Configuración / espera
```

Paro es una orden manual transversal y no se ubica sin más dentro de esa escala.

## Política conceptual

| Evento entrante | Efecto previsto |
|---|---|
| Mayor prioridad | interrumpe el evento o menú inferior y deja auditoría |
| Igual prioridad | se rechaza y audita en esta primera implementación |
| Menor prioridad | no degrada el activo; registrar decisión |
| Inválido/caducado | rechazar y conservar evidencia diagnóstica apropiada |
| Paro | detener solo los eventos autorizados y auditar siempre |

Los eventos físicos locales y los recibidos deben converger en comandos semánticos, sin omitir sus distintos datos de procedencia.

## Implementación actual

`IMPLEMENTADO`: `EventPriority` concentra la escala y la máquina acepta un inicio
desde `IDLE` o cuando supera estrictamente al evento activo. `START_EQW` también
interrumpe `TECH_MODE`. Un evento igual o inferior se rechaza mediante
`InvalidTransition` y el controlador conserva la decisión en auditoría.

`IMPLEMENTADO`: `EventSource` distingue `SYSTEM`, `LOCAL_PANEL` y `RADIO` en cada
`AuditRecord`. Los botones GPIO llegan mediante `PanelCommandRouter`; por tanto,
Simulacro, Evacuación y Paro conservan procedencia `LOCAL_PANEL` sin que el
dominio conozca GPIO.

## Condiciones de aceptación pendientes

- Identidad, autenticidad, formato y checksum de mensajes.
- Ventana temporal, tolerancia del RTC y repetición.
- Correlación y deduplicación.
- Inicio, duración, cancelación y término de cada evento.
- Conducta ante almacenamiento, audio, receptor o energía degradados.

## Relacionados

[Modelos](04-logica-de-negocio.md), [estados](05-maquina-de-estados.md) y [logging](10-logging-y-diagnostico.md).
