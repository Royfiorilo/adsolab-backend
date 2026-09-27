# Test spec — Guardar y gestionar versiones cinéticas (`KSAVE`)

**Bajo prueba:**
- `POST /kinetics/investigation/save` → `validate_and_save_kinetic_version` (`app/services/kinetics_investigation_service.py`)
  → `create_kinetic_investigation` + `save_kinetic_version` (`app/services/kinetics_version_service.py`)
- `GET /kinetics/investigation/<id>/versions`, `GET …/version/<ver>`, `DELETE …/version/<ver>`, `DELETE /kinetics/investigation/<id>`

**Entradas:** `kinetic_sample_id`, `kinetic_investigation_id` (opcional), `results[]` (`model`, `best_adjust`, `adjustment_methods`, `seeds`), `comparison` (`heuristic`, `ml`), `iterations`, `steps`, usuario autenticado.
**Salidas / efectos:** filas en `kinetic_investigation`, `kinetic_version`, `kinetic_fitted_model`, `kinetic_comparison`; señales `version_saved` / `version_deleted`.
**Errores:** `BadRequestError` (400), `NotFoundError` (404), `ForbiddenError` (403).
**Niveles:** `unit` (sin base) · `integration` (PostgreSQL real, `@pytest.mark.integration`) · `controller` (cliente Flask, service mockeado)
**Tipos:** H feliz · B límite · N negativo · E borde · S estado/secuencia

## Casos

### Guardar

| ID | Tipo | Nivel | Dado / entrada | Esperado | Estado | Test |
|---|---|---|---|---|---|---|
| KSAVE-H01 | H | integration | muestra válida, sin investigación previa, 1 resultado | 1 investigación, versión 1, 1 fitted model, 1 comparación | new | `test_should_create_investigation_and_first_version_when_sample_has_none` |
| KSAVE-H02 | H | integration | guardar y leer la versión | `adjustment_methods`, `seeds`, `heuristic`, `ml` vuelven idénticos (JSON/ARRAY) | new | `test_should_read_back_exactly_what_was_saved` |
| KSAVE-H03 | H | controller | payload válido | 201 con `kinetic_investigation_id` y `version_id` | covered | `test_save_kinetics_investigation` |
| KSAVE-B01 | B | integration | primera versión de una investigación | `version_id = 1` | new | `test_should_create_investigation_and_first_version_when_sample_has_none` |
| KSAVE-B02 | B | integration | `comparison.heuristic = {}` (dict vacío) | 400, nada escrito | new | `test_should_reject_and_write_nothing_when_heuristic_is_an_empty_dict` |
| KSAVE-N01 | N | unit | `results = []` | 400 | covered | `test_should_raise_bad_request_when_results_are_empty` |
| KSAVE-N02 | N | unit | resultado sin `model` / sin `best_adjust` / sin `adjustment_methods` (uno por campo) | 400 nombrando el campo | new | `test_should_raise_bad_request_naming_each_missing_required_field` |
| KSAVE-N03 | N | unit | `comparison` sin `heuristic` | 400 | covered | `test_should_raise_bad_request_when_comparison_has_no_heuristic` |
| KSAVE-N04 | N | integration | `kinetic_sample_id` inexistente | 404, nada escrito | new | `test_should_raise_not_found_and_write_nothing_when_sample_does_not_exist` |
| KSAVE-N05 | N | integration | muestra con soft-delete (`deleted_at`) | 404, nada escrito | new | `test_should_raise_not_found_when_sample_is_soft_deleted` |
| KSAVE-N06 | N | integration | `kinetic_investigation_id` de otro usuario | 403, la investigación ajena no gana versiones | new | `test_should_forbid_saving_into_another_user_investigation` |
| KSAVE-N07 | N | unit | `kinetic_investigation_id` inexistente | 404 | covered | `test_should_raise_not_found_when_the_given_investigation_does_not_exist` |
| KSAVE-N08 | N | integration | falta `kinetic_sample_id` (y no hay investigación) | 400 | open | Q1 |
| KSAVE-N09 | N | integration | `model` no numérico (`"abc"`) | 400 | open | Q2 |
| KSAVE-E01 | E | integration | `comparison.ml = null` | se guarda con `ml` NULL | new | `test_should_store_null_ml_when_comparison_has_no_ml` |
| KSAVE-E02 | E | integration | resultado sin `seeds` | se guarda `seeds = []` | new | `test_should_store_empty_seeds_when_result_has_none` |
| KSAVE-E03 | E | integration | `iterations` / `steps` presentes y ausentes | se guardan tal cual / NULL | new | `test_should_store_iterations_and_steps_as_given` |
| KSAVE-S01 | S | integration | 2º guardado, misma muestra y usuario | misma investigación, versión 2 | new | `test_should_add_version_two_to_the_same_investigation_on_second_save` |
| KSAVE-S02 | S | integration | payload inválido sobre muestra nueva | ninguna investigación creada (atomicidad) | new | `test_should_create_no_investigation_when_payload_is_invalid` |
| KSAVE-S03 | S | integration | dos investigaciones distintas, cada una su versión 1 | ambas se guardan (bug de los UNIQUE) | new | `test_should_let_each_investigation_have_its_own_version_one` |
| KSAVE-S04 | S | integration | falla la escritura después de crear la investigación (error de base al hacer commit) | rollback completo: ni investigación ni versión | new | `test_should_roll_back_the_new_investigation_when_writing_the_version_fails` |
| KSAVE-S05 | S | integration | guardar con `kinetic_investigation_id` propio explícito | versión n+1 en esa investigación | new | `test_should_add_next_version_when_saving_into_own_investigation_explicitly` |
| KSAVE-S06 | S | unit | comparación duplicada para la misma versión | la restricción la rechaza | covered | `test_should_reject_a_second_comparison_for_the_same_version` |

