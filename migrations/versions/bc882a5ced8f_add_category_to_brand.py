"""Add Category to Brand

Revision ID: bc882a5ced8f
Revises: d5729cd0fc25
Create Date: 2025-04-10 14:14:38.217338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc882a5ced8f'
down_revision: Union[str, None] = 'd5729cd0fc25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('brands', sa.Column('category', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('brands', 'category')
    # ### end Alembic commands ###
