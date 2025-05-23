"""add car modifications

Revision ID: 079c2b3a55d8
Revises: 83633af0d5af
Create Date: 2025-04-25 22:20:53.782511

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '079c2b3a55d8'
down_revision = '83633af0d5af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cars', schema=None) as batch_op:
        batch_op.add_column(sa.Column('modification', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('trim', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cars', schema=None) as batch_op:
        batch_op.drop_column('trim')
        batch_op.drop_column('modification')

    # ### end Alembic commands ###
