"""Add brand_trims table

Revision ID: a5c2b3d4e5f6
Revises: bc0e5c0728e8
Create Date: 2025-04-28 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5c2b3d4e5f6'
down_revision = 'bc0e5c0728e8'  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('brand_trims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'brand_id', name='unique_trim_per_brand')
    )


def downgrade():
    op.drop_table('brand_trims')
