"""Paquete para que su conftest se importe como `integration.conftest` y no pise a `test/conftest.py`
(los tests de controllers hacen `from conftest import TEST_USER_ID`)."""
