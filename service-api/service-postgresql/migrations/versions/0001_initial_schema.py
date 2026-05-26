"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_user_username", "users", ["username"], unique=True)
    op.create_index("idx_user_email", "users", ["email"], unique=True)

    op.create_table(
        "sentiment_analyses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("all_scores", sa.JSON(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("text_hash", sa.String(length=64), nullable=True),
        sa.Column("processing_time_ms", sa.Float(), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_sentiment_created", "sentiment_analyses", ["sentiment", "created_at"])
    op.create_index("idx_language", "sentiment_analyses", ["language"])
    op.create_index("idx_confidence", "sentiment_analyses", ["confidence"])
    op.create_index(
        "idx_sentiment_lang_date",
        "sentiment_analyses",
        ["sentiment", "language", "created_at"],
    )
    op.create_index("idx_created_at", "sentiment_analyses", ["created_at"])
    op.create_index("idx_text_hash", "sentiment_analyses", ["text_hash"])
    op.create_index("idx_request_id", "sentiment_analyses", ["request_id"])

    op.create_table(
        "sentiment_feedback",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("user_sentiment", sa.String(length=20), nullable=False),
        sa.Column("model_sentiment", sa.String(length=20), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_analysis_id", "sentiment_feedback", ["analysis_id"])
    op.create_index("idx_is_correct", "sentiment_feedback", ["is_correct"])
    op.create_index("idx_feedback_created", "sentiment_feedback", ["created_at"])


def downgrade() -> None:
    op.drop_table("sentiment_feedback")
    op.drop_table("sentiment_analyses")
    op.drop_table("users")
