# How to Run This Project in Spyder + MySQL Workbench

**Project:** Biometric-Based Secure Access Mechanism for Cloud Services — Python version, converted from the real Java/JSP source.
**Folder:** `biometric-python-source/`
**Database:** MySQL `Designing` (default). SQLite is the fallback if you do not have MySQL.

This guide assumes you have **Python, Spyder and MySQL Workbench**
installed on Windows (the steps are the same on any computer, with
the folder path changed). No Java, no Tomcat, no Eclipse needed.

---

## Step 0 — What you need before you start

| What | Why | How to check |
|---|---|---|
| Python 3.10 or newer | The app is Python | In Spyder's IPython console: `import sys; print(sys.version)` |
| Spyder | To open and run `app.py` | Open Spyder |
| MySQL Server (running) | The database the app uses | In Workbench: can you connect to `localhost:3306` as `root`? |
| MySQL Workbench | To see the tables and data | Open Workbench |

> **If MySQL is not installed or not running**, use the SQLite
> mode instead — jump to Step 5. The app works the same way.

---

## Step 1 — Unzip the project and open it in Spyder

1. Clone the repo (or download it as a ZIP from GitHub and unzip it)
   to a folder you can find, for example
   `C:\Users\YourName\final-year-project\`.
2. Open **Spyder**.
3. **File → Open** (or Ctrl+O) and open `app.py` from the project
   folder.
4. Also open `config.py` (same folder) — you will edit one line in
   it.

## Step 2 — Install the Python packages (one time only)

In Spyder's **IPython console** (bottom-right pane), type these
lines **one at a time** and press Enter after each:

```python
!pip install flask cryptography pymysql pillow
```

Wait until you see `Successfully installed ...` for each package.
If you see `Requirement already satisfied`, that package is already
installed — that is fine.

> **Why Spyder needs this:** Spyder runs its own Python. Installing
> here puts the packages where Spyder's Python can find them. If you
> install them in a normal Command Prompt instead, Spyder may not see
> them.

## Step 3 — Set your MySQL password in `config.py` (one change only)

Open `config.py` in Spyder. It looks like this:

```python
DB_TYPE = "mysql"          # "mysql" (default) or "sqlite"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"    # ← CHANGE THIS to your own MySQL password
MYSQL_DATABASE = "Designing"
SQLITE_PATH = "app.db"
FLASK_SECRET_KEY = "biometric-python-source-secret"
```

**Change only `MYSQL_PASSWORD`** — replace `"root"` with the password
you use to log in to MySQL Workbench. Do not change anything else.
Save the file (Ctrl+S).

> **How to know your password is right:** open MySQL Workbench and
> connect to `localhost:3306` as `root` with that password. If
> Workbench connects, the app will connect.

## Step 4 — Run `app.py` (F5)

1. Click on the `app.py` tab in Spyder.
2. Press **F5** (or the green ▶ Run button).
3. Spyder may ask "Run the file?" — click **Run**.
4. Watch the **IPython console**. On the first run you will see:

```
Biometric-Based Secure Access Mechanism for Cloud Services (Python/Flask, converted from the real Java/JSP source)
Database: mysql root@localhost:3306/Designing
Open http://127.0.0.1:5000
Demo logins - Owner: Raja/Raja | Client: Harish/Harish | Cloud Server: Server/Server | Trustee: AServer/AServer | Authority: authority/authority
 * Running on http://127.0.0.1:5000
