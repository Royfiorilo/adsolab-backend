# Test spec: save and manage kinetic versions (`KSAVE`)

**Under test:**
- `POST /kinetics/investigation/save` → `validate_and_save_kinetic_version` (`app/services/kinetics_investigation_service.py`)
  → `create_kinetic_investigation` + `save_kinetic_version` (`app/services/kinetics_version_service.py`)
- `GET /kinetics/investigation/<id>/versions`, `GET …/version/<ver>`, `DELETE …/version/<ver>`, `DELETE /kinetics/investigation/<id>`

**Inputs:** `kinetic_sample_id`, `kinetic_investigation_id` (optional), `results[]` (`model`, `best_adjust`, `adjustment_methods`, `seeds`), `comparison` (`heuristic`, `ml`), `iterations`, `steps`, authenticated user.
**Outputs / side effects:** rows in `kinetic_investigation`, `kinetic_version`, `kinetic_fitted_model`, `kinetic_comparison`; signals `version_saved` / `version_deleted`.
**Errors:** `BadRequestError` (400), `NotFoundError` (404), `ForbiddenError` (403).
**Levels:** `unit` (no DB) · `integration` (real PostgreSQL, `@pytest.mark.integration`) · `controller` (Flask client, service mocked)
**Types:** H happy · B boundary · N negative · E edge · S state/sequence

## Cases

### Save

| ID | Type | Level | Given / input | Expected | Status | Test |
|---|---|---|---|---|---|---|
| KSAVE-H01 | H | integration | valid sample, no previous investigation, 1 result | 1 investigation, version 1, 1 fitted model, 1 comparison | new | `test_should_create_investigation_and_first_version_when_sample_has_none` |
| KSAVE-H02 | H | integration | save, then read the version | `adjustment_methods`, `seeds`, `heuristic`, `ml` come back identical (JSON/ARRAY) | new | `test_should_read_back_exactly_what_was_saved` |
| KSAVE-H03 | H | controller | valid payload | 201 with `kinetic_investigation_id` and `version_id` | covered | `test_save_kinetics_investigation` |
| KSAVE-B01 | B | integration | first version of an investigation | `version_id = 1` | new | `test_should_create_investigation_and_first_version_when_sample_has_none` |
| KSAVE-B02 | B | integration | `comparison.heuristic = {}` (empty dict) | 400, nothing written | new | `test_should_reject_and_write_nothing_when_heuristic_is_an_empty_dict` |
| KSAVE-N01 | N | unit | `results = []` | 400 | covered | `test_should_raise_bad_request_when_results_are_empty` |
| KSAVE-N02 | N | unit | result without `model` / `best_adjust` / `adjustment_methods` (one per field) | 400 naming the field | new | `test_should_raise_bad_request_naming_each_missing_required_field` |
| KSAVE-N03 | N | unit | `comparison` without `heuristic` | 400 | covered | `test_should_raise_bad_request_when_comparison_has_no_heuristic` |
| KSAVE-N04 | N | integration | unknown `kinetic_sample_id` | 404, nothing written | new | `test_should_raise_not_found_and_write_nothing_when_sample_does_not_exist` |
| KSAVE-N05 | N | integration | soft-deleted sample (`deleted_at`) | 404, nothing written | new | `test_should_raise_not_found_when_sample_is_soft_deleted` |
| KSAVE-N06 | N | integration | another user's `kinetic_investigation_id` | 403, that investigation gets no new version | new | `test_should_forbid_saving_into_another_user_investigation` |
| KSAVE-N07 | N | unit | unknown `kinetic_investigation_id` | 404 | covered | `test_should_raise_not_found_when_the_given_investigation_does_not_exist` |
| KSAVE-N08 | N | integration | missing `kinetic_sample_id` (and no investigation) | 400 | open | Q1 |
| KSAVE-N09 | N | integration | non-numeric `model` (`"abc"`) | 400 | open | Q2 |
| KSAVE-E01 | E | integration | `comparison.ml = null` | saved with `ml` NULL | new | `test_should_store_null_ml_when_comparison_has_no_ml` |
| KSAVE-E02 | E | integration | result without `seeds` | saved with `seeds = []` | new | `test_should_store_empty_seeds_when_result_has_none` |
| KSAVE-E03 | E | integration | `iterations` / `steps` present and absent | stored as given / NULL | new | `test_should_store_iterations_and_steps_as_given` |
| KSAVE-S01 | S | integration | 2nd save, same sample and user | same investigation, version 2 | new | `test_should_add_version_two_to_the_same_investigation_on_second_save` |
| KSAVE-S02 | S | integration | invalid payload on a new sample | no investigation created (atomicity) | new | `test_should_create_no_investigation_when_payload_is_invalid` |
| KSAVE-S03 | S | integration | two investigations, each with its version 1 | both saved (UNIQUE bug) | new | `test_should_let_each_investigation_have_its_own_version_one` |
| KSAVE-S04 | S | integration | writing fails after the investigation is created (DB error at commit) | full rollback: no investigation, no version | new | `test_should_roll_back_the_new_investigation_when_writing_the_version_fails` |
| KSAVE-S05 | S | integration | save with own `kinetic_investigation_id` given explicitly | version n+1 in that investigation | new | `test_should_add_next_version_when_saving_into_own_investigation_explicitly` |
| KSAVE-S06 | S | unit | duplicate comparison for the same version | rejected by the constraint | covered | `test_should_reject_a_second_comparison_for_the_same_version` |

