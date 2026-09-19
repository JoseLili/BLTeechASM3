# Logging y diagnóstico

Además de `diagnostics.jsonl`, las cabeceras SAME aceptadas se conservan en
`notices.jsonl` con recepción y vencimiento UTC. Este segundo archivo permite
restaurar vigencias y alimentar el historial del menú; no reemplaza la bitácora
diagnóstica ni vuelve a reproducir audio después de un reinicio. Véase
[ADR-019](adr/ADR-019-historial-y-restauracion-same.md).

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

## Implementación actual

`IMPLEMENTADO`: el daemon receptor escribe su diagnóstico de producción en
`/var/lib/asm-blteech/diagnostics.jsonl`. Registra la salud del RTC, la
configuración verificada del receptor, inicio/reinicio del decoder, cada línea
SAME relevante, decisiones aceptadas/duplicadas/rechazadas, cambios del aviso y
apagado ordenado. Cada append se vacía con `fsync`.

`IMPLEMENTADO`: los cambios estables de las cinco entradas Mean Well se
persisten en `~/.local/state/asm-blteech/diagnostics.jsonl`. Cada línea contiene
timestamp ISO 8601, componente, código estable, severidad, mensaje y contexto
`signal/previous/current`. Cada append se vacía con `fsync` para reducir la
pérdida ante un corte abrupto.

Este flujo es distinto de `AuditRecord`: observar un cambio eléctrico no
equivale a aceptar una transición de la máquina de estados. La rotación,
retención, tolerancia a disco lleno y señalización de error de escritura siguen
pendientes antes de producción.

`IMPLEMENTADO`: `JsonLineAuditLog` conserva también decisiones operativas
aceptadas y rechazadas, incluida su procedencia. La demo de panel utiliza
`~/.local/state/asm-blteech/demo-audit.jsonl` deliberadamente separado de una
futura bitácora de producción y aplica `fsync` después de cada decisión.

## Catálogos pendientes

Ya existe el catálogo estable `POWER.<SEÑAL>.<ESTADO>` para esta primera fuente.
Siguen pendientes códigos para otros componentes, política general de
deduplicación/rate limiting y la matriz que determine qué diagnósticos exigen
`MAINTENANCE_REQUIRED`.

## Estado del reloj de la unidad de pruebas

`VALIDADO` el 2026-09-11: el HW-084 en I²C `0x68` está expuesto como
`/dev/rtc0`, con nombre de kernel `rtc-ds1307 1-0068`. El sistema reportó
`hctosys=1`, NTP sincronizado y coincidencia entre RTC y hora civil UTC.

Al conectarlo en caliente, el primer registro del kernel todavía mostró el año
2000 y después NTP corrigió tanto sistema como RTC. Por ello el daemon registra
explícitamente `RTC.READY` o `RTC.DEGRADED` en cada arranque. Sigue pendiente
una prueba de corte y reenergización con el HW-084 conectado desde el inicio
para cerrar la evidencia de retención temporal sin red.

## Supervisión y watchdogs

Se separan responsabilidades:

- **Liveness de proceso:** heartbeat para que un supervisor externo detecte bloqueo y reinicie el proceso.
- **Progreso de aplicación:** confirma que el ciclo procesa entradas y salidas, no solo que el proceso existe.
- **Plazos de estado:** reglas específicas por estado; nunca un retorno genérico a `IDLE`.
- **Salud de adaptadores:** receptor, audio, display, almacenamiento, energía y reloj reportan fallas semánticas.
- **Recuperación:** cada reinicio y decisión posterior queda auditado.

`IMPLEMENTADO`: systemd supervisa el daemon receptor y lo reinicia tres segundos
después de una salida con error. El pipeline SAME aplica además backoff
exponencial acotado entre uno y treinta segundos.

`PENDIENTE`: watchdog de progreso, límites de reinicios, rotación/retención y
recuperación de vigencias SAME activas después de reiniciar.

## Relacionados

[Modelos](04-logica-de-negocio.md), [estados](05-maquina-de-estados.md) y [certificación](12-requisitos-certificacion.md).
