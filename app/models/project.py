# ============================================================
# AETHER LINK - PROJECT MODEL (Software House)
# ============================================================
# Purpose: Manage client projects, tasks, and team assignments
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriority(str, enum.Enum):
    """Project priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ProjectVisibility(str, enum.Enum):
    """Project visibility enumeration."""
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM_ONLY = "team_only"
    CLIENT_ONLY = "client_only"


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskType(str, enum.Enum):
    """Task type enumeration."""
    FEATURE = "feature"
    BUG = "bug"
    TASK = "task"
    DESIGN = "design"
    RESEARCH = "research"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    MEETING = "meeting"
    OTHER = "other"


# ============================================================
# 1. CLIENT PROJECT MODEL
# ============================================================

class ClientProject(Base):
    __tablename__ = "client_projects"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(200), nullable=True)
    
    # ============================================================
    # PROJECT TYPE
    # ============================================================
    project_type = Column(String(50), nullable=True)  # web_dev, mobile_app, design, consulting, etc.
    
    # ============================================================
    # STATUS & PRIORITY
    # ============================================================
    status = Column(
        String(20),
        default=ProjectStatus.PLANNING.value,
        nullable=False,
        index=True
    )
    
    priority = Column(
        String(20),
        default=ProjectPriority.MEDIUM.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # VISIBILITY
    # ============================================================
    visibility = Column(
        String(20),
        default=ProjectVisibility.TEAM_ONLY.value,
        nullable=False
    )
    
    # ============================================================
    # DATES
    # ============================================================
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Estimated duration
    estimated_duration_days = Column(Integer, nullable=True)
    actual_duration_days = Column(Integer, nullable=True)
    
    # ============================================================
    # BUDGET
    # ============================================================
    budget = Column(DECIMAL(12, 2), nullable=True)
    actual_cost = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), default="PKR", nullable=False)
    
    # NEW: Hourly rate
    hourly_rate = Column(DECIMAL(10, 2), nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    
    # ============================================================
    # TEAM
    # ============================================================
    project_manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # CLIENT CONTACT
    # ============================================================
    client_contact_id = Column(Integer, ForeignKey("client_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # STATISTICS (Cached)
    # ============================================================
    total_tasks = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)
    in_progress_tasks = Column(Integer, default=0, nullable=False)
    blocked_tasks = Column(Integer, default=0, nullable=False)
    
    # NEW: Progress percentage
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # NEW: REPOSITORY & INTEGRATION
    # ============================================================
    repository_url = Column(String(500), nullable=True)
    repository_type = Column(String(50), nullable=True)  # github, gitlab, bitbucket
    
    # NEW: Deployment URL
    staging_url = Column(String(500), nullable=True)
    production_url = Column(String(500), nullable=True)
    
    # ============================================================
    # NEW: TAGS
    # ============================================================
    tags = Column(JSON, nullable=True)  # ["react", "python", "aws"]
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_client_projects_client', 'client_id'),
        Index('ix_client_projects_status', 'status'),
        Index('ix_client_projects_priority', 'priority'),
        Index('ix_client_projects_manager', 'project_manager_id'),
        Index('ix_client_projects_start_date', 'start_date'),
        Index('ix_client_projects_end_date', 'end_date'),
        Index('ix_client_projects_slug', 'slug'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    client = relationship(
        "Client",
        back_populates="projects",
        foreign_keys=[client_id]
    )
    
    project_manager = relationship(
        "User",
        foreign_keys=[project_manager_id],
        uselist=False
    )
    
    client_contact = relationship(
        "ClientContact",
        foreign_keys=[client_contact_id],
        uselist=False
    )
    
    tasks = relationship(
        "ProjectTask",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # NEW: Team assignments
    assignments = relationship(
        "ProjectAssignment",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # NEW: Invoices
    invoices = relationship(
        "Invoice",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ClientProject {self.id}: {self.name}>"
    
    def __str__(self) -> str:
        return self.name
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active_project(self) -> bool:
        """Check if project is active."""
        return self.status == ProjectStatus.ACTIVE.value
    
    @property
    def is_completed_project(self) -> bool:
        """Check if project is completed."""
        return self.status == ProjectStatus.COMPLETED.value
    
    @property
    def is_on_hold(self) -> bool:
        """Check if project is on hold."""
        return self.status == ProjectStatus.ON_HOLD.value
    
    @property
    def is_cancelled_project(self) -> bool:
        """Check if project is cancelled."""
        return self.status == ProjectStatus.CANCELLED.value
    
    @property
    def is_archived_project(self) -> bool:
        """Check if project is archived."""
        return self.status == ProjectStatus.ARCHIVED.value
    
    @property
    def is_high_priority(self) -> bool:
        """Check if project has high priority."""
        return self.priority in [ProjectPriority.HIGH.value, ProjectPriority.URGENT.value, ProjectPriority.CRITICAL.value]
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "planning": "📋 Planning",
            "active": "🚀 Active",
            "on_hold": "⏸️ On Hold",
            "review": "🔍 Review",
            "completed": "✅ Completed",
            "cancelled": "❌ Cancelled",
            "archived": "📦 Archived",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def display_priority(self) -> str:
        """Get human-readable priority."""
        priority_map = {
            "low": "🟢 Low",
            "medium": "🔵 Medium",
            "high": "🟠 High",
            "urgent": "🔴 Urgent",
            "critical": "⛔ Critical",
        }
        return priority_map.get(self.priority, "Medium")
    
    @property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        if self.end_date is None or self.is_completed_project or self.is_cancelled_project:
            return False
        return self.end_date < func.now()
    
    @property
    def days_until_deadline(self) -> int:
        """Get days until project deadline."""
        if self.end_date is None:
            return -1
        delta = self.end_date - func.now()
        return max(0, delta.days)
    
    @property
    def is_over_budget(self) -> bool:
        """Check if project is over budget."""
        if self.budget is None or self.actual_cost is None:
            return False
        return self.actual_cost > self.budget
    
    @property
    def budget_usage_percentage(self) -> float:
        """Calculate budget usage percentage."""
        if self.budget is None or self.budget == 0:
            return 0.0
        return (self.actual_cost or 0) / self.budget * 100
    
    @property
    def team_members(self) -> list:
        """Get list of team members assigned to this project."""
        if not self.assignments:
            return []
        return [a.user for a in self.assignments if a.user]
    
    @property
    def team_size(self) -> int:
        """Get team size."""
        return len(self.team_members)
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def start_project(self) -> None:
        """Start the project."""
        self.status = ProjectStatus.ACTIVE.value
        self.start_date = func.now() if not self.start_date else self.start_date
    
    def complete_project(self) -> None:
        """Complete the project."""
        self.status = ProjectStatus.COMPLETED.value
        self.actual_end_date = func.now()
        self.progress_percentage = 100
    
    def put_on_hold(self) -> None:
        """Put project on hold."""
        self.status = ProjectStatus.ON_HOLD.value
    
    def resume_project(self) -> None:
        """Resume a project from hold."""
        self.status = ProjectStatus.ACTIVE.value
    
    def cancel_project(self) -> None:
        """Cancel the project."""
        self.status = ProjectStatus.CANCELLED.value
        self.actual_end_date = func.now()
    
    def archive_project(self) -> None:
        """Archive the project."""
        self.status = ProjectStatus.ARCHIVED.value
    
    def update_progress(self) -> None:
        """Update project progress based on tasks."""
        if self.total_tasks == 0:
            self.progress_percentage = 0
            return
        self.progress_percentage = int((self.completed_tasks / self.total_tasks) * 100)
        
        # Auto-complete if all tasks done
        if self.progress_percentage >= 100 and self.status != ProjectStatus.COMPLETED.value:
            self.complete_project()
    
    def add_task(self, task: 'ProjectTask') -> None:
        """Add a task to the project."""
        if self.tasks is None:
            self.tasks = []
        self.tasks.append(task)
        self.total_tasks += 1
    
    def update_task_stats(self) -> None:
        """Update task statistics."""
        if not self.tasks:
            self.total_tasks = 0
            self.completed_tasks = 0
            self.in_progress_tasks = 0
            self.blocked_tasks = 0
            return
        
        self.total_tasks = len(self.tasks)
        self.completed_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.DONE.value)
        self.in_progress_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS.value)
        self.blocked_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED.value)
        
        self.update_progress()
    
    def set_budget(self, budget: float) -> None:
        """Set project budget."""
        self.budget = budget
    
    def add_cost(self, cost: float) -> None:
        """Add to actual cost."""
        if self.actual_cost is None:
            self.actual_cost = 0
        self.actual_cost += cost
    
    def add_hours(self, hours: int) -> None:
        """Add to actual hours."""
        if self.actual_hours is None:
            self.actual_hours = 0
        self.actual_hours += hours
    
    def assign_team_member(self, user_id: int, role: str = "member") -> None:
        """Assign a team member to the project."""
        # Check if already assigned
        existing = [a for a in self.assignments if a.user_id == user_id]
        if existing:
            return
        
        assignment = ProjectAssignment(
            user_id=user_id,
            role=role
        )
        self.assignments.append(assignment)
    
    def remove_team_member(self, user_id: int) -> None:
        """Remove a team member from the project."""
        self.assignments = [a for a in self.assignments if a.user_id != user_id]
    
    def soft_delete_project(self) -> None:
        """Soft delete the project."""
        self.deleted_at = func.now()
    
    def restore_project(self) -> None:
        """Restore a soft-deleted project."""
        self.deleted_at = None
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert project to dictionary."""
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client.company_name if self.client else None,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "project_type": self.project_type,
            "status": self.status,
            "display_status": self.display_status,
            "priority": self.priority,
            "display_priority": self.display_priority,
            "is_high_priority": self.is_high_priority,
            "visibility": self.visibility,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "actual_end_date": self.actual_end_date.isoformat() if self.actual_end_date else None,
            "is_overdue": self.is_overdue,
            "days_until_deadline": self.days_until_deadline,
            "budget": float(self.budget) if self.budget else None,
            "actual_cost": float(self.actual_cost) if self.actual_cost else None,
            "currency": self.currency,
            "is_over_budget": self.is_over_budget,
            "budget_usage_percentage": self.budget_usage_percentage,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "project_manager_id": self.project_manager_id,
            "project_manager_name": self.project_manager.full_name if self.project_manager else None,
            "client_contact_id": self.client_contact_id,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "in_progress_tasks": self.in_progress_tasks,
            "blocked_tasks": self.blocked_tasks,
            "progress_percentage": self.progress_percentage,
            "completion_rate": self.completion_rate,
            "team_size": self.team_size,
            "repository_url": self.repository_url,
            "repository_type": self.repository_type,
            "staging_url": self.staging_url,
            "production_url": self.production_url,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "estimated_duration_days": self.estimated_duration_days,
                "actual_duration_days": self.actual_duration_days,
                "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing project data."""
        data = self.to_dict()
        data.pop("budget", None)
        data.pop("actual_cost", None)
        data.pop("hourly_rate", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing project data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. PROJECT ASSIGNMENT MODEL
# ============================================================

class ProjectAssignment(Base):
    __tablename__ = "project_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("client_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Role
    role = Column(String(50), default="member", nullable=False)  # lead, developer, designer, tester, member
    
    # NEW: Assigned by
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Hours allocated
    hours_allocated = Column(Integer, nullable=True)
    hours_worked = Column(Integer, default=0, nullable=False)
    
    # NEW: Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # NEW: Start date
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # NEW: End date
    assigned_until = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_project_assignments_unique', 'project_id', 'user_id', unique=True),
        Index('ix_project_assignments_project', 'project_id'),
        Index('ix_project_assignments_user', 'user_id'),
        Index('ix_project_assignments_active', 'is_active'),
    )
    
    # RELATIONSHIPS
    project = relationship(
        "ClientProject",
        back_populates="assignments",
        foreign_keys=[project_id]
    )
    
    user = relationship(
        "User",
        back_populates="project_assignments",
        foreign_keys=[user_id]
    )
    
    assigner = relationship(
        "User",
        foreign_keys=[assigned_by],
        uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<ProjectAssignment {self.id}: {self.user_id} -> {self.project_id}>"
    
    @property
    def display_role(self) -> str:
        """Get human-readable role."""
        role_map = {
            "lead": "👔 Lead",
            "developer": "💻 Developer",
            "designer": "🎨 Designer",
            "tester": "🧪 Tester",
            "member": "👤 Member",
        }
        return role_map.get(self.role, "Member")
    
    @property
    def is_lead(self) -> bool:
        """Check if user is lead."""
        return self.role == "lead"
    
    @property
    def hours_remaining(self) -> int:
        """Get remaining hours."""
        if self.hours_allocated is None:
            return -1
        return max(0, self.hours_allocated - self.hours_worked)
    
    def add_hours(self, hours: int) -> None:
        """Add hours worked."""
        self.hours_worked += hours
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "role": self.role,
            "display_role": self.display_role,
            "is_lead": self.is_lead,
            "is_active": self.is_active,
            "hours_allocated": self.hours_allocated,
            "hours_worked": self.hours_worked,
            "hours_remaining": self.hours_remaining,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_until": self.assigned_until.isoformat() if self.assigned_until else None,
            "assigned_by": self.assigned_by,
            "assigned_by_name": self.assigner.full_name if self.assigner else None,
        }


