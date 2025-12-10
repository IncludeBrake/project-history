import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

def get_db_path() -> str:
    base = Path(os.path.expanduser("~")) / ".project_history"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / "ph.db")

engine = create_engine(f"sqlite:///{get_db_path()}", echo=False)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
