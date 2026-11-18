# Code Explanation — Biometric Secure Access (Python / Flask, converted from the real Java/JSP source)

Source zip: `Secure_and_efficient_biometric-based_secure_access_mechanism_for_cloud_services.zip`
(15 MB, 381 files). Converted: 2026-11-11.

This file explains the Python code file by file and function by
function, maps every original JSP page to its Python route, translates
the 7 Java files, and records the differences from the earlier
reconstruction (`~/workspace/biometric-python/`).

## 1. How the whole thing fits together

```
Browser ──HTTP──► Flask app (app.py)
                     │  templates/ (Jinja2 pages, same look as the JSPs)
                     │  static/    (original CSS / JS / images)
                     │
                     ├─► MySQL (default) — database `Designing`
                     │   config.py: DB_TYPE="mysql", localhost:3306, root/<your password>
                     │   Created on first run from schema_mysql.sql
                     │
                     └─► SQLite (fallback) — app.db in the project folder
                         config.py: DB_TYPE="sqlite"
                         Created on first run from schema.sql
```

All SQL goes through two helpers in `app.py`: `q()` (a query) and
`exec_sql()` (an INSERT / UPDATE / DELETE). Both call
`_translate_sql()` first, which converts SQLite-style SQL
(`?` placeholders, `"transaction"` table name) into MySQL SQL
(`%s` placeholders, `` `transaction` ``) when the MySQL backend is
active. That is the whole "one code path, two databases" trick.

Startup (`if __name__ == "__main__"`) calls `init_db()`, which:
1. creates the `Designing` database (MySQL) or `app.db` (SQLite),
2. creates the 10 tables from the schema,
3. seeds the demo data (owners, users, fixed logins, files, results,
   transactions, attackers) **only if the tables are empty**,
4. creates the Fernet key in `instance/fernet.key` if it does not
   exist,
5. prints the database in use and the demo logins.

`init_db()` is idempotent — running the app a second time does not
duplicate the seed data.

---

## 2. File-by-file — what each file is

| File | Lines | Purpose |
|---|---|---|
| `app.py` | 1,451 | The entire web application: database layer, crypto helpers, all routes, seed data, and the dev-server entry point. Routes are grouped by role (index, owner, client, cloud, trustee, authority) |
| `config.py` | 43 | One place for all settings: `DB_TYPE = "mysql"` (default) or `"sqlite"`, `MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE = "Designing"`, `SQLITE_PATH`, `FLASK_SECRET_KEY`, upload limits, the Fernet key path. **This is the only file the user edits** |
| `schema.sql` | 98 | SQLite schema: 10 tables, exactly as `DATABASE/Database.sql` (INTEGER PRIMARY KEY AUTOINCREMENT, BLOB for the pictures) |
| `schema_mysql.sql` | 106 | Same 10 tables for MySQL (INT AUTO_INCREMENT PRIMARY KEY, LONGBLOB for the pictures, `` `transaction` `` backticked) |
| `requirements.txt` | — | Flask ≥ 3.0, cryptography ≥ 42, PyMySQL ≥ 1.1, Pillow ≥ 10.0 |
| `templates/` | 27 files | Jinja2 pages rebuilt from the original JSP pages — see §8 |
| `static/` | CSS + JS | The original CSS/JS (template image assets are not included in this repo — see README §6) |
| `seed_data/` | — | `Sample1.txt`, `Note1.txt` (sample resource files). The original fingerprint sample images are not included in this repo; the app generates synthetic fingerprint patterns on first run (see README §7) |
| `README.md` | — | Run guide, demo logins, flows, testing, troubleshooting |
| `SPYDER_MYSQL_GUIDE.md` | — | Step-by-step Spyder + MySQL Workbench guide with screenshots |
| `FRONTEND_NOTE.md` | — | What was kept unchanged in the frontend, and what had to change |

---

## 3. `app.py` — the database layer

```python
def get_conn():
    # MySQL: pymysql.connect(host, port, user, password, db, charset="utf8mb4")
    # SQLite: sqlite3.connect(SQLITE_PATH)  +  conn.row_factory = sqlite3.Row
```

