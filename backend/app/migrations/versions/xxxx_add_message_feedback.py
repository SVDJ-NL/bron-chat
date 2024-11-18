"""add message feedback

Revision ID: xxxx
Revises: previous_revision
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'message_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('feedback_type', sa.Enum('like', 'dislike', name='feedbacktype'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_feedback_id'), 'message_feedback', ['id'], unique=False)
    op.create_index(op.f('ix_message_feedback_message_id'), 'message_feedback', ['message_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_message_feedback_message_id'), table_name='message_feedback')
    op.drop_index(op.f('ix_message_feedback_id'), table_name='message_feedback')
    op.drop_table('message_feedback') 