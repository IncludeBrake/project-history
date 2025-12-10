import json
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from git import Repo  # from GitPython
from sqlalchemy import desc, asc
from datetime import datetime
from .db import init_db, get_session
from .models import Project, Snapshot, RunCommand, Task, Note

app = typer.Typer()
console = Console()

PH_CONFIG_NAME = "ph.yml"


def find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return start


def load_or_create_project(root: Path) -> Project:
    from sqlmodel import select

    session = get_session()
    proj = session.exec(
        select(Project).where(Project.root_path == str(root))
    ).first()
    if proj:
        return proj

    console.print("[bold yellow]Project not initialized. Run `ph init` first.[/]")
    raise typer.Exit(code=1)


@app.command()
def init(
    name: str = typer.Option(None, help="Project name (default: folder name)"),
    description: str = typer.Option(..., help="Short project description"),
    stack: str = typer.Option("python", help='Comma-separated tech stack, e.g. "python,crewai,fastapi"'),
):
    """Initialize project history for current repo."""
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)

    try:
        repo = Repo(root)
        remote_url = next(iter(repo.remotes)).url if repo.remotes else None
    except Exception:
        remote_url = None

    if not name:
        name = root.name

    stack_list = [s.strip() for s in stack.split(",") if s.strip()]

    from sqlmodel import select
    session = get_session()
    existing = session.exec(
        select(Project).where(Project.root_path == str(root))
    ).first()
    if existing:
        console.print("[green]Project already initialized.[/]")
        raise typer.Exit(0)

    proj = Project(
        name=name,
        root_path=str(root),
        remote_url=remote_url,
        description=description,
        stack=stack_list,
    )
    session.add(proj)
    session.commit()
    console.print(f"[green]Initialized project history for {name} at {root}[/]")


@app.command()
def status():
    """Show current status for this project."""
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)

    from sqlmodel import select
    session = get_session()
    proj = load_or_create_project(root)

    console.rule(f"[bold cyan]{proj.name}[/]")
    console.print(proj.description)
    console.print(f"[dim]{proj.root_path}[/]")
    console.print(f"[dim]Stack: {', '.join(proj.stack)}[/]")

    # Last snapshot
    last_snap = session.exec(
        select(Snapshot)
        .where(Snapshot.project_id == proj.id)
        .order_by(Snapshot.timestamp.desc())
    ).first()

    if last_snap:
        console.print("\n[bold]Last snapshot:[/]")
        console.print(
            f"- {last_snap.timestamp} | {last_snap.status} | {last_snap.summary}"
        )
        if last_snap.git_commit:
            console.print(f"- Commit: {last_snap.git_commit} ({last_snap.branch})")
    else:
        console.print("\n[bold yellow]No snapshots yet.[/] Use `ph snapshot --summary \"...\"`")

    # Run commands
    cmds = session.exec(
        select(RunCommand).where(RunCommand.project_id == proj.id)
    ).all()
    if cmds:
        table = Table(title="How to run")
        table.add_column("Label")
        table.add_column("Command")
        table.add_column("Verified At", justify="right")
        for c in cmds:
            table.add_row(c.label, c.command, str(c.last_verified_at or "never"))
        console.print()
        console.print(table)

    # Top tasks
    tasks = session.exec(
        select(Task)
        .where(Task.project_id == proj.id, Task.status != "done")
        .order_by(asc(Task.priority))
        .limit(5)
    ).all()
    if tasks:
        console.print("\n[bold]Top tasks:[/]")
        for t in tasks:
            console.print(f"- [b]{t.status.upper()}[/] (P{t.priority}) {t.title}")
        # Recent notes
    from sqlmodel import select
    last_note = session.exec(
        select(Note)
        .where(Note.project_id == proj.id)
        .order_by(Note.created_at.desc())
    ).first()

    if last_note:
        console.print("\n[bold]Last note:[/]")
        console.print(
            f"- [{last_note.note_type}] {last_note.created_at} "
            f"| {last_note.content[:120].replace('\n', ' ')}"
        )
        if last_note.source_link:
            console.print(f"- Link: {last_note.source_link}")

@app.command()
def snapshot(
    summary: str = typer.Option(
        ...,
        "--summary",
        "-s",
        help="Short summary of the current state or what you just did",), 
    status: str = typer.Option( "unknown", "--status", "-t", help="Status tag: e.g. green, broken, refactor, spike",),
):
    """Log a snapshot of current state (optionally ties to git commit)."""
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)
    proj = load_or_create_project(root)

    from sqlmodel import select
    from .models import Snapshot

    try:
        repo = Repo(root)
        git_commit = repo.head.commit.hexsha
        branch = repo.active_branch.name
    except Exception:
        git_commit = None
        branch = None

    session = get_session()
    snap = Snapshot(
        project_id=proj.id,
        git_commit=git_commit,
        branch=branch,
        summary=summary,
        status=status,
    )
    session.add(snap)
    session.commit()
    console.print(f"[green]Snapshot recorded for {proj.name}[/]")

