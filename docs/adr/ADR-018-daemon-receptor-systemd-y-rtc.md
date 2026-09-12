# ADR-018 — Daemon receptor, systemd y RTC

## Estado

Aceptado e implementado para la primera porción productiva del receptor.

## Contexto

La unidad debe quedar lista para recibir RWT/EQW después de energizarse, sin
sesión SSH ni intervención manual. La cadena de audio usa tres procesos del
sistema y comparte OLED, GPIO, UART y bitácora. Los registros requieren hora
civil aun después de perder alimentación de la Raspberry Pi.

## Decisión

- Ejecutar un daemon Python único que sea propietario de OLED, LEDs, receptor y
  decisiones SAME.
- Crear `arecord`, SoX y `multimon-ng` directamente, sin shell, y cerrar todos
  los hijos al detener el servicio.
- Reiniciar el pipeline con backoff exponencial de uno a treinta segundos; dejar
  a systemd reiniciar el daemon después de una falla no recuperable.
- Arrancar después de ALSA, `/dev/rtc0` y la precarga WM8960; mostrar BOOT,
  verificar el canal persistido y después presentar estado IDLE.
- Usar el HW-084 mediante el driver RTC del kernel. `hctosys=1` establece la
  hora del sistema durante el arranque; la lógica de vigencia continúa usando
  reloj monotónico.
- Escribir diagnóstico JSONL append-only con `fsync` bajo
  `/var/lib/asm-blteech`.
- Desplegar releases inmutables identificados por commit y seleccionar la
  versión activa mediante `/opt/asm-blteech/current`.

## Consecuencias

La Pi puede iniciar y recuperarse sin una terminal. El cierre coordinado evita
capturas huérfanas y un único proceso compone las salidas físicas. El RTC mejora
la trazabilidad, pero se conserva su estado de salud junto al timestamp para no
presentar como confiable una hora degradada.

Esta porción todavía no integra Mean Well, botones operativos, menú ni audio de
EQW. También quedan pendientes la persistencia de vigencias SAME a través de un
reinicio, el watchdog de progreso y la rotación de logs.

## Relacionados

[Logging](../10-logging-y-diagnostico.md),
[entornos](../13-entornos-desarrollo-y-raspberry-pi.md),
[ADR-016](ADR-016-perfil-audio-wm8960-y-gold-same.md) y
[ADR-017](ADR-017-vigencia-same-e-indicadores.md).
