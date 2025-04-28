"""Add car engine table

Revision ID: add_car_engines_table
Revises: add_brand_trims_table
Create Date: 2025-04-28 19:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_car_engines_table'
down_revision = 'add_brand_trims_table'  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('car_engines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('car_id', sa.Integer(), nullable=False),
        sa.Column('displacement', sa.String(length=20), nullable=True),
        sa.Column('power_hp', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('drive', sa.String(length=20), nullable=True),
        sa.Column('transmission', sa.String(length=20), nullable=True),
        sa.Column('engine_text', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['car_id'], ['cars.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('car_engines')
