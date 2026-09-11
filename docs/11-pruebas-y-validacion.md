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

Prueba HIL de la política completa:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/indicator_policy_test.py --seconds 1.5
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
