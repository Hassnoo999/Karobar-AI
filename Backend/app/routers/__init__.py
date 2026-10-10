"""All API routers; app.main mounts each one under the /api prefix."""
from app.routers import (
    ask,
    bridge,
    capture,
    customers,
    dashboard,
    events,
    evidence,
    financing,
    health,
    reminders,
)

ALL_ROUTERS = (
    bridge.router,
    health.router,
    capture.router,
    events.router,
    customers.router,
    dashboard.router,
    ask.router,
    evidence.router,
    financing.router,
    reminders.router,
)
