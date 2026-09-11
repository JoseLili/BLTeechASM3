# Interfaces de hardware

## Separación obligatoria

```text
GPIO crudo → interpretación eléctrica post-opto → estado funcional → reglas
```

`DECIDIDO`: las polaridades se encapsulan en adaptadores; nunca se dispersan por el dominio.

## Inventario actual

### Botones

| Función | BCM | Pin | Estado |
|---|---:|---:|---|
| Simulacro | GPIO17 | 11 | normalmente abierto, pull-up, activo bajo previsto |
| Paro | GPIO27 | 13 | normalmente abierto, pull-up, activo bajo previsto |
| Evacuación | GPIO22 | 15 | normalmente abierto, pull-up, activo bajo previsto |

Primera validación física:

- `VALIDADO`: Simulacro corresponde a GPIO17, permanece `HIGH` en reposo y cambia a `LOW` al presionar.
- `VALIDADO`: una pulsación de 6.599 s produjo un solo `PRESSED` y un solo `RELEASED` con debounce de 50 ms.
- `PROPUESTO`: mantener 50 ms como debounce inicial hasta repetir muestras cortas, largas y rápidas.
- `VALIDADO`: Paro corresponde a GPIO27, activo en bajo, y produjo un único ciclo completo.
- `VALIDADO`: Evacuación corresponde a GPIO22, activo en bajo, y produjo un único ciclo completo.
- `VALIDADO`: la prueba conjunta reconoció los tres botones sin cruces de mapeo ni duplicados observados.
- `VALIDADO` mediante pruebas: `GpioButtonPanel` encapsula BCM, pull-up, debounce y callbacks; entrega únicamente comandos semánticos y protege con exclusión mutua el intérprete compartido.
- `PENDIENTE`: validar físicamente la cadena GPIO → política → comando antes de conectarla a estados.

### LEDs

| Función | BCM | Pin | Estado |
|---|---:|---:|---|
| Verde | GPIO23 | 16 | activo alto mediante resistencia serie |
| Ámbar | GPIO24 | 18 | activo alto mediante resistencia serie |
| Rojo | GPIO25 | 22 | activo alto mediante resistencia serie |
| Energía | GPIO4 | 7 | activo alto mediante R39 330 Ω |

`IMPLEMENTADO`: `GpioIndicatorPanel` encapsula el mapa activo-alto, aplica
siempre los cuatro valores como un estado completo y apaga todo antes de liberar
los GPIO. La herramienta HIL recorre AVISO, PRECAUCIÓN, ALERTA y ENERGÍA en
modo one-hot.

`IMPLEMENTADO`: `SameIndicatorSupervisor` produce parpadeo lento no bloqueante,
inicialmente un segundo encendido y uno apagado. RWT usa AVISO/amarillo durante
`TTTT`; EQW usa ALERTA/rojo y lo preempta mientras esté vigente. El LED de
ENERGÍA permanece estable. La cadencia queda explícita para poder ajustarla sin
cambiar el parser ni la vigencia.

`PENDIENTE`: confirmar visualmente cada rótulo y cerrar la composición entre
avisos SAME, simulacro/evacuación y fallas concurrentes.

### I²C

| Señal/dispositivo | BCM / dirección | Pin |
|---|---:|---:|
| SDA1 | GPIO2 | 3 |
| SCL1 | GPIO3 | 5 |
| WM8960 | `0x1A` | — |
| PCF8574P, botones de configuración | `0x20` | INT en GPIO16/pin 36 |
| OLED SSD1306 | `0x3C` | — |
| RTC DS3231 | `0x68` | — |
| EEPROM AT24C32 | `0x57` | — |

La interfaz local usa exclusivamente la OLED SSD1306; el LCD de versiones
anteriores no forma parte de Carrier v3.1 Rev A.

#### Botones de configuración PCF8574P

`DECIDIDO`: P0–P6 corresponden, en orden, a Arriba, Abajo, Izquierda, Derecha,
Enter, Regresar y Escucha. P7 queda reservado. Reposo es `0xFF`; una pulsación
lleva su bit a LOW. INT permanece HIGH en reposo y señala cambios mediante LOW
en GPIO16.

`DECIDIDO`: estos controles navegan y editan los submenús del sistema. No
reemplazan ni condicionan Simulacro, Evacuación o Paro, que permanecen como
entradas GPIO directas independientes del bus I²C.

`IMPLEMENTADO`: `Pcf8574MenuButtons` libera los ocho puertos con `0xFF`, difiere
las lecturas I²C fuera del callback GPIO y entrega comandos semánticos sin
exponer bytes ni polaridad a la aplicación.

`PENDIENTE`: inventariar pull-ups poblados y resistencia equivalente. `DECIDIDO`: I²C no transportará audio continuo.

#### Validación inicial en Raspberry Pi

- `VALIDADO`: `/dev/i2c-1` corresponde al bus de la carrier.
- `VALIDADO`: OLED SSD1306 128×64 detectada en `0x3C` y texto visible correctamente.
- `VALIDADO`: EEPROM detectada en `0x57`.
- `VALIDADO`: RTC en `0x68`, reclamado por el driver del kernel y expuesto como `/dev/rtc0`.
- `DECIDIDO`: el primer adaptador OLED usará `python3-luma.oled`, instalado globalmente mediante Debian `apt`; véase [ADR-008](adr/ADR-008-adaptador-oled-luma.md).
- `VALIDADO`: `LumaOledDisplay` presenta la vista `BOOT` producida por `SystemController`.
- `DECIDIDO`: la animación de marca solo se permite durante arranque; EQW, RWT, simulacro y evacuación usan vistas inmediatas sin animación.
- `VALIDADO`: la animación de marca configurada a cinco segundos se observó completa y terminó en la vista `BOOT` estable.

