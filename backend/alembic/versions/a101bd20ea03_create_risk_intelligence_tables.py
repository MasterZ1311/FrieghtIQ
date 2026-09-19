"""create_risk_intelligence_tables

Revision ID: a101bd20ea03
Revises: f928bd10ea02
Create Date: 2026-09-19 10:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a101bd20ea03'
down_revision: Union[str, Sequence[str], None] = 'f928bd10ea02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. weather_observations
    op.create_table('weather_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('location_type', sa.String(length=50), nullable=False),
        sa.Column('location_id', sa.String(length=36), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.Column('forecast_for', sa.DateTime(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=False),
        sa.Column('wind_direction', sa.Float(), nullable=True),
        sa.Column('wave_height', sa.Float(), nullable=False),
        sa.Column('rainfall', sa.Float(), nullable=True),
        sa.Column('visibility', sa.Float(), nullable=True),
        sa.Column('storm_indicator', sa.String(length=100), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['ports.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_observations_id'), 'weather_observations', ['id'], unique=False)
    op.create_index(op.f('ix_weather_observations_location_id'), 'weather_observations', ['location_id'], unique=False)
    op.create_index(op.f('ix_weather_observations_observed_at'), 'weather_observations', ['observed_at'], unique=False)
    op.create_index(op.f('ix_weather_observations_forecast_for'), 'weather_observations', ['forecast_for'], unique=False)
    op.create_index(op.f('ix_weather_observations_created_at'), 'weather_observations', ['created_at'], unique=False)

    # 2. tidal_windows
    op.create_table('tidal_windows',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('port_id', sa.String(length=36), nullable=False),
        sa.Column('berth_id', sa.String(length=36), nullable=True),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.Column('window_end', sa.DateTime(), nullable=False),
        sa.Column('predicted_tide', sa.Float(), nullable=False),
        sa.Column('required_depth', sa.Float(), nullable=True),
        sa.Column('available_depth', sa.Float(), nullable=False),
        sa.Column('vessel_draft', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('PASS', 'CONDITIONAL', 'FAIL', 'UNKNOWN', name='tidalwindowstatus'), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tidal_windows_id'), 'tidal_windows', ['id'], unique=False)
    op.create_index(op.f('ix_tidal_windows_port_id'), 'tidal_windows', ['port_id'], unique=False)
    op.create_index(op.f('ix_tidal_windows_berth_id'), 'tidal_windows', ['berth_id'], unique=False)
    op.create_index(op.f('ix_tidal_windows_window_start'), 'tidal_windows', ['window_start'], unique=False)
    op.create_index(op.f('ix_tidal_windows_window_end'), 'tidal_windows', ['window_end'], unique=False)
    op.create_index(op.f('ix_tidal_windows_created_at'), 'tidal_windows', ['created_at'], unique=False)

    # 3. port_congestion
    op.create_table('port_congestion',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('port_id', sa.String(length=36), nullable=False),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.Column('vessels_in_port', sa.Integer(), nullable=False),
        sa.Column('vessels_waiting', sa.Integer(), nullable=False),
        sa.Column('berths_occupied', sa.Integer(), nullable=False),
        sa.Column('estimated_wait_hours', sa.Float(), nullable=False),
        sa.Column('congestion_indicator', sa.Enum('LOW', 'MODERATE', 'SEVERE', 'CRITICAL', 'UNKNOWN', name='congestionindicator'), nullable=False),
        sa.Column('methodology', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_port_congestion_id'), 'port_congestion', ['id'], unique=False)
    op.create_index(op.f('ix_port_congestion_port_id'), 'port_congestion', ['port_id'], unique=False)
    op.create_index(op.f('ix_port_congestion_observed_at'), 'port_congestion', ['observed_at'], unique=False)
    op.create_index(op.f('ix_port_congestion_created_at'), 'port_congestion', ['created_at'], unique=False)

    # 4. risk_events
    op.create_table('risk_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('voyage_id', sa.String(length=36), nullable=True),
        sa.Column('risk_type', sa.Enum('PORT_CONGESTION', 'WEATHER', 'TIDAL', 'VESSEL', 'PORT_OPERATION', 'TIMING', 'IDLE', 'REPOSITIONING', 'DATA_QUALITY', name='risktype'), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN', name='riskseverity'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'MONITORED', 'MITIGATED', 'RESOLVED', 'EXPIRED', 'SIMULATED', name='riskstatus'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=False),
        sa.Column('potential_impact', sa.Text(), nullable=False),
        sa.Column('affected_start', sa.DateTime(), nullable=True),
        sa.Column('affected_end', sa.DateTime(), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('confidence', sa.Enum('HIGH', 'MEDIUM', 'LOW', name='decisionconfidence'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_events_id'), 'risk_events', ['id'], unique=False)
    op.create_index(op.f('ix_risk_events_entity_id'), 'risk_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_risk_events_voyage_id'), 'risk_events', ['voyage_id'], unique=False)
    op.create_index(op.f('ix_risk_events_risk_type'), 'risk_events', ['risk_type'], unique=False)
    op.create_index(op.f('ix_risk_events_severity'), 'risk_events', ['severity'], unique=False)
    op.create_index(op.f('ix_risk_events_created_at'), 'risk_events', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('risk_events')
    op.drop_table('port_congestion')
    op.drop_table('tidal_windows')
    op.drop_table('weather_observations')
