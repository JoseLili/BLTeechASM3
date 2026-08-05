# ADR-005: Selección local de canal

## Estado

Aceptado conceptualmente (`DECIDIDO`); interacción exacta `PROPUESTO`.

## Contexto

El equipo opera sin internet y debe configurarse entre C1–C7 durante instalación o mantenimiento sin interferir con alertas.

## Decisión

Ofrecer modo técnico local solo en espera y sin evento. Aplicar el canal temporalmente, verificar el receptor y persistirlo solo tras confirmación. EQW interrumpe el menú.

## Consecuencias positivas

- Configuración autónoma y validación antes de guardar.
- Reduce configuraciones persistentes inválidas.

## Consecuencias negativas

- Combinaciones de tres botones pueden ser menos descubribles.
- Requiere debounce, timeouts, rollback y auditoría cuidadosos.

## Alternativas consideradas

- Configuración remota: incompatible como dependencia operativa sin internet.
- Archivo editado manualmente: útil en desarrollo, inadecuado como interfaz de campo única.
- Selector físico: más componentes y menor flexibilidad.

## Puntos pendientes

Umbrales de pulsación, timeout, autenticación, valores iniciales, squelch y definición de verificación exitosa.
