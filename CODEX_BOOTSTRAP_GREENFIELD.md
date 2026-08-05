# Prompt maestro para Codex CLI — ASM BLTeech v3 greenfield

Estás trabajando en un repositorio nuevo llamado ASM BLTeech v3.

## Condición esencial

Este repositorio inicia desde cero. No existe código legado que debas migrar, conservar o hacer compatible. No inventes archivos heredados, servicios systemd anteriores, clases antiguas, nombres de módulos previos ni dependencias no presentes en el repositorio.

La información funcional y de hardware está contenida en `README.md`. Léelo completo antes de realizar cualquier cambio.

## Objetivo de esta ejecución

Crear la base documental y arquitectónica del proyecto. Todavía no debes implementar la lógica completa de producción ni escribir drivers reales de Raspberry Pi.

Debes transformar el contexto del README en una estructura clara que permita desarrollar posteriormente:

- modelos de dominio;
- lógica de negocio;
- máquina de estados;
- eventos y prioridades;
- interfaces de hardware;
- drivers;
- servicios de aplicación;
- simuladores;
- pruebas unitarias y de integración;
- subsistema receptor ASM-RX;
- supervisión de Mean Well LAD-120A.

## Reglas

1. No asumas compatibilidad con ASM v2.x.
2. No agregues código GPIO real en esta primera ejecución.
3. No elijas librerías de hardware definitivas sin documentar la decisión.
4. No inventes el GPIO faltante de la señal Mean Well `Discharge`.
5. No fijes la polaridad lógica final de las señales Mean Well hasta que exista validación con una LAD-120A real.
6. Mantén separados:
   - nivel GPIO crudo;
   - interpretación eléctrica post-opto;
   - estado funcional del dominio.
7. No asumas que GPIO14/GPIO15 serán necesariamente el UART final de ASM-RX. Debe quedar como decisión pendiente.
8. No uses I²C para audio continuo.
9. La lógica del dominio debe ser independiente de Linux, Raspberry Pi y librerías GPIO.
10. Cualquier supuesto debe etiquetarse como `PROPUESTO` o `PENDIENTE`.

## Trabajo solicitado

### 1. Inspección inicial

- Lista el contenido actual del repositorio.
- Confirma que es un proyecto greenfield.
- Lee `README.md` completo.
- No busques ni solicites archivos legacy.

### 2. Crear estructura documental

Crea:

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

Cada documento debe:

- derivar del README;
- evitar duplicar contenido innecesariamente;
- marcar hechos como VALIDADO, CONFIRMADO, DECIDIDO, PROPUESTO o PENDIENTE;
- incluir preguntas abiertas cuando falten datos;
- enlazar a documentos relacionados.

### 3. Crear ADR iniciales

Crea al menos:

```text
docs/adr/ADR-001-arquitectura-greenfield.md
docs/adr/ADR-002-reemplazo-de-receptor-cerrado.md
docs/adr/ADR-003-asm-rx-como-daughterboard.md
docs/adr/ADR-004-dos-variantes-sa818s-dra818v.md
docs/adr/ADR-005-seleccion-local-de-canal.md
docs/adr/ADR-006-separacion-dominio-hardware.md
```

Formato ADR:

- Estado
- Contexto
- Decisión
- Consecuencias positivas
- Consecuencias negativas
- Alternativas consideradas
- Puntos pendientes

### 4. Definir arquitectura de software, sin implementación real

Propón una estructura Python similar a:

```text
src/asm/
├── domain/
├── application/
├── infrastructure/
├── config/
└── __init__.py

tests/
├── unit/
├── integration/
├── fakes/
└── fixtures/
```

No crees todavía drivers funcionales de GPIO. Puedes crear documentos o archivos de interfaz mínimos solo si ayudan a expresar la arquitectura, pero evita implementar comportamiento de producción.

### 5. Modelos conceptuales