`q(sql, params=(), one=False)` — runs a SELECT and returns a list of
dict-like rows (or one row, or `None` if nothing matched — this was
the bug fixed during testing: it used to crash with `IndexError` on
an empty result). `exec_sql(sql, params=())` — runs an INSERT /
UPDATE / DELETE, commits, and returns the new row id.

`_translate_sql(sql)` — the SQLite → MySQL translator:
- `?` → `%s`
- `"transaction"` → `` `transaction` ``
- `CAST(x AS INTEGER)` → `CAST(x AS SIGNED)` (not needed here — the
  `results` values are stored as plain text in this app, as in the
  original, which is why the results pages sort in Python)

`init_db()` — creates the database + tables + seed data (see §1).
The schema loader reads `schema_mysql.sql` / `schema.sql`, strips
`--` comment lines first (a bug fixed during testing: the leading
`--` comment block made the first `CREATE TABLE` statement get
skipped), splits on `;`, and runs each statement.

---

## 4. `app.py` — encryption and the fingerprint check

```python
def _fernet():
    # Loads instance/fernet.key (creates it on first run).
    # Returns None if cryptography is not installed.
```

`encrypt_content(text)` — Fernet-encrypts the file content (AES-128-CBC
+ HMAC-SHA256). If `cryptography` is missing, it falls back to
Base64-only encoding and prints a warning at startup (exactly the
original's storage behaviour).

`decrypt_content(value)` — the reverse; if the value is not a Fernet
token, it falls back to Base64-decoding, then to returning the value
as-is.

```python
def _sha1(text):
    # hashlib.sha1(text.encode()).hexdigest() — the trapdoor / session key
    # (Upload1.jsp used MessageDigest SHA1 for the same thing)
```

```python
def _fingerprint_match(uploaded_filename, uploaded_bytes, thumbname, thumbbytes):
    # True if the uploaded file has the SAME NAME as the stored fingerprint
    # (the original's only check), OR if its bytes are identical to the
    # stored fingerprint image. This is what "fingerprint matching" is in
    # this demo: no minutiae extraction, no fuzzy extractor.
```

**Owner/user passwords** are stored with
`werkzeug.security.generate_password_hash` (PBKDF2-SHA256) and checked
with `check_password_hash`. The seed accounts are hashed at seed time
(password = name). The three fixed system logins (authority, cloud,
trustee) stay plain text, exactly as in the original.

**Per-user sessions**: each role stores its logged-in name in the
Flask session cookie (`session["owner"]`, `session["user"]`,
`session["cloud"]`, `session["trustee"]`, `session["authority"]`),
checked by `_require(session, role)` before a role's pages are shown.
The original used one global `application` login for everyone — this
is one of the deliberate security improvements.

---

## 5. `app.py` — the flows, in code order

### 5.1 Index / home (`GET /`)

Renders `index.html`: the original title, the five tabs, the cloud
image slider (3 images), the "The proposed BioCAP. An overview"
architecture diagram, the short project description, the demo
logins, and a note explaining how the demo fingerprint step works (upload
any file named e.g. `Raja.jpg`). The original home page had **no**
login forms on it (login links were in the menu) — same here.

### 5.2 Owner (Authenticate Server) — register, login, fingerprint, main, upload, files, transactions

- `GET/POST /owner/register` — `O_Register.jsp` → `o_InsertData.jsp`.
  Reads `userid, pass, email, mobile, address, dob, gender, pincode`
  and the two uploads `pic` (profile picture) and `pic2`
  (fingerprint). A duplicate name is rejected ("Owner Name Already
  Exist"), exactly as `o_InsertData.jsp` did. Inserts the owner with
  `status = "Waiting"`. Flashes "Registered Successfully".
- `GET/POST /owner/login` — `AuthorityLogin.jsp` →
  `DO_Authentication.jsp`. Checks the password, then checks
  `status`. `Waiting` → `wronglogin.html` (the same message as the
  original: "Sorry, You are in Waiting state !!!" for an
  unauthorised owner). On success: stores `session["owner"]` and
  redirects to `/owner/biometric`.
- `GET/POST /owner/biometric` — `Owner_BioIdentification.jsp` →
  `OBioIdentiry.jsp`. Shows the fingerprint form (file input `pic2`
  + Submit). On POST, compares the uploaded file with the owner's
  stored `thumbname`/bytes (`_fingerprint_match`). Match → Owner
  main page; mismatch → the mismatch message and a link back to the
  login.
- `GET /owner/` — `AuthorityMain.jsp`. "WELCOME TO OWNER ::
  `<name>`", Owner menu (Upload / View All Uploaded Files / View
  All Transactions / Log Out).
- `GET/POST /owner/upload` — `Upload.jsp`. File chooser `t42`
  (loads the file's text into the textarea via JavaScript), File
  Name `tt`, content textarea, Session Key `t4` (read-only,
  auto-filled with a random key). If a file with that name already
  exists for this owner, it is rejected (the original
  `Upload.jsp`/`Upload1.jsp` inserted a duplicate row silently — the
  rejection is a deliberate, small improvement).
- `GET/POST /owner/upload1` — `Upload1.jsp`. Computes the SHA-1
  trapdoor and the Base64 value and shows them on the confirm page
  (the same two values `Upload1.jsp` displayed).
- `GET/POST /owner/upload2` — `Upload2.jsp`. Stores the file in
  **both** `cloudserver` and `authorityfile` with `ct` =
  Fernet-encrypted content, `trapdoor` = SHA-1, `sk = "No"`,
  `rank = 0`, `Access = "No"`, `dt` = now; inserts a `transaction`
  row (`task = "Upload"`) and a `results` row (`tdelay` /
  `tpt` are generated here — the original generated them the same
  way in `Upload2.jsp`). Flashes "Data Uploaded Successfully !!!".
- `GET /owner/files` — `ViewAllAuthorityFiles.jsp`. Table of the
  owner's files: File Name, Secret Key, File Owner, Rank, Date &
  Time.
- `GET /owner/transactions` — `ViewAllTransactions.jsp`. All
  transaction rows.
- `GET /owner/logout` — clears the session.

### 5.3 Client (End User) — register, login, fingerprint, main, files, download, OTP

- `GET/POST /client/register` — `ClientRegister.jsp` →
  `c_InsertData.jsp`. Same fields as the owner; duplicate name
  rejected; status starts `Waiting`.
- `GET/POST /client/login` — `ClientLogin.jsp` →
  `DU_Authentication.jsp`. Password + `Waiting` check, then the
  fingerprint page.
- `GET/POST /client/biometric` — `Client_BioIdentification.jsp` →
  `UBioIdentiry.jsp`. Fingerprint name/bytes check against the
  client's stored fingerprint. Match → Client main page.
- `GET /client/` — `ClientMain.jsp`. "WELCOME TO USER ::
  `<name>`".
- `GET /client/files` — `View_All_Files.jsp`. **All** files in
  `cloudserver`: File Name, Session Key (trapdoor), Private Key
  (secret key), Rank, Date & Time, Access Authorization, File
  Owner. This is where the user reads a file's secret key.
- `GET/POST /client/download` — `Download.jsp`. Fields: File Name
  `t1`, Owner Name `t22`. (The original's first step; the secret
  key was only asked on the next page.)
- `POST /client/download1` — `Download1.jsp`. Checks that some file
  with that name has Access = `Yes`; if none does, shows "No Access
  Permission For this File !!!". Otherwise shows the file + secret
  key and the secret-key form.
- `POST /client/download2` — `Download2.jsp`. The full check, in
  the original's order:
  1. `Access = "Yes"` for the file, **and** `sk` matches the entered
     key, **and** `sk != "No"` → `rank = rank + 1`, Base64-decodes /
     Fernet-decrypts the content, shows it with a Download link, and
     logs a `transaction` row (`task = "Downloaded"`).
  2. `sk` wrong or `sk = "No"` → inserts an `attacker` row and
     shows "No Secret Key Generated or Secret key is mis Matched !!!".
  3. `Access = "No"` → "No Access Permission For this File !!!".
- `GET /client/download-file/<id>` — the Download link: returns
  the decrypted content as a file download.
- `GET/POST /client/otp` — `ClientAuthentication.jsp`. Name +
  password; on success generates a 6-digit OTP, stores it in the
  session, and shows it on the page. **The original could not run
  this flow at all**: `ClientOTP.jsp` is missing from the zip and
  `user.otp` does not exist in `Database.sql`. Here the OTP is
  shown on the page because the original had no SMS or email to
  send it with.
- `POST /client/otp-check` — `OTPCheck.jsp`. Correct OTP →
  Client main page. Wrong OTP → inserts an `attacker` row
  ("OTP Attacker") and shows the wrong-OTP page.
- `GET /client/logout` — clears the session.

### 5.4 Cloud Server (Remote Server) — login, authorise, files, access control, transactions, attackers, results

- `GET/POST /cloud/login` — `CloudLogin.jsp` →
  `CAuthentication.jsp`. Fixed login `Server / Server`.
- `GET /cloud/` — `CloudMain.jsp`. "WELCOME TO CLOUD :: Server".
- `GET /cloud/owners` — `ViewClients.jsp`. Owners table with
  Details, Status (Authorised / Waiting), Authorize, and
  View All Cloud Files.
- `GET /cloud/clients` — `D_ViewOwners.jsp`. The same for users
  (clients). (The original names are confusing — `ViewClients.jsp`
  lists **owners**, `D_ViewOwners.jsp` lists **users** — kept as
  is, with a comment in the code.)
- `GET /cloud/authorize-owner/<id>` / `/cloud/authorize-client/<id>`
  — `C_StatusClient.jsp` / `C_StatusOwner.jsp`. Sets
  `status = "Authorized"`.
- `GET /cloud/owner-details?id=<id>` / `/cloud/client-details?id=<id>`
  — `C_OwnerDetails.jsp` / `C_ClientDetails.jsp`. Full details +
  the profile picture and the fingerprint image.
- `GET /cloud/files` — `ViewAllCloudFiles.jsp`. Files with Session
  Key, Private Key, Rank, Date & Time, Access Authorization, File
  Owner, and Give Access Control.
- `GET/POST /cloud/access/<id>` — `C_Access_Control.jsp` →
  `FileBioIdentiry.jsp`. Shows the file; on POST, an Owner's
  fingerprint check (file name or bytes vs the owner's stored
  fingerprint) sets `Access = "Yes"`.
- `GET /cloud/transactions` — `ViewAllCloudTransactions.jsp`.
- `GET /cloud/attackers` — `ViewAllAttackers.jsp`. Attacker Name,
  File Name, Secret Key Used, Date & Time. (`AViewOTP.jsp` was
  supposed to be the same page but is broken in the original — its
  JDBC-ODBC connection targets a different database and different
  columns; this route replaces it.)
- `GET /cloud/results` — `ViewResults.jsp` / `Results.jsp`.
  `results` table: File Name, Time Delay, Throughput.
- `GET /cloud/results-td` — `C_ViewTDResults.jsp`. Time-delay bars.
- `GET /cloud/results-tpt` — `C_ViewTPTResults.jsp`. Throughput
  bars. (The original drew JavaScript charts with `jscharts.js`;
  here the numbers are shown as CSS bars — same values.)
- `GET /cloud/logout` — clears the session.

### 5.5 Trustee (Trusted Authority / Authentication Server) — login, generate key, attackers

- `GET/POST /trustee/login` — `TrusteeLogin.jsp` →
  `TAuthentication.jsp`. Fixed login `AServer / AServer`.
- `GET /trustee/` — `TrusteeMain.jsp`. "WELCOME TO TRUSTEE ::
  AServer".
- `GET /trustee/generate-key` — `GenerateKey.jsp`. File list with
  Trapdoor, Secret Key, and a Generate Private Key link per file.
- `GET/POST /trustee/generate-key/<id>` — `TA_GenerateKey.jsp` →
  `KeyBioIdentiry.jsp`. Shows the file; on POST, an Owner's
  fingerprint check (against the file's owner) must pass.
- `GET /trustee/generate-key-direct/<id>` — `GenerateKey1.jsp`.
  Generates a random 12-character secret key and updates `sk` in
  **both** `cloudserver` and `authorityfile`, then redirects to the
  list page with "Secret Key generated for file id `<id>`".
- `GET /trustee/attackers` — `ViewAttackers.jsp`. Same table as the
  cloud's attackers page.
- `GET /trustee/logout` — clears the session.

### 5.6 Authority — the fixed login

- `GET/POST /authority/login` — `AAuthentication.jsp`. Fixed login
  `authority / authority`; on success redirects to the Owner main
  page (`AuthorityMain.jsp`), exactly as the original did. (No
  menu link points to it in the original — the login is reachable
  at `/authority/login`.)

### 5.7 Images and error pages

- `GET /image/<kind>/<id>` — `ownprofileimage.jsp` /
  `userprofileimage.jsp`: serves the profile picture BLOB.
- `GET /image/thumb/<kind>/<id>` — serves the fingerprint image
  BLOB (the `thumbname` column stores the file name, the
  `thumbimage` column the bytes).
- `GET /wronglogin` — `wronglogin.html`: "Sorry Wrong
  Credentials!". `GET /wrongotp` — `wrongotp.jsp`.
- `GET /logout` — clears every session key and redirects home.

---

## 6. `config.py` — the one file the user edits

```python
DB_TYPE = "mysql"          # "mysql" (default) or "sqlite"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"    # ← CHANGE THIS to your own MySQL password
MYSQL_DATABASE = "Designing"
SQLITE_PATH = "app.db"
FLASK_SECRET_KEY = "biometric-python-source-secret"   # change for real use
```

If `DB_TYPE = "mysql"` but PyMySQL is not installed, the app stops
with a clear message instead of crashing. The SQLite fallback needs
no install beyond Flask and `cryptography`.

---

## 7. Templates — how the JSP pages became Jinja2

Every template extends `templates/base.html`, which is the original
page shell: the blue title "Designing Secure and Efficient
Biometric-Based Secure Access Mechanism for Cloud Services", the
menu tabs (HOME PAGE / CLIENT / REMOTE SERVER / AUTHENTICATE SERVER
/ OWNER), the cloud image slider, the sidebar menu box, and the
footer. Only these JSP constructs were replaced:

| JSP construct | Jinja2 / Flask equivalent |
|---|---|
| `<%@ include file="connect.jsp" %>` + `Class.forName(...)` + `DriverManager.getConnection(...)` | `get_conn()` in `app.py` |
| `<% ResultSet rs = st.executeQuery("SELECT ...") %>` | `q("SELECT ...", params)` |
| `<%= rs.getString("fname") %>` | `{{ row.fname }}` |
| `<% while(rs.next()) { %> ... <% } %>` | `{% for row in rows %} ... {% endfor %}` |
| `<% if(...) { %> ... <% } %>` | `{% if ... %} ... {% endif %}` |
| `request.getParameter("t1")` | `request.form.get("t1")` |
| `session.setAttribute("username", ...)` | `session["owner"] = ...` |
| `response.sendRedirect("wronglogin.html")` | `redirect(url_for("wronglogin"))` |
| `application.getAttribute("username")` | `session["owner"]` (per-user, not global) |

All form field names, button texts, table column headings and menu
labels are unchanged — see `FRONTEND_NOTE.md`.

---

## 8. JSP → route mapping (complete)

"–" means the page had no live behaviour to rebuild, or was broken
in the original; the reason is given.

### Home / shared

| Original | Route | Template |
|---|---|---|
| `index.html` | `GET /` | `index.html` |
| `wronglogin.html` | `GET /wronglogin` | `wronglogin.html` |
| `wrongotp.jsp` | `GET /wrongotp` | `wrongotp.html` |
| `login1.jsp` | – | A login page with no form posts to it and no links from any page — not rebuilt |
| `Asearchservices.jsp` | – | Only checks a session attribute and prints a message — no live behaviour; not rebuilt |
| `images.jsp` | – | Lists images from the `images/` folder of the original project; the static images are served from `static/images/` instead |
| `images1.jsp` | – | A leftover page connecting to the `Efficient_Privacypreserving` database with a different table/column (`imagess` in `user`) — broken in the original; not rebuilt |
| `ownprofileimage.jsp`, `userprofileimage.jsp` | `GET /image/<kind>/<id>`, `GET /image/thumb/<kind>/<id>` | (binary response, no template) |

### Client (End User)

| Original | Route | Template |
|---|---|---|
| `ClientRegister.jsp` | `GET /client/register` | `client_register.html` |
| `c_InsertData.jsp` | `POST /client/register` | (redirect + flash) |
| `ClientLogin.jsp` | `GET /client/login` | `client_login.html` |
| `DU_Authentication.jsp` | `POST /client/login` | (redirect) |
| `Client_BioIdentification.jsp` | `GET /client/biometric` | `client_biometric.html` |
| `UBioIdentiry.jsp` | `POST /client/biometric` | (redirect) |
| `ClientMain.jsp` | `GET /client/` | `client_main.html` |
| `View_All_Files.jsp` | `GET /client/files` | `client_files.html` |
| `Download.jsp` | `GET /client/download` | `client_download.html` |
| `Download1.jsp` | `POST /client/download1` | `client_download1.html` |
| `Download2.jsp` | `POST /client/download2` | `client_download2.html` |
| `ClientAuthentication.jsp` | `GET /client/otp` | `client_otp.html` |
| `ClientOTP.jsp` | – | **Missing from the zip** — the OTP form is rendered by `/client/otp` instead |
| `OTPCheck.jsp` | `POST /client/otp-check` | (redirect) |
| `ClientRegisters.jsp` | – | A second copy of the register form with no links from any page — not rebuilt |
| `C_SendReq.jsp` | – | Checks only a session attribute and prints a message — no live behaviour; not rebuilt |

### Owner (Authenticate Server)

| Original | Route | Template |
|---|---|---|
| `O_Register.jsp` | `GET /owner/register` | `owner_register.html` |
| `o_InsertData.jsp` | `POST /owner/register` | (redirect + flash) |
| `AuthorityLogin.jsp` | `GET /owner/login` | `owner_login.html` |
| `DO_Authentication.jsp` | `POST /owner/login` | (redirect) |
| `Owner_BioIdentification.jsp` | `GET /owner/biometric` | `owner_biometric.html` |
| `OBioIdentiry.jsp` | `POST /owner/biometric` | (redirect) |
| `AuthorityMain.jsp` | `GET /owner/` | `owner_main.html` |
| `Upload.jsp` | `GET /owner/upload` | `owner_upload.html` |
| `Upload1.jsp` | `POST /owner/upload1` | `owner_upload1.html` |
| `Upload2.jsp` | `POST /owner/upload2` | (redirect + flash) |
| `ViewAllAuthorityFiles.jsp` | `GET /owner/files` | `owner_files.html` |
| `ViewAllTransactions.jsp` | `GET /owner/transactions` | `owner_transactions.html` |

### Cloud Server (Remote Server)

| Original | Route | Template |
|---|---|---|
| `CloudLogin.jsp` | `GET /cloud/login` | `cloud_login.html` |
| `CAuthentication.jsp` | `POST /cloud/login` | (redirect) |
| `CloudMain.jsp` | `GET /cloud/` | `cloud_main.html` |
| `ViewClients.jsp` | `GET /cloud/owners` | `cloud_owners.html` |
| `D_ViewOwners.jsp` | `GET /cloud/clients` | `cloud_clients.html` |
| `C_OwnerDetails.jsp` | `GET /cloud/owner-details?id=<id>` | `cloud_owner_details.html` |
| `C_ClientDetails.jsp` | `GET /cloud/client-details?id=<id>` | `cloud_client_details.html` |
| `C_StatusClient.jsp` | `GET /cloud/authorize-owner/<id>` | (redirect) |
| `C_StatusOwner.jsp` | `GET /cloud/authorize-client/<id>` | (redirect) |
| `ViewAllCloudFiles.jsp` | `GET /cloud/files` | `cloud_files.html` |
| `C_Access_Control.jsp` | `GET /cloud/access/<id>` | `cloud_access.html` |
| `Access_Control.jsp` | `GET /cloud/access/<id>` | `cloud_access.html` (a second copy of the same fingerprint form — same route) |
| `FileBioIdentiry.jsp` | `POST /cloud/access/<id>` | (redirect) |
| `ViewAllCloudTransactions.jsp` | `GET /cloud/transactions` | `cloud_transactions.html` |
| `ViewAllAttackers.jsp` | `GET /cloud/attackers` | `cloud_attackers.html` |
| `AViewOTP.jsp` | – | **Broken in the original**: JDBC-ODBC connection to a different database and different columns — replaced by `/cloud/attackers` |
| `ViewResults.jsp` / `Results.jsp` | `GET /cloud/results` | `cloud_results.html` |
| `Results1.jsp` / `Results2.jsp` | – | Only a JavaScript chart of the same `results` table — the numbers are shown on `/cloud/results` instead |
| `C_ViewTDResults.jsp` | `GET /cloud/results-td` | `cloud_results_td.html` |
| `C_ViewTPTResults.jsp` | `GET /cloud/results-tpt` | `cloud_results_tpt.html` |

### Trustee (Trusted Authority / Authentication Server)

| Original | Route | Template |
|---|---|---|
| `TrusteeLogin.jsp` | `GET /trustee/login` | `trustee_login.html` |
| `TAuthentication.jsp` | `POST /trustee/login` | (redirect) |
| `TrusteeMain.jsp` | `GET /trustee/` | `trustee_main.html` |
| `GenerateKey.jsp` | `GET /trustee/generate-key` | `trustee_generate_key.html` |
| `TA_GenerateKey.jsp` | `GET /trustee/generate-key/<id>` | `trustee_generate_key_detail.html` |
| `KeyBioIdentiry.jsp` | `POST /trustee/generate-key/<id>` | (redirect) |
| `GenerateKey1.jsp` | `GET /trustee/generate-key-direct/<id>` | (redirect + flash) |
| `ViewAttackers.jsp` | `GET /trustee/attackers` | `trustee_attackers.html` |

### Authority

| Original | Route | Template |
|---|---|---|
| `AAuthentication.jsp` | `GET/POST /authority/login` | (redirect to Owner main page) |

### 46 routes in total (counted with `grep -c "@app.route" app.py`).

---

## 9. The nested `Design_of_bio_metric` sub-project — translated, not rebuilt

The zip contains a second, smaller implementation of the same paper
inside `Design_of_bio_metric/` (an Eclipse project). Its source was
used as reference during the conversion and is not included in this
repo (Python files only). It was
**not** rebuilt as a second Flask app — the main top-level app is
the one the user asked to convert. Here is what its 7 Java files do,
in plain words, so the user can talk about them in a viva:

| File | What it does |
|---|---|
| `Algorithm/CaesarCipher.java` | A Caesar cipher: shifts each letter by a fixed key (classic substitution). Used in the sub-project to encrypt the file content before upload. **It is a toy cipher** — trivially breakable — and is not used by the main app. |
| `DataBaseCon/DbConnection.java` | JDBC connection to MySQL database **`multi_user`** (`root`/`root`), same host/port. This is where the second database name comes from. |
| `Ftpcon.java` | A helper that copies an uploaded file to an FTP / remote folder (the sub-project stored files on disk, not in the database). |
| `Mail.java` | Sends an email (JavaMail) — used in the sub-project to email the user a key / OTP. No SMTP server is configured in the zip, so it could not run as written. |
| `Network/download.java` | A servlet that streams a stored file back to the browser for download (sets the content type and the `Content-Disposition` header). |
| `NewServlet.java` | The upload servlet: receives a multipart file upload, splits the file into blocks (see `SplitFile.java`), encrypts each block with the Caesar cipher, and stores the blocks in the `file_storage` table. |
| `SplitFile.java` | Splits a file into **3 blocks** (byte ranges) so the blocks can be stored / uploaded separately. |

Its 5 tables (`DATABASE/multi-user.sql`): `register` (user
registration), `file_storage` (encrypted file blocks), `file_view`
(file metadata), `userrequests` (download requests) and `downloads`
(download log). Its `web.xml` maps the servlets `FileUpload`,
`Upload`, `NewServlet` and `download`.

Its index.jsp title and abstract match the BioCAP paper, and its
pages (login / register / cloud home / upload / download /
`verifyBiometric` / `biometricValidation` / activate / deactivate)
mirror the same roles as the main app. The differences that matter
for a viva: **it encrypts with a Caesar cipher (weak) and splits
files into 3 blocks**, while the main app stored files as plain text
with an unused AES object; **this Python conversion encrypts with
Fernet**, which is a real, standard construction (AES-128-CBC +
HMAC-SHA256).

---

## 10. Differences from the earlier reconstruction (`~/workspace/biometric-python/`)

| | Earlier reconstruction (2026-11-07, from `DOCUMENT.rar`) | This conversion (2026-11-11, from the real zip) |
|---|---|---|
| Source | Word documents + screenshots only — **no code** | The real Java/JSP source (121 JSP, 7 Java, `Database.sql`) |
| Database | `biometric` (a name invented for the reconstruction — the docs gave no DB name) | **`Designing`** (from `connect.jsp` and `Database.sql`) |
| Tables | 8 (client, admin, auth_server, resource_server, resource_file, synthetic_fingerprint, service_request, transaction) | **10, exactly as `Database.sql`** (owner, user, authority, cloud, trustee, cloudserver, authorityfile, transaction, attacker, results) |
| Roles | Client / Authentication Server / Resource Server / Admin | **Owner / Client / Cloud Server (Remote Server) / Trustee (Trusted Authority) / Authority** — the roles in the real JSPs |
| Demo users | `venkat` (CID987788) and `kishan` (CID636553) — taken from the screenshots | **Raja, Kannan, Manjunath, Srini, Kiran, Rajesh** (owners) and **Harish, Murugesh, tmksmanju, Lokesh, Saleem** (clients) — from `Database.sql` |
| Private key | Random 22-char key pre-filled on the register form | Random 12-char secret key generated by the Trustee per file |
| Fingerprint | SHA-256 hash of the uploaded file (exact bytes) | File **name** or identical bytes — matching the original's name check, widened to bytes |
| OTP | Not present | Present (repaired — the original's OTP flow was broken) |
| File access | Resource Server verifies a service request | Cloud Server gives access control after an Owner fingerprint check |
| Frontend | Built to look like the IoMT project | **The original's own 2011 template** (blue title, cloud slider, sidebar) — byte-identical CSS/JS/images |
| Session key | Generated from two biometric templates (per the paper) | SHA-1 trapdoor of the file content (per `Upload1.jsp`) |

---

## 11. Testing (2026-11-11)

Live curl tests against the running app in **SQLite mode**:
**39 checks, 39 passed, 0 failed** (test script
`/tmp/test_bio_source.py`). Full flow (Raja upload → Trustee key
generation → Cloud access control → new client register → Cloud
authorise → client login + fingerprint → download with the correct
secret key) plus the failure paths (wrong password, wrong
fingerprint, wrong secret key → attacker logged, wrong OTP →
attacker logged, Waiting client blocked). See README §10 for the
check-by-check table.

Two bugs found and fixed during testing:
1. `q(..., one=True)` raised `IndexError` on an empty result — now
   returns `None`.
2. The schema loader skipped the first `CREATE TABLE` because of
   the leading `--` comment block — comment lines are now stripped
   before splitting on `;`.

**MySQL mode was not tested live here** — this machine has no
MySQL / MariaDB server. The MySQL code path is the same pattern as
the earlier IoMT and Biometric reconstruction projects, whose MySQL
mode was tested live on MariaDB. State this if asked.

Screenshots of the running app (12 PNGs: home, owner login,
owner dashboard, owner upload, owner files, client dashboard,
client files, client download, cloud dashboard, cloud files, cloud
results, trustee generate-key) were taken with `wkhtmltoimage`
against the running app with a real logged-in session cookie.
They are not included in this repo.
