# Audios operativos

El daemon reconoce exactamente estos cuatro archivos WAV:

- `rwt.wav`
- `eqw.wav`
- `simulacro.wav`
- `evacuacion.wav`

El repositorio incluye actualmente:

- `eqw.wav`, convertido de `alerta_sismica.mp3`.
- `simulacro.wav`, convertido de `simulacro.mp3`.
- `evacuacion.wav`, convertido de `evacuacion.mp3`.

Falta proporcionar `rwt.wav`; no se reutiliza un audio sísmico o de simulacro
para una prueba rutinaria porque comunicaría un evento distinto al recibido.

El daemon los reproduce por `plughw:CARD=Headphones,DEV=0`, correspondiente al
jack analógico de la Raspberry Pi 4 instalada. Se recomienda WAV PCM de 16 bits
a 44.1 o 48 kHz. ALSA adapta canales y frecuencia mediante `plughw`.

La ausencia o falla de un archivo se registra en el diagnóstico, pero nunca
impide activar los LED, actualizar la pantalla ni continuar la recepción SAME.
