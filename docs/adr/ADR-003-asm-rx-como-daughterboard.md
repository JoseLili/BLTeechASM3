# ADR-003: ASM-RX como daughterboard

## Estado

Aceptado (`DECIDIDO`).

## Contexto

La carrier ya concentra energía e interfaces de panel. El receptor requiere iteración RF, alimentación limpia y comparación de módulos sin rediseñar toda la carrier.

## Decisión

Construir ASM-RX como daughterboard independiente con SMA 50 Ω, control, `AF_OUT`, PTT en recepción, enable y puntos de prueba.

## Consecuencias positivas

- Aísla revisiones y pruebas RF.
- Permite sustituir variantes mediante una arquitectura común.

## Consecuencias negativas

- Añade conectores, integración mecánica y rutas susceptibles a ruido.
- Exige contratos eléctricos y de diagnóstico explícitos.

## Alternativas consideradas

- Integrar RF en carrier: menor modularidad y mayor riesgo de rediseño.
- Receptor externo completo: conserva dependencia e integración menos controlada.

## Puntos pendientes

Conector/pinout, mecánica, alimentación, protección RF, audio, control y criterios EMC.
