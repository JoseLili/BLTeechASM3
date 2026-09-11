# ASM BLTeech v3

## Estado del repositorio

Este repositorio inicia **desde cero**. No es una migración directa del código de ASM v2.x y no debe asumir compatibilidad con archivos, servicios, clases, GPIO, dependencias o decisiones heredadas.

La versión v3 conserva el conocimiento funcional aprendido en prototipos anteriores, pero su arquitectura de software se definirá como un sistema nuevo, modular, comprobable y orientado a producción y certificación.

## Propósito

ASM BLTeech v3 es un sistema de difusión secundaria para alertamiento sísmico basado en Raspberry Pi 4, una carrier board propia y un subsistema receptor VHF propio.

El objetivo principal es eliminar la dependencia de receptores comerciales cerrados como Midland y desarrollar una cadena de recepción controlada por BLTeech:

```text
Antena VHF
    ↓
ASM-RX: recepción y demodulación FM
    ↓
Audio inteligible + señal apta para AFSK
    ↓
Raspberry Pi 4: decodificación, validación y reglas
    ↓
Audio, OLED, LEDs, bitácora y salidas del sistema
```

## Objetivo central del receptor

El subsistema ASM-RX deberá ser propio, reproducible, diagnosticable y fabricable en serie. Debe:

- Recibir los siete canales VHF FM autorizados:
  - C1: 162.400 MHz
  - C2: 162.425 MHz
  - C3: 162.450 MHz
  - C4: 162.475 MHz
  - C5: 162.500 MHz
  - C6: 162.525 MHz
  - C7: 162.550 MHz
- Producir audio claro para escucha humana de avisos de emergencia.
- Entregar una señal demodulada estable para decodificación AFSK.
- Permitir selección de canal desde la interfaz local.
- Detectar y reportar fallas de recepción.
- Operar sin depender de internet.
- Generar evidencia y bitácoras útiles para validación y certificación.

## Arquitectura física

### Raspberry Pi 4

Es el cerebro del sistema. Se encargará de:

- Máquina de estados.
- Decodificación y validación de mensajes.
- Motor de reglas y prioridades.
- Interfaz OLED.
- Lectura de botones.
- Control de LEDs.
- Supervisión de energía.
- Configuración del receptor.
- Reproducción de audio.
- Bitácora, diagnóstico y watchdog.

### Carrier board

Placa de dos capas conectada a la Raspberry Pi mediante header de 40 pines. Integra:

- Entrada de energía desde Mean Well LAD-120A.
- Conversión a 5 V para Raspberry Pi mediante Mini560.
- Tres botones de panel.
- Cuatro LEDs indicadores.
- Bus I²C para OLED, RTC y EEPROM.
- Entradas aisladas mediante PC817 para estados de Mean Well.
- Borneras y conexiones robustas hacia el gabinete.
- Plano de tierra para reducir ruido y mejorar retornos.

El amplificador de audio se alimenta fuera de la carrier.

### ASM-RX

Será una daughterboard independiente. Se evaluarán dos variantes:

- `ASM-RX-SA818S v0.1` con NiceRF SA818S-V.
- `ASM-RX-DRA818V v0.1` con Dorji DRA818V.

Ambas compartirán una arquitectura general:

- Entrada de antena SMA de 50 Ω.
- Alimentación limpia dedicada.
- UART de configuración.
- PTT fijado por hardware en recepción.
- Enable/Power Down controlado.
- Salida AF_OUT.
- Puntos de prueba.
- Posibilidad de agregar protección y filtrado RF.

La selección final se hará mediante pruebas comparativas de sensibilidad, ruido, audio, decodificación AFSK, inmunidad a interferencias y reproducibilidad.

## Inventario actual de GPIO

La siguiente asignación proviene del inventario de pines de la carrier y se considera la referencia actual de hardware. Las polaridades funcionales deberán aislarse en drivers y validarse con el hardware real.

### Botones

Los botones son normalmente abiertos y se leen con pull-up; por lo tanto, una pulsación normalmente produce nivel activo bajo.

| Función | GPIO BCM | Pin físico |
|---|---:|---:|
| Simulacro | GPIO17 | 11 |
| Paro / emergencia | GPIO27 | 13 |
| Evacuación | GPIO22 | 15 |

### LEDs indicadores

Los LEDs se consideran activos en alto mediante resistencia serie de 220–330 Ω.

| LED | GPIO BCM | Pin físico | Uso previsto |
|---|---:|---:|---|
| Verde | GPIO23 | 16 | Espera / sistema operativo |
| Ámbar | GPIO24 | 18 | Simulacro / evacuación / advisory |
| Rojo | GPIO25 | 22 | Alerta sísmica / falla / paro |
| Energía | GPIO4 | 7 | Estado de alimentación |

