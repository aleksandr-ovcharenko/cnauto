"""Merge multiple heads

Revision ID: eee9ecce1ce4
Revises: 51b2cdf79d55, add_car_engines_table
Create Date: 2025-04-28 21:36:13.009958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eee9ecce1ce4'
down_revision = ('51b2cdf79d55', 'add_car_engines_table')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
