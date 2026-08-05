# Logging y diagnóstico

## Objetivos

`DECIDIDO`: conservar evidencia útil para operación, validación y certificación, aun sin internet. Auditoría, diagnóstico técnico y logs de depuración son flujos distintos aunque puedan compartir almacenamiento.

## Registros previstos

- Auditoría append-only: eventos recibidos/validados/rechazados, transiciones, Paro y cambios de configuración.
- Diagnóstico estructurado: componente, código estable, severidad, instante, contexto acotado y recuperación.
- Salud: receptor, energía, almacenamiento, reloj, watchdog y arranque/autoprueba.

## Requisitos propuestos

- Timestamps civil y monotónico cuando corresponda, con calidad del reloj.
- Identidad de hardware/software y correlación entre recepción, decisión y salida.
- Escritura tolerante a corte de energía y almacenamiento limitado.
- Rotación, exportación y consulta sin impedir funciones críticas.
- Evitar secretos o datos personales innecesarios.

## Fallas de logging

`PROPUESTO`: una escritura fallida genera diagnóstico visible y usa un buffer acotado, sin bloquear la atención de EQW. `PENDIENTE`: política exacta ante medio lleno/corrupto, retención, integridad criptográfica y exportación.

## Catálogos pendientes

Se requieren códigos estables, severidades, política de deduplicación/rate limiting y matriz que determine qué diagnósticos exigen `MAINTENANCE_REQUIRED`.

## Estado del reloj de la unidad de pruebas

`VALIDADO`: la Raspberry Pi expone el RTC I²C `0x68` como `/dev/rtc0`. `PENDIENTE`: durante la primera ejecución el reloj del sistema no estaba sincronizado, NTP estaba inactivo y el RTC reportaba el año 2000. Hasta configurar y validar recuperación tras corte de energía, los timestamps generados por esa unidad no constituyen evidencia temporal confiable.

## Supervisión y watchdogs

Se separan responsabilidades:

- **Liveness de proceso:** heartbeat para que un supervisor externo detecte bloqueo y reinicie el proceso.
- **Progreso de aplicación:** confirma que el ciclo procesa entradas y salidas, no solo que el proceso existe.
- **Plazos de estado:** reglas específicas por estado; nunca un retorno genérico a `IDLE`.
- **Salud de adaptadores:** receptor, audio, display, almacenamiento, energía y reloj reportan fallas semánticas.
- **Recuperación:** cada reinicio y decisión posterior queda auditado.

`PENDIENTE`: elegir supervisor de producción, intervalo de heartbeat, política de reinicio, límites de reinicios y recuperación de eventos activos mediante ADR.

## Relacionados

[Modelos](04-logica-de-negocio.md), [estados](05-maquina-de-estados.md) y [certificación](12-requisitos-certificacion.md).
