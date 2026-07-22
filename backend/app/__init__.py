"""ACME Project Tracker backend.

Layered architecture, top to bottom:

    api/            HTTP routes. Parse the request, call a service, return.
    services/       Business rules. The only layer that makes decisions.
    repositories/   Database queries. The only layer that touches SQLAlchemy.
    models/         ORM entities mapped to tables.
    dto/            Request and response shapes crossing the API boundary.
    core/           Cross-cutting concerns: config, security, dependencies, errors.
    db/             Engine, session and declarative base.
    seeds/          Demo data.

Each layer depends only on the ones below it, so a change to the database does
not ripple up into the routes.
"""

__version__ = "2.0.0"
