Here is a comprehensive `README.md` file for the `ph` (Project History) repository, based on the development logs, usage examples, and source code excerpts provided.

***

# ph (Project History)

**ph** is a CLI tool designed to solve the problem: *"Where am I on this project? What does it do? How do I run it? And where is the LLM conversation that told me how to build it?"*

It creates a local database to track development context, run commands, task priorities, and AI conversation logs, bridging the gap between your Git commit history and your mental state.

## Features

*   **Context Awareness:** Tracks project description and tech stack info alongside the code.
*   **Snapshots:** Logs development milestones with summaries and status colors (e.g., green/red). Automatically links to the current Git commit hash and branch.
*   **Runbook:** Saves "How to run" commands (e.g., dev servers, test suites) so you never forget the entry points.
*   **Task Management:** Lightweight, priority-based todo list directly in your terminal.
*   **LLM Documentation:** Standardized templates for saving conversations with AI assistants (ChatGPT, Claude, etc.) directly into your project file structure.

## Installation

**ph** is built with Python and managed using `uv`.

### Prerequisites
*   Python 3.x
*   [uv](https://github.com/astral-sh/uv) (recommended)

### Local Development Setup
```bash
# Clone the repository
git clone <repo-url>
cd project-history

# Install dependencies
uv sync
# OR manually add dependencies
uv add sqlmodel typer rich gitpython
```
*[Source: 3, 4]*

## Usage

### 1. Initialization
Navigate to your project root and initialize the `ph` database. You can optionally specify the stack and description immediately.
```bash
ph init --description "My MVP" --stack "python,fastapi,openai"
```
*[Source: 14, 21]*

### 2. Checking Status
The `status` command is your dashboard. It displays the project info, the last recorded snapshot, a table of saved run commands, and your top priority tasks.
```bash
ph status
```
*[Source: 16, 23]*

### 3. Recording Snapshots
When you reach a stopping point or a milestone, save a snapshot. If you are in a Git repository, `ph` automatically captures the commit hash and branch.
```bash
# -s for summary, -t for status tag (e.g., green, yellow, red)
ph snapshot -s "Completed validation loop" -t green
```
*[Source: 19, 22]*

### 4. Managing "Run" Commands
Stop searching through shell history for start commands. Save them to the project context:
```bash
# Usage: ph add-run <label> "<command>" -n "<description>"
ph add-run dev "uv run uvicorn app.main:app --reload" -n "Start Dev Server"
ph add-run tests "uv run pytest"
```
These will appear in a "How to run" table when you check `ph status`. [Source: 17, 24]

### 5. Task Tracking
Keep a prioritized list of immediate next steps.
```bash
# Add a task with priority 1 (High)
ph add-task "Wire up /health endpoint" -p 1

# Mark a task as done by ID
ph done-task 1
```
*[Source: 26, 29]*

### 6. LLM Conversation Logging
Standardize how you save AI pair-programming logs. This command generates a templated markdown file in your `docs/` folder.
```bash
ph add-note --type chatgpt --summary "Database Schema" --file docs/chatgpt/2025-12-08-db-schema.md
```
**The Template Structure:**
The command generates files with the following headers to ensure consistency:
*   **SUMMARY:** Brief overview of the chat.
*   **KEY DECISIONS:** What was actually decided or changed.
*   **FULL LLM CONVO:** The raw conversation log.
*[Source: 1]*

## Tech Stack
*   **Typer:** CLI interface construction.
*   **Rich:** Beautiful terminal formatting (tables, rules, colors).
*   **SQLModel:** Database interaction (SQLite).
*   **GitPython:** Automatic Git context detection.

## License
[License Information Here]