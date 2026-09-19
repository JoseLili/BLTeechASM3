# ADR-005: Selección local de canal

## Estado

Aceptado e implementado para el menú OLED de Carrier v3.1 Rev A.

## Contexto

El equipo opera sin internet y debe configurarse entre C1–C7 durante instalación o mantenimiento sin interferir con alertas.

## Decisión

Ofrecer modo técnico local solo en espera y sin evento. Los botones dedicados
Arriba/Abajo seleccionan exclusivamente C1–C7. El primer Enter aplica el canal
temporalmente y verifica el SA818; el segundo Enter lo persiste. Regresar
restaura el canal confirmado. EQW interrumpe el menú.

## Consecuencias positivas

- Configuración autónoma y validación antes de guardar.
- Reduce configuraciones persistentes inválidas.

## Consecuencias negativas

- Requiere debounce, timeouts, rollback y auditoría cuidadosos.

## Alternativas consideradas

- Configuración remota: incompatible como dependencia operativa sin internet.
- Archivo editado manualmente: útil en desarrollo, inadecuado como interfaz de campo única.
- Selector físico: más componentes y menor flexibilidad.

## Puntos pendientes

Integrar la preempción EQW en la composición de producción, definir timeout y
autenticación del modo técnico, y auditar cada confirmación persistente.
