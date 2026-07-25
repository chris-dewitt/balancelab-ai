"""FastAPI dependencies.

The unit-of-work factory is chosen once at app-construction time and stored on
``app.state``. Each request opens a fresh unit of work, which is committed if the
handler succeeds and rolled back otherwise. Handlers depend only on the
:class:`~balancelab.storage.interfaces.UnitOfWork` Protocol, never on a backend.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request

from balancelab.storage import UnitOfWork, UnitOfWorkFactory


def get_uow_factory(request: Request) -> UnitOfWorkFactory:
    factory: UnitOfWorkFactory = request.app.state.uow_factory
    return factory


def get_uow(request: Request) -> Iterator[UnitOfWork]:
    """Yield a per-request unit of work, committing on success."""

    factory = get_uow_factory(request)
    with factory() as uow:
        yield uow
        uow.commit()
