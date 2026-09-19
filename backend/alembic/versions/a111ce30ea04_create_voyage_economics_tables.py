"""create_voyage_economics_tables

Revision ID: a111ce30ea04
Revises: a101bd20ea03
Create Date: 2026-09-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a111ce30ea04'
down_revision: Union[str, Sequence[str], None] = 'a101bd20ea03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. voyage_economic_analyses
    op.create_table('voyage_economic_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('voyage_id', sa.String(length=36), nullable=True),
        sa.Column('cargo_request_id', sa.String(length=36), nullable=True),
        sa.Column('vessel_id', sa.String(length=36), nullable=True),
        sa.Column('origin_port_id', sa.String(length=36), nullable=False),
        sa.Column('destination_port_id', sa.String(length=36), nullable=False),
        sa.Column('distance_nm', sa.Float(), nullable=False),
        sa.Column('cargo_quantity_mt', sa.Float(), nullable=False),
        sa.Column('freight_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('bunker_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('port_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('time_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('delay_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('repositioning_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('other_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cost_per_mt', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('data_status', sa.String(length=50), nullable=False, server_default='SYNTHETIC'),
        sa.Column('model_version', sa.String(length=100), nullable=False, server_default='VOYAGE_ECONOMICS_V1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cargo_request_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['origin_port_id'], ['ports.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['destination_port_id'], ['ports.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voyage_economic_analyses_id'), 'voyage_economic_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_voyage_economic_analyses_voyage_id'), 'voyage_economic_analyses', ['voyage_id'], unique=False)
    op.create_index(op.f('ix_voyage_economic_analyses_cargo_request_id'), 'voyage_economic_analyses', ['cargo_request_id'], unique=False)
    op.create_index(op.f('ix_voyage_economic_analyses_vessel_id'), 'voyage_economic_analyses', ['vessel_id'], unique=False)
    op.create_index(op.f('ix_voyage_economic_analyses_origin_port_id'), 'voyage_economic_analyses', ['origin_port_id'], unique=False)
    op.create_index(op.f('ix_voyage_economic_analyses_destination_port_id'), 'voyage_economic_analyses', ['destination_port_id'], unique=False)
    op.create_index(op.f('ix_voyage_economic_analyses_created_at'), 'voyage_economic_analyses', ['created_at'], unique=False)

    # 2. voyage_cost_components
    op.create_table('voyage_cost_components',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='USD'),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('rate', sa.Float(), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.String(length=50), nullable=False, server_default='SYNTHETIC'),
        sa.Column('assumption', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['voyage_economic_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voyage_cost_components_id'), 'voyage_cost_components', ['id'], unique=False)
    op.create_index(op.f('ix_voyage_cost_components_analysis_id'), 'voyage_cost_components', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_voyage_cost_components_component_type'), 'voyage_cost_components', ['component_type'], unique=False)

    # 3. speed_scenarios
    op.create_table('speed_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('speed_knots', sa.Float(), nullable=False),
        sa.Column('sailing_hours', sa.Float(), nullable=False),
        sa.Column('sailing_days', sa.Float(), nullable=False),
        sa.Column('fuel_consumption', sa.Float(), nullable=True),
        sa.Column('fuel_consumed', sa.Float(), nullable=True),
        sa.Column('bunker_price', sa.Float(), nullable=True),
        sa.Column('bunker_cost', sa.Float(), nullable=True),
        sa.Column('time_cost', sa.Float(), nullable=True),
        sa.Column('delay_exposure', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('cost_per_mt', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='EVALUATED'),
        sa.Column('assumptions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['voyage_economic_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_speed_scenarios_id'), 'speed_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_speed_scenarios_analysis_id'), 'speed_scenarios', ['analysis_id'], unique=False)

    # 4. voyage_scenarios
    op.create_table('voyage_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('scenario_name', sa.String(length=50), nullable=False),
        sa.Column('freight_rate', sa.Float(), nullable=True),
        sa.Column('bunker_price', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('port_delay_hours', sa.Float(), nullable=True),
        sa.Column('idle_days', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('cost_per_mt', sa.Float(), nullable=False),
        sa.Column('assumptions', sa.Text(), nullable=True),
        sa.Column('data_status', sa.String(length=50), nullable=False, server_default='SYNTHETIC'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['voyage_economic_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voyage_scenarios_id'), 'voyage_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_voyage_scenarios_analysis_id'), 'voyage_scenarios', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_voyage_scenarios_scenario_name'), 'voyage_scenarios', ['scenario_name'], unique=False)


def downgrade() -> None:
    op.drop_table('voyage_scenarios')
    op.drop_table('speed_scenarios')
    op.drop_table('voyage_cost_components')
    op.drop_table('voyage_economic_analyses')
