# ADR-019: Historial y restauración de avisos SAME

## Estado

Aceptado e implementado.

## Contexto

La vigencia RWT/EQW se calculaba únicamente con tiempo monotónico en memoria.
Esto era correcto durante una ejecución, pero un reinicio borraba el aviso
vigente y dejaba a la pantalla principal sin historial estructurado. La
bitácora diagnóstica contiene evidencia suficiente para auditoría, pero no debe
convertirse en una base de estado mutable.

## Decisión

- Guardar cada cabecera SAME aceptada en `notices.jsonl`, separada de
  `diagnostics.jsonl`.
- Persistir la cabecera original, la recepción UTC y su vencimiento UTC.
- Hacer `fsync` después de cada inserción y conservar formato append-only.
- Al arrancar, restaurar solamente el recibo no vencido más reciente de cada
  tipo de evento.
- Reconstruir el tiempo monotónico restante desde el reloj civil; nunca
  extender una vigencia al reiniciar.
- Restaurar LED y presentación, pero no volver a reproducir el audio de una
  alerta recibida antes del reinicio.
- Tratar una falla de lectura o escritura como degradación auditable; la
  recepción RF debe continuar.

## Consecuencias

La pantalla y los indicadores pueden recuperar una RWT/EQW vigente después de
reiniciar. El historial reciente queda disponible para el menú sin interpretar
texto libre del journal. Su exactitud tras una pérdida total de energía depende
de que RTC o NTP proporcionen una hora civil correcta.
