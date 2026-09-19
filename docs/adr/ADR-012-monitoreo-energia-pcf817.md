# ADR-012 — Monitoreo semántico de energía mediante PC817

## Estado

Aceptado e implementado para Carrier v3.1 Rev A; reglas de severidad pendientes.

## Contexto

J6 recibe cinco salidas de estado de la Mean Well LAD-120A. Cada señal cruza un
PC817 cuya salida tiene pull-up a 3.3 V: opto excitado conduce y produce LOW.
Documentación preliminar omitía `Discharge` y asignaba batería baja a GPIO19;
el mapa de hardware final corrige ambos puntos.

## Decisión

- Congelar AC OK/GPIO5, batería desconectada/GPIO13, batería baja/GPIO26,
  batería llena/GPIO6 y descarga/GPIO12.
- Encapsular pull-up, BCM y activo-bajo en el adaptador GPIO.
- Entregar solamente `ASSERTED`, `CLEAR` o `UNKNOWN` al dominio.
- No inferir todavía normalidad global, falla, autonomía ni severidad hasta
  medir una LAD-120A real y congelar combinaciones y tiempos.
- Mantener la primera herramienta HIL como observador de sólo lectura.

## Consecuencias

La lógica futura no conoce GPIO ni polaridad y las pruebas pueden inyectar las
cinco entradas. Un snapshot completo ya es diagnosticable, pero no debe activar
alarmas de producción hasta validar debounce y tabla de verdad con la fuente real.

## Pendiente

Provocar cada condición con LAD-120A, registrar tiempos y combinaciones, definir
debounce/estabilidad y convertir estados confirmados en eventos de la máquina.
