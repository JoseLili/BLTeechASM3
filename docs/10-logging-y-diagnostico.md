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

## Relacionados

[Modelos](04-logica-de-negocio.md), [estados](05-maquina-de-estados.md) y [certificación](12-requisitos-certificacion.md).
