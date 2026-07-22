# ============================================================
# AETHER LINK - PROJECT SCHEMAS (Software House)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# PROJECT ENUMS
# ============================================================

class ProjectStatusEnum(str, Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriorityEnum(str, Enum):
    """Project priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ProjectVisibilityEnum(str, Enum):
    """Project visibility enumeration."""
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM_ONLY = "team_only"
    CLIENT_ONLY = "client_only"


class TaskStatusEnum(str, Enum):
    """Task status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriorityEnum(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskTypeEnum(str, Enum):
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
# BASE SCHEMA
# ============================================================

class ProjectBase(BaseModel):
    """Base project schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# PROJECT CREATE SCHEMA
# ============================================================

class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    
    client_id: int = Field(..., gt=0, description="Client ID")
    name: str = Field(..., min_length=3, max_length=255, description="Project name")
    slug: str = Field(..., min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=5000, description="Project description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description")
    
    project_type: Optional[str] = Field(default=None, max_length=50, description="Project type")
    
    status: ProjectStatusEnum = Field(
        default=ProjectStatusEnum.PLANNING,
        description="Project status"
    )
    priority: ProjectPriorityEnum = Field(
        default=ProjectPriorityEnum.MEDIUM,
        description="Project priority"
    )
    visibility: ProjectVisibilityEnum = Field(
        default=ProjectVisibilityEnum.TEAM_ONLY,
        description="Project visibility"
    )
    
    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")
    estimated_duration_days: Optional[int] = Field(default=None, ge=0, description="Estimated duration in days")
    
    budget: Optional[float] = Field(default=None, ge=0, description="Project budget")
    currency: str = Field(default="PKR", max_length=3, description="Currency code")
    hourly_rate: Optional[float] = Field(default=None, ge=0, description="Hourly rate")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="Estimated hours")
    
    project_manager_id: Optional[int] = Field(default=None, gt=0, description="Project manager user ID")
    client_contact_id: Optional[int] = Field(default=None, gt=0, description="Client contact ID")
    
    repository_url: Optional[str] = Field(default=None, max_length=500, description="Repository URL")
    repository_type: Optional[str] = Field(default=None, max_length=50, description="Repository type")
    staging_url: Optional[str] = Field(default=None, max_length=500, description="Staging URL")
    production_url: Optional[str] = Field(default=None, max_length=500, description="Production URL")
    
    tags: Optional[List[str]] = Field(default=None, description="Project tags")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()


# ============================================================
# PROJECT UPDATE SCHEMA
# ============================================================

class ProjectUpdate(ProjectBase):
    """Schema for updating a project."""
    
    name: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Project name")
    slug: Optional[str] = Field(default=None, min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=5000, description="Project description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description")
    
    project_type: Optional[str] = Field(default=None, max_length=50, description="Project type")
    
    status: Optional[ProjectStatusEnum] = Field(default=None, description="Project status")
    priority: Optional[ProjectPriorityEnum] = Field(default=None, description="Project priority")
    visibility: Optional[ProjectVisibilityEnum] = Field(default=None, description="Project visibility")
    
    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")
    estimated_duration_days: Optional[int] = Field(default=None, ge=0, description="Estimated duration in days")
    
    budget: Optional[float] = Field(default=None, ge=0, description="Project budget")
    currency: Optional[str] = Field(default=None, max_length=3, description="Currency code")
    hourly_rate: Optional[float] = Field(default=None, ge=0, description="Hourly rate")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="Estimated hours")
    
    project_manager_id: Optional[int] = Field(default=None, gt=0, description="Project manager user ID")
    client_contact_id: Optional[int] = Field(default=None, gt=0, description="Client contact ID")
    
    repository_url: Optional[str] = Field(default=None, max_length=500, description="Repository URL")
    repository_type: Optional[str] = Field(default=None, max_length=50, description="Repository type")
    staging_url: Optional[str] = Field(default=None, max_length=500, description="Staging URL")
    production_url: Optional[str] = Field(default=None, max_length=500, description="Production URL")
    
    tags: Optional[List[str]] = Field(default=None, description="Project tags")


# ============================================================
# PROJECT ASSIGNMENT SCHEMAS
# ============================================================

class ProjectAssignmentCreate(ProjectBase):
    """Schema for assigning a team member to a project."""
    
    project_id: int = Field(..., gt=0, description="Project ID")
    user_id: int = Field(..., gt=0, description="User ID")
    role: str = Field(default="member", max_length=50, description="Role (lead, developer, designer, tester, member)")
    hours_allocated: Optional[int] = Field(default=None, ge=0, description="Hours allocated")
    assigned_until: Optional[datetime] = Field(default=None, description="Assignment end date")


class ProjectAssignmentUpdate(ProjectBase):
    """Schema for updating a project assignment."""
    
    role: Optional[str] = Field(default=None, max_length=50, description="Role")
    hours_allocated: Optional[int] = Field(default=None, ge=0, description="Hours allocated")
    is_active: Optional[bool] = Field(default=None, description="Is active")
    assigned_until: Optional[datetime] = Field(default=None, description="Assignment end date")


class ProjectAssignmentResponse(ProjectBase):
    """Schema for project assignment response."""
    
    id: int = Field(..., description="Assignment ID")
    project_id: int = Field(..., description="Project ID")
    user_id: int = Field(..., description="User ID")
    user_name: Optional[str] = Field(default=None, description="User name")
    user_email: Optional[str] = Field(default=None, description="User email")
    
    role: str = Field(..., description="Role")
    display_role: str = Field(..., description="Human-readable role")
    is_lead: bool = Field(..., description="Is lead")
    is_active: bool = Field(..., description="Is active")
    
    hours_allocated: Optional[int] = Field(default=None, description="Hours allocated")
    hours_worked: int = Field(..., description="Hours worked")
    hours_remaining: int = Field(..., description="Hours remaining")
    
    assigned_by: Optional[int] = Field(default=None, description="Assigned by user ID")
    assigned_by_name: Optional[str] = Field(default=None, description="Assigned by user name")
    
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    assigned_until: Optional[datetime] = Field(default=None, description="Assignment end date")


# ============================================================
# PROJECT TASK SCHEMAS
# ============================================================

class ProjectTaskCreate(ProjectBase):
    """Schema for creating a project task."""
    
    project_id: int = Field(..., gt=0, description="Project ID")
    
    title: str = Field(..., min_length=3, max_length=255, description="Task title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Task description")
    
    task_type: TaskTypeEnum = Field(
        default=TaskTypeEnum.TASK,
        description="Task type"
    )
    status: TaskStatusEnum = Field(
        default=TaskStatusEnum.TODO,
        description="Task status"
    )
    priority: TaskPriorityEnum = Field(
        default=TaskPriorityEnum.MEDIUM,
        description="Task priority"
    )
    
    story_points: Optional[int] = Field(default=None, ge=0, description="Story points")
    
    assigned_to: Optional[int] = Field(default=None, gt=0, description="Assigned to user ID")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="Estimated hours")
    
    parent_task_id: Optional[int] = Field(default=None, gt=0, description="Parent task ID")
    related_to: Optional[str] = Field(default=None, max_length=50, description="Related to")
    depends_on: Optional[List[int]] = Field(default=None, description="Dependent task IDs")


class ProjectTaskUpdate(ProjectBase):
    """Schema for updating a project task."""
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Task title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Task description")
    
    task_type: Optional[TaskTypeEnum] = Field(default=None, description="Task type")
    status: Optional[TaskStatusEnum] = Field(default=None, description="Task status")
    priority: Optional[TaskPriorityEnum] = Field(default=None, description="Task priority")
    
    story_points: Optional[int] = Field(default=None, ge=0, description="Story points")
    
    assigned_to: Optional[int] = Field(default=None, gt=0, description="Assigned to user ID")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="Estimated hours")
    
    parent_task_id: Optional[int] = Field(default=None, gt=0, description="Parent task ID")
    depends_on: Optional[List[int]] = Field(default=None, description="Dependent task IDs")


class ProjectTaskResponse(ProjectBase):
    """Schema for project task response."""
    
    id: int = Field(..., description="Task ID")
    project_id: int = Field(..., description="Project ID")
    project_name: Optional[str] = Field(default=None, description="Project name")
    
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    
    task_type: str = Field(..., description="Task type")
    display_type: str = Field(..., description="Human-readable type")
    status: str = Field(..., description="Task status")
    display_status: str = Field(..., description="Human-readable status")
    priority: str = Field(..., description="Task priority")
    display_priority: str = Field(..., description="Human-readable priority")
    is_high_priority: bool = Field(..., description="Is high priority")
    
    story_points: Optional[int] = Field(default=None, description="Story points")
    
    assigned_to: Optional[int] = Field(default=None, description="Assigned to user ID")
    assigned_to_name: Optional[str] = Field(default=None, description="Assigned to user name")
    assigned_to_avatar: Optional[str] = Field(default=None, description="Assigned to user avatar")
    
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    is_overdue: bool = Field(..., description="Is overdue")
    days_until_due: int = Field(..., description="Days until due")
    
    started_at: Optional[datetime] = Field(default=None, description="Started timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completed timestamp")
    
    estimated_hours: Optional[int] = Field(default=None, description="Estimated hours")
    actual_hours: Optional[int] = Field(default=None, description="Actual hours")
    
    parent_task_id: Optional[int] = Field(default=None, description="Parent task ID")
    depends_on: Optional[List[int]] = Field(default=None, description="Dependent task IDs")
    
    comments_count: int = Field(..., description="Comments count")
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# TASK COMMENT SCHEMAS
# ============================================================

class TaskCommentCreate(ProjectBase):
    """Schema for creating a task comment."""
    
    task_id: int = Field(..., gt=0, description="Task ID")
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    mentioned_users: Optional[List[int]] = Field(
        default=None,
        description="Mentioned user IDs"
    )


class TaskCommentUpdate(ProjectBase):
    """Schema for updating a task comment."""
    
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")


class TaskCommentResponse(ProjectBase):
    """Schema for task comment response."""
    
    id: int = Field(..., description="Comment ID")
    task_id: int = Field(..., description="Task ID")
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    user_avatar: Optional[str] = Field(default=None, description="User avatar")
    
    content: str = Field(..., description="Comment content")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    mentioned_users: Optional[List[int]] = Field(
        default=None,
        description="Mentioned user IDs"
    )
    
    is_edited: bool = Field(..., description="Is edited")
    edited_at: Optional[datetime] = Field(default=None, description="Edit timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# TASK TIME ENTRY SCHEMAS
# ============================================================

class TaskTimeEntryCreate(ProjectBase):
    """Schema for creating a time entry."""
    
    task_id: int = Field(..., gt=0, description="Task ID")
    hours: float = Field(..., gt=0, le=24, description="Hours worked")
    description: Optional[str] = Field(default=None, max_length=500, description="Description")
    work_date: datetime = Field(..., description="Work date")
    is_billable: bool = Field(default=True, description="Is billable")


class TaskTimeEntryResponse(ProjectBase):
    """Schema for time entry response."""
    
    id: int = Field(..., description="Time entry ID")
    task_id: int = Field(..., description="Task ID")
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    
    hours: float = Field(..., description="Hours worked")
    description: Optional[str] = Field(default=None, description="Description")
    work_date: datetime = Field(..., description="Work date")
    is_billable: bool = Field(..., description="Is billable")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# PROJECT RESPONSE SCHEMA
# ============================================================

class ProjectResponse(ProjectBase):
    """Schema for project response."""
    
    id: int = Field(..., description="Project ID")
    client_id: int = Field(..., description="Client ID")
    client_name: Optional[str] = Field(default=None, description="Client name")
    
    name: str = Field(..., description="Project name")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(default=None, description="Project description")
    short_description: Optional[str] = Field(default=None, description="Short description")
    
    project_type: Optional[str] = Field(default=None, description="Project type")
    
    status: str = Field(..., description="Project status")
    display_status: str = Field(..., description="Human-readable status")
    priority: str = Field(..., description="Project priority")
    display_priority: str = Field(..., description="Human-readable priority")
    is_high_priority: bool = Field(..., description="Is high priority")
    visibility: str = Field(..., description="Project visibility")
    
    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")
    actual_end_date: Optional[datetime] = Field(default=None, description="Actual end date")
    
    is_overdue: bool = Field(..., description="Is overdue")
    days_until_deadline: int = Field(..., description="Days until deadline")
    
    budget: Optional[float] = Field(default=None, description="Project budget")
    actual_cost: Optional[float] = Field(default=None, description="Actual cost")
    currency: str = Field(..., description="Currency code")
    is_over_budget: bool = Field(..., description="Is over budget")
    budget_usage_percentage: float = Field(..., description="Budget usage percentage")
    
    estimated_hours: Optional[int] = Field(default=None, description="Estimated hours")
    actual_hours: Optional[int] = Field(default=None, description="Actual hours")
    
    project_manager_id: Optional[int] = Field(default=None, description="Project manager user ID")
    project_manager_name: Optional[str] = Field(default=None, description="Project manager name")
    
    client_contact_id: Optional[int] = Field(default=None, description="Client contact ID")
    
    total_tasks: int = Field(..., description="Total tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    in_progress_tasks: int = Field(..., description="In progress tasks")
    blocked_tasks: int = Field(..., description="Blocked tasks")
    progress_percentage: int = Field(..., description="Progress percentage")
    completion_rate: float = Field(..., description="Completion rate")
    
    team_size: int = Field(..., description="Team size")
    
    repository_url: Optional[str] = Field(default=None, description="Repository URL")
    repository_type: Optional[str] = Field(default=None, description="Repository type")
    staging_url: Optional[str] = Field(default=None, description="Staging URL")
    production_url: Optional[str] = Field(default=None, description="Production URL")
    
    tags: Optional[List[str]] = Field(default=None, description="Project tags")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# PROJECT DETAIL RESPONSE
# ============================================================

class ProjectDetailResponse(ProjectResponse):
    """Schema for project detail response."""
    
    assignments: Optional[List[ProjectAssignmentResponse]] = Field(
        default=None,
        description="Team assignments"
    )
    
    tasks: Optional[List[ProjectTaskResponse]] = Field(
        default=None,
        description="Project tasks"
    )
    
    invoices: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Project invoices"
    )


# ============================================================
# PROJECT LIST REQUEST (Filters)
# ============================================================

class ProjectListRequest(ProjectBase):
    """Schema for project list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by name or description")
    status: Optional[ProjectStatusEnum] = Field(default=None, description="Filter by status")
    priority: Optional[ProjectPriorityEnum] = Field(default=None, description="Filter by priority")
    client_id: Optional[int] = Field(default=None, description="Filter by client")
    project_manager_id: Optional[int] = Field(default=None, description="Filter by project manager")
    assigned_to: Optional[int] = Field(default=None, description="Filter by assigned team member")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# PROJECT LIST RESPONSE
# ============================================================

class ProjectListResponse(ProjectBase):
    """Schema for paginated project list response."""
    
    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total projects")
    active_count: int = Field(..., description="Active projects")
    planning_count: int = Field(..., description="Planning projects")
    completed_count: int = Field(..., description="Completed projects")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# PROJECT STATISTICS (Admin View)
# ============================================================

class ProjectStatistics(ProjectBase):
    """Schema for project statistics."""
    
    total_projects: int = Field(..., description="Total projects")
    planning: int = Field(..., description="Planning projects")
    active: int = Field(..., description="Active projects")
    on_hold: int = Field(..., description="On hold projects")
    review: int = Field(..., description="Review projects")
    completed: int = Field(..., description="Completed projects")
    cancelled: int = Field(..., description="Cancelled projects")
    archived: int = Field(..., description="Archived projects")
    
    # NEW: Priority breakdown
    priority_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Projects by priority"
    )
    
    # NEW: Revenue stats
    total_budget: float = Field(..., description="Total budget")
    total_actual_cost: float = Field(..., description="Total actual cost")
    total_revenue: float = Field(..., description="Total revenue")
    average_project_budget: float = Field(..., description="Average project budget")
    
    # NEW: Task stats
    total_tasks: int = Field(..., description="Total tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    in_progress_tasks: int = Field(..., description="In progress tasks")
    blocked_tasks: int = Field(..., description="Blocked tasks")
    average_task_completion: float = Field(..., description="Average task completion")
    
    # NEW: Team stats
    total_team_members: int = Field(..., description="Total team members")
    average_team_size: float = Field(..., description="Average team size")
    
    # NEW: Top projects
    top_projects: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top performing projects"
    )


# ============================================================
# PROJECT BULK OPERATIONS
# ============================================================

class ProjectBulkAction(ProjectBase):
    """Schema for bulk project actions."""
    
    project_ids: List[int] = Field(..., min_length=1, description="List of project IDs")
    action: str = Field(..., description="Action to perform (archive, delete, complete, cancel)")
    note: Optional[str] = Field(default=None, max_length=500, description="Action note")


# ============================================================
# PROJECT TASK BULK UPDATE
# ============================================================

class TaskBulkUpdate(ProjectBase):
    """Schema for bulk task updates."""
    
    task_ids: List[int] = Field(..., min_length=1, description="List of task IDs")
    status: Optional[TaskStatusEnum] = Field(default=None, description="New status")
    priority: Optional[TaskPriorityEnum] = Field(default=None, description="New priority")
    assigned_to: Optional[int] = Field(default=None, description="Assign to user ID")
    due_date: Optional[datetime] = Field(default=None, description="New due date")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ProjectStatusEnum",
    "ProjectPriorityEnum",
    "ProjectVisibilityEnum",
    "TaskStatusEnum",
    "TaskPriorityEnum",
    "TaskTypeEnum",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectAssignmentCreate",
    "ProjectAssignmentUpdate",
    "ProjectAssignmentResponse",
    "ProjectTaskCreate",
    "ProjectTaskUpdate",
    "ProjectTaskResponse",
    "TaskCommentCreate",
    "TaskCommentUpdate",
    "TaskCommentResponse",
    "TaskTimeEntryCreate",
    "TaskTimeEntryResponse",
    "ProjectResponse",
    "ProjectDetailResponse",
    "ProjectListRequest",
    "ProjectListResponse",
    "ProjectStatistics",
    "ProjectBulkAction",
    "TaskBulkUpdate",
]