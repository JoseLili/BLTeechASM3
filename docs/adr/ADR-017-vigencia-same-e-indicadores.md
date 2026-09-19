# ADR-017 — Vigencia SAME e indicadores persistentes

## Estado

Aceptado e implementado, incluida la conexión al stream continuo.

## Contexto

RWT y EQW contienen `TTTT`, la vigencia del aviso. El fin de mensaje `NNNN`
ocurre segundos después de la cabecera, pero la indicación debe continuar tres
horas para una RWT `+0300` y un minuto para una EQW `+0001`. El material oficial
disponible no congela una cadencia de parpadeo y sus ejemplos de fecha, áreas y
emisores no representan necesariamente la red actual.

La evidencia real del proyecto es
`ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-`. El contrato vigente indicado por el
proyecto usa `000000` para todas las unidades y no autoriza rechazar un mensaje
por fecha juliana o emisor.

## Decisión

- Aceptar únicamente origen `CIV` y eventos soportados `RWT`/`EQW`.
- Interpretar uno o más campos de área de seis dígitos; `000000` significa todas
  las unidades.
- Conservar fecha y emisor como metadatos opacos, sin lista oficial ni validación
  de calendario para decidir una activación.
- Derivar la vigencia exclusivamente de `TTTT` y del tiempo monotónico de la
  primera recepción aceptada.
- Agrupar cabeceras idénticas durante diez segundos como una sola ráfaga; las
  repeticiones no reinician el plazo.
- Mantener RWT en AVISO/amarillo y EQW en ALERTA/rojo con parpadeo inicial de un
  segundo encendido y uno apagado.
- Mostrar la pantalla prominente de RWT durante ocho segundos y después volver
  a la vista `Esperando evento`, conservando `RWT vigente <minutos>m` en el pie.
  Este cambio es sólo de presentación: el LED Advisory, la vigencia y el log no
  se cancelan. EQW permanece prominente durante toda su vigencia.
- Mantener avisos vigentes por separado: EQW tiene precedencia visual y, al
  vencer, reaparece una RWT todavía vigente.
- Tratar `NNNN` únicamente como fin del encuadre RF, nunca como orden de apagar.

## Consecuencias

La fecha incorrecta y un emisor nuevo no provocan falsos rechazos. El control de
tiempo no depende del RTC. El proceso continuo todavía deberá persistir la
vigencia para recuperarse de un reinicio y será responsable de componer esta indicación con
simulacro, evacuación y fallas, manteniendo un único escritor de GPIO.

SAME no incluye un checksum; la resistencia ante corrupción se deberá probar
con repetición, corpus de tramas y reglas explícitas antes de activar audio EQW.

## Relacionados

[Eventos](../06-eventos-y-prioridades.md), [interfaces](../07-interfaces-de-hardware.md), [pruebas](../11-pruebas-y-validacion.md) y [ADR-015](ADR-015-prioridad-y-origen-de-eventos-locales.md).
