"""Add task_id to image_tasks table

Revision ID: bfe702e2a74b
Revises: eee9ecce1ce4
Create Date: 2025-05-27 13:29:41.004857

"""
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'bfe702e2a74b'
down_revision = 'eee9ecce1ce4'
branch_labels = None
depends_on = None


def upgrade():
    # Add the column as nullable first
    with op.batch_alter_table('image_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('task_id', sa.String(length=64), nullable=True))
    
    # Create a connection and session
    conn = op.get_bind()
    session = Session(bind=conn)
    
    # Update existing records with UUIDs
    try:
        # For each record in image_tasks, set a unique task_id
        conn.execute(
            sa.text("UPDATE image_tasks SET task_id = :prefix || id || :suffix"),
            {
                'prefix': str(uuid.uuid4())[:8] + '-',
                'suffix': '-' + str(uuid.uuid4())[:4]
            }
        )
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
    
    # Now alter the column to be non-nullable
    with op.batch_alter_table('image_tasks', schema=None) as batch_op:
        batch_op.alter_column('task_id', nullable=False)
        batch_op.create_index('idx_image_tasks_car_status', ['car_id', 'status'], unique=False)
        batch_op.create_index('idx_image_tasks_created', ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_image_tasks_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_image_tasks_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_image_tasks_task_id'), ['task_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_image_tasks_updated_at'), ['updated_at'], unique=False)


def downgrade():
    with op.batch_alter_table('image_tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_image_tasks_updated_at'))
        batch_op.drop_index(batch_op.f('ix_image_tasks_task_id'))
        batch_op.drop_index(batch_op.f('ix_image_tasks_status'))
        batch_op.drop_index(batch_op.f('ix_image_tasks_created_at'))
        batch_op.drop_index('idx_image_tasks_created')
        batch_op.drop_index('idx_image_tasks_car_status')
        batch_op.drop_column('task_id')
