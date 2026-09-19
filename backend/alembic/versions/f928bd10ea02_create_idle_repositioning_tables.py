"""create_idle_repositioning_tables

Revision ID: f928bd10ea02
Revises: e817bc92da01
Create Date: 2026-09-18 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f928bd10ea02'
down_revision: Union[str, Sequence[str], None] = 'e817bc92da01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. vessel_employment_events
    op.create_table('vessel_employment_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vessel_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.Enum('VOYAGE_TRANSIT', 'DISCHARGE', 'LOAD', 'ANCHORAGE_WAIT', 'BALLAST_REPOSITION', 'MAINTENANCE', name='employmenteventtype'), nullable=False),
        sa.Column('voyage_id', sa.String(length=36), nullable=True),
        sa.Column('cargo_request_id', sa.String(length=36), nullable=True),
        sa.Column('origin_port_id', sa.String(length=36), nullable=True),
        sa.Column('destination_port_id', sa.String(length=36), nullable=True),
        sa.Column('event_start', sa.DateTime(), nullable=False),
        sa.Column('event_end', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cargo_request_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['destination_port_id'], ['ports.id'], ),
        sa.ForeignKeyConstraint(['origin_port_id'], ['ports.id'], ),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vessel_employment_events_id'), 'vessel_employment_events', ['id'], unique=False)
    op.create_index(op.f('ix_vessel_employment_events_vessel_id'), 'vessel_employment_events', ['vessel_id'], unique=False)
    op.create_index(op.f('ix_vessel_employment_events_cargo_request_id'), 'vessel_employment_events', ['cargo_request_id'], unique=False)
    op.create_index(op.f('ix_vessel_employment_events_created_at'), 'vessel_employment_events', ['created_at'], unique=False)

    # 2. idle_scenarios
    op.create_table('idle_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vessel_id', sa.String(length=36), nullable=False),
        sa.Column('voyage_id', sa.String(length=36), nullable=True),
        sa.Column('scenario_type', sa.Enum('EARLY_ARRIVAL', 'EMPLOYMENT_GAP', 'PORT_DELAY', 'REPOSITIONING_GAP', 'DEMAND_GAP', 'UNKNOWN', name='idlescenariotype'), nullable=False),
        sa.Column('current_location', sa.String(length=100), nullable=False),
        sa.Column('next_known_employment', sa.String(length=255), nullable=True),
        sa.Column('estimated_available_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_next_employment_at', sa.DateTime(), nullable=True),
        sa.Column('idle_days', sa.Float(), nullable=True),
        sa.Column('idle_cost', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Enum('HIGH', 'MEDIUM', 'LOW', name='decisionconfidence'), nullable=False),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_idle_scenarios_id'), 'idle_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_idle_scenarios_vessel_id'), 'idle_scenarios', ['vessel_id'], unique=False)
    op.create_index(op.f('ix_idle_scenarios_scenario_type'), 'idle_scenarios', ['scenario_type'], unique=False)
    op.create_index(op.f('ix_idle_scenarios_created_at'), 'idle_scenarios', ['created_at'], unique=False)

    # 3. repositioning_options
    op.create_table('repositioning_options',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('idle_scenario_id', sa.String(length=36), nullable=True),
        sa.Column('vessel_id', sa.String(length=36), nullable=False),
        sa.Column('target_port_id', sa.String(length=36), nullable=False),
        sa.Column('target_cargo_request_id', sa.String(length=36), nullable=True),
        sa.Column('distance', sa.Float(), nullable=False),
        sa.Column('distance_method', sa.String(length=50), nullable=True),
        sa.Column('estimated_sailing_days', sa.Float(), nullable=False),
        sa.Column('estimated_bunker_cost', sa.Float(), nullable=True),
        sa.Column('estimated_total_cost', sa.Float(), nullable=True),
        sa.Column('port_compatibility', sa.String(length=50), nullable=True),
        sa.Column('timing_compatibility', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('REPOSITION', 'DO_NOT_REPOSITION', 'UNKNOWN', name='repositioningdecision'), nullable=False),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['idle_scenario_id'], ['idle_scenarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_cargo_request_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_port_id'], ['ports.id'], ),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repositioning_options_id'), 'repositioning_options', ['id'], unique=False)
    op.create_index(op.f('ix_repositioning_options_vessel_id'), 'repositioning_options', ['vessel_id'], unique=False)
    op.create_index(op.f('ix_repositioning_options_idle_scenario_id'), 'repositioning_options', ['idle_scenario_id'], unique=False)
    op.create_index(op.f('ix_repositioning_options_target_port_id'), 'repositioning_options', ['target_port_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_repositioning_options_target_port_id'), table_name='repositioning_options')
    op.drop_index(op.f('ix_repositioning_options_idle_scenario_id'), table_name='repositioning_options')
    op.drop_index(op.f('ix_repositioning_options_vessel_id'), table_name='repositioning_options')
    op.drop_index(op.f('ix_repositioning_options_id'), table_name='repositioning_options')
    op.drop_table('repositioning_options')

    op.drop_index(op.f('ix_idle_scenarios_created_at'), table_name='idle_scenarios')
    op.drop_index(op.f('ix_idle_scenarios_scenario_type'), table_name='idle_scenarios')
    op.drop_index(op.f('ix_idle_scenarios_vessel_id'), table_name='idle_scenarios')
    op.drop_index(op.f('ix_idle_scenarios_id'), table_name='idle_scenarios')
    op.drop_table('idle_scenarios')

    op.drop_index(op.f('ix_vessel_employment_events_created_at'), table_name='vessel_employment_events')
    op.drop_index(op.f('ix_vessel_employment_events_cargo_request_id'), table_name='vessel_employment_events')
    op.drop_index(op.f('ix_vessel_employment_events_vessel_id'), table_name='vessel_employment_events')
    op.drop_index(op.f('ix_vessel_employment_events_id'), table_name='vessel_employment_events')
    op.drop_table('vessel_employment_events')
