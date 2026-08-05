# ADR-006: Separación de dominio y hardware

## Estado

Aceptado (`DECIDIDO`).

## Contexto

GPIO, optoacopladores, buses y módulos presentan polaridades y protocolos variables. Mezclarlos con prioridades impediría simular, probar y cambiar hardware con seguridad.

## Decisión

El dominio contiene modelos y reglas puras. La aplicación declara puertos y coordina casos de uso. Infraestructura adapta dispositivos a estados semánticos. Se separan GPIO crudo, interpretación post-opto y estado funcional.

## Consecuencias positivas

- Tests unitarios sin Raspberry Pi y adaptadores reemplazables.
- Polaridades y protocolos quedan localizados.
- SA818S y DRA818V pueden compartir contrato.

## Consecuencias negativas

- Más contratos, mapeo y disciplina arquitectónica.
- Riesgo de abstracciones prematuras si se congelan antes de medir hardware.

## Alternativas consideradas

- Acceso directo a GPIO desde reglas: rechazado por acoplamiento y lógica invertida dispersa.
- Abstracción única de «hardware»: rechazada por ocultar responsabilidades y fallas distintas.

## Puntos pendientes

Firmas de puertos, modelo async/sync, manejo de errores/timeouts, contratos de calidad de datos y librerías concretas.
