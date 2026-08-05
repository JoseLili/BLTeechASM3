# ADR-004: Dos variantes SA818S y DRA818V

## Estado

Aceptado para evaluación (`DECIDIDO`); selección final `PENDIENTE`.

## Contexto

No existe evidencia comparativa suficiente para seleccionar NiceRF SA818S-V o Dorji DRA818V.

## Decisión

Diseñar ASM-RX-SA818S v0.1 y ASM-RX-DRA818V v0.1 bajo una interfaz común y compararlas con el mismo banco y criterios.

## Consecuencias positivas

- Selección basada en evidencia y menor dependencia temprana de proveedor.
- Fuerza un contrato desacoplado del módulo.

## Consecuencias negativas

- Duplica parte del prototipado, compras y pruebas.
- Las capacidades diferentes pueden tensionar la abstracción común.

## Alternativas consideradas

- Elegir SA818S o DRA818V por especificación: rechazado sin prueba en condiciones objetivo.
- Mantener ambas en producción: posible, pero eleva soporte y certificación.

## Puntos pendientes

Datasheets oficiales, disponibilidad, matriz ponderada, umbrales, lotes de muestra y decisión de producción.
