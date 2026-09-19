# ADR-013 — Indicadores GPIO activo-alto como estado completo

## Estado

Aceptado e implementado eléctricamente; política visual inicial implementada.

## Contexto

Carrier v3.1 Rev A expone cuatro indicadores en J9: AVISO/GPIO23,
PRECAUCIÓN/GPIO24, ALERTA/GPIO25 y ENERGÍA/GPIO4. Todos son activos en HIGH.
Actualizar sólo un LED puede dejar encendida una indicación anterior y producir
una combinación engañosa.

## Decisión

- Modelar siempre los cuatro valores en un `IndicatorState` inmutable.
- Hacer que cada `apply` escriba las cuatro salidas, incluidas las apagadas.
- Inicializar apagado y garantizar todo LOW antes de liberar recursos.
- Mantener fuera del adaptador los patrones, parpadeo, prioridades y asociación
  definitiva con estados del sistema.
- Proveer una prueba HIL one-hot que termina con todas las salidas apagadas.
- Derivar el patrón completo desde `SystemState` en una política pura y aplicarlo
  cada vez que el controlador presenta un estado.

La política inicial es: ENERGÍA durante todo estado controlado; AVISO para RWT;
PRECAUCIÓN para simulacro y evacuación; ALERTA para EQW, fallo de receptor,
fallo de energía y mantenimiento. BOOT, SELF_TEST, IDLE, TECH_MODE y STOPPED no
encienden un indicador de evento.

## Consecuencias

No sobreviven LEDs residuales entre estados y la futura política puede probarse
sin GPIO. La ejecución confirma niveles lógicos, pero cada unidad requiere una
confirmación visual para detectar polaridad de LED, montaje o fallas físicas.

## Pendiente

Validar visualmente la política con el ensamble completo, congelar precedencia
cuando coexistan EQW/fallas/operación, repetir el lamp test en las cinco carriers
y registrar qué indicador físico se iluminó en cada paso.
