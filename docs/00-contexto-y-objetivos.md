# Contexto y objetivos

## Estado

- `DECIDIDO`: ASM BLTeech v3 es un desarrollo *greenfield*; no hereda contratos ni código de ASM v2.x.
- `VALIDADO`: existen cinco unidades de la carrier; alimentación, OLED, RTC, EEPROM, botones y LEDs funcionan en pruebas iniciales.
- `PENDIENTE`: validar la cadena completa con receptor ASM-RX y Mean Well LAD-120A reales.

## Propósito

ASM BLTeech v3 es un sistema de difusión secundaria de alertamiento sísmico basado en Raspberry Pi 4, carrier propia y receptor VHF propio. Debe operar sin internet, producir avisos audibles y visibles y conservar evidencia diagnóstica y de auditoría.

La cadena objetivo es: antena VHF → ASM-RX → audio y señal apta para AFSK → Raspberry Pi → validación y reglas → salidas y bitácora.

## Objetivos

- Recibir los siete canales autorizados entre 162.400 y 162.550 MHz.
- Sustituir receptores comerciales cerrados por un subsistema reproducible, diagnosticable y fabricable.
- Separar reglas de negocio, orquestación y detalles de hardware.
- Permitir simulación, pruebas automatizadas, trazabilidad y futura certificación.

## Fuera de alcance de esta base

- Drivers Raspberry Pi o comportamiento de producción.
- Elección final de receptor, audio, UART o librerías de hardware.
- Cierre de polaridades Mean Well sin medición física.
- Compatibilidad con artefactos ASM v2.x.

## Preguntas abiertas

- ¿Qué normativa y organismo definirán la certificación?
- ¿Cuáles son los formatos, autenticidad, temporización y criterios de validez de los mensajes AFSK?
- ¿Qué metas cuantitativas aplican a disponibilidad, latencia, autonomía y retención de registros?

## Documentos relacionados

[Arquitectura](01-arquitectura-general.md), [ASM-RX](03-subsistema-asm-rx.md), [pruebas](11-pruebas-y-validacion.md) y [certificación](12-requisitos-certificacion.md).
