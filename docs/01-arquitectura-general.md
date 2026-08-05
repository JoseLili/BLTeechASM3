# Arquitectura general

## Decisiones vigentes

- `DECIDIDO`: arquitectura nueva, modular y por capas.
- `DECIDIDO`: el dominio no depende de Linux, Raspberry Pi ni librerías de hardware.
- `DECIDIDO`: los efectos laterales se acceden mediante puertos.
- `PROPUESTO`: distribución Python bajo `src/asm` con `domain`, `application`, `infrastructure` y `config`.

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

## Estructura propuesta

```text
src/asm/{domain,application,infrastructure,config}
tests/{unit,integration,fakes,fixtures}
```

Los directorios creados en esta iteración son deliberadamente vacíos. Los contratos solo se implementarán cuando sus semánticas y pruebas estén acordadas.

## Restricciones

- La frecuencia se deriva del canal.
- SA818S y DRA818V deberán compartir un contrato de receptor.
- GPIO crudo, interpretación post-opto y estado funcional son capas distintas.
- I²C no se usa para audio continuo.

## Pendientes arquitectónicos

- `PENDIENTE`: runtime, versión Python, empaquetado y librerías.
- `PENDIENTE`: enlace de control y transporte de audio de ASM-RX.
- `PENDIENTE`: estrategia de procesos, concurrencia, reinicio y despliegue.

## Documentos relacionados

[Lógica](04-logica-de-negocio.md), [interfaces](07-interfaces-de-hardware.md), [ADR-001](adr/ADR-001-arquitectura-greenfield.md) y [ADR-006](adr/ADR-006-separacion-dominio-hardware.md).
