# ADR-001: Arquitectura greenfield

## Estado

Aceptado (`DECIDIDO`).

## Contexto

ASM v3 conserva conocimiento funcional de prototipos, pero el repositorio no contiene una base heredada confiable ni requiere compatibilidad con ASM v2.x.

## Decisión

Diseñar v3 desde cero con límites modulares, contratos comprobables y trazabilidad explícita de supuestos.

## Consecuencias positivas

- Evita acoplamiento y decisiones implícitas heredadas.
- Permite pruebas, simulación y diseño orientado a producción.

## Consecuencias negativas

- Requiere redefinir contratos, despliegue y comportamiento.
- El avance inicial prioriza diseño y evidencia sobre funciones visibles.

## Alternativas consideradas

- Migrar ASM v2.x: descartado por condición esencial del proyecto.
- Prototipo monolítico inmediato: descartado por mantenibilidad y certificación.

## Puntos pendientes

Runtime, empaquetado, despliegue, objetivos no funcionales y estrategia de actualización.
