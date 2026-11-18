# Run in VS Code — Biometric Secure Access (Python / Flask)

This guide is written for **VS Code on Windows with Anaconda Python**.
The project folder lives on the OneDrive Desktop, e.g.

```
C:\Users\venup\OneDrive\Desktop\final-year-project
```

> ⚠️ **There is more than one Python on this machine** — Anaconda Python
> and a standalone Python 3.12 install. Almost every "it still shows the
> error" problem comes from installing packages into one Python while
> VS Code runs the code with the other one. Step 2 below fixes that.

---

## 1. Open the project

1. Extract the zip (if you downloaded it) and open the folder in VS Code:
   **File → Open Folder** → pick the project folder.
2. When VS Code asks *"Do you trust the authors of the files in this
   folder?"* click **Yes, I trust the authors**.

## 2. Pick the right Python interpreter (do this FIRST)

1. Press `Ctrl+Shift+P`
2. Type **Python: Select Interpreter** and press Enter.
3. Pick the **Anaconda** one — its path looks like:

```
C:\Users\venup\anaconda3\python.exe
```

   Do **NOT** pick `C:\Users\venup\AppData\Local\Programs\Python\Python312\python.exe`
   (the standalone Python 3.12) unless you install the packages there too.
4. Check the bottom-right of the VS Code window: it should now show the
   Anaconda Python version.

## 3. Install the packages (in the VS Code terminal)

Open a terminal in VS Code: **Terminal → New Terminal**, then run:

```bash
python -m pip install -r requirements.txt
```

Always use `python -m pip ...` — never bare `pip` — so the packages go
into the Python VS Code is actually using.

Verify it worked:

```bash
python -m pip show flask
```

You should see `Name: Flask` and a version number. If it says
`WARNING: Package(s) not found`, you are in the wrong interpreter —
go back to step 2 and pick the other Python, then run the install again.

## 4. Choose the database

### Option A — SQLite (easiest, no setup) ⭐ recommended first run

No MySQL needed. Either:

- Press **F5**, then pick **"Run (SQLite, no setup)"** from the list, or
- In the terminal:

```bash
python app.py
```

  with `DB_TYPE=sqlite` set (the F5 config does this for you).
  The app creates `app.db` itself on first run.

### Option B — MySQL (the real database for this project)

1. Make sure MySQL is running (MySQL Workbench / MySQL Server installed).
2. Open `config.py` and set `MYSQL_PASSWORD` to **your own** MySQL root
   password (the one you set when you installed MySQL). Do not share this
   file with your real password in it.
3. Press **F5**, then pick **"Run (MySQL)"**, or in the terminal:

```bash
python app.py
```

   The app creates the `Designing` database and its 10 tables by itself
   on first run and seeds the demo data. (You can also run
   `schema_mysql.sql` in MySQL Workbench first — same result.)

## 5. Open the app

When the terminal shows:

```
Open http://127.0.0.1:5000
```

open **http://127.0.0.1:5000** in your browser.

## 6. Try the demo flow

| Step | Who | Login | Fingerprint file |
|------|-----|-------|------------------|
| 1. Owner uploads a file | Owner | `Raja` / `Raja` | `Raja.jpg` |
| 2. Trustee generates the secret key | Trustee | `AServer` / `AServer` | — |
| 3. Cloud Server gives access | Cloud Server | `Server` / `Server` | — |
| 4. Client downloads with the key | Client | `Harish` / `Harish` | `Harish.jpg` |
| 5. Authority (fixed login) | Authority | `authority` / `authority` | — |

Full demo accounts (password = name): owners Raja, Kannan, Manjunath,
Srini, Kiran, Rajesh; clients Harish, Murugesh, tmksmanju, Lokesh, Saleem.
For the fingerprint step, upload any file named e.g. `Raja.jpg` (Owner) or `Harish.jpg` (Client).

Demo order: **Raja uploads → Trustee generates key → Cloud gives access
→ Harish downloads.**

## 7. Stop the app

Click in the VS Code terminal and press `Ctrl+C`.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'flask'` | Flask was installed into a different Python than the one VS Code is using | Pick the Anaconda interpreter (step 2), then run `python -m pip install -r requirements.txt` again in the VS Code terminal. Check with `python -m pip show flask`. |
| `pymysql.err.DataError: (1406, "Data too long for column 'password'")` | You are running the **old** zip from before 2026-11-12 | This repo already contains the fix (password column widened to `VARCHAR(255)` + an automatic `ALTER` on start). Re-download this repo/zip — do not use the old one. |
| `... port 5000 is already in use` | The app is already running in another terminal | Stop the other one (`Ctrl+C`), or close the extra VS Code terminal. |
| MySQL: `Access denied for user 'root'` | Wrong password in `config.py` | Put your real MySQL root password in `MYSQL_PASSWORD` in `config.py`. |
| MySQL: `Can't connect to MySQL server` | MySQL is not running | Start MySQL (Services → MySQL, or open MySQL Workbench and connect once). Or use the SQLite launch config instead — no MySQL needed. |
| Page shows "Waiting" after register/login | New accounts start as **Waiting** until authorised | That is the original design: the Authority / Cloud Server authorises owners and clients before they can use the system. |
| Wrong password / wrong fingerprint / wrong secret key | Deliberate test | The app logs these as **attackers** (see the Cloud Server → Attackers page). That is the security feature working, not a bug. |

Still stuck? Take a photo of the **last lines** of the terminal
(the very last error line matters most) and send it — that is enough
to diagnose the problem.
