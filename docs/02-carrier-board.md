# Carrier board

## Estado conocido

- `VALIDADO`: cinco unidades fabricadas; alimentación por header, OLED, RTC, EEPROM, botones y LEDs funcionales.
- `VALIDADO`: orientación física del header y ruta básica PC817→GPIO probadas con jumper.
- `VALIDADO`: cuatro de cinco optoacopladores respondieron.
- `PENDIENTE`: sustituir U7, dañado por calor, y revisar la quinta ruta.

## Responsabilidad

La placa de dos capas conecta la Raspberry Pi por el header de 40 pines e integra entrada desde LAD-120A, conversión Mini560 a 5 V, tres botones, tres LEDs, bus I²C, entradas aisladas PC817 y conexiones de gabinete. El amplificador de audio se alimenta fuera de la carrier.

El plano de tierra busca reducir ruido y mejorar retornos; su eficacia EMC todavía requiere pruebas.

## Límites

El inventario eléctrico autoritativo se registra en [interfaces de hardware](07-interfaces-de-hardware.md). La interpretación funcional de energía se documenta en [Mean Well](09-energia-meanwell.md).

## Preguntas abiertas

- ¿Qué revisión exacta tienen las cinco placas y dónde están sus esquemáticos/BOM/Gerber controlados?
- ¿Qué pull-ups I²C están poblados y cuál es la resistencia equivalente?
- ¿Qué pruebas térmicas, EMC, consumo y protección se requieren?

## Relacionados

[Arquitectura](01-arquitectura-general.md), [hardware](07-interfaces-de-hardware.md) y [pruebas](11-pruebas-y-validacion.md).
