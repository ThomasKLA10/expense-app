"""Add travel fields to Receipt model

Revision ID: 670beb49c0e0
Revises: 
Create Date: 2024-12-17 14:10:30.742888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '670beb49c0e0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('receipt', schema=None) as batch_op:
        batch_op.add_column(sa.Column('purpose', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('travel_from', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('travel_to', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('departure_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('return_date', sa.Date(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('receipt', schema=None) as batch_op:
        batch_op.drop_column('return_date')
        batch_op.drop_column('departure_date')
        batch_op.drop_column('travel_to')
        batch_op.drop_column('travel_from')
        batch_op.drop_column('purpose')

    # ### end Alembic commands ###