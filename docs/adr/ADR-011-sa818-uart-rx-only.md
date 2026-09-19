# ADR-011 — SA818S-V por UART0 con contrato RX-only

## Estado

Aceptado e implementado para Carrier v3.1 Rev A.

## Contexto

La placa fabricada integra el SA818S-V como U12. GPIO14/GPIO15 están conectados
a RXD/TXD del módulo; PTT y PD tienen pull-up físico a 3.3 V. La configuración
es volátil y debe restablecerse en cada arranque. Un fallo parcial no puede
presentarse como receptor listo.

## Decisión

- Usar `/dev/serial0` a 9600 8N1 y mantener deshabilitado el getty serial.
- Representar C1–C7 en el dominio y derivar de allí la frecuencia.
- Aplicar la secuencia completa GOLD: 25 kHz, SQ 0, volumen 6 y filtros 0,0,0.
- Leer el grupo después de configurarlo y exigir coincidencia exacta.
- Exponer solamente `configure(profile)` al sistema. No crear métodos de PTT,
  potencia de transmisión ni envío.
- Distinguir timeout, rechazo del módulo, respuesta inválida y readback distinto.

## Consecuencias

El arranque puede demostrar qué perfil quedó realmente activo y los tests puros
pueden reproducir fallas sin UART. Cambiar de canal reenvía toda la configuración,
lo que evita estados parciales. El readback confirma grupo, frecuencia y squelch;
volumen y filtros sólo quedan confirmados por sus respuestas individuales porque
el protocolo no los incluye en `DMOREADGROUP`.

## Evidencia

El 10 de septiembre de 2026, Carrier v3.1 Rev A respondió:

```text
+DMOCONNECT:0
+DMOSETGROUP:0
+DMOSETVOLUME:0
+DMOSETFILTER:0
+DMOREADGROUP:1,162.5500,162.5500,0000,0,0000
```

La referencia de protocolo es el
[manual oficial SA818S de NiceRF](https://www.nicerf.com/upload/20250814/d374728c4b5426c63631449da8745cc6.pdf?file_name=SA818S+1W+Embedded+walkie+talkie+module+V1.7.pdf).

## Pendiente

Integrar la configuración en el arranque de producción, instrumentar reintentos
acotados y conectar el cambio transaccional de canal con persistencia atómica.
