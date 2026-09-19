# Entornos de desarrollo y Raspberry Pi

## Estado

- `DECIDIDO`: Python 3.11 es la versión mínima de compatibilidad del proyecto.
- `VALIDADO`: el PC de desarrollo inicial ejecuta Python 3.12 sobre x86_64.
- `VALIDADO`: la Raspberry Pi objetivo ejecuta Python 3.13.5 sobre Debian 13 `aarch64`.
- `DECIDIDO`: dominio y aplicación deben ejecutar igual en x86_64 y ARM; el hardware entra mediante adaptadores opcionales.
- `VALIDADO`: Raspberry Pi 4 Model B Rev 1.5; el usuario operativo pertenece a los grupos `gpio`, `i2c`, `spi`, `dialout` y `audio`.

## Perfiles

### Común

El paquete `asm-blteech` no añade dependencias Python de ejecución todavía.
Modelos, reglas, fakes y simulación deben permanecer en este perfil.

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

En la Pi se crea `.venv` y se instala el mismo paquete. Las dependencias
exclusivas de hardware se definirán en un extra separado y mediante ADR; no
formarán parte del núcleo. Los adaptadores de audio actuales usan la biblioteca
estándar de Python y herramientas del sistema operativo:

- `/usr/bin/arecord` y `/usr/bin/aplay` para ALSA;
- `wm8960-audio-board-preload.service` activo antes de abrir streams;
- `sox` para la conversión GOLD reproducible en pruebas;
- `multimon-ng` para la demodulación SAME/EAS de laboratorio.

`sox` y `multimon-ng` no son dependencias del dominio ni de los diagnósticos
básicos; son dependencias externas del daemon receptor desplegado en la Pi.

## Servicio de arranque

`asm-blteech.service` inicia automáticamente después de que estén disponibles
el sistema de archivos, ALSA y la precarga WM8960. Inspecciona el RTC sin
bloquear la recepción si éste falta, ejecuta BOOT en OLED, verifica el canal
C1-C7 del SA818, abre el pipeline continuo SAME y se reinicia si el proceso
falla.

```bash
sudo systemctl status asm-blteech.service
sudo journalctl -u asm-blteech.service -f
sudo tail -f /var/lib/asm-blteech/diagnostics.jsonl
```

Cada despliegue se extrae en `/opt/asm-blteech/releases/<commit>` y el enlace
`/opt/asm-blteech/current` apunta a la versión activa.

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
- `VALIDADO`: ALSA expone `wm8960soundcard` dispositivo 0 para captura y salida;
  una captura real desde RINPUT1 derecho y una reproducción silenciosa
  finalizaron correctamente.
- `VALIDADO`: el RTC en I²C-1 dirección `0x68` está expuesto como `/dev/rtc0` mediante el driver `rtc-ds1307`.
- `VALIDADO`: la partición raíz tiene 22 GB disponibles durante el inventario inicial.
- `PENDIENTE`: definir política de retención y umbrales de almacenamiento.
- `VALIDADO`: `i2c-tools` está disponible y `i2cdetect -y 1` mostró PCF8574P
  `0x20`, OLED `0x3C`, EEPROM `0x57` y RTC ocupado por el kernel en `0x68`.
- Modelo de OLED y resolución física.
- Resultado de detección I²C y direcciones observadas.
- `VALIDADO`: el usuario `blteech` tiene grupos de acceso a GPIO/I²C/SPI; falta una prueba funcional no destructiva.
- `VALIDADO` el 2026-09-11: RTC y sistema coincidieron, NTP estaba sincronizado y
  el driver reportó `hctosys=1`. Queda pendiente validar retención mediante un
  corte real con el HW-084 conectado desde el arranque.
- Revisión de carrier conectada; no conectar LAD-120A hasta tener procedimiento de validación.

## Relacionados

[Arquitectura](01-arquitectura-general.md), [interfaces](07-interfaces-de-hardware.md), [pruebas](11-pruebas-y-validacion.md) y [ADR-007](adr/ADR-007-entorno-python-multiplataforma.md).
