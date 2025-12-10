# ph – Project History System for ADHDrs

> Answer this for any repo in one command:  
> **What is this? Where am I? How do I run it? What’s next?**

`ph` is a small CLI tool that tracks per-project history in a local SQLite database:

- **Project registry** – name, path, stack, remote.
- **Snapshots** – timeline of work sessions tied to git commits.
- **Run commands** – “how to run dev / tests / workers” per project.
- **Tasks** – top next actions per repo.
- **Notes** – links to LLM convos / decision docs (ChatGPT, Claude, etc.).

Once installed, you can run `ph` inside any git repo on your machine and get a one-screen status dashboard.

---

## 1. Installation

Requirements:

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) installed and on your PATH

Clone and install as a global editable tool:

```bash
git clone <this-repo> project-history
cd project-history

# Install dependencies + tool
uv sync
uv tool install . -e
````

Check that it works:

```bash
ph --help
```

You should see the Typer help output.

> **Note:** `uv tool install . -e` makes `ph` editable. Changes in `src/ph` take effect immediately without reinstall.

---

## 2. Concept

`ph` stores all data in a local SQLite database under your user profile (one DB for all projects).

For each repo, it tracks:

* **Project** – name, root path, stack, remote URL.
* **Snapshots** – what you did, when, and on which commit/branch.
* **Run commands** – commands you trust to start dev servers, tests, workers, etc.
* **Tasks** – small, prioritized items (P1–P3) to keep momentum.
* **Notes** – pointers to `docs/chatgpt/*.md`, `docs/claude/*.md`, and other decision artefacts.

You run it *inside* project folders. `ph` auto-detects the project root by walking up to the nearest `.git`.

---

## 3. Daily Workflow

Typical pattern for **each** project:

1. **First time in a repo**

   ```bash
   ph init --description "TractionBuild_MVP" \
           --stack "python,fastapi,openai,pydantic,typer,rich,uvicorn"
   ```

2. **End of a work session**

   ```bash
   ph snapshot -s "Implemented X, refactored Y, noted bug Z" -t green
   ph status
   ```

3. **When you discover run commands**

   ```bash
   ph add-run dev "uv run uvicorn app.main:app --reload" -n "Dev API server on :8000"
   ph add-run tests "uv run pytest" -n "Run test suite"
   ```

4. **When you choose next actions**

   ```bash
   ph add-task "Add basic auth guard on admin routes" -p 1
   ph add-task "Document local dev setup in README" -p 2
   ph status
   ```

5. **When you finish something**

   ```bash
   ph done-task 1
   ph status
   ```

6. **When you finish an AI convo and save it**

   Convention (per project):

   ```text
   <ProjectRoot>/
     docs/
       chatgpt/
         <topic>-YYYY-MM-DD-<project>.md
       claude/
         <topic>-YYYY-MM-DD-<project>.md
   ```

   Then:

   ```bash
   ph add-note \
     --type chatgpt \
     --summary "Designed ph status + run/task loop" \
     --file docs/chatgpt/status-dashboard-2025-12-08-someproject.md
   ```

7. **When you want a portfolio view**

   ```bash
   ph projects
   ```

---

## 4. Commands

All commands are run **inside a project repo** (or a subfolder inside it).

### 4.1 Project lifecycle

#### `ph init`

Register the current git repo with `ph`.

```bash
ph init --description "Short description" \
        --stack "python,fastapi,openai" \
        [--name CustomName]
```

* Auto-detects project root via `.git`.
* Stores name, root path, stack, and remote URL (if any).
* Safe to re-run; it will no-op if already initialized.

#### `ph status`

Show the “where am I?” dashboard for this project.

```bash
ph status
```

Displays:

* Project name, path, stack
* Last snapshot (timestamp, status, summary, commit/branch)
* “How to run” commands (label, command, last verified time)
* Top open tasks (status, priority, title)
* Last note summary/link

---

### 4.2 Snapshots

#### `ph snapshot`

Log a snapshot of the current repo state.

```bash
ph snapshot -s "What you did" -t green
```

Arguments:

* `-s, --summary` – short description of the work this snapshot represents.
* `-t, --status` – tag for the state (e.g. `green`, `broken`, `refactor`, `spike`).

Behavior:

* Binds snapshot to current git commit + branch (if git repo).
* Used by `ph status` and `ph projects` to show a recent timeline.

---

### 4.3 Run commands (“How do I run this?”)

#### `ph add-run`

Add or update a “how to run” command for this project.

```bash
ph add-run dev "uv run uvicorn app.main:app --reload" \
  -n "Dev API server on :8000"

ph add-run tests "uv run pytest" \
  -n "Run test suite"
```

Arguments:

* `label` (positional) – short name like `dev`, `tests`, `worker`.
* `command` (positional) – the shell command to run.
* `-n, --notes` – optional notes or context.

If the label already exists, it will be updated and re-verified.

Commands appear in the **“How to run”** section of `ph status`.

---

### 4.4 Tasks (“What’s next?”)

#### `ph add-task`

Add a small task for this project.

```bash
ph add-task "Wire up /health endpoint" -p 1
```

Arguments:

* `title` (positional) – short description.
* `-p, --priority` – `1=high`, `2=medium`, `3=low` (default: `2`).

#### `ph done-task`

Mark a task as done.

```bash
ph done-task 1
```

Arguments:

* `task_id` (positional) – internal ID of the task.

`ph status` shows up to 5 non-done tasks ordered by priority.

---

### 4.5 Notes & LLM convos

#### Convention

Per project, store LLM sessions under the project root, e.g.:

```text
docs/chatgpt/status-dashboard-2025-12-08-someproject.md
docs/claude/pricing-experiments-2025-12-09-someproject.md
```

Each file should start with a manual summary and key decisions, followed by the transcript.

#### `ph add-note`

Attach a note to the project (and latest snapshot).

```bash
ph add-note \
  --type chatgpt \
  --summary "Designed ph status UX + run/task commands" \
  --file docs/chatgpt/status-dashboard-2025-12-08-someproject.md

ph add-note \
  --type claude \
  --summary "Refined pricing experiments" \
  --file docs/claude/pricing-experiments-2025-12-09-someproject.md
```

Arguments (intended):

* `--type, -k` – category (e.g. `chatgpt`, `claude`, `manual`, `decision`, `bug`).
* `--summary, -s` – short description of the note.
* `--file, -f` – optional path to a markdown file with full content.
* `--link, -l` – optional external URL (e.g. ChatGPT conversation link).

`ph status` will show the latest note as a small summary block.

---

### 4.6 Multi-project view

#### `ph projects`

List all projects known to `ph`.

```bash
ph projects
```

Shows:

* Project ID
* Name
* Root path
* Status
* Last snapshot (timestamp + status)
* Last commit summary (short SHA + branch, if available)

---

## 5. Development Notes

Project layout:

```text
project-history/
  pyproject.toml
  src/
    ph/
      __init__.py
      cli.py         # Typer-based CLI entrypoints
      db.py          # SQLite engine + session helpers
      models.py      # SQLModel definitions (Project, Snapshot, RunCommand, Task, Note)
      config.py      # (optional future config)
  .venv/             # uv-managed virtualenv
  uv.lock            # lockfile
  README.md
```

Run tests / local commands (examples):

```bash
# Run ph from source
uv run ph --help

# Reinstall tool if entrypoint/layout changes
uv tool uninstall ph
uv tool install . -e
```

---

## 6. Suggested habits

To get real value from `ph`, enforce these habits:

* **Every active repo:**

  * Run `ph init` once.
* **Every real work session:**

  * End with `ph snapshot` + `ph status`.
* **When you figure out run commands:**

  * Capture them with `ph add-run`.
* **When you decide “what’s next”:**

  * Capture 1–3 items with `ph add-task`.
* **When you use LLMs seriously:**

  * Save the transcript under `docs/chatgpt/` or `docs/claude/`.
  * Attach it with `ph add-note`.

Over time, `ph` becomes the index of your projects’ reality, not just another tool.

