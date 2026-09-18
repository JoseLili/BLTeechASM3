# Pruebas y validación

## Estrategia

Las pruebas avanzan de reglas puras a integración simulada y después a hardware real. Cada evidencia identifica versión de software, revisión de carrier/receptor, configuración, instrumentos y resultado.

## Capas

### Unitarias de dominio

- Invariantes de los modelos, canales y frecuencia derivada.
- Validación, vigencia, duplicados y comandos locales cuando las reglas se definan.
- Cero dependencias de Linux o hardware.

### Máquina de estados y prioridad

- Toda transición válida y prohibida.
- Matriz de preempción `EQW > Evacuación > Simulacro > RWT`.
- EQW desde cada estado, incluido `TECH_MODE`.
- Paro permitido/prohibido y auditoría.
- Fallas concurrentes, recuperación y eventos simultáneos.

### Configuración

- Esquema, canal C1–C7, frecuencia derivada, escritura atómica y rollback.
- Cancelación, timeout, reinicio durante guardado y configuración corrupta.

### Integración con fakes

- Fakes controlables de GPIO, I²C, UART, reloj, receptor, audio y almacenamiento.
- Errores, latencias, desconexiones, rebotes, reloj inválido y disco lleno.
- Contratos idénticos para adaptadores SA818S/DRA818V.

### HIL de carrier

- Pinout, niveles, polaridades, debounce, LED, direcciones y pull-ups I²C.
- Arranque, reinicio, carga, ruido, temperatura y recuperación.
- Evidencia específica por cada una de las cinco unidades.

Primera evidencia registrada:

- `VALIDADO`: OLED SSD1306 128×64 en I²C-1 `0x3C`; mostró marco y textos de prueba y se limpió al finalizar.
- `VALIDADO`: botón Simulacro en GPIO17 activo en bajo; una pulsación completa con debounce de 50 ms produjo un único par `PRESSED`/`RELEASED`.
- `VALIDADO`: prueba conjunta de Simulacro/GPIO17, Paro/GPIO27 y Evacuación/GPIO22; los tres ciclos físicos fueron reconocidos correctamente y sin cruces.
- `VALIDADO` mediante dobles: el adaptador GPIO produce los tres comandos semánticos, libera recursos y soporta `HOLD` mediante polling no bloqueante.
- `VALIDADO`: PCF8574P `0x20` entrega botones de menú semánticos y la OLED mostró
  el árbol navegable completo en Carrier v3.1 Rev A.
- `VALIDADO`: SA818S-V sobre `/dev/serial0` aceptó conexión, grupo GOLD C7,
  volumen 6 y filtros 0,0,0; `AT+DMOREADGROUP` devolvió
  `1,162.5500,162.5500,0000,0,0000`.
- `VALIDADO` mediante dobles: timeout, rechazo, escritura UART corta y readback
  distinto impiden reportar una configuración como verificada.
- `VALIDADO` mediante dobles: el editor C1-C7 requiere aplicar/verificar antes
  de guardar; cancelar o fallar la escritura restaura el canal confirmado.
- `VALIDADO`: el SA818S-V cambió físicamente de C7 a C6, leyó de vuelta
  162.5250 MHz y después restauró C7/162.5500 MHz correctamente.
- `VALIDADO` mediante dobles: el monitor de energía exige las cinco señales,
  traduce activo-bajo una sola vez, conserva `UNKNOWN` y libera cada GPIO.
- `OBSERVADO`: sin salidas LAD-120A excitadas, GPIO5/13/26/6/12 permanecieron
  HIGH y el diagnóstico reportó las cinco señales como `CLEAR`.
- `VALIDADO` mediante dobles: cada estado de indicadores escribe los cuatro
  GPIO, elimina salidas residuales y el cierre garantiza todo apagado.
- `EJECUTADO`: la secuencia HIL activó individualmente GPIO23, GPIO24, GPIO25 y
  GPIO4 y finalizó con los cuatro en LOW; confirmación visual aún pendiente.
