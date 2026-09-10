# ADR-010 — Botones dedicados de menú mediante PCF8574P

## Estado

`DECIDIDO` — 2026-09-09.

## Contexto

Documentación anterior reutilizaba Simulacro, Evacuación y Paro para navegar
el modo técnico. Carrier v3.1 Rev A incorpora siete botones independientes en
J7, conectados a P0–P6 del PCF8574P `0x20`, con INT en GPIO16.

## Decisión

- Los botones GPIO17, GPIO22 y GPIO27 conservan exclusivamente sus funciones
  operativas y no dependen de I²C.
- El PCF8574P entrega Arriba, Abajo, Izquierda, Derecha, Enter, Regresar y
  Escucha al sistema de menús mediante comandos semánticos.
- P7 permanece reservado.
- El callback de INT no realiza transacciones I²C; sólo despierta al ciclo de
  aplicación, que posteriormente lee el expansor.
- Escucha controla únicamente la rama de monitor local. El decoder SAME no
  recibe ganancia, filtros ni transformaciones procedentes de la interfaz.

## Consecuencias

El árbol de menús puede probarse sin hardware y el adaptador PCF8574 puede
diagnosticarse independientemente. La aplicación debe continuar aceptando
eventos críticos mientras se muestra un submenú y debe abandonar el menú de
inmediato ante un EQW válido.
