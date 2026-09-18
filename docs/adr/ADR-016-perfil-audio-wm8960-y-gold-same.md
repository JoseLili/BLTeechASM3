# ADR-016 — Perfil de audio WM8960 y entrada GOLD SAME

## Estado

Aceptado, implementado para captura WM8960 y reproducción por jack de Pi 4, y
validado en una RWT real.

## Contexto

Carrier v3.1 Rev A conecta `AF_OUT` del SA818S-V a RINPUT1 derecho del WM8960.
La aplicación necesita distinguir el formato físico del codec, la señal exacta
que recibe el decoder y una futura escucha local. También se observó que tocar
registros I²C o mezclador durante I²S puede provocar EIO, y una captura inicial
llegó a contener solamente ceros aun cuando ALSA enumeraba la tarjeta.

## Decisión

- Identificar la tarjeta por el nombre ALSA exacto `wm8960soundcard` y usar
  `hw:wm8960soundcard,0`.
- Reproducir las alertas por el dispositivo independiente
  `plughw:CARD=Headphones,DEV=0`; nunca por el PCM de captura WM8960.
- Capturar `S32_LE`, 48000 Hz, dos canales y seleccionar el canal derecho
  (índice 1) como entrada del SA818S-V.
- Alimentar al decoder GOLD con `S16_LE`, 22050 Hz, mono, obtenido únicamente
  del canal derecho.
- Mantener esa rama sin ganancia, normalización, compresor, high-pass, low-pass
  ni otros filtros digitales. La monitorización local será una rama distinta.
- Tratar precarga, captura y reproducción como hechos de salud separados.
- Detectar en el diagnóstico finito el caso inequívoco de muestras exactamente
  en cero sin declarar todavía un umbral acústico arbitrario.
- No modificar I²C ni mezclador mientras exista un stream I²S activo.
- Permitir una sola reproducción WAV y reemplazarla únicamente por un evento
  de mayor prioridad; Paro y vencimiento conservan detención explícita.

## Evidencia

El 11 de septiembre de 2026 el usuario capturó una RWT real con el perfil físico,
convirtió el canal derecho con SoX al perfil GOLD y `multimon-ng 1.3.1` obtuvo
`ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-` y tres terminadores `NNNN`.

La HAL también comprobó tarjeta/precarga, 96000 cuadros no nulos en una captura
de dos segundos, reproducción WAV silenciosa y presentación diagnóstica OLED.

## Consecuencias

El contrato reproducible ya no depende de opciones dispersas de comandos. La
captura diagnóstica no es el decoder continuo: todavía faltan propiedad del
proceso, streaming, buffering, reinicio, deduplicación SAME y métricas de señal.
La prueba RWT valida funcionalidad, pero no fija sensibilidad, SNR, BER, tasas
de falsos positivos/negativos ni márgenes eléctricos de producción.

## Relacionados

[ASM-RX](../03-subsistema-asm-rx.md), [interfaces](../07-interfaces-de-hardware.md), [configuración](../08-configuracion-y-modo-tecnico.md) y [pruebas](../11-pruebas-y-validacion.md).
