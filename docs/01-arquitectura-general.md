# Arquitectura general

## Decisiones vigentes

- `DECIDIDO`: arquitectura nueva, modular y por capas.
- `DECIDIDO`: el dominio no depende de Linux, Raspberry Pi ni librerías de hardware.
- `DECIDIDO`: los efectos laterales se acceden mediante puertos.
- `IMPLEMENTADO`: distribución Python bajo `src/asm` con `domain`,
  `application`, `infrastructure` y `config`.

## Vista física

La Raspberry Pi 4 ejecuta estados, reglas, interfaz, audio, diagnóstico y supervisión. La carrier concentra energía, controles, indicadores, I²C y aislamiento Mean Well. ASM-RX es una daughterboard independiente que recibe y demodula VHF.

## Vista de software

```text
Entradas físicas / mensajes
          ↓
adaptadores de infraestructura
          ↓
puertos de aplicación → casos de uso
          ↓
dominio: modelos, estados y prioridades
          ↓
puertos de salida → display, LEDs, audio, almacenamiento y watchdog
```

`domain` contiene reglas puras; `application` coordina casos de uso y declara puertos; `infrastructure` adapta GPIO, I²C, receptor, audio y persistencia; `config` carga y valida configuración sin introducir reglas de negocio.

## Estructura implementada

```text
src/asm/{domain,application,infrastructure,config}
tests/{unit,integration,fakes,fixtures}
```

Los contratos aíslan dominio y aplicación del hardware. Los adaptadores reales
cubren actualmente OLED, GPIO, PCF8574, SA818, WM8960/ALSA, persistencia y RTC.

## Restricciones

- La frecuencia se deriva del canal.
- SA818S y DRA818V deberán compartir un contrato de receptor.
- GPIO crudo, interpretación post-opto y estado funcional son capas distintas.
- I²C no se usa para audio continuo.

## Pendientes arquitectónicos

- `PENDIENTE`: enlace de control y transporte de audio de ASM-RX.
- `IMPLEMENTADO`: primer runtime productivo como daemon único supervisado por
  systemd, con pipeline SAME hijo y releases identificados por commit.
- `PENDIENTE`: integrar en ese runtime los botones operativos, menú, Mean Well
  y watchdog de progreso sin crear escritores concurrentes de OLED o
  GPIO.
- `IMPLEMENTADO`: RWT y EQW disparan WAV no bloqueante por el jack analógico
  antes de LED y OLED; el mismo servicio está conectado al controlador de
  Simulacro/Evacuación usado por la demo física.

## Documentos relacionados

[Lógica](04-logica-de-negocio.md), [interfaces](07-interfaces-de-hardware.md), [ADR-001](adr/ADR-001-arquitectura-greenfield.md) y [ADR-006](adr/ADR-006-separacion-dominio-hardware.md).
