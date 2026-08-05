# ADR-002: Reemplazo del receptor cerrado

## Estado

Aceptado (`DECIDIDO`).

## Contexto

La dependencia de receptores comerciales cerrados como Midland limita control, diagnóstico, reproducibilidad y evidencia de la cadena de recepción.

## Decisión

Desarrollar ASM-RX propio para recepción y demodulación de los siete canales VHF autorizados.

## Consecuencias positivas

- Control de configuración, audio, diagnóstico y fabricación.
- Evidencia de desempeño y fallas de extremo a extremo.

## Consecuencias negativas

- Aumenta trabajo de RF, validación, fabricación y certificación.
- BLTeech asume riesgos de desempeño y suministro.

## Alternativas consideradas

- Mantener Midland: rechazado por dependencia cerrada.
- Otro receptor comercial: posible referencia de comparación, no arquitectura objetivo.

## Puntos pendientes

Umbrales de aceptación, diseño RF, interfaz de audio, módulo ganador y requisitos regulatorios.
