"""add brand synonyms

Revision ID: 41046ee64407
Revises: 2772cbfd6690
Create Date: 2025-04-15 13:44:16.590278

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41046ee64407'
down_revision = '2772cbfd6690'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('brand_synonyms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('brand_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('brand_synonyms')
    # ### end Alembic commands ###
