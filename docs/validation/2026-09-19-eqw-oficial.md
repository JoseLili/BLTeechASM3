# Validación de campo: EQW oficial del 2026-09-19

## Resultado

`VALIDADO`: el prototipo Carrier v3.1 Rev A recibió, aceptó y presentó una
alerta sísmica oficial mediante su cadena RF real. La prueba se ejecutó con la
versión `2c3ca36` y el servicio `asm-blteech.service`.

## Cabecera recibida

```text
ZCZC-CIV-EQW-000000+0005-832326-XDIF/005-
```

- Recepción local: `2026-09-19 11:52:04` (`America/Mexico_City`).
- Registro UTC: `2026-09-19T17:52:04.294206+00:00`.
- Originador: `CIV`.
- Evento: `EQW`.
- Área: `000000`, todas las unidades.
- Vigencia declarada: `+0005`, equivalente a 300 segundos.
- Emisor conservado como metadato: `XDIF/005`.

## Evidencia observada

El registro persistente contiene, en orden:

1. `AUDIO.PLAYBACK.STARTED` para `START_EQW`, usando
   `assets/audio/eqw.wav`.
2. `SAME.HEADER.ACCEPTED` con la cabecera completa y 300 segundos de vigencia.
3. `DISPLAY.SAFE_WINDOW.STARTED` para actualizar la OLED sin mantener dos
   escritores concurrentes.
4. `SAME.VISIBLE.CHANGED` de `RWT` a `EQW`, demostrando la preempción por
   prioridad.
5. Dos terminadores `NNNN`, registrados sin cancelar la vigencia.
6. `AUDIO.PLAYBACK.COMPLETED` a las `17:53:03.946738+00:00`, después de la
   reproducción completa del WAV.

El journal de systemd publicó simultáneamente:

```text
SAME outcome=ACCEPTED line=EAS: ZCZC-CIV-EQW-000000+0005-832326-XDIF/005-
SAME outcome=END_OF_MESSAGE line=EAS: NNNN
SAME outcome=END_OF_MESSAGE line=EAS: NNNN
```

## Alcance de la validación

La prueba valida conjuntamente antena, SA818, ruta analógica hacia WM8960,
captura ALSA, conversión SoX, demodulación `multimon-ng`, parser SAME, prioridad
EQW, audio por jack, actualización OLED y bitácora persistente. No fue una
inyección de software ni una transmisión sintética local.

El HW-084 estaba conectado sin batería de respaldo. Su conservación de hora
ante pérdida total de energía queda pendiente de repetir después de instalarla;
esto no invalida la recepción RF observada.