### Leer, listar, borrar

| ID | Tipo | Nivel | Dado / entrada | Esperado | Estado | Test |
|---|---|---|---|---|---|---|
| KSAVE-H04 | H | integration | investigación con v1, v2, v3 | lista ordenada ascendente por `version_id` | new | `test_should_list_versions_in_ascending_order` |
| KSAVE-N10 | N | unit | versión inexistente | 404 | covered | `test_should_raise_not_found_when_version_does_not_exist` |
| KSAVE-N11 | N | unit | listar versiones de investigación inexistente | 404 | covered | `TestGetKineticVersions.test_should_raise_not_found_when_investigation_does_not_exist` |
| KSAVE-N12 | N | integration | borrar versión siendo otro usuario | 403 y la versión sigue existiendo | new | `test_should_forbid_deleting_a_version_of_another_user` |
| KSAVE-S07 | S | integration | borrar una versión | desaparecen sus fitted models y su comparación (cascada); las otras versiones quedan | new | `test_should_delete_a_version_with_its_fitted_models_and_comparison_only` |
| KSAVE-S08 | S | integration | borrar la investigación | desaparecen todas sus versiones y dependientes | new | `test_should_delete_every_version_when_deleting_the_investigation` |
| KSAVE-S09 | S | integration | con v1 y v2, borrar v2 y volver a guardar | la nueva versión es la 2 (se reutiliza el número) | open | Q3 |

## Preguntas abiertas

Comportamientos que el código no define bien. No se resuelven adivinando.

1. **Q1 — falta `kinetic_sample_id`.** Hoy llega `None` a `find_kinetic_sample` y responde **404**
   "Kinetic sample with id None". ¿Debería ser **400** (campo requerido faltante)?
2. **Q2 — tipos incorrectos en `results`.** La validación sólo mira que las claves existan. Un
   `model` no numérico explota en la base al hacer commit → **500**. ¿Validamos tipos → 400?
3. **Q3 — reutilización del número de versión.** `version_id = max + 1`: si se borra la última
   versión, el próximo guardado reutiliza su número, y un link viejo a `…/version/2` pasa a mostrar
   otros resultados. ¿Es aceptable o el número debe ser monotónico?
4. **Q4 — guardar sobre la muestra de otro usuario.** Con `kinetic_sample_id` de una muestra ajena,
   se crea una investigación del usuario actual sobre esa muestra. ¿Está permitido?

## Tests existentes sin caso asociado

- `test_should_flush_without_committing_a_new_investigation` — contrato de implementación que
  sostiene KSAVE-S02/S04 a nivel unitario; se mantiene.
- `test_should_allow_version_one_in_several_investigations` / `…several_versions_of_one_investigation`
  (SQLite) — duplican KSAVE-S03/S01 sin base real; se mantienen porque corren sin Postgres.
