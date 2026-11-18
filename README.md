# Secure and Efficient Biometric-Based Access Control for Cloud Service

[![Python 3](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.x-green)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-Designing-orange)](https://www.mysql.com/)
[![SQLite](https://img.shields.io/badge/SQLite-fallback-lightgrey)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A complete, working **Python (Flask) implementation** of the final-year
project **"Secure and Efficient Biometric-Based Access Control for
Cloud Service"** — converted from the project's original Java/JSP
source code (121 JSP pages, 7 Java files, `DATABASE/Database.sql`).
The backend (JSP scriptlets + JDBC on Tomcat) is replaced by Flask
routes; the frontend is kept exactly as the original.

> **Student demo, not production-secure.** Do not put real fingerprint
> images or real personal data in it. See
> [Honest notes](#honest-notes-and-limitations) and
> [Disclaimer](#disclaimer).

## 1. Project overview

Cloud storage lets anyone upload and share files from anywhere — but
that convenience creates a security problem: once a file is on a
remote server, how do you make sure only the right person can read
it, and how do you prove who accessed it?

This project answers that with **two-factor, role-based access
control**:

1. **Something you know** — a password.
2. **Something you are** — a fingerprint image, checked at login and
   again before a secret key is issued or a file is downloaded.

A file is never handed over on a single login. It moves through a
chain of four independent checks — **Owner → Trustee → Cloud Server
→ Client** — and every failed attempt is recorded as an attack. The
result is a small, complete model of how a cloud service can protect
files with biometric authentication and per-file secret keys.

### Problem statement

In a cloud environment, files are stored on servers the user does not
control. Password-only logins are routinely stolen or guessed, and a
single compromised account can expose every file that account can
see. This project adds a second, biometric factor and splits the
power to release a file across three separate roles, so no single
account — not even the file's owner — can hand a file to a client
alone.

### Objectives

- Build a cloud file-sharing system where every download needs a
  **password + fingerprint + per-file secret key**.
- Separate duties across five roles so that upload, key generation,
  access approval and download are done by different parties.
- Encrypt every stored file so that even direct database access does
  not reveal its contents.
- Detect and log misuse: wrong passwords, wrong fingerprints, wrong
  secret keys and wrong OTPs are all recorded as attacker activity.
- Deliver the system as a runnable Python web application with MySQL
  as the primary database and SQLite as a zero-setup fallback.

## 2. How it works

### The five roles

| Role | What it does |
|---|---|
| **Owner** | Registers with a fingerprint, uploads files, sees who requested them |
| **Client** | Registers with a fingerprint, requests files, downloads with a secret key |
| **Trustee** | Verifies the client's fingerprint, then generates the file's secret key |
| **Cloud Server** | Authorises owners and clients, controls access, views transactions, attackers and results |
| **Authority** | Fixed system login; views requests and permits downloads |

### End-to-end flow (demo: Raja → Harish)

```
Owner (Raja) registers + fingerprint
        │  uploads a file (file is encrypted before it is stored)
        ▼
Client (Harish) registers + fingerprint
        │  searches for the file, requests it
        ▼
Trustee verifies Harish's fingerprint
        │  generates a random 12-character secret key
        ▼
Cloud Server authorises the access
        │  Authority permits the download
        ▼
Harish downloads with the secret key → file is decrypted
```

Any wrong step — a wrong password, a wrong fingerprint image, a
wrong secret key, a wrong OTP — stops the flow and is written to the
`attacker` table with the time and the type of failure.

### Authentication, step by step

1. **Registration** — Owner/Client signs up with name, email, mobile,
   address and a fingerprint image upload. The account starts in
   `Waiting` status until the Cloud Server authorises it.
2. **Login** — Password check, then a fingerprint check (upload the
   fingerprint image again). Clients then complete an **OTP step**.
3. **File request** — A client searches the file list and requests a
   file. The request waits for the Trustee.
4. **Key generation** — The Trustee checks the client's fingerprint
   once more and generates the file's secret key.
5. **Access control** — The Cloud Server authorises the owner/client
   and the Authority permits the download.
6. **Download** — The client enters the secret key; the file is
   decrypted with Fernet and downloaded.

## 3. Features

- **5 roles** with separate logins, dashboards and permissions
- Owner / Client registration with profile picture + fingerprint upload
- Login with **password + fingerprint**, plus an **OTP step** for clients
- File upload with **Fernet encryption** before storage, decrypt on download
- **Secret-key generation** by the Trustee (random 12-character key)
- Access control by the Cloud Server; download permission by the Authority
- **Attacker logging** for wrong login / fingerprint / secret key / OTP
- Transaction, results and attacker views for the Cloud Server
- Session key shown as a SHA-1 digest of the file content (as in the original)
- **MySQL first** (database `Designing`), **SQLite fallback** with zero setup
- 46 Flask routes, 10 database tables, same table names and columns as the original

## 4. System architecture

```
                    ┌─────────────┐
                    │  Web browser │
                    └──────┬──────┘
                           │ HTTP
                    ┌──────▼──────┐
                    │  Flask app   │  app.py — 46 routes
                    │  (app.py)    │  sessions, crypto, OTP
                    └──────┬──────┘
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  MySQL   │ │ SQLite   │ │  Fernet  │
        │ Designing│ │ app.db   │ │  AES-128 │
        │ 10 tables│ │ fallback │ │  + HMAC  │
        └──────────┘ └──────────┘ └──────────┘
```

### Database design (10 tables, database `Designing`)

| Table | Purpose |
|---|---|
| `owner` | File owners: login, hashed password, fingerprint image + file name, status |
| `user` | Clients: login, hashed password, fingerprint image + file name, status, OTP |
| `authority` | Fixed Authority login |
| `cloud` | Fixed Cloud Server login |
| `trustee` | Fixed Trustee (Authentication Server) login |
| `cloudserver` | Cloud Server's record of files and access decisions |
| `authorityfile` | Files awaiting / granted Authority permission |
| `transaction` | Every file request, key issue and download |
| `attacker` | Failed logins, fingerprints, secret keys and OTPs |
| `results` | Outcome records shown on the Cloud Server dashboard |

Schemas are in [`schema_mysql.sql`](schema_mysql.sql) (MySQL) and
[`schema.sql`](schema.sql) (SQLite). The app creates the database,
tables and demo data by itself on first run.

### Security design

| Concern | How this project handles it |
|---|---|
| File contents | **Fernet-encrypted** in the database (AES-128-CBC + HMAC); decrypted only on a permitted download |
| Secret key | Random 12-character key, generated by the Trustee per file |
| Passwords | Hashed with werkzeug PBKDF2 (owner / client accounts) |
| SQL injection | **Parameterised queries** everywhere |
| Login state | Per-user Flask session cookie (the original had one global login for everyone) |
| Misuse | Failed attempts logged in the `attacker` table with timestamp and failure type |
| Fingerprint | Matched by uploaded file **name or identical file bytes** |

## 5. Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Web framework | Flask 3 |
| Database | MySQL (`Designing`) or SQLite (`app.db`, fallback) |
| DB driver | PyMySQL |
| Encryption | `cryptography` (Fernet — AES-128-CBC + HMAC) |
| Passwords | werkzeug PBKDF2 hashing (owner / client accounts) |
| Frontend | Original 2011 HTML/CSS/JS templates, unchanged |
| Fingerprint images | Pillow (synthetic demo patterns when the originals are absent) |

## 6. Project structure

```
.
├── app.py                  # The whole web app (46 Flask routes, DB, crypto)
├── config.py               # All settings: DB_TYPE, MySQL password, secret key
├── requirements.txt        # Flask, cryptography, PyMySQL, Pillow
├── schema.sql              # SQLite schema (10 tables)
├── schema_mysql.sql        # MySQL schema (database `Designing`, 10 tables)
├── static/                 # Original CSS / JS (unchanged)
├── templates/              # Original JSP pages as Jinja templates (unchanged)
├── seed_data/              # Demo files (Note1.txt, Sample1.txt)
├── .vscode/                # VS Code launch configs (SQLite + MySQL)
├── CODE_EXPLANATION.md     # How each part of the Python code maps to the Java
├── FRONTEND_NOTE.md        # Which JSP page became which template
├── SPYDER_MYSQL_GUIDE.md   # Spyder + MySQL run guide
├── VSCODE_GUIDE.md         # VS Code run guide (Windows + Anaconda)
└── CONTRIBUTING.md
```

**What is not in this repository:** the original Java/JSP source
code — this repo contains the Python implementation only, as
requested. The original template image assets (`static/images/`) and
the original fingerprint sample images are also not included, because
this upload carries text files only. The app still runs without them:
the pages load with plain styling, and demo fingerprint images are
generated automatically on first run (see
[Demo logins](#7-demo-logins)). To restore the full original look,
drag the `static/images/` folder into the repo on github.com.

## 7. Demo logins

All demo accounts come from the original `DATABASE/Database.sql`
(password = name).

| Role | Username | Password | Fingerprint |
|---|---|---|---|
| Owner | `Raja` | `Raja` | Upload any file named `Raja.jpg` |
| Client | `Harish` | `Harish` | Upload any file named `Harish.jpg` |
| Cloud Server | `Server` | `Server` | — |
| Trustee | `AServer` | `AServer` | — |
| Authority | `authority` | `authority` | — |

Other demo owners: Kannan, Manjunath, Srini, Kiran, Rajesh.
Other demo clients: Murugesh, tmksmanju, Lokesh, Saleem.

The fingerprint check matches the uploaded file's **name** (or
identical file bytes) against the stored fingerprint, exactly as the
original did. If the original fingerprint image files are added to
`seed_data/biometric_images/`, they are used as the stored
fingerprints; otherwise the app generates a synthetic fingerprint
pattern for each demo account on first run.

## 8. Quick start

```bash
# 1. Get the code
git clone https://github.com/Venupeetha/Secure-and-Efficient-Biometric-Based-Access-Control-for-Cloud-Service.git
cd Secure-and-Efficient-Biometric-Based-Access-Control-for-Cloud-Service

# 2. Install the packages (use `python -m pip`, never bare `pip`)
python -m pip install -r requirements.txt

# 3. Run it — SQLite mode needs no setup at all
python app.py
# open http://127.0.0.1:5000
```

For MySQL instead: set your MySQL root password in `config.py`
(`MYSQL_PASSWORD`) and run the same `python app.py` — the app creates
the `Designing` database, its tables, and the demo data by itself.
Full steps, including VS Code + Anaconda setup, are in
[**VSCODE_GUIDE.md**](VSCODE_GUIDE.md), and Spyder + MySQL steps in
[**SPYDER_MYSQL_GUIDE.md**](SPYDER_MYSQL_GUIDE.md).

## 9. Testing

- **39/39 live checks passed** in SQLite mode: the full
  Raja → Trustee → Cloud Server → Harish download flow, plus
  wrong-login, wrong-fingerprint, wrong-secret-key and wrong-OTP
  attacker paths.
- **MySQL mode verified live** on MariaDB 10.11: the app created the
  `Designing` database itself with all 10 tables, seeded 6 owners +
  5 clients, and Owner login (Raja/Raja) reached the fingerprint step.
- **Known fix (2026-11-12):** the original schema used
  `password VARCHAR(45)`, but a hashed password is ~160 characters,
  so MySQL refused the first seeded row (`Data too long for column
  'password'`). The schemas here use `VARCHAR(255)`, and `app.py`
  automatically widens the column on databases created with the old
  schema.

## 10. What was converted — and honest notes

The original project was Java/JSP on Tomcat + MySQL. Its backend was
replaced by Flask; its frontend templates were kept unchanged. The
original source was used as the reference for this conversion and is
not included in this repository (Python files only).

| | Original (Java/JSP) | This version (Python/Flask) |
|---|---|---|
| File content | Stored as **plain text**; an AES cipher object was created but never used | **Fernet-encrypted** in the database, decrypted on download |
| Secret key | A Java object-reference string, not a usable key | Random 12-character key generated by the Trustee |
| Passwords | Plain text | Hashed with werkzeug PBKDF2 (owner / client) |
| Fingerprint | Compared only by uploaded file **name** | File name **or** identical file bytes. **Still no minutiae extraction** — this is not real biometric recognition |
| OTP | Could never run — the OTP page and `user.otp` column did not exist in the source | Repaired: OTP is generated at login and shown on the OTP page (no SMS/email in the original) |
| Login state | One global login for everyone | Per-user Flask session cookie |
| SQL | String-concatenated queries (SQL-injection prone) | Parameterised queries everywhere |

### Honest notes and limitations

- **This is not real biometric recognition.** Fingerprint matching
  here is a file-name / identical-bytes comparison — the original
  did the same. There is no minutiae extraction and no fuzzy
  matching, so do not present it as a biometric recognition system
  in a viva; present it as a fingerprint-*gated* access demo.
- **No accuracy claims.** This is not a machine-learning project —
  there is no accuracy / R² figure to report, and the paper's claims
  are not repeated here as verified.
- The demo fingerprint images are synthetic patterns when the
  originals are absent (see §7).
- See `CODE_EXPLANATION.md` for the full mapping of Python code to
  the original Java.

## 11. Future scope

- Replace file-name fingerprint matching with real minutiae-based
  matching (e.g. a fingerprint SDK) for a production system.
- Deliver the OTP by SMS/email instead of showing it on the page.
- Add HTTPS, rate limiting and account lockout after repeated
  failures.
- Move file storage from the database to encrypted object storage.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). One feature per PR, keep the
frontend unchanged, and keep the demo flow working.

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

Student demo for learning and viva purposes only. It is not
production-secure: the Flask dev server, the fixed demo logins, and
the demo fingerprint images must not be used with real people or real
data.
