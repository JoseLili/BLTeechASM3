# Energía — Mean Well LAD-120A

## Pinout funcional de CN2

| Pin | Función |
|---:|---|
| 1 | AC OK |
| 2 | batería desconectada / polaridad inversa |
| 3 | batería baja |
| 4 | retorno común |
| 5 | batería llena |
| 6 | descarga / operación desde batería |
| 7–8 | Forced Start mediante contacto |

`CONFIRMADO` según la información técnica revisada en el contexto inicial: las salidas 1, 2, 3, 5 y 6 son open-collector/open-drain funcional, requieren polarización externa y admiten hasta 50 VDC externos y 30 mA de hundimiento. Los pines 7–8 son una entrada, no un estado.

## Estado de evidencia

- `VALIDADO`: orientación del header, cambio de flanco al puentear contra CN2-4 y ruta básica PC817→GPIO con jumper.
- `DECIDIDO` por el mapa final Carrier v3.1 Rev A: CN2-1/GPIO5,
  CN2-2/GPIO13, CN2-3/GPIO26, CN2-5/GPIO6 y CN2-6/GPIO12.
- `DECIDIDO`: PC817 excitado produce LOW en la entrada Raspberry Pi.
- `PENDIENTE`: prueba con LAD-120A real, niveles, tiempos y tabla de estados.

El mapa preliminar de cuatro GPIO queda supersedido. Software no debe volver a
usar GPIO19 para batería baja ni tratar `Discharge` como señal ausente.

## Interpretación de software

El adaptador conserva por separado lectura cruda, traducción eléctrica validada, calidad/conocimiento del dato y `PowerStatus`. Mientras no exista validación, los estados admiten `UNKNOWN`; no se infiere normalidad de una señal ausente.

`IMPLEMENTADO`: `GpioPowerMonitor` abre las cinco entradas con pull-up, traduce
LOW a `ASSERTED`, HIGH a `CLEAR` y cualquier lectura no binaria a `UNKNOWN`.
Entrega snapshots inmutables mediante `PowerMonitorPort`; todavía no asigna
severidad, alarmas ni combinaciones físicamente imposibles.

`IMPLEMENTADO`: `Diagnóstico → Energía` presenta en la OLED las cinco señales
semánticas. `SI` significa que la salida correspondiente está afirmada; no
significa por sí solo que el sistema completo esté sano o en falla.

`OBSERVADO` en la carrier energizada sin entradas LAD-120A excitadas: GPIO5,
GPIO13, GPIO26, GPIO6 y GPIO12 quedaron HIGH y las cinco señales se reportaron
`CLEAR`.

Diagnóstico de banco:

```bash
PYTHONPATH=src /usr/bin/python3 scripts/power_input_test.py --duration 30
```

## Plan mínimo de validación física

1. Verificar revisión, pin 1 y retorno con equipo desenergizado.
2. Comprobar tensión/corriente y aislamiento antes de conectar la Raspberry Pi.
3. Provocar de forma controlada cada condición y registrar CN2, salida PC817, GPIO y tiempos.
4. Repetir ciclos, combinaciones y recuperación, incluida operación desde batería.
5. Congelar tabla de verdad y evidencia por revisión de carrier.

Los procedimientos eléctricos detallados deben ser revisados por personal competente y documentación oficial antes de ejecutarse.

## Preguntas abiertas

- Umbrales y retardos que evitan falsos cambios.
- Combinaciones de estados posibles y severidad funcional.
- Autonomía objetivo, Forced Start y estrategia segura de apagado.
- Ventana de debounce y cantidad de muestras estables antes de publicar cambios.

## Relacionados

[Carrier](02-carrier-board.md), [interfaces](07-interfaces-de-hardware.md) y [pruebas](11-pruebas-y-validacion.md).
