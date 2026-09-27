# Estrategia de testing (backend)

Cómo se testea este repo y dónde vive cada cosa. Las especificaciones de casos de cada
funcionalidad están en esta misma carpeta (`<funcionalidad>.md`).

## Principios

- **Mayormente integración.** Los mocks esconden errores en los bordes: un `UNIQUE` mal definido
  en PostgreSQL pasó todos los tests mockeados y rompía el guardado de la segunda versión. Todo lo
  que depende de la base se prueba contra **PostgreSQL real**.
- **Primero los casos, después los tests.** Cada funcionalidad tiene una especificación con casos
  identificados (felices, límite, negativos, borde, de estado), derivados con técnicas estándar:
  particiones de equivalencia, valores límite, tablas de decisión, transiciones de estado.
- **Un test que no puede fallar no sirve.** Cada test nuevo se verifica rompiendo a propósito el
  comportamiento que cubre (mutación manual): tiene que ponerse en rojo.
- **Comportamiento, no implementación.** Se verifica lo observable: valor devuelto, respuesta
  HTTP, filas en la base.

## Qué nivel para qué

| Qué | Nivel | Marker |
|---|---|---|
| Matemática: modelos, ajuste, linealización, estadísticos | Unitario, con datos sintéticos de parámetros conocidos y tolerancia explícita | — |
| Schemas / validación | Unitario: cada partición válida e inválida + límites | — |
| Services que tocan la base (guardar, versiones, borrar, restricciones, cascadas, transacciones) | **Integración** (PostgreSQL real) | `integration` |
| Controllers (ruteo, códigos HTTP, mapeo de errores) | Cliente Flask con el service mockeado | — |
| Migraciones | CI las aplica todas sobre una base vacía antes de los tests | — |

Mockear la base sólo vale para orquestación sin semántica de base (p. ej. "se valida antes de
crear la investigación"). Restricciones, cascadas y transacciones **nunca** se prueban con mocks.

## Convenciones

- Tests nuevos en estilo pytest (funciones + fixtures). Los archivos existentes en
  `unittest.TestCase` se dejan como están; no se mezclan estilos dentro de un archivo.
- Nombre: `test_should_<resultado>_when_<condición>`. El ID del caso va en el docstring
  (`"""KSAVE-N03"""`), así cada test se rastrea hasta su caso.
- Estructura Arrange / Act / Assert, separada por líneas en blanco. Un comportamiento por test.
- Datos: funciones o fixtures con valores válidos por defecto, sobrescribiendo sólo lo que el test
  prueba (`payload(sample, results=[])`).
- Números: nunca `==` con floats; `pytest.approx` / `numpy.testing.assert_allclose` con la
  tolerancia y su motivo.
- Determinismo: sin red, sin hora real, semillas fijas.
- Ubicación: `test/<capa>/<modulo>_test.py` (unitarios), `test/integration/<funcionalidad>_test.py`.

## Tipos de caso

| Prefijo | Significado |
|---|---|
| `H` | Feliz: entrada válida y representativa |
| `B` | Límite: justo en / dentro / fuera de un límite (mín-1, mín, mín+1, máx, máx+1) |
| `N` | Negativo: entrada inválida o acción prohibida, rechazada con el error correcto |
| `E` | Borde: válido pero inusual (cero, vacío permitido, duplicados, desordenado, magnitudes extremas) |
| `S` | Estado / secuencia: orden de operaciones, idempotencia, atomicidad |

IDs: `<FUNCIONALIDAD>-<tipo><nn>`, p. ej. `KSAVE-N03`.

## Tests de integración

- Necesitan `TEST_DATABASE_URL` apuntando a una base cuyo nombre termine en **`_test`**,
  construida sólo con `dbmate up`. Sin la variable, se **omiten** (no fallan). El fixture se niega
  a correr contra cualquier otra base.
- Cada test corre dentro de una transacción que se revierte al final; los `commit()` del código
  caen en un SAVEPOINT. La base queda igual que antes.
- Fixtures (`test/integration/conftest.py`): `db_session`, `make_user`, `make_kinetic_sample`.
- Detalle técnico: se reemplaza `db.session` por un `scoped_session` de SQLAlchemy atado a la
  conexión del test, porque Flask-SQLAlchemy 3.1 ignora el `bind` de la sesión y con
  `db.session.configure(bind=...)` las filas sobreviven al rollback (verificado).

## Cobertura

Cobertura de líneas con `pytest-cov`, publicada como badge por CI. Es una señal, no una meta: no
hay umbral mínimo. Código crítico sin cubrir es motivo para escribir una especificación, no para
agregar tests sin asserts.

## Lo que se decidió no adoptar

- **`pytest-flask-sqlalchemy`:** sin mantenimiento, hecho para SQLAlchemy 1.x (usamos 2.0).
- **testcontainers:** redundante con docker compose (local) y el service container (CI).
- **Umbral de cobertura y herramientas de mutación (mutmut):** a este tamaño cuestan más de lo que
  aportan; la verificación manual por test cubre la intención.