La semántica definitiva de cada LED debe congelarse antes de producción.

### Bus I²C

| Señal | GPIO BCM | Pin físico |
|---|---:|---:|
| SDA1 | GPIO2 | 3 |
| SCL1 | GPIO3 | 5 |

Dispositivos previstos:

| Dispositivo | Dirección actual |
|---|---:|
| OLED SSD1306 | 0x3C |
| LCD PCF8574, si se usa | 0x27 |
| RTC DS3231 | 0x68 |
| EEPROM AT24C32 | 0x57 |

Debe existir un único diseño consciente de pull-ups. Los módulos I²C pueden incluir resistencias propias en paralelo.

### Señales Mean Well actualmente mapeadas

| Función física | GPIO BCM | Pin físico |
|---|---:|---:|
| AC OK / AC FAIL | GPIO5 | 29 |
| Estado de carga / batería llena | GPIO6 | 31 |
| Batería desconectada o invertida | GPIO13 | 33 |
| Batería baja / normal | GPIO26 | 37 |
| Descarga / operación desde batería | GPIO12 | 32 |

Estas señales pasan por optoacopladores PC817. El software deberá separar:

```text
GPIO crudo → interpretación eléctrica post-opto → estado funcional → reglas del sistema
```

No se debe dispersar lógica invertida en el código de negocio.

### UART

| Señal | GPIO BCM | Pin físico | Estado |
|---|---:|---:|---|
| TXD | GPIO14 | 8 | Reservado / opcional |
| RXD | GPIO15 | 10 | Reservado / opcional |

Aún no se considera decidido que este UART sea el enlace definitivo con ASM-RX. Puede usarse UART GPIO, USB-UART u otra interfaz durante desarrollo. La decisión debe documentarse mediante ADR.

### Pines reservados

| Función | GPIO BCM | Pin físico |
|---|---:|---:|
| ID_SD | GPIO0 | 27 |
| ID_SC | GPIO1 | 28 |

Se reservan para funciones especiales del ecosistema HAT/EEPROM y no deben reutilizarse sin una decisión explícita.

### GPIO libres identificados actualmente

GPIO4, GPIO18, GPIO10, GPIO9, GPIO11, GPIO8, GPIO7, GPIO12, GPIO16, GPIO20, GPIO21 y GPIO26 aparecen como libres o experimentales en el inventario actual.

La disponibilidad real debe validarse contra futuras interfaces de audio, UART, SPI y ASM-RX antes de asignarlos.

## Mean Well LAD-120A

### Pinout funcional de CN2

| Pin CN2 | Función |
|---:|---|
| 1 | AC OK |
| 2 | Battery disconnected / reverse polarity |
| 3 | Battery low |
| 4 | Retorno común de señales |
| 5 | Battery full |
| 6 | Discharge / operación desde batería |
| 7–8 | Forced Start mediante contacto |

Las salidas 1, 2, 3, 5 y 6 son de tipo open-collector/open-drain funcional: requieren polarización externa, soportan hasta 50 VDC externos y una corriente máxima de hundimiento de 30 mA según la información técnica revisada.

Los pines 7 y 8 son una entrada de control y no una salida de estado.

### Estado actual de validación

- [VALIDADO] Orientación física del header de la carrier.
- [VALIDADO] Cambio de flanco al puentear una señal contra el pin 4.
- [VALIDADO] Ruta básica entrada → PC817 → GPIO en pruebas con jumper.
- [PENDIENTE] Prueba con una LAD-120A real.
- [PENDIENTE] Medición de niveles y tiempos de transición reales.
- [DECIDIDO] En Carrier v3.1 Rev A la salida PC817 activa lleva el GPIO a LOW.
- [DECIDIDO] `Discharge` corresponde a GPIO12 y batería baja a GPIO26.
- [PENDIENTE] Validar condiciones y tiempos con una LAD-120A real.

El mapa de cinco señales de Carrier v3.1 Rev A reemplaza el inventario
preliminar de cuatro GPIO.

## Lógica de botones

### Operación normal

| Botón | Acción |
|---|---|
| Simulacro | Iniciar simulacro |
| Evacuación | Iniciar evacuación |
| Paro | Detener el evento permitido y generar bitácora |

### Modo técnico

El cambio de canal es una función de instalación y mantenimiento.

Condiciones de acceso:

- Sistema en espera.
- Sin evento activo.
- Combinación prolongada, por ejemplo Simulacro + Paro.

Funciones dentro del menú:

| Botón físico | Función técnica |
|---|---|
| Simulacro | Anterior / disminuir |
| Evacuación | Siguiente / aumentar |
| Paro corto | Confirmar |
| Paro largo | Regresar / cancelar |