### Read, list, delete

| ID | Type | Level | Given / input | Expected | Status | Test |
|---|---|---|---|---|---|---|
| KSAVE-H04 | H | integration | investigation with v1, v2, v3 | list sorted ascending by `version_id` | new | `test_should_list_versions_in_ascending_order` |
| KSAVE-N10 | N | unit | unknown version | 404 | covered | `test_should_raise_not_found_when_version_does_not_exist` |
| KSAVE-N11 | N | unit | list versions of an unknown investigation | 404 | covered | `TestGetKineticVersions.test_should_raise_not_found_when_investigation_does_not_exist` |
| KSAVE-N12 | N | integration | delete a version as another user | 403, version still exists | new | `test_should_forbid_deleting_a_version_of_another_user` |
| KSAVE-S07 | S | integration | delete a version | its fitted models and comparison are gone (cascade); other versions stay | new | `test_should_delete_a_version_with_its_fitted_models_and_comparison_only` |
| KSAVE-S08 | S | integration | delete the investigation | all its versions and dependants are gone | new | `test_should_delete_every_version_when_deleting_the_investigation` |
| KSAVE-S09 | S | integration | with v1 and v2, delete v2 and save again | the new version is 2 (number reused) | open | Q3 |

## Open questions

Behaviour the code does not clearly define. Not resolved by guessing.

1. **Q1: Missing `kinetic_sample_id`.** `None` reaches `find_kinetic_sample` and the API answers
   **404** "Kinetic sample with id None". Should it be **400** (missing required field)?
2. **Q2: Wrong types in `results`.** Validation only checks that keys exist. A non-numeric
   `model` fails in the DB at commit → **500**. Validate types → 400?
3. **Q3: Version number reuse.** `version_id = max + 1`: deleting the last version makes the next
   save reuse its number, so an old link to `…/version/2` shows different results. Acceptable, or
   should numbers be monotonic?
4. **Q4: Saving on another user's sample.** Given someone else's `kinetic_sample_id`, an
   investigation of the current user is created on that sample. Allowed?

## Existing tests not mapped to a case

- `test_should_flush_without_committing_a_new_investigation`: implementation contract behind
  KSAVE-S02/S04 at unit level; kept.
- `test_should_allow_version_one_in_several_investigations` / `…several_versions_of_one_investigation`
  (SQLite): duplicate KSAVE-S03/S01 without a real DB; kept because they run without Postgres.