```

That is the app running. **Do not close Spyder while you use the
app** — stopping the run stops the website.

> **What happened on the first run:** the app created the
> `Designing` database, the 10 tables, and the demo data (owners,
> clients, files, results) by itself. You do **not** need to run any
> SQL yourself. If you want to check: in Workbench, refresh the
> Schemas list — `Designing` appears, with tables `owner`, `user`,
> `authority`, `cloud`, `trustee`, `cloudserver`, `authorityfile`,
> `transaction`, `attacker`, `results`.

## Step 5 — Open the app in your browser

Open your browser (Chrome / Edge / Firefox) and go to:

```
http://127.0.0.1:5000
```

You should see the home page: the blue title "Designing Secure and
Efficient Biometric-Based Secure Access Mechanism for Cloud
Services", the five tabs (HOME PAGE / CLIENT / REMOTE SERVER /
AUTHENTICATE SERVER / OWNER), the cloud image slider and the
architecture diagram "The proposed BioCAP. An overview" — the same
look as the original Java site.

> **SQLite mode (no MySQL):** in `config.py` set
> `DB_TYPE = "sqlite"`, save, press F5 again. The console will print
> `Database: SQLite .../app.db`. Everything else is identical.
> Delete `app.db` for a completely fresh start.

---

## Step 6 — Try the full demo (5 minutes)

Do these steps in order — they are the main flow of the project.

### 6.1 Log in as the Owner and upload a file

1. Home → **OWNER** → **Login**. Username `Raja`, password `Raja`
   → **Login**.
2. **Biometric Authentication** page: click **Choose File**, pick any file named `Raja.jpg`, click **Submit**.
   (This is the Owner's fingerprint — the same file the demo
   account was registered with.)
3. You see **"WELCOME TO OWNER :: Raja"**.
4. Owner Menu → **Upload**:
   - **Select File**: pick any small `.txt` file on your computer
     (for example `seed_data/Sample1.txt`) — its text appears in
     the box.
   - **File Name**: type a name, for example `MyFile.txt`.
   - Click **Encrypt** → the confirm page shows the Base64 value
     and the Session Key (a SHA-1 code).
   - Click **Upload** → "Data Uploaded Successfully !!!".
5. **View All Uploaded Files** — your file is listed with Secret
   Key `No` and Access `No`.

### 6.2 Log in as the Trustee and generate the secret key

1. Log out (Owner Menu → Log Out), or open a new browser tab.
2. Home → **AUTHENTICATE SERVER** → **Login**. Username `AServer`,
   password `AServer` → **Login**.
3. Trustee Menu → **Generate Private Key**.
4. Find your file (`MyFile.txt`) and click **Generate Private Key**.
5. **Biometric Authentication**: choose `Raja.jpg` again (the file's
   Owner's fingerprint) → **Submit** → the page shows a real
   12-character secret key for your file, for example `0z0PQWDCSz0v`.
   **Write this key down** — you need it in step 6.4.

### 6.3 Log in as the Cloud Server and give access control

1. Home → **REMOTE SERVER** → **Login**. Username `Server`,
   password `Server` → **Login**.
2. Cloud Menu → **View All Cloud Files**.
3. Find `MyFile.txt` and click **Give Access Control**.
4. **Biometric Authentication**: choose `Raja.jpg` → **Submit** →
   the file's Access becomes **Yes**.

### 6.4 Log in as the Client and download the file

1. Home → **CLIENT** → **Login**. Username `Harish`, password
   `Harish` → **Login**.
2. **Biometric Authentication**: choose
   any file named `Harish.jpg` → **Submit** → "WELCOME
   TO USER :: Harish".
3. Client Menu → **Download**:
   - **File Name**: `MyFile.txt`
   - **Owner Name**: `Raja`
   - Click **Download** → the confirm page shows the file.
   - **Secret Key**: type the 12-character key from step 6.2.
   - Click **Download** → the decrypted file content is shown,
     with a **Download** link to save it.
4. **Try the failure path:** go back and enter a wrong secret key.
   You get "No Secret Key Generated or Secret key is mis Matched
   !!!" — and the attempt is recorded in the `attacker` table
   (Cloud Menu → View All Attackers).

### 6.5 A shortcut with the demo data

The seeded files already have Access = Yes and a secret key. Log in
as `Harish / Harish` (fingerprint `Harish.jpg`), go to **View All
Files**, read the secret key
shown for `DBase.jsp`, then **Download** → File Name `DBase.jsp`,
Owner Name `Raja`, Secret Key = the key you read.

---

## Step 7 — See the data in MySQL Workbench

1. In Workbench, connect to `localhost:3306` as `root`.
2. In the Schemas panel, expand **`Designing`** → Tables.
3. Right-click a table → **Select Rows - Limit 1000**:
   - `owner` — the Owners (Raja, Kannan, …) and any Owner you
     registered. `status` is `Waiting` until the Cloud Server
     authorises them.
   - `user` — the Clients (Harish, Murugesh, …).
   - `cloudserver` — the files: `fname`, `ct` (the encrypted
     content — it looks like random characters), `trapdoor` (SHA-1),
     `sk` (secret key), `rank` (download count), `Access`.
   - `transaction` — every upload and download, with date and time.
   - `attacker` — every wrong-secret-key and wrong-OTP attempt.
   - `results` — time delay and throughput per file (Cloud Menu →
     View File Score Results / View Time Delay Results / View
     Throughput Results).
4. After you register a new Owner/Client in the app, click the
   **refresh** button in Workbench and the new row appears.

> **To start completely fresh:** in Workbench run
> `DROP DATABASE Designing;` and run the app again — it recreates
> everything and re-seeds the demo data. In SQLite mode, just delete
> `app.db`.

---

## Step 8 — Stopping the app

- In Spyder, press the red **■ Stop** button in the IPython
  console, or close Spyder.
- To run it again later, press **F5** on `app.py` — the data is
  still there (MySQL keeps it; `app.db` keeps it in SQLite mode).

---

## Demo logins (all from the original `DATABASE/Database.sql`)

| Role | Username | Password | Fingerprint file |
|---|---|---|---|
| Owner | `Raja` | `Raja` | Any file named `Raja.jpg` |
| Owner | `Kannan` | `Kannan` | `Kannan.png` |
| Owner | `Manjunath` | `Manjunath` | `manjunath.jpg` |
| Owner | `Srini` | `Srini` | `Srini.jpg` |
| Owner | `Kiran` | `Kiran` | `kiran.jpg` |
| Owner | `Rajesh` | `Rajesh` | `Rajesh.png` |
| Client | `Harish` | `Harish` | Any file named `Harish.jpg` |
| Client | `Murugesh` | `Murugesh` | `Murugesh.png` |
| Client | `tmksmanju` | `tmksmanju` | `tmksmanju.jpg` |
| Client | `Lokesh` | `Lokesh` | `Lokesh.jpg` |
| Client | `Saleem` | `Saleem` | `Saleem.jpg` |
| Cloud Server | `Server` | `Server` | — |
| Trustee | `AServer` | `AServer` | — |
| Authority | `authority` | `authority` | — |

New Owners/Clients you register start as **Waiting** — the Cloud
Server must Authorize them first (Cloud Menu → View All Owners and
Authorize / View All Clients and Authorize).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to MySQL at localhost:3306 as user 'root'` / `Access denied (1045)` | Wrong MySQL password, or the server is not running. Test the same password in Workbench first, then check `MYSQL_PASSWORD` in `config.py`. |
| `Can't connect to MySQL server on 'localhost' (2003)` | MySQL server is off. Start it: Windows → Services → MySQL → Start (or restart it from Workbench). |
| `DB_TYPE is 'mysql' but PyMySQL is not installed` | In Spyder's IPython console: `!pip install pymysql`. |
| `ModuleNotFoundError: No module named 'flask'` | Spyder is using a different Python than the one you installed into. In Spyder's IPython console run `!pip install flask cryptography pymysql pillow` (Step 2). |
| Console prints `Database: SQLite .../app.db` (you wanted MySQL) | `DB_TYPE` is still `"sqlite"` in `config.py` — set it to `"mysql"`, save, press F5 again. |
| `Address already in use` / port 5000 busy | An old run is still going. Press the red ■ Stop button in the IPython console, wait 5 seconds, press F5 again. |
| "Sorry Wrong Credentials!" at login | Wrong password, or the account is still `Waiting` (new Owner/Client). The Cloud Server has to Authorize it first. |
| "Finger Print Mismatch, Please Provide Correct Finger Print!!" | The fingerprint file is not the one you registered with. Use a file with the same name (e.g. `Raja.jpg` for the Owner, `Harish.jpg` for the Client). |
| "No Secret Key Generated or Secret key is mis Matched !!!" | The secret key is wrong, or the Trustee has not generated one yet (Secret Key is still `No`). Check the key on View All Files. |
| "No Access Permission For this File !!!" | The Cloud Server has not given access control for the file yet (Access is still `No`). |
| "File Doesn't Exist !!!" | The file name is spelt differently from the uploaded name — check View All Files. |
| The browser shows "This site can't be reached" | The app is not running — press F5 in Spyder and wait for `Running on http://127.0.0.1:5000` in the console, then refresh the browser. |
| Old files unreadable after deleting `instance/fernet.key` | Expected: the Fernet key decrypts the file contents. Delete the database too for a clean start (`DROP DATABASE Designing;` in MySQL, or delete `app.db` in SQLite). |

---

## Screenshots

Screenshots of the running app were taken during development; they are
not included in this repository. The pages they show: home, owner login,
owner main page, owner upload, owner's files, client main page, view all
files, client download, cloud main page, cloud files, file score results,
and trustee generate-key.
