"""Initial migration for setting up credit tables and soft-delete + OTP fields

Revision ID: 2700fcaedab5
Revises:
Create Date: 2025-01-14 11:54:57.804119
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# Revision identifiers
revision = '2700fcaedab5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Get bind and inspector to check existing columns/tables/indexes
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    # Create 'business_credit' table if not exists
    if 'business_credit' not in inspector.get_table_names():
        op.create_table(
            'business_credit',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('credit_count', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.ForeignKeyConstraint(['company_id'], ['company.id']),
            sa.PrimaryKeyConstraint('id')
        )

    # Create 'personal_credit' table if not exists
    if 'personal_credit' not in inspector.get_table_names():
        op.create_table(
            'personal_credit',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('credit_count', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id')
        )

    # Add columns to 'company' table safely
    company_columns = [col['name'] for col in inspector.get_columns('company')]
    with op.batch_alter_table('company', schema=None) as batch_op:
        if 'is_deleted' not in company_columns:
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
        if 'deleted_at' not in company_columns:
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        indexes = [idx['name'] for idx in inspector.get_indexes('company')]
        if 'ix_company_id' not in indexes:
            batch_op.create_index('ix_company_id', ['id'], unique=False)

    # Add columns to 'user' table safely
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    with op.batch_alter_table('user', schema=None) as batch_op:
        if 'special_admin' not in user_columns:
            batch_op.add_column(sa.Column('special_admin', sa.Boolean(), nullable=True))
        if 'is_deleted' not in user_columns:
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
        if 'deleted_at' not in user_columns:
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if 'otp_code' not in user_columns:
            batch_op.add_column(sa.Column('otp_code', sa.String(length=6), nullable=True))
        if 'otp_created_at' not in user_columns:
            batch_op.add_column(sa.Column('otp_created_at', sa.DateTime(), nullable=True))
        if 'otp_attempts' not in user_columns:
            batch_op.add_column(sa.Column('otp_attempts', sa.Integer(), nullable=True))


def downgrade():
    # Drop user table columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        for col in ['otp_attempts', 'otp_created_at', 'otp_code', 'deleted_at', 'is_deleted', 'special_admin']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass  # Safe downgrade; column might not exist

    # Drop company table columns and index
    with op.batch_alter_table('company', schema=None) as batch_op:
        try:
            batch_op.drop_index('ix_company_id')
        except Exception:
            pass
        for col in ['deleted_at', 'is_deleted']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

    # Drop tables if they exist
    for table in ['personal_credit', 'business_credit']:
        if table in Inspector.from_engine(op.get_bind()).get_table_names():
            op.drop_table(table)