@app.command("add-run")
def add_run(
    label: str = typer.Argument(..., help="Short name for this command, e.g. dev, tests, worker"),
    command: str = typer.Argument(..., help="The shell command to run, e.g. 'uv run fastapi dev'"),
    notes: str = typer.Option("", "--notes", "-n", help="Optional notes about when/why to use this command"),
):
    """Register a 'how to run this project' command."""
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)
    proj = load_or_create_project(root)

    session = get_session()

    from sqlmodel import select

    existing = session.exec(
        select(RunCommand)
        .where(RunCommand.project_id == proj.id, RunCommand.label == label)
    ).first()

    if existing:
        existing.command = command
        existing.notes = notes or existing.notes
        existing.last_verified_at = datetime.utcnow()
        console.print(f"[yellow]Updated run command '{label}' for {proj.name}[/]")
    else:
        rc = RunCommand(
            project_id=proj.id,
            label=label,
            command=command,
            notes=notes or None,
            last_verified_at=datetime.utcnow(),
        )
        session.add(rc)
        console.print(f"[green]Added run command '{label}' for {proj.name}[/]")

    session.commit()

@app.command("add-task")
def add_task(
    title: str = typer.Argument(..., help="Short description of the task"),
    priority: int = typer.Option(2, "--priority", "-p", min=1, max=3, help="1=high, 2=medium, 3=low"),
):
    """Add a task for this project."""
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)
    proj = load_or_create_project(root)

    session = get_session()

    task = Task(
        project_id=proj.id,
        title=title,
        priority=priority,
        status="todo",
    )
    session.add(task)
    session.commit()

    console.print(f"[green]Added task (P{priority}) for {proj.name}:[/] {title}")
@app.command("done-task")
def done_task(
    task_id: int = typer.Argument(..., help="ID of the task to mark as done"),
):
    """Mark a task as done."""
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)
    proj = load_or_create_project(root)

    from sqlmodel import select
    session = get_session()

    task = session.exec(
        select(Task).where(Task.project_id == proj.id, Task.id == task_id)
    ).first()

    if not task:
        console.print(f"[red]No task with id {task_id} for project {proj.name}[/]")
        raise typer.Exit(code=1)

    from datetime import datetime

    task.status = "done"
    task.completed_at = datetime.utcnow()
    session.add(task)
    session.commit()
    console.print(f"[green]Marked task {task_id} as DONE:[/] {task.title}")
@app.command("add-note")
def add_note(
    note_type: str = typer.Option(
        "manual",
        "--type",
        "-k",
        help="Type of note: chatgpt, manual, decision, bug",
    ),
    summary: str = typer.Option(
        ...,
        "--summary",
        "-s",
        help="Short description of what this note is about",
    ),
    path: Path = typer.Option(
        None,
        "--file",
        "-f",
        help="Optional path to a file containing the full note (e.g. ChatGPT export, markdown)",
    ),
    link: str = typer.Option(
        "",
        "--link",
        "-l",
        help="Optional URL to the ChatGPT conversation or external doc",
    ),
):
    """
    Attach a note to this project (optionally the latest snapshot).
    Use for ChatGPT instructions, decisions, bug reports, etc.
    """
    init_db()
    cwd = Path.cwd()
    root = find_project_root(cwd)
    proj = load_or_create_project(root)

    from sqlmodel import select

    session = get_session()

    # Attach to latest snapshot if it exists
    last_snap = session.exec(
        select(Snapshot)
        .where(Snapshot.project_id == proj.id)
        .order_by(Snapshot.timestamp.desc())
    ).first()

    if path is not None and path.exists():
        content = path.read_text(encoding="utf-8")
    else:
        # For now, just store the summary as content if no file
        content = summary

    note = Note(
        project_id=proj.id,
        snapshot_id=last_snap.id if last_snap else None,
        note_type=note_type,
        content=content,
        source_link=link or None,
    )
    session.add(note)
    session.commit()

    console.print(
        f"[green]Added {note_type} note for {proj.name}[/] "
        f"(snapshot: {last_snap.id if last_snap else 'none'})"
    )
@app.command("projects")
def list_projects(
    limit: int = typer.Option(20, "--limit", "-n", help="Max number of projects to show"),
):
    """List known projects with their last snapshot and status."""
    init_db()
    session = get_session()

    from sqlmodel import select, func

    # Grab projects ordered by most recent snapshot / creation
    projects = session.exec(select(Project)).all()

    table = Table(title="Projects", show_lines=False)
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Path")
    table.add_column("Status")
    table.add_column("Last Snapshot")
    table.add_column("Last Commit")

    for proj in projects[:limit]:
        # last snapshot per project
        last_snap = session.exec(
            select(Snapshot)
            .where(Snapshot.project_id == proj.id)
            .order_by(Snapshot.timestamp.desc())
        ).first()

        if last_snap:
            snap_text = f"{last_snap.timestamp} | {last_snap.status}"
            commit_text = (
                f"{last_snap.git_commit[:8]} ({last_snap.branch})"
                if last_snap.git_commit
                else "-"
            )
        else:
            snap_text = "—"
            commit_text = "—"

        table.add_row(
            str(proj.id),
            proj.name,
            proj.root_path,
            proj.status,
            snap_text,
            commit_text,
        )

    console.print(table)
   
def main():
    app()  # app is typer.Typer()


if __name__ == "__main__":
    main()

