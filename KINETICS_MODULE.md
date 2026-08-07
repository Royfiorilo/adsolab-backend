# Módulo cinético — Estructura y decisiones de diseño

Este documento describe los archivos creados para el módulo cinético de AdsoLab,
las decisiones tomadas y el motivo de existencia de cada pieza.

---

## Decisión de arquitectura: tablas separadas

Se optó por **tablas completamente separadas** (`kinetic_*`) en lugar de reutilizar
las tablas del módulo de equilibrio con un campo `type`. Motivos:

- Las muestras de equilibrio tienen `ce/qe`; las cinéticas tienen `time/qt/concentration`.
  No son intercambiables y mezclarlas en la misma tabla requeriría columnas nullable
  que no tienen sentido en el otro dominio.
- Evita el riesgo de romper queries, schemas y validaciones del módulo de equilibrio
  que hoy asumen `ce/qe` siempre presentes.
- Permite evolucionar ambos módulos de forma independiente.

---

## Archivos creados

### Entidades (`app/entities/`)

| Archivo | Propósito |
|---------|-----------|
| `kinetics_sample.py` | Dataclass `KineticsSampleEntity`. Equivalente a `sample.py` pero con `time`, `qt`, `concentration`, `volume`, `adsorbent_mass`. Incluye `remove()` para filtrar outliers y `create_sample_name()` para auto-título. |
| `kinetics_model.py` | Dataclasses `KineticsModelEntity` y `KineticsLinearizationEntity`. Representan un modelo cinético (fórmula, parámetros, LaTeX) y sus linealizaciones opcionales. |

### Schemas (`app/entities/schemas/`)

| Archivo | Propósito |
|---------|-----------|
| `kinetics_sample_schema.py` | Schema Marshmallow para `KineticSample`. Valida que `time + qt` **o** `time + concentration` (con sus parámetros derivados) estén presentes, que las longitudes coincidan y que los valores no sean negativos. |
| `kinetics_model_schema.py` | Schema para `KineticsModelEntity` y `KineticsLinearizationEntity`. |
| `kinetics_investigation_schema.py` | Schema para listar investigaciones cinéticas (incluye muestra y usuario anidados). |
| `kinetics_historic_schema.py` | Schemas para versiones guardadas: `KineticsVersionSchema`, `KineticsFittedModelSchema`, `KineticsFittedMethodSchema`, `KineticsComparisonSchema`. Espejo de `historic_schema.py`. |

### Base de datos (`app/database.py`)

Se agregaron al final del archivo los siguientes modelos SQLAlchemy (tablas separadas):

| Clase | Tabla | Propósito |
|-------|-------|-----------|
| `KineticModel` | `kinetic_model` | Modelos cinéticos con fórmula, parámetros y LaTeX. |
| `KineticLinearization` | `kinetic_linearization` | Linealizaciones de modelos cinéticos (opcional). |
| `KineticSample` | `kinetic_sample` | Datos experimentales cinéticos (time, qt, metadatos). |
| `KineticInvestigation` | `kinetic_investigation` | Sesión de análisis para una muestra cinética. |
| `KineticVersion` | `kinetic_version` | Versión con clave primaria compuesta (version_id, kinetic_investigation_id). |
| `KineticFittedModel` | `kinetic_fitted_model` | Resultado de ajuste de un modelo cinético con todos sus métodos. |
| `KineticComparison` | `kinetic_comparison` | Comparación heurística + ML de modelos cinéticos. |

### Servicios (`app/services/`)

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `kinetics_model_service.py` | Consulta `kinetic_model` en DB. Expone `find_kinetic_models()` y `find_kinetic_model(id)`. | Implementado |
| `kinetics_sample_service.py` | Valida, ordena y persiste muestras cinéticas. Calcula `qt` desde concentración si aplica. Implementa soft-delete. | Implementado |
| `kinetics_no_linear_model_service.py` | Ejecuta ajuste no lineal cinético con `time/qt`. Incluye `predict_kinetic_seeds()` (implementado con heurísticas simples) y `run_kinetic_no_linear_models()` (stub pendiente de validación científica). | Parcial |
| `kinetics_linearization_service.py` | Ejecuta linealizaciones cinéticas (e.g., ln(qe-qt) vs t). Stub pendiente; el primer alcance puede omitirse. | Stub |
| `kinetics_comparison_service.py` | Compara modelos cinéticos ajustados con heurística y Ridge Regression. Stub pendiente del ajuste no lineal. | Stub |
| `kinetics_version_service.py` | Persiste y recupera versiones de investigaciones cinéticas. Stub pendiente. | Stub |
| `kinetics_investigation_service.py` | Orquesta el flujo completo: seeds, ajuste, guardado, historial. `create_kinetic_investigation()` y `get_kinetic_investigations()` están implementados; los wrappers de análisis delegan a sus respectivos servicios. | Parcial |

