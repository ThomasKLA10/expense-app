"""rename file_path to file_path_db

Revision ID: 4b6b252aa9d1
Revises: 670beb49c0e0
Create Date: 2023-12-18 17:35:24.696601

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4b6b252aa9d1'
down_revision = '670beb49c0e0'
branch_labels = None
depends_on = None

def upgrade():
    # Rename column, preserving the data
    op.alter_column('receipt', 'file_path',
                    new_column_name='file_path_db',
                    existing_type=sa.String(200),
                    nullable=False)

def downgrade():
    op.alter_column('receipt', 'file_path_db',
                    new_column_name='file_path',
                    existing_type=sa.String(200),
                    nullable=False)