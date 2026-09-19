"""create_integration_and_audit_tables

Revision ID: c131ef50ea06
Revises: b121df40ea05
Create Date: 2026-09-19 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c131ef50ea06'
down_revision: Union[str, Sequence[str], None] = 'b121df40ea05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. chartering_decisions
    op.create_table('chartering_decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('cargo_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('readiness_status', sa.String(length=50), nullable=False, server_default='PARTIAL'),
        sa.Column('readiness_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('latest_analysis_run_id', sa.String(length=36), nullable=True),
        sa.Column('canonical_context_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cargo_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chartering_decisions_id'), 'chartering_decisions', ['id'], unique=False)
    op.create_index(op.f('ix_chartering_decisions_cargo_id'), 'chartering_decisions', ['cargo_id'], unique=False)
    op.create_index(op.f('ix_chartering_decisions_status'), 'chartering_decisions', ['status'], unique=False)
    op.create_index(op.f('ix_chartering_decisions_latest_analysis_run_id'), 'chartering_decisions', ['latest_analysis_run_id'], unique=False)
    op.create_index(op.f('ix_chartering_decisions_created_at'), 'chartering_decisions', ['created_at'], unique=False)

    # 2. analysis_runs
    op.create_table('analysis_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('decision_id', sa.String(length=36), nullable=True),
        sa.Column('cargo_id', sa.String(length=36), nullable=True),
        sa.Column('voyage_id', sa.String(length=36), nullable=True),
        sa.Column('vessel_id', sa.String(length=36), nullable=True),
        sa.Column('origin_port_id', sa.String(length=36), nullable=True),
        sa.Column('destination_port_id', sa.String(length=36), nullable=True),
        sa.Column('context_version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='VALIDATING'),
        sa.Column('stage', sa.String(length=50), nullable=False, server_default='INIT'),
        sa.Column('model_versions', sa.Text(), nullable=True),
        sa.Column('dataset_versions', sa.Text(), nullable=True),
        sa.Column('inputs_json', sa.Text(), nullable=True),
        sa.Column('outputs_json', sa.Text(), nullable=True),
        sa.Column('data_quality_json', sa.Text(), nullable=True),
        sa.Column('readiness_json', sa.Text(), nullable=True),
        sa.Column('timeline_json', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['decision_id'], ['chartering_decisions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cargo_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['origin_port_id'], ['ports.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['destination_port_id'], ['ports.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_runs_id'), 'analysis_runs', ['id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_decision_id'), 'analysis_runs', ['decision_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_cargo_id'), 'analysis_runs', ['cargo_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_voyage_id'), 'analysis_runs', ['voyage_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_vessel_id'), 'analysis_runs', ['vessel_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_origin_port_id'), 'analysis_runs', ['origin_port_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_destination_port_id'), 'analysis_runs', ['destination_port_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_status'), 'analysis_runs', ['status'], unique=False)
    op.create_index(op.f('ix_analysis_runs_created_at'), 'analysis_runs', ['created_at'], unique=False)

    # 3. audit_logs
    op.create_table('audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='SAIL-COMMERCIAL-OFFICER'),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('analysis_run_id', sa.String(length=36), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True, server_default='127.0.0.1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_analysis_run_id'), 'audit_logs', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_analysis_run_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_analysis_runs_created_at'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_status'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_destination_port_id'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_origin_port_id'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_vessel_id'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_voyage_id'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_cargo_id'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_decision_id'), table_name='analysis_runs')
    op.drop_index(op.f('ix_analysis_runs_id'), table_name='analysis_runs')
    op.drop_table('analysis_runs')

    op.drop_index(op.f('ix_chartering_decisions_created_at'), table_name='chartering_decisions')
    op.drop_index(op.f('ix_chartering_decisions_latest_analysis_run_id'), table_name='chartering_decisions')
    op.drop_index(op.f('ix_chartering_decisions_status'), table_name='chartering_decisions')
    op.drop_index(op.f('ix_chartering_decisions_cargo_id'), table_name='chartering_decisions')
    op.drop_index(op.f('ix_chartering_decisions_id'), table_name='chartering_decisions')
    op.drop_table('chartering_decisions')
