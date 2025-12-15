"""rename author_name to author_username

Revision ID: 8debb87afd2d
Revises: 001
Create Date: 2025-12-15 16:39:54.597222

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8debb87afd2d'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Переименование колонки author_name -> author_username
    bind = op.get_bind()
    
    if bind.dialect.name == 'sqlite':
        # SQLite требует batch mode для переименования колонки
        with op.batch_alter_table('comments', schema=None) as batch_op:
            batch_op.alter_column('author_name', new_column_name='author_username')
    else:
        # PostgreSQL и другие БД
        op.alter_column('comments', 'author_name', new_column_name='author_username')


def downgrade() -> None:
    # Откат: переименовать обратно author_username -> author_name
    bind = op.get_bind()
    
    if bind.dialect.name == 'sqlite':
        with op.batch_alter_table('comments', schema=None) as batch_op:
            batch_op.alter_column('author_username', new_column_name='author_name')
    else:
        op.alter_column('comments', 'author_username', new_column_name='author_name')

