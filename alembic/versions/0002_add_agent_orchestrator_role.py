"""add_agent_orchestrator_role

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-08 00:00:00.000000

Adds the non-human AGENT_ORCHESTRATOR value to the userrole enum
(Phase 11 Step 11.1). Additive only — does not touch any existing enum
value or row.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE ... ADD VALUE to run outside an explicit
    # transaction block in older versions; psycopg/Alembic's autocommit
    # block handles this via op.execute with the connection's isolation
    # level already set to AUTOCOMMIT by Alembic for DDL of this kind on PG.
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'agent_orchestrator'")


def downgrade() -> None:
    # PostgreSQL does not support removing a value from an existing enum
    # type directly. A downgrade would require rebuilding the enum type
    # (create new type without the value, alter every dependent column to
    # the new type, drop the old type) and is deliberately not implemented
    # here, since Phase 11 depends on this value existing and no downgrade
    # path is exercised in this project's migration history. If a downgrade
    # is ever required, first ensure no `users.role = 'agent_orchestrator'`
    # row exists, then perform the enum-rebuild sequence described above.
    raise NotImplementedError(
        "Downgrading past the agent_orchestrator enum value requires a manual "
        "enum-rebuild migration; not implemented as this project does not "
        "exercise a downgrade path for this revision."
    )