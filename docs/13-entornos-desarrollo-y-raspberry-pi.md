# Entornos de desarrollo y Raspberry Pi

## Estado

- `DECIDIDO`: Python 3.11 es la versión mínima de compatibilidad del proyecto.
- `VALIDADO`: el PC de desarrollo inicial ejecuta Python 3.12 sobre x86_64.
- `VALIDADO`: la Raspberry Pi objetivo ejecuta Python 3.13.5 sobre Debian 13 `aarch64`.
- `DECIDIDO`: dominio y aplicación deben ejecutar igual en x86_64 y ARM; el hardware entra mediante adaptadores opcionales.
- `VALIDADO`: Raspberry Pi 4 Model B Rev 1.5; el usuario operativo pertenece a los grupos `gpio`, `i2c`, `spi`, `dialout` y `audio`.

## Perfiles

### Común

El paquete `asm-blteech` no tiene dependencias de ejecución todavía. Modelos, reglas, fakes y simulación deben permanecer en este perfil.

### Desarrollo

El extra `dev` incorpora pruebas, cobertura, lint y tipos. Se instala dentro de un entorno virtual, nunca sobre el Python administrado por el sistema operativo.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy
python -m asm
```

### Raspberry Pi

No se agregan librerías de GPIO, I²C u OLED hasta elegirlas mediante ADR. La preparación inicial es deliberadamente no destructiva:

```bash
python3 --version
uname -m
python3 scripts/environment_report.py
```

En la Pi se crea `.venv` y se instala el mismo paquete. Las dependencias exclusivas de hardware se definirán en un extra separado y mediante ADR; no formarán parte del núcleo.

## Flujo de trabajo

1. Ejecutar reglas y pruebas en PC con fakes.
2. Ejecutar las mismas pruebas puras en Raspberry Pi.
3. Añadir pruebas de contrato para cada puerto.
4. Ejecutar adaptadores reales solo en pruebas marcadas como HIL.
5. Registrar versión, arquitectura y revisión de hardware junto a cada evidencia.

## Diagnóstico reproducible

`scripts/environment_report.py` informa Python, arquitectura, modelo Raspberry Pi, nodos I²C visibles, entorno virtual y herramientas instaladas. Es de solo lectura y no habilita interfaces ni instala paquetes.

No deben versionarse `.venv`, caches, builds ni reportes locales. Las versiones exactas de herramientas se congelarán después de comprobar instalación tanto en PC como en Pi.

## Inventario inicial de la Pi

- `VALIDADO`: Raspberry Pi 4 Model B Rev 1.5.
- `VALIDADO`: Debian GNU/Linux 13 (Trixie), `aarch64`, Python 3.13.5.
- `VALIDADO`: existen `/dev/i2c-1`, `/dev/i2c-20` y `/dev/i2c-21`.
- `VALIDADO`: el RTC en I²C-1 dirección `0x68` está expuesto como `/dev/rtc0` mediante el driver `rtc-ds1307`.
- `VALIDADO`: la partición raíz tiene 22 GB disponibles durante el inventario inicial.
- `PENDIENTE`: definir política de retención y umbrales de almacenamiento.
- `PENDIENTE`: `i2c-tools` no está instalado; no es requisito del núcleo y se añadirá solo al preparar pruebas HIL.
- Modelo de OLED y resolución física.
- Resultado de detección I²C y direcciones observadas.
- `VALIDADO`: el usuario `blteech` tiene grupos de acceso a GPIO/I²C/SPI; falta una prueba funcional no destructiva.
- `PENDIENTE`: el reloj del sistema no está sincronizado, NTP está inactivo y el RTC reportó el año 2000 durante el inventario; no debe usarse aún como evidencia temporal.
- Revisión de carrier conectada; no conectar LAD-120A hasta tener procedimiento de validación.

## Relacionados

[Arquitectura](01-arquitectura-general.md), [interfaces](07-interfaces-de-hardware.md), [pruebas](11-pruebas-y-validacion.md) y [ADR-007](adr/ADR-007-entorno-python-multiplataforma.md).