Documenta, sin cerrar todavía todos los campos, los modelos previstos:

- `SystemState`
- `EventType`
- `ReceivedMessage`
- `ValidatedEvent`
- `ReceiverStatus`
- `PowerStatus`
- `ButtonEvent`
- `ChannelConfiguration`
- `HardwareIdentity`
- `DiagnosticEvent`
- `AuditRecord`

Para cada modelo define:

- propósito;
- campos sugeridos;
- invariantes;
- datos de origen;
- consumidores;
- preguntas abiertas.

### 6. Puertos e interfaces

Documenta interfaces conceptuales para:

- `ReceiverPort`
- `AudioInputPort`
- `DisplayPort`
- `ButtonInputPort`
- `LedOutputPort`
- `PowerMonitorPort`
- `ClockPort`
- `ConfigurationRepository`
- `EventLogRepository`
- `WatchdogPort`

El dominio no debe conocer SA818S, DRA818V, gpiozero, pigpio, smbus ni luma.oled.

### 7. Máquina de estados

Documenta los estados:

- BOOT
- SELF_TEST
- IDLE
- TECH_MODE
- RWT_ACTIVE
- SIMULACRO_ACTIVE
- EVACUACION_ACTIVE
- EQW_ACTIVE
- STOPPED
- RECEIVER_FAULT
- POWER_FAULT
- MAINTENANCE_REQUIRED

Incluye:

- eventos de entrada;
- condiciones;
- acciones;
- transiciones válidas;
- transiciones prohibidas;
- comportamiento ante EQW;
- comportamiento ante Paro;
- comportamiento ante fallas concurrentes.

No implementes la máquina todavía.

### 8. Interfaces de hardware

En `docs/07-interfaces-de-hardware.md` registra como fuente actual:

#### Botones

- GPIO17 / pin 11: Simulacro
- GPIO27 / pin 13: Paro
- GPIO22 / pin 15: Evacuación
- Normalmente abiertos con pull-up; activos en bajo por diseño previsto.

#### LEDs

- GPIO23 / pin 16: Verde
- GPIO24 / pin 18: Ámbar
- GPIO25 / pin 22: Rojo
- Activos en alto mediante resistencia serie.

#### I²C

- GPIO2 / pin 3: SDA
- GPIO3 / pin 5: SCL
- OLED 0x3C
- LCD opcional 0x27
- RTC 0x68
- EEPROM 0x57

#### Mean Well actualmente mapeada

- GPIO5 / pin 29: AC OK / AC FAIL
- GPIO6 / pin 31: estado de carga / batería llena
- GPIO13 / pin 33: batería desconectada o invertida
- GPIO19 / pin 35: batería baja / normal

Marca expresamente:

- `PENDIENTE`: GPIO de CN2-6 Discharge.
- `PENDIENTE`: polaridades finales post-opto.
- `PENDIENTE`: validación con LAD-120A real.

#### UART reservado

- GPIO14 / pin 8: TXD opcional
- GPIO15 / pin 10: RXD opcional

No declararlo como enlace definitivo de ASM-RX.

### 9. Plan de pruebas

Crea un plan que separe:

- tests unitarios de dominio;
- tests de máquina de estados;
- tests de prioridad;
- tests de configuración;
- pruebas con fakes de GPIO/I²C/UART;
- pruebas HIL de carrier;
- pruebas con LAD-120A real;
- pruebas de ASM-RX;
- pruebas de interferencia y ruido;
- pruebas de mensajes AFSK;
- pruebas de autonomía y recuperación.

### 10. Resultado esperado

Al terminar esta ejecución entrega:

1. Resumen de archivos creados.
2. Decisiones extraídas del README.
3. Inconsistencias o preguntas abiertas detectadas.
4. Riesgos principales.
5. Orden recomendado para la siguiente iteración.
6. Estado de git diff.

No empieces la implementación completa. Detente después de crear la base documental y el diseño arquitectónico.
