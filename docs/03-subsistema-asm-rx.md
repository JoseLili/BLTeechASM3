# Subsistema ASM-RX

## Objetivo

ASM-RX reemplaza al receptor comercial cerrado y debe ser propio, reproducible, diagnosticable y fabricable. Recibirá C1–C7, producirá audio inteligible y señal estable para AFSK, admitirá configuración local y reportará fallas sin depender de internet.

## Arquitectura compartida

- SMA de 50 Ω, alimentación limpia dedicada y salida `AF_OUT`.
- UART de configuración, sin transporte definitivo decidido.
- PTT fijado por hardware en recepción y control Enable/Power Down.
- Puntos de prueba y posibilidad de protección y filtrado RF.

## Variantes

- `PROPUESTO`: ASM-RX-SA818S v0.1 con NiceRF SA818S-V.
- `PROPUESTO`: ASM-RX-DRA818V v0.1 con Dorji DRA818V.
- `DECIDIDO`: comparar ambas mediante el mismo contrato y banco de pruebas antes de seleccionar.

## Criterios de comparación

Sensibilidad, ruido, inteligibilidad, calidad de decodificación AFSK, inmunidad a interferencia, reproducibilidad, consumo, control, disponibilidad y fabricabilidad. Los umbrales cuantitativos son `PENDIENTE`.

## Canales confirmados por el contexto del proyecto

| Canal | Frecuencia MHz |
|---|---:|
| C1 | 162.400 |
| C2 | 162.425 |
| C3 | 162.450 |
| C4 | 162.475 |
| C5 | 162.500 |
| C6 | 162.525 |
| C7 | 162.550 |

`DECIDIDO`: la frecuencia se deriva del canal; no son valores configurables independientes.

## Preguntas abiertas

- ¿Qué documentación oficial confirma límites eléctricos, comandos y prestaciones de cada módulo?
- ¿Qué niveles, impedancia, ancho de banda y ruta física requiere `AF_OUT` para escucha y AFSK?
- ¿Cómo se define y detecta una falla de recepción?
- ¿UART GPIO, USB-UART u otra interfaz será el control definitivo?

## Relacionados

[ADR-002](adr/ADR-002-reemplazo-de-receptor-cerrado.md), [ADR-003](adr/ADR-003-asm-rx-como-daughterboard.md), [ADR-004](adr/ADR-004-dos-variantes-sa818s-dra818v.md) y [pruebas](11-pruebas-y-validacion.md).
