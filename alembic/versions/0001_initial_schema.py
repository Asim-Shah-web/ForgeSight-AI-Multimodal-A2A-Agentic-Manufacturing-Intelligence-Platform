"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-02-10 00:00:00.000000

Creates the pgvector extension and all Phase 2 conceptual tables, in
dependency order (referenced tables before referencing tables).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Extension (must exist before any Vector columns are created) -----
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- Enum types ---------------------------------------------------------
    user_role_enum = sa.Enum(
        "production_operator",
        "quality_engineer",
        "manufacturing_engineer",
        "maintenance_engineer",
        "quality_manager",
        "supplier_quality_engineer",
        "system_administrator",
        name="userrole",
    )
    audit_event_type_enum = sa.Enum(
        "user_authentication",
        "incident_created",
        "incident_modified",
        "incident_status_changed",
        "evidence_submitted",
        "cv_execution",
        "mcp_tool_invocation",
        "rag_retrieval",
        "ai_recommendation_generated",
        "human_modification_of_ai_recommendation",
        "human_approval",
        "human_rejection",
        "high_risk_action_execution",
        "report_generation",
        "system_configuration_change",
        "user_created",
        "user_role_changed",
        name="auditeventtype",
    )
    work_order_status_enum = sa.Enum(
        "open", "in_progress", "completed", "cancelled", name="workorderstatus"
    )
    incident_status_enum = sa.Enum(
        "open", "in_progress", "awaiting_approval", "closed", "escalated",
        name="incidentstatus",
    )

    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    audit_event_type_enum.create(bind, checkfirst=True)
    work_order_status_enum.create(bind, checkfirst=True)
    incident_status_enum.create(bind, checkfirst=True)

    # --- users ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    # --- products --------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("product_id"),
    )

    # --- lines -------------------------------------------------------------
    op.create_table(
        "lines",
        sa.Column("line_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("facility", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("line_id"),
    )

    # --- machines ------------------------------------------------------------
    op.create_table(
        "machines",
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("line_id", sa.String(), nullable=False),
        sa.Column("machine_type", sa.String(), nullable=False),
        sa.Column("manufacturer", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["lines.line_id"]),
        sa.PrimaryKeyConstraint("machine_id"),
    )
    op.create_index("ix_machines_line_id", "machines", ["line_id"])

    # --- nozzles -------------------------------------------------------------
    op.create_table(
        "nozzles",
        sa.Column("nozzle_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("size_class", sa.String(), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.machine_id"]),
        sa.PrimaryKeyConstraint("nozzle_id"),
    )
    op.create_index("ix_nozzles_machine_id", "nozzles", ["machine_id"])

    # --- feeders -------------------------------------------------------------
    op.create_table(
        "feeders",
        sa.Column("feeder_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("slot_number", sa.Integer(), nullable=False),
        sa.Column("part_number", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.machine_id"]),
        sa.PrimaryKeyConstraint("feeder_id"),
    )
    op.create_index("ix_feeders_machine_id", "feeders", ["machine_id"])

    # --- batches -------------------------------------------------------------
    op.create_table(
        "batches",
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("line_id", sa.String(), nullable=False),
        sa.Column("board_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"]),
        sa.ForeignKeyConstraint(["line_id"], ["lines.line_id"]),
        sa.PrimaryKeyConstraint("batch_id"),
    )
    op.create_index("ix_batches_product_id", "batches", ["product_id"])
    op.create_index("ix_batches_line_id", "batches", ["line_id"])

    # --- boards ----------------------------------------------------------
    op.create_table(
        "boards",
        sa.Column("board_id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("serial_number", sa.String(), nullable=False),
        sa.Column("position_in_batch", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.batch_id"]),
        sa.PrimaryKeyConstraint("board_id"),
    )
    op.create_index("ix_boards_batch_id", "boards", ["batch_id"])
    op.create_index("ix_boards_serial_number", "boards", ["serial_number"], unique=True)

    # --- suppliers -----------------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("supplier_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("supplier_id"),
    )

    # --- components ------------------------------------------------------
    op.create_table(
        "components",
        sa.Column("part_number", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("part_number"),
    )

    # --- component_lots --------------------------------------------------
    op.create_table(
        "component_lots",
        sa.Column("lot_number", sa.String(), nullable=False),
        sa.Column("part_number", sa.String(), nullable=False),
        sa.Column("supplier_id", sa.String(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("defect_count", sa.Integer(), nullable=True),
        sa.Column("rejection_threshold", sa.Integer(), nullable=True),
        sa.Column("disposition", sa.String(), nullable=False),
        sa.Column("historical_defect_rate_pct", sa.Float(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["part_number"], ["components.part_number"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.PrimaryKeyConstraint("lot_number"),
    )
    op.create_index("ix_component_lots_part_number", "component_lots", ["part_number"])
    op.create_index("ix_component_lots_supplier_id", "component_lots", ["supplier_id"])

    # --- maintenance_records -----------------------------------------------
    op.create_table(
        "maintenance_records",
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("nozzle_id", sa.String(), nullable=True),
        sa.Column("last_cleaned", sa.DateTime(timezone=True), nullable=True),
        sa.Column("wear_measurement_mm", sa.Float(), nullable=True),
        sa.Column("vacuum_test_result", sa.String(), nullable=True),
        sa.Column("disposition", sa.String(), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.machine_id"]),
        sa.ForeignKeyConstraint(["nozzle_id"], ["nozzles.nozzle_id"]),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index("ix_maintenance_records_machine_id", "maintenance_records", ["machine_id"])
    op.create_index("ix_maintenance_records_nozzle_id", "maintenance_records", ["nozzle_id"])

    # --- work_orders -----------------------------------------------------
    op.create_table(
        "work_orders",
        sa.Column("work_order_id", sa.Uuid(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("nozzle_id", sa.String(), nullable=True),
        sa.Column("source_record_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", work_order_status_enum, nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.machine_id"]),
        sa.ForeignKeyConstraint(["nozzle_id"], ["nozzles.nozzle_id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["maintenance_records.record_id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("work_order_id"),
    )
    op.create_index("ix_work_orders_machine_id", "work_orders", ["machine_id"])

    # --- inspection_images -------------------------------------------------
    op.create_table(
        "inspection_images",
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.String(), nullable=False),
        sa.Column("image_reference", sa.String(), nullable=False),
        sa.Column("station_id", sa.String(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["board_id"], ["boards.board_id"]),
        sa.PrimaryKeyConstraint("image_id"),
    )
    op.create_index("ix_inspection_images_board_id", "inspection_images", ["board_id"])

    # --- cv_findings -------------------------------------------------------
    op.create_table(
        "cv_findings",
        sa.Column("cv_finding_id", sa.Uuid(), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.String(), nullable=False),
        sa.Column("defect_type", sa.String(), nullable=False),
        sa.Column("component_designator", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bounding_box", sa.JSON(), nullable=False),
        sa.Column("raw_image_reference", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("inference_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dataset_used_for_training", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["inspection_images.image_id"]),
        sa.ForeignKeyConstraint(["board_id"], ["boards.board_id"]),
        sa.PrimaryKeyConstraint("cv_finding_id"),
    )
    op.create_index("ix_cv_findings_image_id", "cv_findings", ["image_id"])
    op.create_index("ix_cv_findings_board_id", "cv_findings", ["board_id"])

    # --- production_telemetry -----------------------------------------------
    op.create_table(
        "production_telemetry",
        sa.Column("telemetry_id", sa.Uuid(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("parameter", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.machine_id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.batch_id"]),
        sa.PrimaryKeyConstraint("telemetry_id"),
    )
    op.create_index("ix_production_telemetry_machine_id", "production_telemetry", ["machine_id"])
    op.create_index("ix_production_telemetry_batch_id", "production_telemetry", ["batch_id"])
    op.create_index("ix_production_telemetry_recorded_at", "production_telemetry", ["recorded_at"])

    # --- reflow_profiles -----------------------------------------------------
    op.create_table(
        "reflow_profiles",
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=True),
        sa.Column("zone", sa.String(), nullable=False),
        sa.Column("measured_temp_c", sa.Float(), nullable=False),
        sa.Column("target_temp_c", sa.Float(), nullable=False),
        sa.Column("acceptable_range_low_c", sa.Float(), nullable=False),
        sa.Column("acceptable_range_high_c", sa.Float(), nullable=False),
        sa.Column("disposition", sa.String(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.machine_id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.batch_id"]),
        sa.PrimaryKeyConstraint("profile_id"),
    )
    op.create_index("ix_reflow_profiles_machine_id", "reflow_profiles", ["machine_id"])

    # --- technical_documents -------------------------------------------------
    op.create_table(
        "technical_documents",
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("document_id"),
    )

    # --- document_chunks (pgvector) ------------------------------------------
    op.create_table(
        "document_chunks",
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("document_title", sa.String(), nullable=False),
        sa.Column("document_version", sa.String(), nullable=False),
        sa.Column("section_title", sa.String(), nullable=True),
        sa.Column("section_reference", sa.String(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.String(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("embedding_model", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["technical_documents.document_id"]),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    # HNSW index with cosine distance, per Phase 4 Section 4.4 selection.
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )

    # --- incidents -------------------------------------------------------
    op.create_table(
        "incidents",
        sa.Column("incident_id", sa.String(), nullable=False),
        sa.Column("board_id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("line_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("defect_type", sa.String(), nullable=False),
        sa.Column("component_designator", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", incident_status_enum, nullable=False),
        sa.Column("current_stage", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signed_off_by", sa.Uuid(), nullable=True),
        sa.Column("signed_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["board_id"], ["boards.board_id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.batch_id"]),
        sa.ForeignKeyConstraint(["line_id"], ["lines.line_id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["signed_off_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("incident_id"),
    )
    op.create_index("ix_incidents_board_id", "incidents", ["board_id"])
    op.create_index("ix_incidents_batch_id", "incidents", ["batch_id"])
    op.create_index("ix_incidents_line_id", "incidents", ["line_id"])
    op.create_index("ix_incidents_product_id", "incidents", ["product_id"])
    op.create_index("ix_incidents_status", "incidents", ["status"])

    # --- incident_embeddings (pgvector) --------------------------------------
    op.create_table(
        "incident_embeddings",
        sa.Column("embedding_id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.String(), nullable=False),
        sa.Column("summary_text", sa.String(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("embedding_model", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.incident_id"]),
        sa.PrimaryKeyConstraint("embedding_id"),
        sa.UniqueConstraint("incident_id"),
    )
    op.execute(
        "CREATE INDEX ix_incident_embeddings_embedding_hnsw "
        "ON incident_embeddings USING hnsw (embedding vector_cosine_ops)"
    )

    # --- root_cause_hypotheses -----------------------------------------------
    op.create_table(
        "root_cause_hypotheses",
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.String(), nullable=False),
        sa.Column("conclusion", sa.String(), nullable=False),
        sa.Column("supporting_evidence_refs", sa.JSON(), nullable=False),
        sa.Column("contradicting_evidence_refs", sa.JSON(), nullable=False),
        sa.Column("confidence_level", sa.Float(), nullable=False),
        sa.Column("reasoning_summary", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("confirmed_by", sa.Uuid(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.incident_id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("hypothesis_id"),
    )
    op.create_index("ix_root_cause_hypotheses_incident_id", "root_cause_hypotheses", ["incident_id"])

    # --- corrective_actions --------------------------------------------------
    op.create_table(
        "corrective_actions",
        sa.Column("action_id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.String(), nullable=False),
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_action", sa.String(), nullable=False),
        sa.Column("supporting_evidence_refs", sa.JSON(), nullable=False),
        sa.Column("requires_approval_by", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.incident_id"]),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["root_cause_hypotheses.hypothesis_id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("action_id"),
    )
    op.create_index("ix_corrective_actions_incident_id", "corrective_actions", ["incident_id"])

    # --- reports ---------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.String(), nullable=False),
        sa.Column("narrative", sa.String(), nullable=False),
        sa.Column("sections_included", sa.JSON(), nullable=False),
        sa.Column("evidence_appendix", sa.JSON(), nullable=False),
        sa.Column("generated_by", sa.String(), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.incident_id"]),
        sa.PrimaryKeyConstraint("report_id"),
        sa.UniqueConstraint("incident_id"),
    )

    # --- audit_events (append-only) ------------------------------------------
    op.create_table(
        "audit_events",
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("who", sa.Uuid(), nullable=False),
        sa.Column("what", audit_event_type_enum, nullable=False),
        sa.Column("when", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("prior_state", sa.JSON(), nullable=True),
        sa.Column("new_state", sa.JSON(), nullable=True),
        sa.Column("approval_by", sa.Uuid(), nullable=True),
        sa.Column("ai_version", sa.String(), nullable=True),
        sa.Column("evidence_version", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["who"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["approval_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index("ix_audit_events_who", "audit_events", ["who"])
    op.create_index("ix_audit_events_what", "audit_events", ["what"])
    op.create_index("ix_audit_events_when", "audit_events", ["when"])
    op.create_index("ix_audit_events_target_id", "audit_events", ["target_id"])
    op.create_index("ix_audit_events_target_type", "audit_events", ["target_type"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("reports")
    op.drop_table("corrective_actions")
    op.drop_table("root_cause_hypotheses")
    op.execute("DROP INDEX IF EXISTS ix_incident_embeddings_embedding_hnsw")
    op.drop_table("incident_embeddings")
    op.drop_table("incidents")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_table("document_chunks")
    op.drop_table("technical_documents")
    op.drop_table("reflow_profiles")
    op.drop_table("production_telemetry")
    op.drop_table("cv_findings")
    op.drop_table("inspection_images")
    op.drop_table("work_orders")
    op.drop_table("maintenance_records")
    op.drop_table("component_lots")
    op.drop_table("components")
    op.drop_table("suppliers")
    op.drop_table("boards")
    op.drop_table("batches")
    op.drop_table("feeders")
    op.drop_table("nozzles")
    op.drop_table("machines")
    op.drop_table("lines")
    op.drop_table("products")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="incidentstatus").drop(bind, checkfirst=True)
    sa.Enum(name="workorderstatus").drop(bind, checkfirst=True)
    sa.Enum(name="auditeventtype").drop(bind, checkfirst=True)
    sa.Enum(name="userrole").drop(bind, checkfirst=True)