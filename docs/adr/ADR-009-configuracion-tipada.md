# ADR-009: Configuración tipada y validada

## Estado

Aceptado (`DECIDIDO`).

## Contexto

Prototipos anteriores centralizaban duraciones, textos, rutas de audio y versión en un `config.py`. La facilidad de ajuste es valiosa, pero un archivo monolítico sin límites puede mezclar preferencias visuales con reglas críticas y aceptar valores inválidos.

## Decisión

Conservar la centralización mediante un `SystemConfig` inmutable compuesto por secciones tipadas. Mantener valores de fábrica versionados y pasar la configuración explícitamente durante la composición. Agregar campos solo cuando exista un consumidor real.

Las prioridades, transiciones de seguridad, pinout, validación de mensajes y límites eléctricos quedan fuera de la configuración editable.

## Consecuencias positivas

- Valores ajustables localizables y documentados.
- Validación temprana y pruebas por sección.
- Evita constantes visuales dispersas en adaptadores.
- Permite agregar carga externa y configuración por sitio posteriormente.

## Consecuencias negativas

- Requiere modelos, loader, precedencia y migración de esquema.
- Algunos cambios que antes eran una variable exigirán una decisión de dominio.
- La configuración externa todavía no está implementada.

## Alternativas consideradas

- Un único módulo con variables globales: simple inicialmente, pero difícil de validar y rastrear.
- Configurar toda regla del sistema: rechazado por riesgo de alterar seguridad accidentalmente.
- Hardcodear cada valor junto a su adaptador: rechazado por dispersión y mantenimiento.

## Puntos pendientes

- Loader, formato persistente, ubicación, versión de esquema y precedencia.
- Catálogo de textos por estado y configuración de recursos de audio.
- Estrategia de última configuración válida, rollback y auditoría de cambios.
- Separar ajustes de fábrica, equipo y sitio con permisos apropiados.
