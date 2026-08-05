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

### LEDs

| Función | BCM | Pin | Estado |
|---|---:|---:|---|
| Verde | GPIO23 | 16 | activo alto mediante resistencia serie |
| Ámbar | GPIO24 | 18 | activo alto mediante resistencia serie |
| Rojo | GPIO25 | 22 | activo alto mediante resistencia serie |

`PENDIENTE`: congelar semántica definitiva, patrones y precedencia entre evento y falla.

### I²C

| Señal/dispositivo | BCM / dirección | Pin |
|---|---:|---:|
| SDA1 | GPIO2 | 3 |
| SCL1 | GPIO3 | 5 |
| OLED SSD1306 | `0x3C` | — |
| LCD PCF8574 opcional | `0x27` | — |
| RTC DS3231 | `0x68` | — |
| EEPROM AT24C32 | `0x57` | — |

`PENDIENTE`: inventariar pull-ups poblados y resistencia equivalente. `DECIDIDO`: I²C no transportará audio continuo.

### Mean Well actualmente mapeada

| Función física | BCM | Pin |
|---|---:|---:|
| AC OK / AC FAIL | GPIO5 | 29 |
| Carga / batería llena | GPIO6 | 31 |
| Batería desconectada o invertida | GPIO13 | 33 |
| Batería baja / normal | GPIO19 | 35 |

- `PENDIENTE`: GPIO de CN2-6 `Discharge`; no debe inventarse.
- `PENDIENTE`: polaridades finales post-opto.
- `PENDIENTE`: validación con LAD-120A real y correspondencia exacta CN2-5↔GPIO6.

### UART reservado

| Señal | BCM | Pin |
|---|---:|---:|
| TXD opcional | GPIO14 | 8 |
| RXD opcional | GPIO15 | 10 |

`PENDIENTE`: enlace definitivo de ASM-RX; UART GPIO, USB-UART u otra opción se decidirán mediante ADR.

### Reservados y libres

GPIO0/pin 27 y GPIO1/pin 28 se reservan al ecosistema HAT/EEPROM. GPIO4, 18, 10, 9, 11, 8, 7, 12, 16, 20, 21 y 26 son `PENDIENTE` de validación contra audio, UART, SPI y ASM-RX antes de asignarlos.

## Puertos conceptuales

| Puerto | Responsabilidad semántica | Operaciones sugeridas / preguntas |
|---|---|---|
| `ReceiverPort` | configurar y observar receptor sin conocer módulo | aplicar canal temporal, confirmar, estado; `PENDIENTE` timeout/capacidades |
| `AudioInputPort` | entregar señal/muestras demoduladas | iniciar/detener/leer; `PENDIENTE` formato, tasa y buffering |
| `DisplayPort` | presentar vistas, no primitivas de bus | mostrar estado/menú/falla; `PENDIENTE` límites y refresco |
| `ButtonInputPort` | emitir gestos filtrados | eventos cortos/largos/combinados; `PENDIENTE` umbrales |
| `LedOutputPort` | expresar patrón semántico | aplicar indicación; `PENDIENTE` catálogo y precedencia |
| `PowerMonitorPort` | entregar `PowerStatus` | observar estado/calidad; `PENDIENTE` debounce y desconocidos |
| `ClockPort` | tiempo monotónico y civil | ahora/monotónico; `PENDIENTE` sincronización RTC |
| `ConfigurationRepository` | carga y escritura atómica | obtener/guardar/versionar; `PENDIENTE` recuperación |
| `EventLogRepository` | persistir auditoría y diagnóstico | append/consulta/exportación; `PENDIENTE` retención/integridad |
| `WatchdogPort` | informar salud de aplicación | heartbeat/estado; `PENDIENTE` watchdog físico/systemd |

El dominio no conoce SA818S, DRA818V, `gpiozero`, `pigpio`, `smbus` ni `luma.oled`.

## Relacionados

[Carrier](02-carrier-board.md), [ASM-RX](03-subsistema-asm-rx.md), [Mean Well](09-energia-meanwell.md) y [ADR-006](adr/ADR-006-separacion-dominio-hardware.md).