- `VALIDADO` mediante dobles: cada entrada Mean Well se estabiliza de forma
  independiente, un pulso menor a 250 ms no genera evidencia, `UNKNOWN` se
  muestra como advertencia y todo cambio publicado llega tanto a OLED como al
  registro estructurado.
- `VALIDADO` mediante dobles: la política de indicadores cubre todos los estados,
  conserva ENERGÍA encendido, usa AVISO para RWT, PRECAUCIÓN para
  simulacro/evacuación y ALERTA para EQW o fallas, sin LEDs residuales.
- `EJECUTADO`: la política recorrió físicamente IDLE, RWT, simulacro,
  evacuación, EQW, fallo de energía y STOPPED; al cerrar, GPIO4/23/24/25
  quedaron como entradas LOW. Sigue pendiente confirmar visualmente cada rótulo.
- `OBSERVADO` el 2026-09-10: I²C mostró PCF8574P en `0x20` y WM8960 ocupado en
  `0x1A`, pero no mostró la OLED en `0x3C`. La notificación OLED del supervisor
  queda pendiente de repetir cuando el módulo vuelva a estar visible en el bus.
- `VALIDADO` en pruebas unitarias: prioridades estrictas, preempción ascendente,
  rechazo de eventos iguales/inferiores, Paro permitido en RWT/simulacro/
  evacuación y Paro rechazado durante EQW.
- `VALIDADO` mediante dobles: los comandos GPIO conservan origen `LOCAL_PANEL` y
  la auditoría JSONL persiste decisiones aceptadas y rechazadas con `fsync`.
- `VALIDADO` el 2026-09-10: la OLED volvió a aparecer físicamente en `0x3C`,
  mostró el smoke test durante tres segundos y se limpió al finalizar.
- `EJECUTADO` el 2026-09-10: OLED y GPIO recorrieron sin error BOOT, SELF_TEST,
  IDLE, RWT, simulacro, evacuación y EQW, con una transición aceptada y emitida
  por cada paso. Sigue pendiente confirmación visual humana de cada cuadro/LED.
- `EJECUTADO`: la demo integrada llegó a IDLE, abrió las cinco entradas de
  energía y creó la auditoría persistente; no se pulsaron botones durante esa
  ventana, por lo que la ruta física botón→estado se debe repetir.
- `VALIDADO` el 2026-09-11: ALSA enumeró `wm8960soundcard` para captura y
  reproducción, y la precarga del codec quedó `active`.
- `VALIDADO` el 2026-09-11: una captura HIL limitada a dos segundos produjo
  96000 cuadros `48 kHz/S32_LE/estéreo`; en el canal derecho se midió pico
  normalizado `0.035966873` y RMS `0.009449328`, descartando la falla de ceros
  exactos en esa ejecución.
- `EJECUTADO` el 2026-09-11: una reproducción WAV silenciosa de un segundo
  finalizó correctamente en el PCM WM8960. Esto valida apertura y control del
  stream, no la salida acústica ni el cableado BTL del altavoz.
- `EJECUTADO` el 2026-09-18: ALSA enumeró el jack de Pi 4 como
  `plughw:CARD=Headphones,DEV=0`; reprodujo un WAV silencioso mientras el daemon
  conservó activos `arecord`, SoX y `multimon-ng`, sin reinicio del servicio.
- `IMPLEMENTADO`: RWT, EQW, Simulacro y Evacuación seleccionan sus WAV locales;
  el inicio se solicita antes de LED/OLED, EQW preempta audios inferiores y un
  archivo ausente se registra sin perder las demás salidas.
- `EJECUTADO` el 2026-09-11: el diagnóstico de audio se dibujó por tres segundos
  en la OLED y se limpió sin error; la confirmación visual humana de los cuatro
  rótulos sigue pendiente.
