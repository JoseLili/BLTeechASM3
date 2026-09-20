# ADR-020: supervisión horaria de recepción RWT

- Estado: aceptado e implementado
- Fecha: 2026-09-19

## Contexto

Las pruebas RWT oficiales se esperan cada tres horas a las `02:45`, `05:45`,
`08:45`, `11:45`, `14:45`, `17:45`, `20:45` y `23:45`, hora local. La
observación de campo del 2026-09-19 demostró que una cabecera completa puede
llegar antes de la hora nominal: la prueba asociada a `17:45` fue recibida a
las `17:37`.

La comprobación de puntualidad no debe modificar la vigencia codificada en la
trama. Por ejemplo, una cabecera `+0300` recibida a las `17:37` vence a las
`20:37`, aunque satisfaga la prueba horaria de `17:45`.

## Decisión

- Cada horario nominal usa una ventana local de ±15 minutos.
- Solo una cabecera RWT completa y aceptada satisface la ventana; `NNNN`,
  fragmentos y EQW no cuentan.
- La ausencia se declara al cerrar el margen posterior y genera
  `RWT.SCHEDULE.MISSED` con severidad `WARNING`.
- Una recepción válida genera `RWT.SCHEDULE.RECEIVED` y conserva hora nominal
  y hora real en contexto estructurado.
- La pantalla muestra el fallo durante diez segundos y después vuelve a
  standby para proteger la demodulación. Enter permite volver a consultar el
  estado en el pie de la pantalla.
- El fallo horario no detiene el decoder, no apaga la escucha y nunca impide
  que un EQW tenga prioridad.

## Consecuencias

La ausencia de una prueba deja de confundirse con la caducidad de un aviso. El
historial `notices.jsonl` permite reconstruir recepciones al reiniciar, mientras
que el supervisor vuelve a evaluar la última ventana cerrada y deja evidencia
en `diagnostics.jsonl`.

La ventana de ±15 minutos es una decisión operacional inicial sustentada por
la recepción real de `17:37`. Debe revisarse si la autoridad publica una
tolerancia normativa distinta o si la campaña de campo muestra mayor deriva.
