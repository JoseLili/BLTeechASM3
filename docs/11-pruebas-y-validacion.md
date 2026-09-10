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