- `VALIDADO` por el usuario el 2026-09-11: una RWT real capturada desde
  `hw:wm8960soundcard,0` y convertida del canal derecho a GOLD fue decodificada
  por `multimon-ng 1.3.1` como
  `ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-`, seguida por tres `NNNN`.
  Es una prueba funcional extremo a extremo, no una medición estadística de BER.
- `VALIDADO` mediante 15 pruebas unitarias: la trama real con área `000000`,
  fecha de seis caracteres y emisor no registrado se acepta; `+0300` produce
  tres horas y `+0001` un minuto. Las tres repeticiones no extienden el plazo,
  `NNNN` no apaga el aviso y EQW/ALERTA preempta RWT/AVISO hasta vencer.
- `EJECUTADO` el 2026-09-11: el carrier aceptó cabeceras sintéticas RWT y EQW,
  mantuvo cada parpadeo no bloqueante durante una ventana acotada de seis
  segundos y apagó los cuatro GPIO al cerrar. Sigue pendiente la confirmación
  visual humana de que los rótulos observados fueron AVISO/amarillo y
  ALERTA/rojo respectivamente.
- `VALIDADO` el 2026-09-11: 237 pruebas unitarias/integración pasaron en la Pi;
  Ruff y mypy finalizaron sin errores sobre 59 archivos fuente.
- `EJECUTADO` el 2026-09-11: el daemon completo mostró BOOT, verificó C7,
  registró `RTC.READY`, abrió `arecord → SoX → multimon-ng` y, al recibir
  SIGTERM, cerró los tres procesos y dejó los indicadores apagados.

Prueba HIL de la política completa:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/indicator_policy_test.py --seconds 1.5
```

Demo integrada de botones directos, OLED, LED, energía y registros:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/operator_panel_demo.py --timeout 180
```

Secuencia visual de prioridades completa:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/priority_oled_test.py --seconds 1.5
```

Prueba visual acotada del parpadeo SAME; detiene y apaga las salidas al concluir,
sin esperar la vigencia completa:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/same_indicator_test.py RWT --seconds 6
PYTHONPATH=src /usr/bin/python3 scripts/same_indicator_test.py EQW --seconds 6
```

Diagnóstico HIL de audio:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/audio_health_test.py
PYTHONPATH=src /usr/bin/python3 scripts/audio_capture_test.py --seconds 2
PYTHONPATH=src /usr/bin/python3 scripts/audio_playback_silence_test.py --seconds 1
PYTHONPATH=src /usr/bin/python3 scripts/audio_health_oled_test.py --seconds 3
```

Daemon receptor en primer plano para una prueba acotada:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/asm_daemon.py \
  --state-file /tmp/asm-receiver.json \
  --diagnostic-log /tmp/asm-diagnostics.jsonl
```

### LAD-120A real

- Tabla de verdad extremo a extremo para CN2-1/2/3/5/6.
- Niveles, transiciones, aislamiento, desconexión/inversión, batería baja/llena y descarga.
- Autonomía, corte/retorno de red, Forced Start y recuperación segura.

### ASM-RX

- Siete canales, sensibilidad, selectividad, squelch, estabilidad y cambio de canal.
- Audio inteligible, niveles/impedancia, ruido e inmunidad a interferencia.
- Pérdida de antena/configuración/alimentación y diagnóstico.
- Comparación reproducible SA818S vs DRA818V.

### AFSK

- Corpus versionado de mensajes válidos, corruptos, truncados, repetidos y caducados.
- Ruido, variación de nivel/frecuencia, interferencia y pérdida de muestras.
- Latencia extremo a extremo y tasas de falsos positivos/negativos.

## Criterios todavía pendientes

Umbrales cuantitativos de sensibilidad, SNR, BER/decodificación, latencia, autonomía, disponibilidad, temperatura, EMC y recuperación. Ninguna prueba se marcará aprobada sin criterio previo y evidencia trazable.

## Relacionados

[ASM-RX](03-subsistema-asm-rx.md), [estados](05-maquina-de-estados.md), [Mean Well](09-energia-meanwell.md) y [certificación](12-requisitos-certificacion.md).
