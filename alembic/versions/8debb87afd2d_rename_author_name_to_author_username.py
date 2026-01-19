"""rename author_name to author_username

Revision ID: 8debb87afd2d
Revises: 001
Create Date: 2025-12-15 16:39:54.597222

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '8debb87afd2d'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Переименование колонки author_name -> author_username (только если author_name существует)
    bind = op.get_bind()
    
    # Проверяем, существует ли колонка author_name
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('comments')]
    
    if 'author_name' in columns and 'author_username' not in columns:
        # Колонка author_name существует, но author_username нет - переименовываем
        if bind.dialect.name == 'sqlite':
            # SQLite требует batch mode для переименования колонки
            with op.batch_alter_table('comments', schema=None) as batch_op:
                batch_op.alter_column('author_name', new_column_name='author_username')
        else:
            # PostgreSQL и другие БД
            op.alter_column('comments', 'author_name', new_column_name='author_username')
    # Если колонка уже называется author_username, ничего не делаем


def downgrade() -> None:
    # Откат: переименовать обратно author_username -> author_name (только если author_username существует)
    bind = op.get_bind()
    
    # Проверяем, существует ли колонка author_username
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('comments')]
    
    if 'author_username' in columns and 'author_name' not in columns:
        # Колонка author_username существует, но author_name нет - переименовываем
        if bind.dialect.name == 'sqlite':
            with op.batch_alter_table('comments', schema=None) as batch_op:
                batch_op.alter_column('author_username', new_column_name='author_name')
        else:
            op.alter_column('comments', 'author_username', new_column_name='author_name')
    # Если колонка уже называется author_name, ничего не делаем

