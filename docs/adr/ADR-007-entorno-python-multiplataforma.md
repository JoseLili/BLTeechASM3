# ADR-007: Entorno Python multiplataforma

## Estado

Aceptado (`DECIDIDO`).

## Contexto

El desarrollo ocurre inicialmente en un PC x86_64 con Python 3.12. La unidad objetivo fue inventariada como Raspberry Pi 4 Model B Rev 1.5, Debian 13 `aarch64` y Python 3.13.5. El núcleo debe probarse sin hardware y los adaptadores tendrán dependencias específicas.

## Decisión

Usar paquete con layout `src`, Python 3.11 como mínimo compatible y entornos virtuales por host. Mantener el núcleo sin dependencias de hardware; separar herramientas de desarrollo y futuros extras de Raspberry Pi.

## Consecuencias positivas

- Mismo código de dominio en PC y ARM.
- Instalaciones aisladas del Python del sistema.
- Dependencias de hardware no contaminan simulación ni tests puros.

## Consecuencias negativas

- Se deben mantener perfiles y pruebas para más de una arquitectura.
- Se debe comprobar cada dependencia futura tanto con Python 3.11 como con Python 3.13.
- Sin archivo de bloqueo inicial no hay reproducibilidad exacta de herramientas.

## Alternativas consideradas

- Desarrollar solamente en la Pi: reduce velocidad, aislamiento y capacidad de simulación.
- Incluir GPIO/OLED como dependencias obligatorias: impediría una instalación limpia en PC.
- Contenedores desde la primera iteración: se posponen hasta conocer necesidades de acceso al hardware y despliegue.

## Puntos pendientes

- Congelar herramientas y dependencias después de probar ambos hosts.
- Decidir extras de hardware, instalación de sistema, despliegue y servicio supervisor.
