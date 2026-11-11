"""numero da ordem

Revision ID: f3a91c0e7b21
Revises: c94bc8e12047
Create Date: 2026-11-10 15:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f3a91c0e7b21"
down_revision = "c94bc8e12047"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("solicitacoes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("numero_ordem", sa.String(length=40), nullable=True))


def downgrade():
    with op.batch_alter_table("solicitacoes", schema=None) as batch_op:
        batch_op.drop_column("numero_ordem")