### Mean Well actualmente mapeada

| Función física | BCM | Pin |
|---|---:|---:|
| AC OK / AC FAIL | GPIO5 | 29 |
| Carga / batería llena | GPIO6 | 31 |
| Batería desconectada o invertida | GPIO13 | 33 |
| Batería baja / normal | GPIO26 | 37 |
| Descarga / operación UPS | GPIO12 | 32 |

- `DECIDIDO`: el mapa anterior corresponde a la PCB Carrier v3.1 Rev A y
  reemplaza el inventario preliminar que usaba GPIO19 y omitía `Discharge`.
- `DECIDIDO`: opto excitado conduce la salida a LOW; la inversión queda dentro
  de `GpioPowerMonitor`.
- `PENDIENTE`: validar condiciones, combinaciones y tiempos con una LAD-120A real.

### UART del receptor SA818S-V

| Señal | BCM | Pin |
|---|---:|---:|
| TXD0 → U12 RXD | GPIO14 | 8 |
| RXD0 ← U12 TXD | GPIO15 | 10 |

`VALIDADO`: `/dev/serial0` apunta a `ttyAMA0`, UART0 opera a 9600 8N1,
`serial-getty@ttyAMA0` está deshabilitado y GPIO14/GPIO15 están en función
TXD0/RXD0. El SA818S-V respondió a los cinco comandos del perfil GOLD.

`IMPLEMENTADO`: el adaptador RX-only configura C1–C7, volumen, squelch y
filtros, y exige lectura de vuelta exacta. No existe API software de PTT.

### Audio WM8960

| Función | Contrato validado |
|---|---|
| Tarjeta ALSA | `wm8960soundcard` |
| PCM dúplex | `hw:wm8960soundcard,0` |
| Captura física | `S32_LE`, 48000 Hz, 2 canales |
| Entrada de radio | canal derecho, índice 1, RINPUT1 |
| Entrada del decoder GOLD | `S16_LE`, 22050 Hz, mono |

`IMPLEMENTADO`: `AlsaAudioHealth` consulta, sin abrir streams, la precarga
`wm8960-audio-board-preload.service` y la presencia exacta de captura/salida.
`AlsaCaptureProbe` realiza únicamente capturas WAV finitas y detecta el caso
anómalo de muestras exactamente en cero; no inventa todavía un umbral de señal
útil. `AlsaAudioPlayer` posee como máximo una reproducción WAV, permite Paro
explícito y no reemplaza audio en curso de forma implícita.

`DECIDIDO`: captura y reproducción son recursos separados. Ningún adaptador
modifica registros I²C o controles de mezclador mientras exista un stream I²S,
porque la carrier ha presentado errores EIO en esa condición. La rama de
monitor podrá aplicar procesamiento independiente; la rama del decoder conserva
el perfil GOLD sin ganancia, normalización, compresor ni filtros digitales.

### Reservados y libres

GPIO0/pin 27 y GPIO1/pin 28 se reservan al ecosistema HAT/EEPROM. GPIO4, 18, 10, 9, 11, 8, 7, 12, 16, 20, 21 y 26 son `PENDIENTE` de validación contra audio, UART, SPI y ASM-RX antes de asignarlos.

## Puertos conceptuales

| Puerto | Responsabilidad semántica | Operaciones sugeridas / preguntas |
|---|---|---|
| `ReceiverPort` | configurar y observar receptor sin conocer módulo | aplicar perfil y devolver estado verificado; implementado para SA818S-V |
| `AudioHealthPort` | informar disponibilidad de precarga/captura/salida | snapshot de solo lectura implementado para WM8960 |
| `AudioPlaybackPort` | reproducir/detener un recurso local | WAV único e interrumpible implementado; selección de recursos pendiente |
| `AudioInputPort` | entregar muestras al decoder SAME | perfil GOLD decidido; streaming, buffering y backpressure pendientes |
| `DisplayPort` | presentar vistas, no primitivas de bus | mostrar estado/menú/falla; `PENDIENTE` límites y refresco |
| `ButtonInputPort` | emitir gestos filtrados | eventos cortos/largos/combinados; `PENDIENTE` umbrales |
| `IndicatorPort` | aplicar los cuatro indicadores como estado completo | adaptador activo-alto implementado; política pendiente |
| `PowerMonitorPort` | entregar `PowerStatus` | snapshot semántico implementado; `PENDIENTE` debounce y reglas de severidad |
| `ClockPort` | tiempo monotónico y civil | ahora/monotónico; `PENDIENTE` sincronización RTC |
| `ConfigurationRepository` | carga y escritura atómica | obtener/guardar/versionar; `PENDIENTE` recuperación |
| `EventLogRepository` | persistir auditoría y diagnóstico | append/consulta/exportación; `PENDIENTE` retención/integridad |
| `WatchdogPort` | informar salud de aplicación | heartbeat/estado; `PENDIENTE` watchdog físico/systemd |

El dominio no conoce SA818S, DRA818V, `gpiozero`, `pigpio`, `smbus` ni `luma.oled`.

## Relacionados

[Carrier](02-carrier-board.md), [ASM-RX](03-subsistema-asm-rx.md), [Mean Well](09-energia-meanwell.md), [ADR-006](adr/ADR-006-separacion-dominio-hardware.md) y [ADR-016](adr/ADR-016-perfil-audio-wm8960-y-gold-same.md).