# ============================================================
# 3. PROJECT TASK MODEL
# ============================================================

class ProjectTask(Base):
    __tablename__ = "project_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("client_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Parent task (for sub-tasks)
    parent_task_id = Column(Integer, ForeignKey("project_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Related to
    related_to = Column(String(50), nullable=True)  # feature, bug, task
    
    # NEW: Task number (e.g., PROJ-001)
    task_number = Column(String(50), nullable=True, index=True)
    
    # BASIC INFORMATION
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # TYPE
    task_type = Column(
        String(50),
        default=TaskType.TASK.value,
        nullable=False
    )
    
    # STATUS & PRIORITY
    status = Column(
        String(20),
        default=TaskStatus.TODO.value,
        nullable=False,
        index=True
    )
    
    priority = Column(
        String(20),
        default=TaskPriority.MEDIUM.value,
        nullable=False,
        index=True
    )
    
    # NEW: Story points (for agile)
    story_points = Column(Integer, nullable=True)
    
    # ASSIGNMENT
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Created by
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # DATES
    due_date = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Estimated vs actual
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    
    # NEW: Dependencies
    depends_on = Column(JSON, nullable=True)  # List of task IDs
    
    # NEW: Attachments
    attachments = Column(JSON, nullable=True)
    
    # NEW: Comments count
    comments_count = Column(Integer, default=0, nullable=False)
    
    # NEW: Metadata
    metadata = Column(JSON, nullable=True)
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_project_tasks_project', 'project_id'),
        Index('ix_project_tasks_assigned_to', 'assigned_to'),
        Index('ix_project_tasks_status', 'status'),
        Index('ix_project_tasks_priority', 'priority'),
        Index('ix_project_tasks_due_date', 'due_date'),
        Index('ix_project_tasks_parent', 'parent_task_id'),
    )
    
    # RELATIONSHIPS
    project = relationship(
        "ClientProject",
        back_populates="tasks",
        foreign_keys=[project_id]
    )
    
    assigned_to_user = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assigned_to]
    )
    
    created_by_user = relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[created_by]
    )
    
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    # NEW: Time entries
    time_entries = relationship(
        "TaskTimeEntry",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ProjectTask {self.id}: {self.title}>"
    
    @property
    def is_done(self) -> bool:
        """Check if task is done."""
        return self.status == TaskStatus.DONE.value
    
    @property
    def is_in_progress(self) -> bool:
        """Check if task is in progress."""
        return self.status == TaskStatus.IN_PROGRESS.value
    
    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self.status == TaskStatus.BLOCKED.value
    
    @property
    def is_todo(self) -> bool:
        """Check if task is todo."""
        return self.status == TaskStatus.TODO.value
    
    @property
    def is_cancelled_task(self) -> bool:
        """Check if task is cancelled."""
        return self.status == TaskStatus.CANCELLED.value
    
    @property
    def is_high_priority_task(self) -> bool:
        """Check if task has high priority."""
        return self.priority in [TaskPriority.HIGH.value, TaskPriority.URGENT.value, TaskPriority.CRITICAL.value]
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "todo": "📋 To Do",
            "in_progress": "🔄 In Progress",
            "review": "🔍 Review",
            "blocked": "🚫 Blocked",
            "done": "✅ Done",
            "cancelled": "❌ Cancelled",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def display_priority(self) -> str:
        """Get human-readable priority."""
        priority_map = {
            "low": "🟢 Low",
            "medium": "🔵 Medium",
            "high": "🟠 High",
            "urgent": "🔴 Urgent",
            "critical": "⛔ Critical",
        }
        return priority_map.get(self.priority, "Medium")
    
    @property
    def display_type(self) -> str:
        """Get human-readable type."""
        type_map = {
            "feature": "✨ Feature",
            "bug": "🐛 Bug",
            "task": "📝 Task",
            "design": "🎨 Design",
            "research": "🔬 Research",
            "testing": "🧪 Testing",
            "documentation": "📄 Documentation",
            "meeting": "🤝 Meeting",
            "other": "📌 Other",
        }
        return type_map.get(self.task_type, "Task")
    
    @property
    def is_overdue_task(self) -> bool:
        """Check if task is overdue."""
        if self.due_date is None or self.is_done or self.is_cancelled_task:
            return False
        return self.due_date < func.now()
    
    @property
    def days_until_due(self) -> int:
        """Get days until task due date."""
        if self.due_date is None:
            return -1
        delta = self.due_date - func.now()
        return max(0, delta.days)
    
    @property
    def has_subtasks(self) -> bool:
        """Check if task has subtasks."""
        return False  # Would need to query children
    
    @property
    def is_estimated(self) -> bool:
        """Check if task has estimate."""
        return self.estimated_hours is not None
    
    def start_task(self) -> None:
        """Start the task."""
        self.status = TaskStatus.IN_PROGRESS.value
        if not self.started_at:
            self.started_at = func.now()
    
    def complete_task(self) -> None:
        """Complete the task."""
        self.status = TaskStatus.DONE.value
        self.completed_at = func.now()
    
    def block_task(self, reason: str = None) -> None:
        """Block the task."""
        self.status = TaskStatus.BLOCKED.value
        if reason:
            if self.metadata is None:
                self.metadata = {}
            self.metadata["blocked_reason"] = reason
    
    def unblock_task(self) -> None:
        """Unblock the task."""
        self.status = TaskStatus.IN_PROGRESS.value
        if self.metadata:
            self.metadata.pop("blocked_reason", None)
    
    def cancel_task(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED.value
    
    def add_comment(self, comment: 'TaskComment') -> None:
        """Add a comment to the task."""
        if self.comments is None:
            self.comments = []
        self.comments.append(comment)
        self.comments_count += 1
    
    def add_time_entry(self, hours: float, description: str = None) -> None:
        """Add a time entry."""
        entry = TaskTimeEntry(
            hours=hours,
            description=description
        )
        if self.time_entries is None:
            self.time_entries = []
        self.time_entries.append(entry)
        if self.actual_hours is None:
            self.actual_hours = 0
        self.actual_hours += hours
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert task to dictionary."""
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "task_number": self.task_number,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "display_type": self.display_type,
            "status": self.status,
            "display_status": self.display_status,
            "priority": self.priority,
            "display_priority": self.display_priority,
            "is_high_priority": self.is_high_priority_task,
            "story_points": self.story_points,
            "assigned_to": self.assigned_to,
            "assigned_to_name": self.assigned_to_user.full_name if self.assigned_to_user else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "is_overdue": self.is_overdue_task,
            "days_until_due": self.days_until_due,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "comments_count": self.comments_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "parent_task_id": self.parent_task_id,
                "related_to": self.related_to,
                "depends_on": self.depends_on,
                "attachments": self.attachments,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data


# ============================================================
# 4. TASK COMMENT MODEL
# ============================================================

class TaskComment(Base):
    __tablename__ = "task_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    
    # NEW: Attachments
    attachments = Column(JSON, nullable=True)
    
    # NEW: Mentions
    mentioned_users = Column(JSON, nullable=True)
    
    # NEW: Edited
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # RELATIONSHIPS
    task = relationship("ProjectTask", back_populates="comments")
    user = relationship("User", back_populates="task_comments")
    
    __table_args__ = (
        Index('ix_task_comments_task', 'task_id'),
        Index('ix_task_comments_user', 'user_id'),
        Index('ix_task_comments_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<TaskComment {self.id}: {self.content[:50]}...>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "user_avatar": self.user.profile_picture if self.user else None,
            "content": self.content,
            "attachments": self.attachments,
            "mentioned_users": self.mentioned_users,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# 5. TASK TIME ENTRY MODEL
# ============================================================

class TaskTimeEntry(Base):
    __tablename__ = "task_time_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    hours = Column(DECIMAL(5, 2), nullable=False)
    description = Column(Text, nullable=True)
    
    # NEW: Date of work
    work_date = Column(DateTime(timezone=True), nullable=False)
    
    # NEW: Billable
    is_billable = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # RELATIONSHIPS
    task = relationship("ProjectTask", back_populates="time_entries")
    user = relationship("User", back_populates="time_entries")
    
    __table_args__ = (
        Index('ix_task_time_entries_task', 'task_id'),
        Index('ix_task_time_entries_user', 'user_id'),
        Index('ix_task_time_entries_date', 'work_date'),
        Index('ix_task_time_entries_billable', 'is_billable'),
    )
    
    def __repr__(self) -> str:
        return f"<TaskTimeEntry {self.id}: {self.hours}h>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "hours": float(self.hours),
            "description": self.description,
            "work_date": self.work_date.isoformat() if self.work_date else None,
            "is_billable": self.is_billable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }