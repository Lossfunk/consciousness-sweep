"""Serialize a bounded local decision and its writes on one SQLite snapshot.

No network or model calls belong inside these transactions. Source snapshots
may be prepared outside the lock; source-generation checks and publication must
commit together. Nested operations use savepoints on the same connection.
"""
from contextlib import contextmanager
from copy import copy
from functools import wraps


def transaction_view(coordinator, conn):
    view, store = copy(coordinator), copy(coordinator.store)
    counter = 0

    @contextmanager
    def connection():
        yield conn

    @contextmanager
    def transaction():
        nonlocal counter
        counter += 1
        name = "nested_operation_" + str(id(store)) + "_" + str(counter)
        conn.execute("SAVEPOINT " + name)
        try:
            yield conn
            conn.execute("RELEASE SAVEPOINT " + name)
        except BaseException:
            conn.execute("ROLLBACK TO SAVEPOINT " + name)
            conn.execute("RELEASE SAVEPOINT " + name)
            raise

    store._connection, store._transaction = connection, transaction
    view.store = store
    return view


def atomic_operation(operation):
    @wraps(operation)
    def execute(coordinator, *args, **kwargs):
        with coordinator.store._transaction() as conn:
            view = transaction_view(coordinator, conn)
            result = operation(view, *args, **kwargs)
        if getattr(view, "_calibration_dirty", False):
            coordinator._calibration_dirty = True
        return result
    return execute
