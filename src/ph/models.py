from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    root_path: str
    remote_url: Optional[str] = None
    description: str
    stack: List[str] = Field(sa_column=Column(JSON))
    status: str = "active"


class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    git_commit: Optional[str] = None
    branch: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    summary: str
    status: str = "unknown"  # green / broken / refactor / spike


class RunCommand(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    label: str
    command: str
    last_verified_at: Optional[datetime] = None
    notes: Optional[str] = None


class Note(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    snapshot_id: Optional[int] = Field(default=None, foreign_key="snapshot.id")
    note_type: str  # chatgpt | manual | decision | bug
    content: str
    source_link: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    title: str
    status: str = "todo"  # todo | doing | done | blocked
    priority: int = 2      # 1=high, 2=medium, 3=low
    blocked_by: Optional[int] = Field(default=None, foreign_key="task.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

