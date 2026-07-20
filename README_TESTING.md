Local testing and setup

Follow these steps to run tests locally on a Windows machine.

1) Create and activate a virtual environment

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

2) Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3) Apply alembic migrations (uses DATABASE_URL from env; for local tests we use sqlite)

```powershell
set DATABASE_URL=sqlite:///./test.db
python -m alembic upgrade head
```

4) Run tests

```powershell
pytest -q
```

Notes
- If `python` is not on PATH, install Python 3.10+ or use the Microsoft Store alias settings.
- CI runs tests in Ubuntu and installs dependencies from `requirements.txt` automatically.
