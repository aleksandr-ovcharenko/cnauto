"""uptading car.currency

Revision ID: 83633af0d5af
Revises: 4fad104e55c3
Create Date: 2025-04-19 15:05:25.933570

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83633af0d5af'
down_revision = '4fad104e55c3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('currencies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locale', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('currencies', schema=None) as batch_op:
        batch_op.drop_column('locale')

    # ### end Alembic commands ###
