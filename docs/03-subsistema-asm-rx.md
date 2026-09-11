# Subsistema ASM-RX

## Objetivo

ASM-RX reemplaza al receptor comercial cerrado y debe ser propio, reproducible, diagnosticable y fabricable. Recibirá C1–C7, producirá audio inteligible y señal estable para AFSK, admitirá configuración local y reportará fallas sin depender de internet.

## Implementación actual — Carrier v3.1 Rev A

- SA818S-V VHF montado como U12, alimentado a 5 V y con salida `AF_OUT` hacia
  WM8960.
- UART0 de la Raspberry Pi mediante GPIO14/GPIO15 y alias `/dev/serial0`, a
  9600 8N1.
- PTT y PD tienen pull-up físico a 3.3 V: transmisión no se expone en software
  y el módulo permanece habilitado en recepción.
- SMA de 50 Ω en J10.

`VALIDADO`: el 10 de septiembre de 2026 el módulo aceptó la secuencia GOLD y
devolvió exactamente el grupo aplicado mediante `AT+DMOREADGROUP`.

`VALIDADO`: el 11 de septiembre de 2026 una transmisión RWT recorrió la cadena
real SA818S-V → `AF_OUT` → entrada derecha/RINPUT1 del WM8960. La captura
`48 kHz/S32_LE/estéreo`, convertida desde el canal derecho a
`22.05 kHz/S16_LE/mono`, fue reconocida por `multimon-ng` como
`ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-` y tres terminadores `NNNN`.
Esta evidencia confirma la ruta funcional; todavía no establece sensibilidad,
SNR, BER ni márgenes eléctricos de producción.

## Variantes futuras

- `IMPLEMENTADO` en la revisión actual: NiceRF SA818S-V.
- `POSPUESTO`: daughterboards SA818S/DRA818V siguen siendo una posible evolución,
  pero no describen el hardware Carrier v3.1 Rev A ya fabricado.
- El contrato de aplicación permanece independiente del modelo para conservar
  capacidad de evaluación futura.

## Criterios de comparación

Sensibilidad, ruido, inteligibilidad, calidad de decodificación AFSK, inmunidad a interferencia, reproducibilidad, consumo, control, disponibilidad y fabricabilidad. Los umbrales cuantitativos son `PENDIENTE`.

## Canales confirmados por el contexto del proyecto

| Canal | Frecuencia MHz |
|---|---:|
| C1 | 162.400 |
| C2 | 162.425 |
| C3 | 162.450 |
| C4 | 162.475 |
| C5 | 162.500 |
| C6 | 162.525 |
| C7 | 162.550 |

`DECIDIDO`: la frecuencia se deriva del canal; no son valores configurables independientes.

## Perfil GOLD y controlador

```text
AT+DMOCONNECT
AT+DMOSETGROUP=1,<frecuencia>,<frecuencia>,0000,0,0000
AT+DMOSETVOLUME=6
AT+SETFILTER=0,0,0
AT+DMOREADGROUP
```

`IMPLEMENTADO`: `Sa818SerialReceiver` envía la configuración completa, exige
respuesta exitosa a cada comando y sólo informa éxito cuando la lectura de
vuelta coincide exactamente. Su API no contiene PTT ni operación de
transmisión. La sintaxis y las respuestas se contrastaron con el
[manual oficial SA818S de NiceRF](https://www.nicerf.com/upload/20250814/d374728c4b5426c63631449da8745cc6.pdf?file_name=SA818S+1W+Embedded+walkie+talkie+module+V1.7.pdf).

## Preguntas abiertas

- ¿Qué límites cuantitativos de nivel, impedancia, ancho de banda y ruido debe
  cumplir `AF_OUT` para producción, aunque la ruta actual ya decodifica RWT?
- ¿Cómo se define y detecta una falla de recepción?
- ¿Qué interfaz usará una eventual daughterboard posterior a Carrier v3.1 Rev A?

## Relacionados

[ADR-002](adr/ADR-002-reemplazo-de-receptor-cerrado.md), [ADR-011](adr/ADR-011-sa818-uart-rx-only.md), [ADR-016](adr/ADR-016-perfil-audio-wm8960-y-gold-same.md) y [pruebas](11-pruebas-y-validacion.md).