Flujo de cambio de canal:

```text
Seleccionar C1–C7
    ↓
Aplicar temporalmente al receptor
    ↓
Verificar respuesta y estado
    ↓
Confirmar
    ↓
Guardar configuración
```

Un EQW válido debe interrumpir inmediatamente cualquier menú técnico.

## Eventos y prioridades

Prioridad funcional prevista:

```text
EQW
 ↓
Evacuación
 ↓
Simulacro
 ↓
RWT
 ↓
Configuración / espera
```

`Paro` es una orden manual de interrupción y debe quedar registrada.

Estados conceptuales iniciales:

- `BOOT`
- `SELF_TEST`
- `IDLE`
- `TECH_MODE`
- `RWT_ACTIVE`
- `SIMULACRO_ACTIVE`
- `EVACUACION_ACTIVE`
- `EQW_ACTIVE`
- `STOPPED`
- `RECEIVER_FAULT`
- `POWER_FAULT`
- `MAINTENANCE_REQUIRED`

## Arquitectura de software objetivo

```text
asm/
├── domain/
│   ├── events
│   ├── states
│   ├── priorities
│   └── models
├── application/
│   ├── services
│   ├── use_cases
│   └── ports
├── infrastructure/
│   ├── gpio
│   ├── i2c
│   ├── display
│   ├── rtc
│   ├── storage
│   ├── meanwell
│   ├── receiver
│   ├── audio
│   └── logging
├── config/
├── tests/
└── main.py
```

Principios:

- El dominio no debe depender de GPIO, I²C, Linux ni librerías de hardware.
- Los drivers deben exponer estados semánticos, no niveles eléctricos crudos.
- SA818S y DRA818V deben implementar una interfaz común de receptor.
- El sistema debe poder ejecutarse en simulación sin hardware real.
- Los efectos laterales deben estar detrás de puertos e interfaces.
- La lógica de prioridad debe probarse con tests unitarios.

## Configuración persistente

Ejemplo conceptual:

```yaml
system:
  version: 3
  site: pendiente
  region: CDMX

receiver:
  model: pending
  channel: 7
  frequency_mhz: 162.550
  squelch: 2

hardware:
  carrier_revision: pending
  receiver_revision: 0.1

power:
  source: LAD-120A
```

La frecuencia debe derivarse del canal para evitar contradicciones.

## Etiquetas de madurez

La documentación debe distinguir:

- `VALIDADO`: comprobado físicamente.
- `CONFIRMADO`: respaldado por documentación oficial.
- `DECIDIDO`: decisión de arquitectura aceptada.
- `PROPUESTO`: sujeto a revisión.
- `PENDIENTE`: falta implementar o comprobar.
- `DESCARTADO`: evaluado y rechazado con motivo.

## Estado actual del proyecto

### Validado

- Carrier fabricada en cinco unidades.
- Alimentación por header funcional.
- OLED, RTC y EEPROM funcionales.
- Botones y LEDs funcionales.
- Cuatro de cinco optoacopladores respondieron en pruebas.
- Pinout físico de CN2 identificado.
- Ruta de señales opto–GPIO probada con jumper.
- SA818S-V configurado por UART y ruta real SA818S-V → WM8960 → GOLD →
  `multimon-ng` decodificando una RWT.
- WM8960 enumerado para captura/salida, con HAL diagnóstica y reproducción WAV
  interrumpible.

### Pendiente

- Reemplazar U7 dañado por calor.
- Probar con LAD-120A real.
- Diseñar ASM-RX-SA818S v0.1.
- Diseñar ASM-RX-DRA818V v0.1.
- Comparar receptores.
- Implementar el stream continuo y supervisor del decoder SAME sobre el perfil
  de audio GOLD ya congelado.
- Definir enlace final de control con ASM-RX.
- Congelar semántica de LEDs.
- Implementar software greenfield.
- Crear pruebas de negocio y simuladores de hardware.

## Documentación prevista

```text
docs/
├── 00-contexto-y-objetivos.md
├── 01-arquitectura-general.md
├── 02-carrier-board.md
├── 03-subsistema-asm-rx.md
├── 04-logica-de-negocio.md
├── 05-maquina-de-estados.md
├── 06-eventos-y-prioridades.md
├── 07-interfaces-de-hardware.md
├── 08-configuracion-y-modo-tecnico.md
├── 09-energia-meanwell.md
├── 10-logging-y-diagnostico.md
├── 11-pruebas-y-validacion.md
├── 12-requisitos-certificacion.md
└── adr/
```

Este README es la fuente inicial de contexto. Las decisiones detalladas deberán moverse progresivamente a documentos especializados y ADR sin duplicar información contradictoria.
