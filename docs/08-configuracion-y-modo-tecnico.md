# Configuración y modo técnico

## Filosofía de configuración

`DECIDIDO`: conservar la filosofía funcional de centralizar valores ajustables del sistema, sin heredar el archivo monolítico de versiones anteriores. La configuración v3 usa modelos tipados, inmutables y validados por sección.

Estructura inicial implementada:

```text
SystemConfig
├── BrandingConfig
│   ├── company_name
│   ├── product_name
│   ├── generation
│   └── startup_text
└── DisplayConfig
    └── startup_animation_seconds
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

## Acceso

`PROPUESTO`: solo desde `IDLE`, sin evento activo, mediante pulsación larga de Simulacro + Paro. Un EQW válido interrumpe el menú inmediatamente.

| Botón | Función técnica |
|---|---|
| Simulacro | anterior/disminuir |
| Evacuación | siguiente/aumentar |
| Paro corto | confirmar |
| Paro largo | regresar/cancelar |

## Cambio transaccional de canal

```text
seleccionar C1–C7 → aplicar temporalmente → verificar receptor
        → confirmar y guardar, o cancelar/revertir
```

`DECIDIDO`: la frecuencia se deriva del canal. `PROPUESTO`: la configuración persistida incluye versión de esquema, sitio/región, canal, squelch e identidad/revisiones de hardware; los valores desconocidos permanecen explícitos.

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
