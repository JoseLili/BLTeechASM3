# Máquina de estados

## Alcance

Diseño conceptual, `PROPUESTO`; no constituye todavía una implementación. Las fallas concurrentes necesitan una decisión explícita antes de congelar el modelo.

## Estado de implementación

`VALIDADO` en simulación: están implementados `BOOT → SELF_TEST → IDLE`, los
cuatro estados activos `RWT`, simulacro, evacuación y EQW, y la preempción
estricta `EQW > Evacuación > Simulacro > RWT`. RWT, simulacro y evacuación
admiten `Paro`; EQW no lo admite todavía. Toda transición no incluida se rechaza
y audita. Los estados de falla y su concurrencia permanecen conceptuales.

## Estados y entradas principales

| Estado | Entrada / condición | Acción conceptual | Salidas normales |
|---|---|---|---|
| `BOOT` | encendido/reinicio | inicializar contexto y auditoría | `SELF_TEST` |
| `SELF_TEST` | arranque | comprobar componentes críticos | `IDLE` o estado de falla |
| `IDLE` | autoprueba aprobada o evento terminado | mantener escucha y supervisión | activos, `TECH_MODE`, fallas |
| `TECH_MODE` | combinación larga en espera y sin evento | permitir selección temporal | `IDLE` o activos |
| `RWT_ACTIVE` | RWT válido | indicar/practicar según reglas | `IDLE`, activos superiores |
| `SIMULACRO_ACTIVE` | botón o evento admitido | reproducir simulacro | `STOPPED`, `IDLE`, activos superiores |
| `EVACUACION_ACTIVE` | botón/evento admitido | reproducir evacuación | `STOPPED`, `IDLE`, `EQW_ACTIVE` |
| `EQW_ACTIVE` | EQW válido | interrumpir y ejecutar alerta | salida definida tras fin válido |
| `STOPPED` | Paro permitido | silenciar/detener y auditar | `IDLE` según reconocimiento |
| `RECEIVER_FAULT` | receptor no disponible/no confiable | diagnosticar y señalar | recuperación o mantenimiento |
| `POWER_FAULT` | condición funcional de energía | diagnosticar y señalar | recuperación o mantenimiento |
| `MAINTENANCE_REQUIRED` | falla no recuperable/umbral | limitar operación y pedir servicio | autoprueba/reinicio autorizado |

## Reglas de transición

- `DECIDIDO`: un EQW válido interrumpe inmediatamente `TECH_MODE` y cualquier evento de menor prioridad.
- `IMPLEMENTADO`: evacuación interrumpe simulacro y RWT; simulacro interrumpe RWT.
- `IMPLEMENTADO`: eventos iguales o inferiores se rechazan durante uno activo,
  se auditan y no quedan en cola.
- `PENDIENTE`: salida de `EQW_ACTIVE`, duración y posibilidad de Paro durante EQW.
- `PENDIENTE`: quién puede reconocer `STOPPED` y cuándo retorna a `IDLE`.

## Transiciones prohibidas

- Entrar a `TECH_MODE` fuera de `IDLE` o con evento activo.
- Confirmar canal si el receptor no aceptó/verificó la aplicación temporal.
- Convertir una entrada no validada directamente en `EQW_ACTIVE` o `RWT_ACTIVE`.
- Degradar un evento activo por la llegada de otro de menor prioridad.
- Ocultar una falla crítica para presentar solamente estado normal.

## Paro

`IMPLEMENTADO` inicialmente: es una orden manual registrada que detiene RWT,
simulacro y evacuación. Se rechaza en IDLE y durante EQW. `PENDIENTE`: decidir si
alguna autoridad puede detener EQW y cómo se reconoce `STOPPED` para volver a
`IDLE`.

## Fallas concurrentes

`PROPUESTO`: conservar un estado operativo principal y un conjunto paralelo de condiciones de salud evita perder información cuando, por ejemplo, existe una alerta durante fallo de energía. Si una falla impide cumplir la función, una política de degradación decide entre continuar el evento, usar salidas disponibles o pasar a mantenimiento. Esa política, precedencias visuales y severidades son `PENDIENTE`.

## Plazos y recuperación

`DECIDIDO`: no existirá un timeout global que fuerce cualquier estado a `IDLE`. Cada estado activo tendrá una condición de terminación o plazo explícito y probado. EQW no se cancelará mediante un watchdog genérico. La recuperación tras reinicio deberá usar evidencia persistente y una política específica antes de reanudar o abandonar un evento.

`PENDIENTE`: definir plazos, finalización de audio, reconocimiento de Paro y recuperación de cada estado.

## Relacionados

[Prioridades](06-eventos-y-prioridades.md), [modo técnico](08-configuracion-y-modo-tecnico.md) y [pruebas](11-pruebas-y-validacion.md).
