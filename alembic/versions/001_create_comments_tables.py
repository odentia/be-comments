"""Create comments tables

Revision ID: 001
Revises: 
Create Date: 2024-12-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицы с внешними ключами сразу при создании (работает для PostgreSQL)
    # Для SQLite внешние ключи будут проигнорированы, но структура таблиц будет создана
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=10), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('author_username', sa.String(length=255), nullable=False),
        sa.Column('author_avatar', sa.String(length=512), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_positive', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'comment_reactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reaction', sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_comments_entity_id', 'comments', ['entity_id'])
    op.create_index('ix_comments_entity_type', 'comments', ['entity_type'])
    op.create_index('ix_comments_author_id', 'comments', ['author_id'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])
    op.create_index('ix_comments_created_at', 'comments', ['created_at'])
    op.create_index('ix_comment_reactions_comment_id', 'comment_reactions', ['comment_id'])
    op.create_index('ix_comment_reactions_user_id', 'comment_reactions', ['user_id'])


def downgrade() -> None:
    op.drop_table('comment_reactions')
    op.drop_table('comments')

