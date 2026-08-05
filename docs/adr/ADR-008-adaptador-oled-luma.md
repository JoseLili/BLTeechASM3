# ADR-008: Adaptador OLED mediante Luma.OLED

## Estado

Aceptado (`DECIDIDO`) para la pantalla SSD1306 actual.

## Contexto

La carrier de pruebas incorpora una OLED I²C de 2.4 pulgadas, 128×64, detectada en el bus 1 y dirección `0x3C`. Debian 13 ofrece `python3-luma.oled` y sus dependencias como paquetes administrados por el sistema.

## Decisión

Usar Luma.OLED como biblioteca del adaptador SSD1306. En Raspberry Pi se instalará globalmente mediante `apt`, no mediante `pip --break-system-packages`. El dominio y la aplicación seguirán dependiendo únicamente de `DisplayPort`.

## Consecuencias positivas

- Paquete mantenido e instalado por Debian.
- Prueba física exitosa con el hardware real.
- Soporta dibujo mediante Pillow sin acoplar el dominio al controlador.

## Consecuencias negativas

- Es una dependencia exclusiva de Raspberry Pi y no estará presente en el PC.
- Debe definirse cómo el entorno de ejecución aislado accede a paquetes Python instalados por Debian.
- Un cambio de controlador de pantalla requerirá otro adaptador o configuración.

## Alternativas consideradas

- Acceso SMBus directo: mayor control, pero duplica inicialización, dibujo y mantenimiento del controlador.
- Instalar Luma.OLED desde PyPI: rechazado para la Pi de producción mientras exista paquete Debian compatible.
- Acoplar vistas del dominio a Luma: rechazado porque impediría simulación y sustitución de pantalla.

## Puntos pendientes

- Definir el entorno de ejecución de producción sin instalación global mediante `pip`.
- Diseñar tipografía, márgenes, refresco y manejo de fallas.
- Crear el adaptador `DisplayPort` y sus pruebas de contrato.
- Validar legibilidad, arranque, reinicio y operación prolongada.
