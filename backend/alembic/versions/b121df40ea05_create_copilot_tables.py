"""create_copilot_tables

Revision ID: b121df40ea05
Revises: a111ce30ea04
Create Date: 2026-09-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b121df40ea05'
down_revision: Union[str, Sequence[str], None] = 'a111ce30ea04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. copilot_sessions
    op.create_table('copilot_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='Chartering Inquiry'),
        sa.Column('cargo_request_id', sa.String(length=36), nullable=True),
        sa.Column('vessel_id', sa.String(length=36), nullable=True),
        sa.Column('voyage_id', sa.String(length=36), nullable=True),
        sa.Column('context_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cargo_request_id'], ['cargo_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_sessions_id'), 'copilot_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_copilot_sessions_cargo_request_id'), 'copilot_sessions', ['cargo_request_id'], unique=False)
    op.create_index(op.f('ix_copilot_sessions_vessel_id'), 'copilot_sessions', ['vessel_id'], unique=False)
    op.create_index(op.f('ix_copilot_sessions_voyage_id'), 'copilot_sessions', ['voyage_id'], unique=False)
    op.create_index(op.f('ix_copilot_sessions_created_at'), 'copilot_sessions', ['created_at'], unique=False)

    # 2. copilot_plans
    op.create_table('copilot_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('user_goal', sa.Text(), nullable=False),
        sa.Column('plan_json', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNED'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['copilot_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_plans_id'), 'copilot_plans', ['id'], unique=False)
    op.create_index(op.f('ix_copilot_plans_session_id'), 'copilot_plans', ['session_id'], unique=False)

    # 3. copilot_messages
    op.create_table('copilot_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('structured_response', sa.Text(), nullable=True),
        sa.Column('plan_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['copilot_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['copilot_plans.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_messages_id'), 'copilot_messages', ['id'], unique=False)
    op.create_index(op.f('ix_copilot_messages_session_id'), 'copilot_messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_copilot_messages_plan_id'), 'copilot_messages', ['plan_id'], unique=False)
    op.create_index(op.f('ix_copilot_messages_created_at'), 'copilot_messages', ['created_at'], unique=False)

    # 4. copilot_tool_calls
    op.create_table('copilot_tool_calls',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('message_id', sa.String(length=36), nullable=True),
        sa.Column('plan_id', sa.String(length=36), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('arguments', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['copilot_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['copilot_messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['copilot_plans.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_tool_calls_id'), 'copilot_tool_calls', ['id'], unique=False)
    op.create_index(op.f('ix_copilot_tool_calls_session_id'), 'copilot_tool_calls', ['session_id'], unique=False)
    op.create_index(op.f('ix_copilot_tool_calls_message_id'), 'copilot_tool_calls', ['message_id'], unique=False)
    op.create_index(op.f('ix_copilot_tool_calls_plan_id'), 'copilot_tool_calls', ['plan_id'], unique=False)
    op.create_index(op.f('ix_copilot_tool_calls_tool_name'), 'copilot_tool_calls', ['tool_name'], unique=False)

    # 5. copilot_tool_results
    op.create_table('copilot_tool_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tool_call_id', sa.String(length=36), nullable=False),
        sa.Column('result_json', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('data_status', sa.String(length=50), nullable=False, server_default='SYNTHETIC'),
        sa.Column('dataset_version_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tool_call_id'], ['copilot_tool_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tool_call_id')
    )
    op.create_index(op.f('ix_copilot_tool_results_id'), 'copilot_tool_results', ['id'], unique=False)
    op.create_index(op.f('ix_copilot_tool_results_tool_call_id'), 'copilot_tool_results', ['tool_call_id'], unique=True)


def downgrade() -> None:
    op.drop_table('copilot_tool_results')
    op.drop_table('copilot_tool_calls')
    op.drop_table('copilot_messages')
    op.drop_table('copilot_plans')
    op.drop_table('copilot_sessions')
