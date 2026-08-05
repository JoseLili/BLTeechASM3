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
- `PENDIENTE`: prueba con LAD-120A real, niveles, tiempos y polaridades post-opto.
- `PENDIENTE`: correspondencia exacta CN2-5↔GPIO6.
- `PENDIENTE`: ruta/GPIO de CN2-6 `Discharge`.

El inventario tiene cuatro GPIO, mientras la carrier contempla cinco estados. Esta discrepancia se resuelve únicamente contra esquemático, PCB y medición física.

## Interpretación de software

El adaptador conserva por separado lectura cruda, traducción eléctrica validada, calidad/conocimiento del dato y `PowerStatus`. Mientras no exista validación, los estados admiten `UNKNOWN`; no se infiere normalidad de una señal ausente.

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

## Relacionados

[Carrier](02-carrier-board.md), [interfaces](07-interfaces-de-hardware.md) y [pruebas](11-pruebas-y-validacion.md).
