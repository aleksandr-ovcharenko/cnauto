"""add specifications table

Revision ID: 2e8bd4f3a712
Revises: bfe702e2a74b
Create Date: 2025-05-27 19:32:10.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2e8bd4f3a712'
down_revision = 'bfe702e2a74b'  # This points to add_task_id_to_image_tasks_table.py
branch_labels = None
depends_on = None


def upgrade():
    # Create specifications table only - don't touch existing tables
    op.create_table('specifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('generation', sa.String(length=50), nullable=True),
        sa.Column('modification', sa.String(length=100), nullable=True),
        
        # Engine specifications
        sa.Column('engine_code', sa.String(length=50), nullable=True),
        sa.Column('engine_type', sa.String(length=50), nullable=True),
        sa.Column('displacement_cc', sa.Integer(), nullable=True),
        sa.Column('power_hp', sa.Integer(), nullable=True),
        sa.Column('power_kw', sa.Integer(), nullable=True),
        sa.Column('torque_nm', sa.Integer(), nullable=True),
        sa.Column('cylinders', sa.Integer(), nullable=True),
        sa.Column('valves_per_cylinder', sa.Integer(), nullable=True),
        sa.Column('fuel_system', sa.String(length=100), nullable=True),
        sa.Column('fuel_type', sa.String(length=50), nullable=True),
        
        # Performance data
        sa.Column('acceleration_0_100', sa.Float(), nullable=True),
        sa.Column('top_speed_kmh', sa.Integer(), nullable=True),
        sa.Column('fuel_consumption_urban', sa.Float(), nullable=True),
        sa.Column('fuel_consumption_extra_urban', sa.Float(), nullable=True),
        sa.Column('fuel_consumption_combined', sa.Float(), nullable=True),
        sa.Column('co2_emissions', sa.Integer(), nullable=True),
        sa.Column('emission_standard', sa.String(length=20), nullable=True),
        
        # Dimensions and weight
        sa.Column('length_mm', sa.Integer(), nullable=True),
        sa.Column('width_mm', sa.Integer(), nullable=True),
        sa.Column('height_mm', sa.Integer(), nullable=True),
        sa.Column('wheelbase_mm', sa.Integer(), nullable=True),
        sa.Column('front_track_mm', sa.Integer(), nullable=True),
        sa.Column('rear_track_mm', sa.Integer(), nullable=True),
        sa.Column('curb_weight_kg', sa.Integer(), nullable=True),
        sa.Column('max_weight_kg', sa.Integer(), nullable=True),
        sa.Column('trunk_volume_l', sa.Integer(), nullable=True),
        sa.Column('fuel_tank_volume_l', sa.Integer(), nullable=True),
        
        # Transmission and drivetrain
        sa.Column('transmission_type', sa.String(length=50), nullable=True),
        sa.Column('transmission_name', sa.String(length=100), nullable=True),
        sa.Column('gears', sa.Integer(), nullable=True),
        sa.Column('drive_type', sa.String(length=50), nullable=True),
        
        # Wheels and tires
        sa.Column('front_tires', sa.String(length=50), nullable=True),
        sa.Column('rear_tires', sa.String(length=50), nullable=True),
        sa.Column('front_brakes', sa.String(length=100), nullable=True),
        sa.Column('rear_brakes', sa.String(length=100), nullable=True),
        
        # JSON field for additional specifications
        sa.Column('specifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        
        # Primary key and foreign keys
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
        sa.UniqueConstraint('name')
    )
    
    # Add index on brand_id for faster lookups
    op.create_index(op.f('ix_specifications_brand_id'), 'specifications', ['brand_id'], unique=False)
    
    # Add specification_id to cars table
    op.add_column('cars', sa.Column('specification_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_cars_specification_id', 'cars', 'specifications', ['specification_id'], ['id'])


def downgrade():
    # Remove foreign key from cars
    op.drop_constraint('fk_cars_specification_id', 'cars', type_='foreignkey')
    op.drop_column('cars', 'specification_id')
    
    # Drop index
    op.drop_index(op.f('ix_specifications_brand_id'), table_name='specifications')
    
    # Drop specifications table
    op.drop_table('specifications')
