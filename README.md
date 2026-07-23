# Home Assistant Orvibo Remote (IR + RF)

Integración custom para controlar Orvibo **AllOne / AllInOne** y **AllInOne Pro** desde Home Assistant.

## Resumen ejecutivo

Este refactor moderniza la integración para:
- arquitectura basada en **config entries**;
- capa cliente/protocolo desacoplada de entidades HA;
- servicios IR + RF con almacenamiento persistente de códigos;
- retrocompatibilidad con uso YAML heredado en la plataforma `remote`.

## Auditoría comparativa de librerías

### Qué módulo embebido se usaba
El repositorio incluye una copia vendorizada en:
- `/home/runner/work/homeassistant-orvibo-remote/homeassistant-orvibo-remote/custom_components/orvibo_remote/orvibo/orvibo.py`

La copia corresponde funcionalmente al módulo de `fjgils/orvibo-python-module` (fork de `cherezov/orvibo`) con los mismos comandos principales de protocolo UDP (`7161`, `636c`, `6c73`, `6963`, `6463`) y soporte IR+RF433 orientado a switches RF de Orvibo.

### Diferencias funcionales relevantes
- `orvibo-python-module`: librería de protocolo (sin capa HA), soporte clásico para discover/subscribe/learn/emit.
- estado previo de esta integración: entidad `remote` muy básica, sin config flow, sin servicios de gestión de códigos, sin separación arquitectura.
- `node-orvibo`: referencia más completa de producto/protocolo a nivel de eventos y modelado de capacidades; documenta mejor limitaciones RF.

### Implementación más actualizada y por qué
Para backend de protocolo, la base Python vendorizada sigue siendo útil por estabilidad y dependencia cero.
Para cobertura funcional/documentación RF, `node-orvibo` es la referencia más completa (capas de eventos, framing RF, documentación de trade-offs de RF).

### Qué partes soportan RF y qué faltaba
Ya existente (backend vendorizado):
- aprendizaje RF (`learn_rf433`) y emisión RF (`_learn_emit_rf433`) para switches RF Orvibo.

Faltaba en integración HA:
- servicios explícitos RF;
- persistencia/normalización de códigos;
- exposición de capacidades y ruta de uso estable para usuarios HA;
- documentación clara de limitaciones RF.

## Decisión técnica de librería base

**Opción C: Vendorizar una versión concreta y documentada** + capa cliente nueva tipada.

Motivos:
- estabilidad y baja fricción de release;
- mantiene compatibilidad con instalaciones existentes;
- permite encapsular deuda técnica del módulo legado detrás de una API async moderna;
- facilita testear integración sin reescribir completamente el stack de protocolo.

Trade-off:
- el backend vendorizado mantiene limitaciones históricas del protocolo RF de Orvibo; se documentan y se exponen fallos de forma explícita.

## Compatibilidad de dispositivos

| Dispositivo | IR | RF | Notas |
|---|---:|---:|---|
| AllOne / AllInOne clásico | ✅ | ⚠️ | RF depende del flujo SmartSwitch RF433 del protocolo legado |
| AllInOne Pro | ✅ | ✅ | RF soportado vía servicios `learn_rf` / `send_rf` |
| S10/S20 socket | ❌ | ❌ | fuera del alcance de esta integración remota |

## Matriz funcional (antes / después)

| Función | Antes | Después |
|---|---:|---:|
| Config flow | ❌ | ✅ |
| Options flow | ❌ | ✅ |
| Entidad remote | ✅ | ✅ |
| Learn IR | parcial | ✅ |
| Send IR | ✅ | ✅ |
| Learn RF | ❌ | ✅ |
| Send RF | ❌ | ✅ |
| Gestión de códigos persistente | ❌ | ✅ |
| Servicios list/delete | ❌ | ✅ |
| Alias legacy | ❌ | ✅ |

## Instalación

1. Instalar desde HACS como repositorio custom.
2. Reiniciar Home Assistant.
3. Añadir integración “Orvibo Remote” desde UI o mantener YAML legado.

## Configuración

### Recomendado (UI)
- `host`: IP del Orvibo.
- `model_hint`: `auto`, `allone`, `allone_pro`.
- `enable_rf`: habilita capacidades RF en servicios.

### YAML legado (retrocompatibilidad)
```yaml
remote:
  - platform: orvibo_remote
    host: 192.168.1.50
    name: Orvibo salón
    model_hint: auto
    enable_rf: true
```

## Servicios

Todos bajo dominio `orvibo_remote`:

| Servicio | Parámetros clave |
|---|---|
| `learn_ir` | `entry_id`, `code_name`, `timeout` |
| `send_ir` | `entry_id`, `code_name` o `code` (`b64:` o base64) |
| `learn_rf` | `entry_id`, `code_name` |
| `send_rf` | `entry_id`, `code_name` o `code`, `state` |
| `list_codes` | `entry_id`, `protocol` opcional |
| `delete_code` | `entry_id`, `protocol`, `code_name` |

Alias legacy mantenidos:
- `learn` → `learn_ir`
- `emit` → `send_ir`

## Ejemplos de automatización

### Enviar IR guardado
```yaml
service: orvibo_remote.send_ir
data:
  entry_id: TU_ENTRY_ID
  code_name: tv_power
```

### Aprender RF
```yaml
service: orvibo_remote.learn_rf
data:
  entry_id: TU_ENTRY_ID
  code_name: luz_salon_on
```

### Enviar RF
```yaml
service: orvibo_remote.send_rf
data:
  entry_id: TU_ENTRY_ID
  code_name: luz_salon_on
  state: true
```

## Troubleshooting

- Si `learn_ir` no captura, repetir con `timeout` mayor y línea de visión limpia.
- En RF, usar distancia corta durante aprendizaje inicial.
- RF433 en Orvibo es esencialmente stateless para switches: no hay lectura fiable de estado real.
- Si hay timeouts, verificar IP fija y estabilidad Wi‑Fi del dispositivo.

## Riesgos y mitigaciones

- Riesgo: diferencias de firmware en modelos antiguos/pro.
  - Mitigación: `model_hint` + `enable_rf` configurable por usuario.
- Riesgo: limitaciones inherentes de RF433.
  - Mitigación: documentación explícita y errores claros en servicios.

## Migración

- Usuarios YAML existentes pueden seguir usando la plataforma `remote`.
- Se recomienda migrar a config entry para usar servicios avanzados y gestión de códigos.
- Servicios legacy `learn` y `emit` se mantienen como alias.

## Limitaciones conocidas

- El protocolo RF soportado está orientado al flujo SmartSwitch RF433 de Orvibo.
- No se garantiza interoperabilidad con dispositivos RF genéricos fuera de ese flujo.

## Licencia

MIT.
