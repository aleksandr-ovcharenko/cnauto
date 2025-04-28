"""merge multiple heads

Revision ID: 15ef925c4c6e
Revises: 079c2b3a55d8, a5c2b3d4e5f6
Create Date: 2025-04-28 16:47:34.070040

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15ef925c4c6e'
down_revision = ('079c2b3a55d8', 'a5c2b3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
