"""empty message

Revision ID: 7549e0752e97
Revises: 
Create Date: 2024-10-29 17:17:12.343032

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7549e0752e97'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tour',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creation_time', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('image_path', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('price_per_person', sa.Float(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('available_spots', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creation_time', sa.DateTime(), nullable=True),
    sa.Column('username', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('booking',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('tour_id', sa.Integer(), nullable=False),
    sa.Column('booking_date', sa.DateTime(), nullable=True),
    sa.Column('num_people', sa.Integer(), nullable=False),
    sa.Column('total_price', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['tour_id'], ['tour.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('booking')
    op.drop_table('user')
    op.drop_table('tour')
    # ### end Alembic commands ###