### Controlador (`app/controller/`)

| Archivo | Propósito |
|---------|-----------|
| `kinetics_controller.py` | Blueprint Flask con todos los endpoints `/kinetics/*`. Incluye los 10 endpoints del plan: modelos, muestras (CRUD), seeds, linealización, ajuste no lineal, guardar, listar/ver/borrar investigaciones y versiones. |

El blueprint se registra en `app/__init__.py` junto a los demás controladores existentes.

### Migraciones (`db/migrations/`)

Siete migraciones nuevas, numeradas a partir de `20260601000001`. Deben aplicarse
en orden:

| Archivo | Tabla creada |
|---------|-------------|
| `20260601000001_create_table_kinetic_model.sql` | `kinetic_model` |
| `20260601000002_create_table_kinetic_linearization.sql` | `kinetic_linearization` |
| `20260601000003_create_table_kinetic_sample.sql` | `kinetic_sample` |
| `20260601000004_create_table_kinetic_investigation.sql` | `kinetic_investigation` |
| `20260601000005_create_table_kinetic_version.sql` | `kinetic_version` |
| `20260601000006_create_table_kinetic_fitted_model.sql` | `kinetic_fitted_model` |
| `20260601000007_create_table_kinetic_comparison.sql` | `kinetic_comparison` |

---

## Archivos del módulo de equilibrio modificados

| Archivo | Cambio |
|---------|--------|
| `app/database.py` | Se agregaron los 7 modelos SQLAlchemy cinéticos al final. Sin cambios en las clases existentes. |
| `app/__init__.py` | Se importa y registra `kinetics_controller.blueprint`. Sin cambios en los demás blueprints. |

---

## Próximos pasos (pendiente de validación científica)

1. **Definir modelos cinéticos iniciales** (PFO, PSO, difusión intraparticular) e
   insertarlos en `kinetic_model` mediante una migración tipo `add_models`.
2. **Implementar `run_kinetic_no_linear_models`** en `kinetics_no_linear_model_service.py`
   siguiendo el patrón de `FitStrategy` de `no_linear_model_service.py`.
3. **Implementar `kinetics_comparison_service.py`** con la misma lógica heurística
   que `comparison_service.py`, ajustando pesos si Jorge/Silvia lo indican.
4. **Implementar `kinetics_version_service.py`** para persistir y recuperar versiones.
5. **Decidir si se incluyen linealizaciones cinéticas** en el primer alcance.
6. **Agregar tests** en `test/controller/` y `test/entities/` para cada nuevo endpoint
   y servicio.
7. **Actualizar `openapi-spec.yml`** con los paths `/kinetics/*` y sus schemas.

---

## Contrato de datos resumido

```
POST /kinetics/sample
  Body: { time[], qt[] | concentration[], initial_concentration, volume, adsorbent_mass,
          temperature, time_unit, measure_unit, adsorbate_id, adsorbent_id, title?, description? }

POST /kinetics/predict-seeds
  Body: { kinetic_sample_id, models: [{model: id}], filter?: [] }

POST /kinetics/run-no-linear-model
  Body: { kinetic_sample_id, models: [{model, seeds, iterations, step, bounds?}], filter?: [] }
  Response: { kinetic_sample_id, results: [...], comparison: {heuristic, ml?} }

POST /kinetics/investigation/save
  Body: { kinetic_sample_id, kinetic_investigation_id?, iterations, steps, results, comparison }
  Response: { status, kinetic_investigation_id, version_id }
```
