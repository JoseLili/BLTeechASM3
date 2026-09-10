# Configuración y modo técnico

## Filosofía de configuración

`DECIDIDO`: conservar la filosofía funcional de centralizar valores ajustables del sistema, sin heredar el archivo monolítico de versiones anteriores. La configuración v3 usa modelos tipados, inmutables y validados por sección.

Estructura inicial implementada:

```text
SystemConfig
├── BrandingConfig
├── DisplayConfig
├── ButtonInputConfig
├── MenuButtonInputConfig
└── ReceiverConfig
    ├── channel
    ├── serial_device
    ├── command_timeout_seconds
    └── startup_settle_seconds
```

`VALIDADO` mediante pruebas: los textos obligatorios no aceptan valores vacíos y la animación solo admite más de cero y hasta diez segundos. El valor de fábrica actual es cinco segundos.

La duración total es configuración; la cantidad de cuadros pertenece al animador. Esto permite cambiar el diseño interno sin obligar a recalcular valores operativos.

### Límites

Pueden configurarse identidad, presentación, audio, sitio, canal, squelch, retención y umbrales aprobados. No son configuración libre las prioridades de eventos, transiciones de seguridad, validación de mensajes, pinout ni límites eléctricos.

`PENDIENTE`: implementar carga externa con precedencia explícita:

```text
valores de fábrica → configuración del equipo → configuración del sitio
```

Una configuración externa inválida deberá impedir su aplicación, conservar la última configuración válida y generar diagnóstico. No existe todavía un loader YAML ni se ha decidido su ubicación definitiva; `/etc/asm-blteech/config.yaml` permanece `PROPUESTO`.

`PENDIENTE`: agregar secciones tipadas para textos por estado y recursos de audio cuando existan consumidores implementados. No se crearán campos sin uso solamente para anticipar código futuro.

## Política configurable de botones

`DECIDIDO`: separar antirrebote, reconocimiento de gesto y activación de acciones.

```text
nivel GPIO → debounce → PRESS/RELEASE → gesto único → política → comando
```

- El debounce elimina flancos eléctricos repetidos; una pulsación sostenida no genera comandos repetidos.
- La duración se mide con reloj monotónico y sin bloquear el ciclo principal.
- `DECIDIDO`: Simulacro y Evacuación admiten modo configurable `IMMEDIATE` o `HOLD`, con duración de retención validada por sitio.
- `DECIDIDO`: Simulacro y Evacuación usan `IMMEDIATE` como valor de fábrica; `HOLD` conserva un umbral configurable de referencia de cinco segundos.
- `DECIDIDO`: Paro es siempre inmediato y su activación no puede retrasarse mediante configuración de sitio.
- EQW y eventos de radio no pasan por políticas de retención de botones.

`PROPUESTO`: el debounce inicial es 50 ms; su configuración solo admite valores mayores que cero y hasta 200 ms. La prueba conjunta no produjo duplicados, pero el valor definitivo requiere más muestras cortas, largas y rápidas.

`VALIDADO` mediante pruebas: `ButtonPolicyInterpreter` emite como máximo un comando por gesto, cancela una retención liberada antes del umbral, no bloquea mientras espera y exige liberación antes de permitir otra activación. La conexión de estos comandos con la máquina de estados permanece `PENDIENTE`.

La futura configuración externa deberá auditar cualquier cambio de modo o duración.

## Acceso

`DECIDIDO`: Carrier v3.1 Rev A tiene siete botones dedicados de configuración
conectados al PCF8574P en `0x20`. El acceso y navegación del menú no reutilizan
los botones operativos. Un EQW válido interrumpe el menú inmediatamente.

| Botón dedicado | Comando semántico inicial |
|---|---|
| Arriba | `MOVE_UP` |
| Abajo | `MOVE_DOWN` |
| Izquierda | `MOVE_LEFT` |
| Derecha | `MOVE_RIGHT` |
| Enter | `CONFIRM` |
| Regresar | `GO_BACK` |
| Escucha | `TOGGLE_LISTEN` |

`DECIDIDO`: Arriba/Abajo/Izquierda/Derecha, Enter y Regresar pertenecen al
controlador de menús. Escucha conmuta la rama de monitor local y nunca altera
la señal entregada al decoder SAME.

`IMPLEMENTADO`: navegación OLED inicial con menú raíz para Recepción, Audio,
Diagnóstico, Sistema e Información, submenús, cursor desplazable, Enter,
Regresar y acción global de Escucha.

`PENDIENTE`: conectar las hojas con ajustes reales, definir timeout y aplicar
edición transaccional. Hasta entonces el diagnóstico OLED es deliberadamente
de solo lectura.

## Cambio transaccional de canal

```text
seleccionar C1–C7 → aplicar temporalmente → verificar receptor
        → confirmar y guardar, o cancelar/revertir
```

`DECIDIDO`: la frecuencia se deriva del canal. `PROPUESTO`: la configuración persistida incluye versión de esquema, sitio/región, canal, squelch e identidad/revisiones de hardware; los valores desconocidos permanecen explícitos.

`IMPLEMENTADO`: C7 es el valor de fábrica y produce 162.5500 MHz sin almacenar
una frecuencia independiente. `ReceiverService` sólo acepta un cambio cuando
el adaptador devuelve el mismo perfil como verificado. La escritura persistente
y el flujo OLED de doble confirmación permanecen `PENDIENTE`.

## Reglas de persistencia

- Validar antes de aplicar y escribir de forma atómica.
- Conservar última configuración válida y valor predeterminado documentado.
- Auditar cambios, actor/origen y resultado.
- No confirmar si el receptor no acepta o no permite verificar el ajuste temporal.

## Preguntas abiertas

- Valor de canal y squelch al aprovisionar; autenticación del modo técnico.
- Tiempo de pulsación, timeout del menú y comportamiento tras reinicio durante escritura.
- Ubicación primaria (archivo/EEPROM) y resolución de discrepancias.
- Qué significa «verificar respuesta y estado» en ambos receptores.

## Relacionados

[Estados](05-maquina-de-estados.md), [hardware](07-interfaces-de-hardware.md), [ADR-005](adr/ADR-005-seleccion-local-de-canal.md) y [ADR-009](adr/ADR-009-configuracion-tipada.md).
