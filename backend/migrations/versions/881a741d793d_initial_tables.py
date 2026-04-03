"""initial tables

Revision ID: 881a741d793d
Revises:
Create Date: 2026-04-03 09:14:49.627929
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '881a741d793d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════
    # LAYER 1: Root tables (no foreign key dependencies)
    # ══════════════════════════════════════════════════════════

    op.create_table('organizations',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('max_users', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('billing_address', sa.String(length=500), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # ══════════════════════════════════════════════════════════
    # LAYER 2: Teams (depends on organizations only)
    #   NOTE: manager_id FK to users is DEFERRED to Layer 2b
    # ══════════════════════════════════════════════════════════

    op.create_table('teams',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('manager_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_teams_organization_id'), 'teams', ['organization_id'], unique=False)

    # ══════════════════════════════════════════════════════════
    # LAYER 2a: Users (depends on organizations, teams)
    # ══════════════════════════════════════════════════════════

    op.create_table('users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('job_title', sa.String(length=200), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('team_id', sa.UUID(), nullable=True),
        sa.Column('notification_settings', sa.JSON(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)

    # ══════════════════════════════════════════════════════════
    # LAYER 2b: Deferred FK — teams.manager_id → users.id
    # ══════════════════════════════════════════════════════════

    op.create_foreign_key('fk_teams_manager_id', 'teams', 'users', ['manager_id'], ['id'])

    # ══════════════════════════════════════════════════════════
    # LAYER 3: Tables depending on users + organizations
    # ══════════════════════════════════════════════════════════

    op.create_table('projects',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('budget_hours', sa.Float(), nullable=True),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('client_name', sa.String(length=255), nullable=True),
        sa.Column('client_email', sa.String(length=255), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_projects_organization_id'), 'projects', ['organization_id'], unique=False)

    op.create_table('attendance',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('clock_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clock_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_tracked_seconds', sa.Integer(), nullable=False),
        sa.Column('total_active_seconds', sa.Integer(), nullable=False),
        sa.Column('total_idle_seconds', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('overtime_seconds', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_attendance_user_date'),
    )
    op.create_index(op.f('ix_attendance_date'), 'attendance', ['date'], unique=False)
    op.create_index(op.f('ix_attendance_user_id'), 'attendance', ['user_id'], unique=False)

    # ══════════════════════════════════════════════════════════
    # LAYER 4: Tasks + Invoices (depend on projects)
    # ══════════════════════════════════════════════════════════

    op.create_table('tasks',
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('assignee_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tasks_assignee_id'), 'tasks', ['assignee_id'], unique=False)
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)

    op.create_table('invoices',
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('client_name', sa.String(length=255), nullable=False),
        sa.Column('client_email', sa.String(length=255), nullable=True),
        sa.Column('client_address', sa.Text(), nullable=True),
        sa.Column('total_hours', sa.Float(), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('tax_percent', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
    )
    op.create_index(op.f('ix_invoices_organization_id'), 'invoices', ['organization_id'], unique=False)

    # ══════════════════════════════════════════════════════════
    # LAYER 5: Time entries (depend on users, projects, tasks)
    # ══════════════════════════════════════════════════════════

    op.create_table('time_entries',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('task_id', sa.UUID(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('activity_percent', sa.Float(), nullable=False),
        sa.Column('mouse_events', sa.Integer(), nullable=False),
        sa.Column('keyboard_events', sa.Integer(), nullable=False),
        sa.Column('is_manual', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_time_entries_project_id'), 'time_entries', ['project_id'], unique=False)
    op.create_index(op.f('ix_time_entries_user_id'), 'time_entries', ['user_id'], unique=False)

    # ══════════════════════════════════════════════════════════
    # LAYER 6: Leaf tables (depend on time_entries + users)
    # ══════════════════════════════════════════════════════════

    op.create_table('screenshots',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('time_entry_id', sa.UUID(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('activity_percent', sa.Float(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_blurred', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('active_app', sa.String(length=255), nullable=True),
        sa.Column('active_window_title', sa.String(length=500), nullable=True),
        sa.Column('active_url', sa.String(length=1000), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_screenshots_time_entry_id'), 'screenshots', ['time_entry_id'], unique=False)
    op.create_index(op.f('ix_screenshots_user_id'), 'screenshots', ['user_id'], unique=False)

    op.create_table('activity_logs',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('time_entry_id', sa.UUID(), nullable=False),
        sa.Column('interval_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interval_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mouse_events', sa.Integer(), nullable=False),
        sa.Column('keyboard_events', sa.Integer(), nullable=False),
        sa.Column('mouse_distance_px', sa.Integer(), nullable=False),
        sa.Column('scroll_events', sa.Integer(), nullable=False),
        sa.Column('click_events', sa.Integer(), nullable=False),
        sa.Column('activity_percent', sa.Float(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_activity_logs_time_entry_id'), 'activity_logs', ['time_entry_id'], unique=False)
    op.create_index(op.f('ix_activity_logs_user_id'), 'activity_logs', ['user_id'], unique=False)

    op.create_table('app_usage',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('time_entry_id', sa.UUID(), nullable=False),
        sa.Column('app_name', sa.String(length=255), nullable=False),
        sa.Column('window_title', sa.String(length=500), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_app_usage_time_entry_id'), 'app_usage', ['time_entry_id'], unique=False)
    op.create_index(op.f('ix_app_usage_user_id'), 'app_usage', ['user_id'], unique=False)

    op.create_table('gps_locations',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('time_entry_id', sa.UUID(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('accuracy_meters', sa.Float(), nullable=True),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_gps_locations_user_id'), 'gps_locations', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop in reverse order (leaf tables first)
    op.drop_index(op.f('ix_gps_locations_user_id'), table_name='gps_locations')
    op.drop_table('gps_locations')

    op.drop_index(op.f('ix_app_usage_user_id'), table_name='app_usage')
    op.drop_index(op.f('ix_app_usage_time_entry_id'), table_name='app_usage')
    op.drop_table('app_usage')

    op.drop_index(op.f('ix_activity_logs_user_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_time_entry_id'), table_name='activity_logs')
    op.drop_table('activity_logs')

    op.drop_index(op.f('ix_screenshots_user_id'), table_name='screenshots')
    op.drop_index(op.f('ix_screenshots_time_entry_id'), table_name='screenshots')
    op.drop_table('screenshots')

    op.drop_index(op.f('ix_time_entries_user_id'), table_name='time_entries')
    op.drop_index(op.f('ix_time_entries_project_id'), table_name='time_entries')
    op.drop_table('time_entries')

    op.drop_index(op.f('ix_invoices_organization_id'), table_name='invoices')
    op.drop_table('invoices')

    op.drop_index(op.f('ix_tasks_project_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_assignee_id'), table_name='tasks')
    op.drop_table('tasks')

    op.drop_index(op.f('ix_attendance_user_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_date'), table_name='attendance')
    op.drop_table('attendance')

    op.drop_index(op.f('ix_projects_organization_id'), table_name='projects')
    op.drop_table('projects')

    # Drop deferred FK before dropping users
    op.drop_constraint('fk_teams_manager_id', 'teams', type_='foreignkey')

    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    op.drop_index(op.f('ix_teams_organization_id'), table_name='teams')
    op.drop_table('teams')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
