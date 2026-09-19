"""create_contract_strategy_tables

Revision ID: e817bc92da01
Revises: d045ad11ea04
Create Date: 2026-09-18 20:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e817bc92da01'
down_revision: Union[str, Sequence[str], None] = 'd045ad11ea04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('contract_strategies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('cargo_request_id', sa.String(length=36), nullable=True),
        sa.Column('strategy_type', sa.Enum('SPOT', 'SHORT_TERM_MULTIPLE_VOYAGE', 'MEDIUM_TERM_MULTIPLE_VOYAGE', name='contractstrategytype'), nullable=False),
        sa.Column('contract_duration', sa.String(length=100), nullable=False),
        sa.Column('voyage_count', sa.Integer(), nullable=False),
        sa.Column('total_quantity', sa.Float(), nullable=False),
        sa.Column('contracted_quantity', sa.Float(), nullable=False),
        sa.Column('spot_quantity', sa.Float(), nullable=False),
        sa.Column('reference_rate', sa.Float(), nullable=True),
        sa.Column('expected_rate', sa.Float(), nullable=False),
        sa.Column('expected_cost', sa.Float(), nullable=False),
        sa.Column('p10_cost', sa.Float(), nullable=False),
        sa.Column('p50_cost', sa.Float(), nullable=False),
        sa.Column('p90_cost', sa.Float(), nullable=False),
        sa.Column('market_exposure', sa.Float(), nullable=False),
        sa.Column('flexibility_measure', sa.Float(), nullable=False),
        sa.Column('risk_adjusted_cost', sa.Float(), nullable=False),
        sa.Column('break_even_rate', sa.Float(), nullable=True),
        sa.Column('decision_confidence', sa.Enum('HIGH', 'MEDIUM', 'LOW', name='decisionconfidence'), nullable=False),
        sa.Column('forecast_id', sa.String(length=36), nullable=True),
        sa.Column('regime_id', sa.String(length=36), nullable=True),
        sa.Column('wait_fix_analysis_id', sa.String(length=36), nullable=True),
        sa.Column('model_version_id', sa.String(length=100), nullable=True),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('data_status', sa.Enum('LIVE', 'RECENT', 'STALE', 'PUBLIC', 'LICENSED', 'DEMO', 'SYNTHETIC', 'UNAVAILABLE', 'UNKNOWN', name='datastatustype'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cargo_request_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['wait_fix_analysis_id'], ['wait_fix_analyses.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contract_strategies_id'), 'contract_strategies', ['id'], unique=False)
    op.create_index(op.f('ix_contract_strategies_cargo_request_id'), 'contract_strategies', ['cargo_request_id'], unique=False)
    op.create_index(op.f('ix_contract_strategies_strategy_type'), 'contract_strategies', ['strategy_type'], unique=False)
    op.create_index(op.f('ix_contract_strategies_created_at'), 'contract_strategies', ['created_at'], unique=False)

    op.create_table('contract_strategy_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('strategy_id', sa.String(length=36), nullable=False),
        sa.Column('scenario_name', sa.String(length=50), nullable=False),
        sa.Column('market_assumption', sa.Text(), nullable=True),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['contract_strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contract_strategy_scenarios_id'), 'contract_strategy_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_contract_strategy_scenarios_strategy_id'), 'contract_strategy_scenarios', ['strategy_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_contract_strategy_scenarios_strategy_id'), table_name='contract_strategy_scenarios')
    op.drop_index(op.f('ix_contract_strategy_scenarios_id'), table_name='contract_strategy_scenarios')
    op.drop_table('contract_strategy_scenarios')
    op.drop_index(op.f('ix_contract_strategies_created_at'), table_name='contract_strategies')
    op.drop_index(op.f('ix_contract_strategies_strategy_type'), table_name='contract_strategies')
    op.drop_index(op.f('ix_contract_strategies_cargo_request_id'), table_name='contract_strategies')
    op.drop_index(op.f('ix_contract_strategies_id'), table_name='contract_strategies')
    op.drop_table('contract_strategies')
