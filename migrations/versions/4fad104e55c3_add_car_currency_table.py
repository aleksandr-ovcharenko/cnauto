"""add car.currency table

Revision ID: 4fad104e55c3
Revises: bc0e5c0728e8
Create Date: 2025-04-19 15:01:00.717772

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fad104e55c3'
down_revision = 'bc0e5c0728e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('currencies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('symbol', sa.String(length=10), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    with op.batch_alter_table('cars', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'currencies', ['currency_id'], ['id'])
        batch_op.drop_column('currency')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cars', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.VARCHAR(length=10), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('currency_id')

    op.drop_table('currencies')
    # ### end Alembic commands ###
