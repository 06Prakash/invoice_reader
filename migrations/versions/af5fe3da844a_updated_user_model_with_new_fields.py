"""Updated User model with new fields

Revision ID: af5fe3da844a
Revises: 22d6c5982713
Create Date: 2025-01-07 18:49:59.486606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af5fe3da844a'
down_revision = '22d6c5982713'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('otp_code', sa.String(length=6), nullable=True))
        batch_op.add_column(sa.Column('otp_created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('otp_attempts', sa.Integer(), nullable=False, server_default="0")
        )

    # Remove the default for otp_attempts to ensure explicit values for future rows
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('otp_attempts', server_default=None)


def downgrade():
    # Drop the newly added columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('otp_attempts')
        batch_op.drop_column('otp_created_at')
        batch_op.drop_column('otp_code')
