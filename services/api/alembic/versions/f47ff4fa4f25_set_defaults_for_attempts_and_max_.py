from alembic import op

revision = "f47ff4fa4f25"
down_revision = "62f7cf3b66ac"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("UPDATE jobs SET attempts = 0 WHERE attempts IS NULL")
    op.execute("UPDATE jobs SET max_attempts = 5 WHERE max_attempts IS NULL")

    op.alter_column("jobs", "attempts", server_default="0")
    op.alter_column("jobs", "max_attempts", server_default="5")

def downgrade() -> None:
    op.alter_column("jobs", "attempts", server_default=None)
    op.alter_column("jobs", "max_attempts", server_default=None) 