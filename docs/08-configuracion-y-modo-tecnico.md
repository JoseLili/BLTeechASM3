# Configuración y modo técnico

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

[Estados](05-maquina-de-estados.md), [hardware](07-interfaces-de-hardware.md) y [ADR-005](adr/ADR-005-seleccion-local-de-canal.md).
