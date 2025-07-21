"""Add startup_command column to mcp_tools

Revision ID: startup_command_001
Revises: 52f6f740362d
Create Date: 2025-07-19 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'startup_command_001'
down_revision = '52f6f740362d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add startup_command column to mcp_tools table
    op.add_column('mcp_tools', sa.Column('startup_command', sa.Text(), nullable=True, comment='启动命令（用于进程监控）'))

    # Add max_memory_mb and max_cpu_percent columns if they don't exist
    op.add_column('mcp_tools', sa.Column('max_memory_mb', sa.Integer(), nullable=True, comment='最大内存使用（MB）'))
    op.add_column('mcp_tools', sa.Column('max_cpu_percent', sa.Integer(), nullable=True, comment='最大CPU使用率（%）'))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('mcp_tools', 'max_cpu_percent')
    op.drop_column('mcp_tools', 'max_memory_mb')
    op.drop_column('mcp_tools', 'startup_command')
