#!/usr/bin/env python3
"""
Biometric-Based Secure Access Mechanism for Cloud Services
----------------------------------------------------------
Python / Flask version, converted from the REAL Java/JSP source the
user shared on 2026-11-11:

    Secure_and_efficient_biometric-based_secure_access_mechanism_
    for_cloud_services.zip  (15 MB, 381 files)

This is a conversion, not a reconstruction: the zip contains the
actual JSP pages, 7 .java files, DATABASE/Database.sql and the
Biometric Images. (The earlier ~/workspace/biometric-python/ project
was a reconstruction, because the DOCUMENT.rar shared on 2026-11-07
contained only Word documents and screenshots, no code.)

What was converted
------------------
* Main app = the top-level JSP application in the zip (index.html,
  connect.jsp, DATABASE/Database.sql, ~67 JSP/HTML pages).
  Database: `Designing` (connect.jsp:
  jdbc:mysql://localhost:3306/Designing). 10 tables, same names and
  columns as Database.sql.
* Roles (the original's own names, kept):
    - Client / End User   (table `user`) - registers with a profile
      picture + fingerprint, logs in with password + fingerprint,
      views all files, downloads a file with its secret key.
    - Owner               (table `owner`) - the "Authenticate Server"
      tab in index.html; AuthorityLogin.jsp logs an Owner in. The
      Owner uploads files, views his uploaded files and transactions.
    - Cloud / Remote Server (table `cloud`, Server/Server) -
      authorises Owners and Clients, views cloud files, gives access
      control (fingerprint check), views transactions, attackers and
      timing/throughput results.
    - Trustee / Trusted Authority / Authentication Server
      (table `trustee`, AServer/AServer) - generates the secret key
      for a file (after a fingerprint check) and views attackers.
    - Authority           (table `authority`, authority/authority) -
      a fixed login whose AAuthentication.jsp is not linked from any
      menu in the original; kept here as a login that opens the
      Owner main page, exactly as AAuthentication.jsp redirects to
      AuthorityMain.jsp.
* The nested Design_of_bio_metric sub-project inside the same zip
  (DB `multi_user`, servlets NewServlet / download / SplitFile /
  CaesarCipher) is a second, smaller implementation of the same
  paper. Its Java files are translated and explained in
  CODE_EXPLANATION.md section 9. Its source is not included in
  this repo (Python files only). It was NOT rebuilt as a
  second Flask app - the top-level app above is the main project
  (its index.html is the welcome page of the zip).

Frontend: unchanged. Templates are rebuilt from the original JSP
pages - same page shell (header, green logo title, menu, coin
slider, mainbar + sidebar, footer), same headings, labels, form
fields and field names, button text and table columns, same CSS/JS/
images. Only JSP directives, scriptlets, <%= %> expressions and
JDBC were replaced by Flask routes + minimal Jinja. The original
JSP/Java/SQL files are not included in this repo (Python files only).

Backend changes (honest list - see README.md section 8):
* Passwords are hashed (werkzeug PBKDF2). The original stored them
  in plain text. The three fixed system logins (authority / cloud /
  trustee) are still plain text in their tables, exactly as in the
  original, because they are single-row fixed accounts.
* SQL is parameterised. The original built queries by string
  concatenation (SQL-injection prone).
* File content: the original created an AES cipher object with the
  hard-coded key "ef50a0ef2c3e3a5f" and an RSA key pair, but never
  used either of them on the stored data - the file content was
  stored as plain text (ct column) and only Base64-encoded for
  display. Here the content is really encrypted with Fernet
  (AES-128-CBC + HMAC) and decrypted on download.
* Secret key: the original set sk to String.valueOf(publicKey
  bytes), e.g. "[B@47122d" - a Java object reference string, not a
  usable key. Here the Trustee generates a real random 12-character
  secret key.
* Fingerprint "matching": the original compared only the uploaded
  file's NAME with the stored thumbname (SELECT ... WHERE
  thumbname='<uploaded filename>'). No image comparison, no
  minutiae. Here a match counts if the uploaded file name matches
  the stored thumbname OR the uploaded file bytes are identical to
  the stored fingerprint image. Still no minutiae extraction.
* OTP: ClientAuthentication.jsp / OTPCheck.jsp in the original
  refer to a `user.otp` column and a ClientOTP.jsp page that do not
  exist in Database.sql / the zip, so that flow could never run.
  Here it is repaired: the OTP is generated at login and shown on
  the OTP entry page (there is no SMS/email in the original), and
  OTPCheck verifies it. A wrong OTP is logged as an attacker, as
  OTPCheck.jsp does.
* The original used one global `application` login (anyone logged in
  as the same user). Here each login is a per-user Flask session.
* The paper's 95.12% accuracy claim is the paper's claim, not
  verified here and not implemented.

Run:  python app.py   (or F5 in Spyder)  ->  http://127.0.0.1:5000
Config: config.py - DB_TYPE = "mysql" (default, database Designing)
        or "sqlite" (fallback, app.db).
"""

import base64
import hashlib
import os
import random
import sqlite3
import string
import time
from datetime import datetime

from flask import (Flask, flash, g, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import config

try:
    import pymysql
except ImportError:  # pragma: no cover
    pymysql = None

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover
    Fernet = None

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB, as in the JSPs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_IMG_DIR = os.path.join(BASE_DIR, "seed_data", "biometric_images")

# ---------------------------------------------------------------- DB layer


def _is_mysql():
    return config.DB_TYPE == "mysql"


def _translate_sql(sql):
    """Translate the SQLite-style SQL used below to MySQL."""
    if not _is_mysql():
        return sql
    sql = sql.replace('"transaction"', "`transaction`")
    return sql.replace("?", "%s")


def get_conn():
    """One connection per request (MySQL via PyMySQL, else SQLite)."""
    if "db" not in g:
        if _is_mysql():
            if pymysql is None:
                raise RuntimeError(
                    "DB_TYPE is 'mysql' but PyMySQL is not installed. "
                    "Run: pip install pymysql (in Spyder: !pip install pymysql), "
                    "or set DB_TYPE = \"sqlite\" in config.py.")
            try:
                conn = pymysql.connect(
                    host=config.MYSQL_HOST, port=config.MYSQL_PORT,
                    user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
                    database=config.MYSQL_DB, charset="utf8mb4",
                    autocommit=True)
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1049:  # Unknown database -> create it
                    tmp = pymysql.connect(
                        host=config.MYSQL_HOST, port=config.MYSQL_PORT,
                        user=config.MYSQL_USER,
                        password=config.MYSQL_PASSWORD, autocommit=True)
                    with tmp.cursor() as cur:
                        cur.execute(
                            "CREATE DATABASE IF NOT EXISTS `%s`"
                            % config.MYSQL_DB)
                    tmp.close()
                    conn = pymysql.connect(
                        host=config.MYSQL_HOST, port=config.MYSQL_PORT,
                        user=config.MYSQL_USER,
                        password=config.MYSQL_PASSWORD,
                        database=config.MYSQL_DB, charset="utf8mb4",
                        autocommit=True)
                else:
                    raise
            g.db = conn
        else:
            path = os.path.join(BASE_DIR, config.SQLITE_FILE)
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            g.db = conn
    return g.db


@app.teardown_appcontext
def close_conn(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def q(sql, args=(), one=False):
    """Run a query; returns a list of dicts (or one dict / None)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_translate_sql(sql), args)
    if cur.description is None:
        if not _is_mysql():
            conn.commit()
        return None
    rows = cur.fetchall()
    if _is_mysql():
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in rows]
    else:
        rows = [dict(r) for r in rows]
    return rows[0] if (one and rows) else (None if one else rows)


def execute(sql, args=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_translate_sql(sql), args)
    if not _is_mysql():
        conn.commit()
    return cur.lastrowid


def _run_schema():
    """Create the tables from schema_mysql.sql / schema.sql."""
    name = "schema_mysql.sql" if _is_mysql() else "schema.sql"
    with open(os.path.join(BASE_DIR, name), encoding="utf-8") as f:
        sql = f.read()
    conn = get_conn()
    cur = conn.cursor()
    # Split on ";" at line ends; the schema has no ";" inside strings.
    for stmt in sql.split(";"):
        # Drop full-line -- comments (the header of the schema file)
        lines = [ln for ln in stmt.splitlines()
                 if not ln.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if not stmt:
            continue
        # Drop the CREATE DATABASE / USE lines for MySQL (DB already made)
        if stmt.upper().startswith(("CREATE DATABASE", "USE ")):
            continue
        cur.execute(stmt)
    if not _is_mysql():
        conn.commit()
    # FIX 2026-11-12: the original schema had password VARCHAR(45), but
    # the hashed password is ~160 chars, so MySQL failed on first seed
    # with "Data too long for column 'password'". Widen it on databases
    # that were already created with the old schema (new databases get
    # VARCHAR(255) from the schema files above).
    if _is_mysql():
        for _tbl in ("owner", "user"):
            try:
                cur.execute(
                    "ALTER TABLE `%s` MODIFY `password` varchar(255) "
                    "DEFAULT NULL" % _tbl)
            except Exception:
                pass


# ---------------------------------------------------------------- crypto


def _fernet():
    """Fernet instance, or None if cryptography is not installed."""
    if Fernet is None:
        return None
    key_file = os.path.join(BASE_DIR, "instance", "fernet.key")
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    if not os.path.exists(key_file):
        with open(key_file, "wb") as f:
            f.write(Fernet.generate_key())
    with open(key_file, "rb") as f:
        return Fernet(f.read())


_FERNET = None


def encrypt_text(text):
    """Encrypt file content for the ct column (Fernet; Base64 fallback)."""
    global _FERNET
    if _FERNET is None:
        _FERNET = _fernet()
    if _FERNET is None:
        return base64.b64encode(text.encode("utf-8")).decode("ascii")
    return _FERNET.encrypt(text.encode("utf-8")).decode("ascii")


def decrypt_text(blob):
    """Decrypt a ct value. Also understands plain Base64 / plain text,
    so old demo rows still display."""
    global _FERNET
    if _FERNET is None:
        _FERNET = _fernet()
    if blob is None:
        return ""
    if _FERNET is not None:
        try:
            return _FERNET.decrypt(blob.encode("ascii")).decode("utf-8")
        except Exception:
            pass
    try:
        return base64.b64decode(blob.encode("ascii")).decode("utf-8")
    except Exception:
        return blob


def trapdoor(content):
    """SHA-1 hex digest of the file content - the 'trapdoor' / digital
    signature the original Upload1.jsp computed (MessageDigest SHA1)."""
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def gen_secret_key(length=12):
    """A real random secret key. The original used
    String.valueOf(RSA public key bytes), e.g. "[B@47122d", which is
    not a usable key at all."""
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def gen_otp():
    return "".join(random.choice(string.digits) for _ in range(6))


def now_str():
    """Date format used everywhere in the original JSPs:
    dd/MM/yyyy   HH:mm:ss (three spaces between date and time)."""
    return datetime.now().strftime("%d/%m/%Y   %H:%M:%S")


def _is_hashed(value):
    return isinstance(value, str) and (
        value.startswith("pbkdf2:") or value.startswith("scrypt:"))


def check_user_password(stored, supplied):
    """Owner/User passwords are hashed here (plain text in the
    original). Accepts a plain-text stored value too, so any row
    seeded the old way still logs in."""
    if stored is None:
        return False
    if _is_hashed(stored):
        try:
            return check_password_hash(stored, supplied)
        except Exception:
            return False
    return stored == supplied


# ---------------------------------------------------------------- seed data

# Demo accounts, exactly as in DATABASE/Database.sql (password = name,
# status Authorized, fingerprint file name from the Biometric Images
# folder in the zip). Emails / mobiles / addresses / DOBs are copied
# from the same SQL file.
SEED_OWNERS = [
    ("Raja", "Raja.123@gmail.com", "9535866270",
     "#748,4th Cross,Malleshwaram", "05/06/1987", "MALE", "560011",
     "Raja.jpg"),
    ("Kannan", "Kannan.123@gmail.com", "9535866270",
     "#7827,4th Block", "05/06/1987", "MALE", "560021", "Kannan.png"),
    ("Manjunath", "tmksmanju13@gmail.com", "9535866270",
     "#6726,4th Cross,Rajajiangar", "05/06/1987", "MALE", "560021",
     "manjunath.jpg"),
    ("Srini", "Srini.123@gmail.com", "9535866270",
     "#82,4th Cross,Rajajiangar", "05/06/1987", "MALE", "560021",
     "Srini.jpg"),
    ("Kiran", "Kiran.123@gmail.com", "9535866270",
     "#7827,4th Cross,Rajajiangar", "05/06/1987", "MALE", "560021",
     "kiran.jpg"),
    ("Rajesh", "Rajesh.123@gmail.com", "9535866270",
     "#8928,4th Cross,Rajajiangar", "05/06/1987", "MALE", "560021",
     "Rajesh.png"),
]

SEED_USERS = [
    ("Harish", "Harish.123@gmail.com", "9535866270",
     "#892,4th Cross,Rajajinagar", "05/06/1987", "MALE", "560021",
     "Harish.jpg"),
    ("Murugesh", "Murugesh.123@gmail.com", "9535866270",
     "#7827,4th Cross,Vijayanagar", "05/06/1987", "MALE", "560040",
     "Murugesh.png"),
    ("tmksmanju", "tmksmanju13@gmail.com", "9535866270",
     "#7827,4th Cross,Viajayangar", "05/06/1987", "MALE", "560021",
     "tmksmanju.jpg"),
    ("Lokesh", "Lokesh.123@gmail.com", "9535866270",
     "#7827,4th Cross,Vijayanagar", "05/06/1987", "MALE", "560040",
     "Lokesh.jpg"),
    ("Saleem", "Saleem.123@gmail.com", "9535866270",
     "#8928,5th Cross,Vijayanagar", "05/06/1987", "MALE", "560040",
     "Saleem.jpg"),
]

# Seeded files, as in Database.sql (authorityfile / cloudserver rows
# id 2-7). The original ct values were the Base64 of whole JSP source
# files and the sk values were "[B@..." Java object strings; here
# each file gets readable sample content (Fernet-encrypted in ct),
# its SHA-1 trapdoor, a real secret key, and the same rank / date /
# Access / owner as the SQL file. cloudserver Access is 'Yes' in the
# SQL file, authorityfile Access is 'No'.
SEED_FILES = [
    # fname, sample content, rank, dt, owner
    ("DBase.jsp",
     "Sample file DBase.jsp - demo content uploaded by Raja.\n"
     "This is the file the Owner uploaded; the Cloud Server stores\n"
     "it encrypted, the Trustee generates its secret key, and the\n"
     "Client downloads it with that secret key.", 7,
     "07/09/2020   15:12:26", "Raja"),
    ("AAuth.jsp",
     "Sample file AAuth.jsp - demo content uploaded by Raja.\n"
     "Authentication page source used as demo file content.", 0,
     "07/09/2020   15:21:42", "Raja"),
    ("DAuth.jsp",
     "Sample file DAuth.jsp - demo content uploaded by Raja.\n"
     "Data-user authentication page used as demo file content.", 0,
     "07/09/2020   16:12:26", "Raja"),
    ("Download.jsp",
     "Sample file Download.jsp - demo content uploaded by Manjunath.\n"
     "Download page used as demo file content.", 2,
     "07/09/2020   18:37:33", "Manjunath"),
    ("CStatus.jsp",
     "Sample file CStatus.jsp - demo content uploaded by Kiran.\n"
     "Status page used as demo file content.", 1,
     "07/09/2020   19:03:21", "Kiran"),
    ("AAuth1.jsp",
     "Sample file AAuth1.jsp - demo content uploaded by Rajesh.\n"
     "Authority authentication page used as demo file content.", 1,
     "07/09/2020   18:10:09", "Rajesh"),
]

SEED_RESULTS = [
    ("DBase.jsp", "307", "1024"),
    ("AAuth.jsp", "329", "5120"),
    ("DAuth.jsp", "300", "7168"),
    ("Download.jsp", "238", "9216"),
    ("CStatus.jsp", "243", "2048"),
    ("AAuth1.jsp", "387", "4096"),
]

# Transaction rows exactly as in Database.sql (id, user, fname, sk,
# task, dt). The sk values 'No' / '0' / '1' ... are the original's.
SEED_TRANSACTIONS = [
    ("Raja", "DBase.jsp", "No", "Upload", "07/09/2020   15:12:26"),
    ("Raja", "AAuth.jsp", "No", "Upload", "07/09/2020   15:21:42"),
    ("Raja", "Dbase.jsp", "0", "Downloaded", "07/09/2020   16:08:16"),
    ("Raja", "DBase.jsp", "1", "Downloaded", "07/09/2020   16:10:37"),
    ("Raja", "DAuth.jsp", "No", "Upload", "07/09/2020   16:12:26"),
    ("Harish", "DAuth.jsp", "0", "Downloaded", "07/09/2020   16:12:43"),
    ("Harish", "DBase.jsp", "0", "Downloaded", "07/09/2020   16:13:46"),
    ("Harish", "DBase.jsp", "3", "Downloaded", "07/09/2020   16:14:35"),
    ("Harish", "DBase.jsp", "4", "Downloaded", "07/09/2020   16:21:18"),
    ("Harish", "DBase.jsp", "4", "Downloaded", "07/09/2020   16:22:22"),
    ("Harish", "DBase.jsp", "4", "Downloaded", "07/09/2020   16:22:42"),
    ("Harish", "DAuth.jsp", "0", "Downloaded", "07/09/2020   16:25:35"),
    ("Manjunath", "Download.jsp", "No", "Upload", "07/09/2020   18:37:33"),
    ("tmksmanju", "Download.jsp", "0", "Downloaded", "07/09/2020   18:42:53"),
    ("Kiran", "CStatus.jsp", "No", "Upload", "07/09/2020   19:03:21"),
    ("Lokesh", "CStatus.jsp", "0", "Downloaded", "07/09/2020   19:06:00"),
    ("Lokesh", "CStatus.jsp", "0", "Downloaded", "07/09/2020   19:06:51"),
    ("Lokesh", "Download.jsp", "1", "Downloaded", "07/09/2020   19:07:29"),
    ("tmksmanju", "Dbase.jsp", "5", "Downloaded", "07/09/2020   17:35:08"),
    ("tmksmanju", "Dbase.jsp", "5", "Downloaded", "07/09/2020   17:36:36"),
    ("tmksmanju", "Dbase.jsp", "5", "Downloaded", "07/09/2020   17:37:10"),
    ("Rajesh", "AAuth1.jsp", "No", "Upload", "07/09/2020   18:10:09"),
    ("Saleem", "AAuth1.jsp", "0", "Downloaded", "07/09/2020   18:13:13"),
]

SEED_ATTACKERS = [
    ("Harish", "DAuth.jsp", "534534", "07/09/2020   16:13:53"),
    ("Harish", "DAuth.jsp", "534534", "07/09/2020   16:14:25"),
    ("Harish", "DAuth.jsp", "[B@47122d", "07/09/2020   16:25:39"),
    ("Harish", "DAuth.jsp", "[B@47122d", "07/09/2020   16:26:47"),
    ("tmksmanju", "Download.jsp", "[B@17d2f0e", "07/09/2020   18:42:57"),
    ("Lokesh", "CStatus.jsp", " [B@b6be69 ", "07/09/2020   19:06:03"),
    ("tmksmanju", "Dbase.jsp", "", "07/09/2020   17:35:10"),
    ("Saleem", "AAuth1.jsp", "", "07/09/2020   18:13:15"),
]


def _seed_image_bytes(filename):
    """Bytes of a demo fingerprint image. Uses the real Biometric
    Images file from the zip when present; otherwise draws a simple
    pattern with Pillow (same approach as the earlier reconstruction)."""
    path = os.path.join(SEED_IMG_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    try:
        from PIL import Image, ImageDraw
        import io
        img = Image.new("RGB", (120, 140), "white")
        d = ImageDraw.Draw(img)
        for i in range(8):
            d.arc([10 + i * 3, 10 + i * 3, 110 - i * 3, 130 - i * 3],
                  start=20 + i * 15, end=200 + i * 15, fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b""


def _seed_person(table, person):
    """Insert one owner/user row. person = (name, email, mobile,
    address, dob, gender, pincode, thumbname). Password = name,
    hashed (plain text in the original)."""
    name, email, mobile, addr, dob, gender, pin, thumb = person
    img = _seed_image_bytes(thumb)
    execute(
        "INSERT INTO %s (username,password,email,mobile,address,dob,"
        "gender,pincode,status,image,thumbimage,thumbname) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)" % table,
        (name, generate_password_hash(name), email, mobile, addr, dob,
         gender, pin, "Authorized", img, img, thumb))


def init_db():
    """Create tables and seed demo data on first run (idempotent)."""
    _run_schema()
    if q("SELECT COUNT(*) AS c FROM owner", one=True)["c"] == 0:
        for p in SEED_OWNERS:
            _seed_person("owner", p)
    if q("SELECT COUNT(*) AS c FROM user", one=True)["c"] == 0:
        for p in SEED_USERS:
            _seed_person("user", p)
    # Fixed system logins, plain text exactly as in Database.sql
    for table, name, pw in (("authority", "authority", "authority"),
                            ("cloud", "Server", "Server"),
                            ("trustee", "AServer", "AServer")):
        if q("SELECT COUNT(*) AS c FROM %s" % table, one=True)["c"] == 0:
            execute("INSERT INTO %s (name, pass) VALUES (?, ?)"
                    % table, (name, pw))
    if q("SELECT COUNT(*) AS c FROM cloudserver", one=True)["c"] == 0:
        for fname, content, rank, dt, owner in SEED_FILES:
            sk = gen_secret_key()
            ct = encrypt_text(content)
            td = trapdoor(content)
            execute(
                "INSERT INTO cloudserver (fname,ct,trapdoor,sk,rank,dt,"
                "Access,user) VALUES (?,?,?,?,?,?,?,?)",
                (fname, ct, td, sk, rank, dt, "Yes", owner))
            execute(
                "INSERT INTO authorityfile (fname,ct,trapdoor,sk,rank,dt,"
                "Access,user) VALUES (?,?,?,?,?,?,?,?)",
                (fname, ct, td, sk, 0, dt, "No", owner))
    if q("SELECT COUNT(*) AS c FROM results", one=True)["c"] == 0:
        for fname, td_, tpt in SEED_RESULTS:
            execute("INSERT INTO results (fname,tdelay,tpt) VALUES (?,?,?)",
                    (fname, td_, tpt))
    if q('SELECT COUNT(*) AS c FROM "transaction"', one=True)["c"] == 0:
        for user, fname, sk, task, dt in SEED_TRANSACTIONS:
            execute('INSERT INTO "transaction" (user,fname,sk,task,dt) '
                    "VALUES (?,?,?,?,?)", (user, fname, sk, task, dt))
    if q("SELECT COUNT(*) AS c FROM attacker", one=True)["c"] == 0:
        for user, fname, sk, dt in SEED_ATTACKERS:
            execute("INSERT INTO attacker (user,fname,sk,dt) VALUES (?,?,?,?)",
                    (user, fname, sk, dt))


# ---------------------------------------------------------------- helpers

def _person_login(table, username, password):
    """Check an owner/user login. Returns the row, 'waiting', or None.
    Mirrors DU_Authentication.jsp / DO_Authentication.jsp: correct
    password + status 'Waiting' -> wronglogin page; wrong password ->
    wrongLogin page."""
    row = q("SELECT * FROM %s WHERE username=?" % table, (username,),
            one=True)
    if not row or not check_user_password(row["password"], password):
        return None
    if row["status"] == "Waiting":
        return "waiting"
    return row


def _fixed_login(table, username, password):
    """Fixed system logins (authority / cloud / trustee): plain-text
    name + pass, exactly as in AAuthentication.jsp / CAuthentication
    .jsp / TAuthentication.jsp."""
    row = q("SELECT * FROM %s WHERE name=? AND pass=?" % table,
            (username, password), one=True)
    return row


def _fingerprint_matches(stored_thumbname, stored_thumb_bytes,
                         uploaded_name, uploaded_bytes):
    """Biometric check, as the original JSPs do it - and a little
    stronger. The original (UBioIdentiry.jsp, OBioIdentiry.jsp,
    FileBioIdentiry.jsp, KeyBioIdentiry.jsp) only compared the
    uploaded file's NAME with the stored thumbname:
        SELECT * FROM owner/user WHERE thumbname='<uploaded name>'
    No image comparison and no minutiae extraction at all. Here a
    match counts if the file name matches OR the uploaded file bytes
    are identical to the stored fingerprint image bytes. Still no
    minutiae extraction - say so in the viva."""
    if uploaded_name and stored_thumbname and \
            uploaded_name == stored_thumbname:
        return True
    if uploaded_bytes and stored_thumb_bytes and \
            uploaded_bytes == bytes(stored_thumb_bytes):
        return True
    return False


def _require(role):
    """Redirect to the home page when the role is not logged in."""
    if session.get("role") != role:
        flash("Please log in first.")
        return redirect(url_for("index"))
    return None


def _log_attacker(user, fname, sk):
    execute("INSERT INTO attacker (user,fname,sk,dt) VALUES (?,?,?,?)",
            (user or "", fname or "", sk or "", now_str()))


def _log_transaction(user, fname, sk, task):
    execute('INSERT INTO "transaction" (user,fname,sk,task,dt) '
            "VALUES (?,?,?,?,?)", (user or "", fname or "", sk or "",
                                   task, now_str()))


def _rows_to_dicts(rows):
    return rows or []


# ---------------------------------------------------------------- home

@app.route("/")
def index():
    """index.html - Home Page. Menu: Home Page / Client /
    Remote Server / Authenticate Server / Owner."""
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/wronglogin")
def wronglogin():
    """wronglogin.html - 'Sorry Wrong Credentials!'"""
    return render_template("wronglogin.html")


# ---------------------------------------------------------------- client
# ClientLogin.jsp -> DU_Authentication.jsp -> Client_BioIdentification
# .jsp -> UBioIdentiry.jsp -> ClientMain.jsp
# ClientRegister.jsp -> c_InsertData.jsp

@app.route("/client/register", methods=["GET", "POST"])
def client_register():
    """ClientRegister.jsp. Fields (same names as the original):
    userid, pass, email, mobile, address, dob, gender, pincode,
    pic (profile picture), pic2 (finger print). New clients start
    with status 'Waiting' (c_InsertData.jsp)."""
    if request.method == "POST":
        uname = request.form.get("userid", "").strip()
        if not uname:
            flash("Client Name is required.")
            return render_template("register.html", role="client")
        if q("SELECT * FROM user WHERE username=?", (uname,), one=True):
            flash("Client Name Already Exist")
            return render_template("register.html", role="client")
        pic = request.files.get("pic")
        fp = request.files.get("pic2")
        pic_bytes = pic.read() if pic and pic.filename else b""
        fp_bytes = fp.read() if fp and fp.filename else b""
        fp_name = secure_filename(fp.filename) if fp and fp.filename else ""
        execute(
            "INSERT INTO user (username,password,email,mobile,address,"
            "dob,gender,pincode,status,image,thumbimage,thumbname) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uname, generate_password_hash(request.form.get("pass", "")),
             request.form.get("email", ""), request.form.get("mobile", ""),
             request.form.get("address", ""), request.form.get("dob", ""),
             request.form.get("gender", ""), request.form.get("pincode", ""),
             "Waiting", pic_bytes, fp_bytes, fp_name))
        flash("Client Registered Successfully")
        return redirect(url_for("client_login"))
    return render_template("register.html", role="client")


@app.route("/client/login", methods=["GET", "POST"])
def client_login():
    """ClientLogin.jsp. Posts to DU_Authentication.jsp."""
    if request.method == "POST":
        name = request.form.get("userid", "").strip()
        result = _person_login("user", name, request.form.get("pass", ""))
        if result is None:
            return redirect(url_for("wronglogin"))
        if result == "waiting":
            return redirect(url_for("wronglogin"))
        session["pending_user"] = name
        session["pending_role"] = "client"
        return redirect(url_for("client_bio"))
    return render_template("login.html", role="client",
                           title="WELCOME TO CLIENT LOGIN")


@app.route("/client/biometric", methods=["GET", "POST"])
def client_bio():
    """Client_BioIdentification.jsp -> UBioIdentiry.jsp. Upload the
    fingerprint; it must match the one given at registration
    (file name, or the same file bytes - see _fingerprint_matches)."""
    if session.get("pending_role") != "client":
        return redirect(url_for("client_login"))
    if request.method == "POST":
        f = request.files.get("pic2")
        name = session.get("pending_user")
        row = q("SELECT * FROM user WHERE username=?", (name,), one=True)
        up_name = secure_filename(f.filename) if f and f.filename else ""
        up_bytes = f.read() if f and f.filename else b""
        if row and _fingerprint_matches(row["thumbname"],
                                        row["thumbimage"], up_name, up_bytes):
            session.pop("pending_user", None)
            session.pop("pending_role", None)
            session["role"] = "client"
            session["username"] = name
            return redirect(url_for("client_main"))
        flash("Finger Print Mismatch, Please Provide Correct "
              "Finger Print!!")
        return render_template("biometric.html", role="client",
                               back=url_for("client_login"))
    return render_template("biometric.html", role="client",
                           back=url_for("client_login"))


@app.route("/client/")
def client_main():
    """ClientMain.jsp - 'WELCOME TO USER :: <name>'. Menu: Home /
    View All Files / Download / Log Out."""
    if _require("client"):
        return _require("client")
    return render_template("client_main.html",
                           username=session["username"])


@app.route("/client/files")
def client_files():
    """View_All_Files.jsp - all cloudserver files with File Name,
    Session Key (trapdoor), Private Key (sk), Rank, Date & Time,
    Access Authorization, File Owner."""
    if _require("client"):
        return _require("client")
    files = q("SELECT * FROM cloudserver ORDER BY id")
    return render_template("file_list.html", files=files,
                           title="VIEW ALL FILES", back="client_main",
                           menu="client")


@app.route("/client/download", methods=["GET", "POST"])
def client_download():
    """Download.jsp -> Download1.jsp. Enter File Name (t1) and Owner
    Name (t22). Download1.jsp first checks that some file has
    Access='Yes'; if not: 'You are not Authorized!! Please Contact
    Proxy Server!!!'. Then it shows the file with its secret key
    and logs a 'Downloaded' transaction."""
    if _require("client"):
        return _require("client")
    if request.method == "POST":
        fname = request.form.get("t1", "").strip()
        oname = request.form.get("t22", "").strip()
        any_access = q("SELECT * FROM cloudserver WHERE Access='Yes'",
                       one=True)
        if not any_access:
            flash("You are not Authorized!! Please Contact Proxy "
                  "Server!!!")
            return render_template("download.html")
        row = q("SELECT * FROM cloudserver WHERE fname=?", (fname,),
                one=True)
        if not row:
            flash("File Doesn't Exist !!!")
            return render_template("download.html")
        _log_transaction(session["username"], fname, row["sk"],
                         "Downloaded")
        return render_template("download1.html", row=row, oname=oname)
    return render_template("download.html")


@app.route("/client/download2", methods=["POST"])
def client_download2():
    """Download2.jsp. Enter the secret key (t13). If Access is 'Yes'
    and the key matches (and is not 'No'), the rank goes up by 1 and
    the decrypted file content is shown with a Download link.
    Wrong key or no access -> the user is logged in `attacker` and
    shown 'No Secret Key Generated or Secret key is mis Matched !!!'
    / 'No Access Permission For this File !!!'."""
    if _require("client"):
        return _require("client")
    fname = request.form.get("t1", "").strip()
    oname = request.form.get("t12", "").strip()
    sk = request.form.get("t13", "").strip()
    row = q("SELECT * FROM cloudserver WHERE fname=?", (fname,), one=True)
    if not row:
        flash("File Doesn't Exist !!!")
        return render_template("download.html")
    if row["Access"] != "Yes":
        _log_attacker(session["username"], fname, sk)
        flash("No Access Permission For this File !!!")
        return render_template("download.html")
    if row["sk"] and row["sk"] != "No" and row["sk"] == sk:
        execute("UPDATE cloudserver SET rank=? WHERE id=?",
                ((row["rank"] or 0) + 1, row["id"]))
        execute("UPDATE authorityfile SET rank=? WHERE fname=?",
                ((row["rank"] or 0) + 1, fname))
        session["verified_file"] = row["id"]
        content = decrypt_text(row["ct"])
        return render_template("download2.html", row=row, oname=oname,
                               content=content)
    _log_attacker(session["username"], fname, sk)
    flash("No Secret Key Generated or Secret key is mis Matched !!!")
    return render_template("download.html")


@app.route("/client/download-file/<int:fid>")
def client_download_file(fid):
    """The Download link on the Download2 page: sends the decrypted
    file. Only after a correct secret key in this session."""
    if _require("client"):
        return _require("client")
    if session.get("verified_file") != fid:
        flash("No Access Permission For this File !!!")
        return redirect(url_for("client_download"))
    row = q("SELECT * FROM cloudserver WHERE id=?", (fid,), one=True)
    if not row:
        flash("File Doesn't Exist !!!")
        return redirect(url_for("client_download"))
    content = decrypt_text(row["ct"])
    path = os.path.join(BASE_DIR, "instance",
                        "dl_%d_%s" % (fid, secure_filename(row["fname"])))
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return send_file(path, as_attachment=True,
                     download_name=row["fname"])


# --- Client OTP flow (repaired, see module docstring) ---
# ClientAuthentication.jsp -> ClientOTP.jsp (missing in the zip) ->
# OTPCheck.jsp. OTPCheck.jsp checks user.otp, a column that does not
# exist in Database.sql. Here the OTP is generated at login and
# shown on the OTP page (no SMS/email in the original).

@app.route("/client/otp", methods=["GET", "POST"])
def client_otp():
    """ClientAuthentication.jsp: name + password, then an OTP page.
    The demo OTP is shown on the page (the original had no way to
    send it)."""
    if request.method == "POST":
        name = request.form.get("userid", "").strip()
        row = q("SELECT * FROM user WHERE username=?", (name,), one=True)
        if not row or not check_user_password(
                row["password"], request.form.get("pass", "")):
            return redirect(url_for("wronglogin"))
        otp = gen_otp()
        session["otp_user"] = name
        session["otp_value"] = otp
        return render_template("otp.html", otp=otp, username=name)
    return render_template("otp_login.html")


@app.route("/client/otp-check", methods=["POST"])
def client_otp_check():
    """OTPCheck.jsp. Correct OTP -> ClientMain.jsp. Wrong OTP -> the
    user is logged in `attacker` (fname 'OTP Attacker') and shown
    wrongotp.jsp."""
    otp = request.form.get("otp", "").strip()
    name = session.get("otp_user")
    if name and otp and otp == session.get("otp_value"):
        session.pop("otp_user", None)
        session.pop("otp_value", None)
        session["role"] = "client"
        session["username"] = name
        return redirect(url_for("client_main"))
    _log_attacker(name, "OTP Attacker", otp)
    return render_template("wrongotp.html")


# ---------------------------------------------------------------- owner
# AuthorityLogin.jsp -> DO_Authentication.jsp -> Owner_BioIdentification
# .jsp -> OBioIdentiry.jsp -> AuthorityMain.jsp ("WELCOME TO OWNER")
# O_Register.jsp -> o_InsertData.jsp ; Upload.jsp -> Upload1.jsp ->
# Upload2.jsp

@app.route("/owner/register", methods=["GET", "POST"])
def owner_register():
    """O_Register.jsp. Same fields as the client registration
    (userid, pass, email, mobile, address, dob, gender, pincode,
    pic, pic2). New owners start with status 'Waiting'."""
    if request.method == "POST":
        uname = request.form.get("userid", "").strip()
        if not uname:
            flash("Owner Name is required.")
            return render_template("register.html", role="owner")
        if q("SELECT * FROM owner WHERE username=?", (uname,), one=True):
            flash("consumer Name Already Exist")
            return render_template("register.html", role="owner")
        pic = request.files.get("pic")
        fp = request.files.get("pic2")
        pic_bytes = pic.read() if pic and pic.filename else b""
        fp_bytes = fp.read() if fp and fp.filename else b""
        fp_name = secure_filename(fp.filename) if fp and fp.filename else ""
        execute(
            "INSERT INTO owner (username,password,email,mobile,address,"
            "dob,gender,pincode,status,image,thumbimage,thumbname) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uname, generate_password_hash(request.form.get("pass", "")),
             request.form.get("email", ""), request.form.get("mobile", ""),
             request.form.get("address", ""), request.form.get("dob", ""),
             request.form.get("gender", ""), request.form.get("pincode", ""),
             "Waiting", pic_bytes, fp_bytes, fp_name))
        flash("Registered Successfully")
        return redirect(url_for("owner_login"))
    return render_template("register.html", role="owner")


@app.route("/owner/login", methods=["GET", "POST"])
def owner_login():
    """AuthorityLogin.jsp ('WELCOME TO OWNER LOGIN'). Posts to
    DO_Authentication.jsp, which checks the `owner` table."""
    if request.method == "POST":
        name = request.form.get("userid", "").strip()
        result = _person_login("owner", name, request.form.get("pass", ""))
        if result is None or result == "waiting":
            return redirect(url_for("wronglogin"))
        session["pending_user"] = name
        session["pending_role"] = "owner"
        return redirect(url_for("owner_bio"))
    return render_template("login.html", role="owner",
                           title="WELCOME TO OWNER LOGIN")


@app.route("/owner/biometric", methods=["GET", "POST"])
def owner_bio():
    """Owner_BioIdentification.jsp -> OBioIdentiry.jsp. Fingerprint
    must match the owner's registered fingerprint."""
    if session.get("pending_role") != "owner":
        return redirect(url_for("owner_login"))
    if request.method == "POST":
        f = request.files.get("pic2")
        name = session.get("pending_user")
        row = q("SELECT * FROM owner WHERE username=?", (name,), one=True)
        up_name = secure_filename(f.filename) if f and f.filename else ""
        up_bytes = f.read() if f and f.filename else b""
        if row and _fingerprint_matches(row["thumbname"],
                                        row["thumbimage"], up_name, up_bytes):
            session.pop("pending_user", None)
            session.pop("pending_role", None)
            session["role"] = "owner"
            session["username"] = name
            return redirect(url_for("owner_main"))
        flash("Finger Print Mismatch, Please Provide Correct "
              "Finger Print!!")
        return render_template("biometric.html", role="owner",
                               back=url_for("owner_login"))
    return render_template("biometric.html", role="owner",
                           back=url_for("owner_login"))


@app.route("/owner/")
def owner_main():
    """AuthorityMain.jsp - 'WELCOME TO OWNER :: <name>'. Menu: Home /
    Upload / View All Uploaded Files / View All Transactions /
    Log Out."""
    if _require("owner"):
        return _require("owner")
    return render_template("owner_main.html",
                           username=session["username"])


@app.route("/owner/upload", methods=["GET", "POST"])
def owner_upload():
    """Upload.jsp - 'Upload Data !!!'. Select File (t42, the file
    chooser fills the textarea with the file text by JavaScript),
    File Name (tt), file content (text), Session Key (t4, read-only).
    Posts to Upload1.jsp."""
    if _require("owner"):
        return _require("owner")
    if request.method == "POST":
        return redirect(url_for("owner_upload1"), code=307)
    return render_template("upload.html")


@app.route("/owner/upload1", methods=["POST"])
def owner_upload1():
    """Upload1.jsp - 'Confirm Upload Data'. The original computed
    the SHA-1 trapdoor of the content and Base64-encoded it (the
    AES cipher object it created was never used). Shows File Name,
    the encrypted (Base64) value and the Session Key (SHA-1 hex),
    then posts to Upload2.jsp."""
    if _require("owner"):
        return _require("owner")
    fname = request.form.get("tt", "").strip()
    content = request.form.get("text", "")
    up = request.files.get("t42")
    if up and up.filename:
        fname = fname or secure_filename(up.filename)
        if not content:
            content = up.read().decode("utf-8", errors="ignore")
    mac = trapdoor(content)
    enc_preview = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return render_template("upload1.html", fname=fname, content=content,
                           mac=mac, enc_preview=enc_preview)


@app.route("/owner/upload2", methods=["POST"])
def owner_upload2():
    """Upload2.jsp - 'Data Uploaded Successfully !!!'. Stores the
    file in cloudserver AND authorityfile (ct = Fernet-encrypted
    content here, plain text in the original; trapdoor = SHA-1;
    sk = 'No'; rank = 0; Access = 'No'), logs an 'Upload'
    transaction and a results row (time delay / throughput, as the
    original computed from the upload time)."""
    if _require("owner"):
        return _require("owner")
    t0 = time.time()
    fname = request.form.get("t42", "").strip()
    content = request.form.get("text2", "")
    mac = request.form.get("t4", "")
    if not fname:
        flash("File Name is required.")
        return redirect(url_for("owner_upload"))
    dt = now_str()
    user = session["username"]
    ct = encrypt_text(content)
    for table in ("cloudserver", "authorityfile"):
        execute(
            "INSERT INTO %s (fname,ct,trapdoor,sk,rank,dt,Access,user) "
            "VALUES (?,?,?,?,?,?,?,?)" % table,
            (fname, ct, mac, "No", 0, dt, "No", user))
    _log_transaction(user, fname, "No", "Upload")
    ttime = max(int((time.time() - t0) * 1000), 1)
    tpt = int(len(content) / ttime * 1024) if ttime else 0
    execute("INSERT INTO results (fname,tdelay,tpt) VALUES (?,?,?)",
            (fname, str(ttime), str(tpt)))
    return render_template("upload2.html")


@app.route("/owner/files")
def owner_files():
    """ViewAllAuthorityFiles.jsp - 'View All Uploaded Data': File
    Name, Sesssion Key (trapdoor), Privatge Key (sk), Rank, Date &
    Time, Access Authorization."""
    if _require("owner"):
        return _require("owner")
    files = q("SELECT * FROM authorityfile ORDER BY id")
    return render_template("file_list.html", files=files,
                           title="View All Uploaded Data",
                           back="owner_main", menu="owner")


@app.route("/owner/transactions")
def owner_transactions():
    """ViewAllTransactions.jsp - 'View All Transactions': Client
    Name, File Name, Operation, Date & Time."""
    if _require("owner"):
        return _require("owner")
    rows = q('SELECT * FROM "transaction" ORDER BY id')
    return render_template("transaction_list.html", rows=rows,
                           title="View All Transactions",
                           back="owner_main", menu="owner")


# ---------------------------------------------------------------- cloud
# CloudLogin.jsp -> CAuthentication.jsp -> CloudMain.jsp
# ("WELCOME TO CLOUD SERVER")

@app.route("/cloud/login", methods=["GET", "POST"])
def cloud_login():
    """CloudLogin.jsp ('WELCOME TO CLOUD SERVER LOGIN'). Posts to
    CAuthentication.jsp, which checks the `cloud` table."""
    if request.method == "POST":
        row = _fixed_login("cloud", request.form.get("userid", "").strip(),
                           request.form.get("pass", ""))
        if not row:
            return redirect(url_for("wronglogin"))
        session["role"] = "cloud"
        session["username"] = row["name"]
        return redirect(url_for("cloud_main"))
    return render_template("login.html", role="cloud",
                           title="WELCOME TO CLOUD SERVER LOGIN")


@app.route("/cloud/")
def cloud_main():
    """CloudMain.jsp - 'WELCOME TO CLOUD SERVER'. Menu: Home /
    View All Owners and Authorize / View All Clients and Authorize /
    View All Cloud Files / View All Transactions / View All Attackers /
    View File Score Results / View Time Delay Results /
    View Throughput Results / Log Out."""
    if _require("cloud"):
        return _require("cloud")
    return render_template("cloud_main.html",
                           username=session["username"])


@app.route("/cloud/owners")
def cloud_owners():
    """ViewClients.jsp - 'View All Data Owners' (the original's
    title; the table lists `owner` rows): ID, Data Owner Name,
    Status, with a details link and an Authorize link."""
    if _require("cloud"):
        return _require("cloud")
    rows = q("SELECT * FROM owner ORDER BY id")
    return render_template("person_list.html", rows=rows,
                           title="View All Data Owners",
                           kind="owner", back="cloud_main")


@app.route("/cloud/clients")
def cloud_clients():
    """D_ViewOwners.jsp - 'View All Clients' (the original's title;
    the table lists `user` rows): ID, Data Client Name, Status."""
    if _require("cloud"):
        return _require("cloud")
    rows = q("SELECT * FROM user ORDER BY id")
    return render_template("person_list.html", rows=rows,
                           title="View All Clients",
                           kind="user", back="cloud_main")


@app.route("/cloud/authorize-owner/<int:pid>")
def cloud_authorize_owner(pid):
    """C_StatusClient.jsp - sets an owner's status to 'Authorized'."""
    if _require("cloud"):
        return _require("cloud")
    execute("UPDATE owner SET status='Authorized' WHERE id=?", (pid,))
    return redirect(url_for("cloud_owners"))


@app.route("/cloud/authorize-client/<int:pid>")
def cloud_authorize_client(pid):
    """C_StatusOwner.jsp - sets a client's status to 'Authorized'."""
    if _require("cloud"):
        return _require("cloud")
    execute("UPDATE user SET status='Authorized' WHERE id=?", (pid,))
    return redirect(url_for("cloud_clients"))


@app.route("/cloud/owner-details")
def cloud_owner_details():
    """C_OwnerDetails.jsp - one owner's details (Name, E-Mail,
    Mobile, Date Of Birth, Address) with profile picture."""
    if _require("cloud"):
        return _require("cloud")
    row = q("SELECT * FROM owner WHERE username=?",
            (request.args.get("name", ""),), one=True)
    return render_template("person_details.html", row=row, kind="owner",
                           back="cloud_owners")


@app.route("/cloud/client-details")
def cloud_client_details():
    """C_ClientDetails.jsp - one client's details."""
    if _require("cloud"):
        return _require("cloud")
    row = q("SELECT * FROM user WHERE username=?",
            (request.args.get("name", ""),), one=True)
    return render_template("person_details.html", row=row, kind="user",
                           back="cloud_clients")


@app.route("/cloud/files")
def cloud_files():
    """ViewAllCloudFiles.jsp - 'View All Cloud Files': File Name,
    Session Key (trapdoor), Private Key (sk), Rank, Date & Time,
    Access Authorization, File Owner, Give Access Control."""
    if _require("cloud"):
        return _require("cloud")
    files = q("SELECT * FROM cloudserver ORDER BY id")
    return render_template("file_list.html", files=files,
                           title="View All Cloud Files",
                           back="cloud_main", menu="cloud")


@app.route("/cloud/access/<int:fid>", methods=["GET", "POST"])
def cloud_access(fid):
    """C_Access_Control.jsp -> FileBioIdentiry.jsp. The Cloud Server
    uploads a fingerprint; if it matches any owner's registered
    fingerprint (thumbname), the file's Access becomes 'Yes' and
    the page goes back to View All Cloud Files. Otherwise:
    'Finger Print Mismatch, Please Provide Correct Finger Print!!'"""
    if _require("cloud"):
        return _require("cloud")
    if request.method == "POST":
        f = request.files.get("pic2")
        up_name = secure_filename(f.filename) if f and f.filename else ""
        up_bytes = f.read() if f and f.filename else b""
        owners = q("SELECT * FROM owner")
        ok = any(_fingerprint_matches(o["thumbname"], o["thumbimage"],
                                      up_name, up_bytes) for o in owners)
        if ok:
            execute("UPDATE cloudserver SET Access='Yes' WHERE id=?",
                    (fid,))
            return redirect(url_for("cloud_files"))
        flash("Finger Print Mismatch, Please Provide Correct "
              "Finger Print!!")
        return render_template("biometric.html", role="cloud",
                               back=url_for("cloud_files"),
                               fid=fid, action="cloud_access")
    return render_template("biometric.html", role="cloud",
                           back=url_for("cloud_files"), fid=fid,
                           action="cloud_access")


@app.route("/cloud/transactions")
def cloud_transactions():
    """ViewAllCloudTransactions.jsp - 'View All Cloud Transactions':
    Client Name, File Name, Operation, Date & Time."""
    if _require("cloud"):
        return _require("cloud")
    rows = q('SELECT * FROM "transaction" ORDER BY id')
    return render_template("transaction_list.html", rows=rows,
                           title="View All Cloud Transactions",
                           back="cloud_main", menu="cloud")


@app.route("/cloud/attackers")
def cloud_attackers():
    """ViewAllAttackers.jsp - 'View All Cloud Attackers': Attacker
    Name, File Name, Secret Key Used, Date & Time. (AViewOTP.jsp in
    the original was meant to show the same attacker rows - it is
    broken in the original (JDBC-ODBC to a different database), so
    it shows this list too.)"""
    if _require("cloud"):
        return _require("cloud")
    rows = q("SELECT * FROM attacker ORDER BY rowid")
    return render_template("attacker_list.html", rows=rows,
                           title="View All Cloud Attackers",
                           back="cloud_main", menu="cloud")


@app.route("/cloud/results")
def cloud_results():
    """ViewResults.jsp / Results.jsp - 'View Results' / 'Transaction
    Results'. The original loads a JavaScript chart (jscharts.js);
    here the same numbers are drawn as bars with plain CSS."""
    if _require("cloud"):
        return _require("cloud")
    rows = q("SELECT * FROM results ORDER BY fname")
    files = q("SELECT * FROM cloudserver ORDER BY id")
    return render_template("results.html", rows=rows, files=files,
                           title="View Results")


@app.route("/cloud/results-td")
def cloud_results_td():
    """C_ViewTDResults.jsp - 'View Data Time Delay Results !!!'"""
    if _require("cloud"):
        return _require("cloud")
    rows = q("SELECT * FROM results ORDER BY fname")
    return render_template("results_table.html", rows=rows,
                           col="tdelay", col_title="Time Delay",
                           title="View Data Time Delay Results !!!")


@app.route("/cloud/results-tpt")
def cloud_results_tpt():
    """C_ViewTPTResults.jsp - 'View TPT Results' (throughput)."""
    if _require("cloud"):
        return _require("cloud")
    rows = q("SELECT * FROM results ORDER BY fname")
    return render_template("results_table.html", rows=rows,
                           col="tpt", col_title="Throughput",
                           title="View TPT Results")


# ---------------------------------------------------------------- trustee
# TrusteeLogin.jsp -> TAuthentication.jsp -> TrusteeMain.jsp
# ("WELCOME TO Authentication Server...")

@app.route("/trustee/login", methods=["GET", "POST"])
def trustee_login():
    """TrusteeLogin.jsp ('Trustee Login'). Posts to
    TAuthentication.jsp, which checks the `trustee` table."""
    if request.method == "POST":
        row = _fixed_login("trustee",
                           request.form.get("userid", "").strip(),
                           request.form.get("pass", ""))
        if not row:
            return redirect(url_for("wronglogin"))
        session["role"] = "trustee"
        session["username"] = row["name"]
        return redirect(url_for("trustee_main"))
    return render_template("login.html", role="trustee",
                           title="Trustee Login")


@app.route("/trustee/")
def trustee_main():
    """TrusteeMain.jsp - 'WELCOME TO Authentication Server...'.
    CA Menu: Home / Generate Private Key / View All Attackers /
    Log Out."""
    if _require("trustee"):
        return _require("trustee")
    return render_template("trustee_main.html",
                           username=session["username"])


@app.route("/trustee/generate-key")
def trustee_generate_key():
    """GenerateKey.jsp - 'View Files and Generate Private Key':
    File Name, Digital Sign (trapdoor), Secret Key, Rank, Date &
    Time, Access Authorization, File Owner. Files whose secret key
    is still 'No' get a 'Generate Private Key' link."""
    if _require("trustee"):
        return _require("trustee")
    files = q("SELECT * FROM cloudserver ORDER BY id")
    return render_template("generate_key.html", files=files)


@app.route("/trustee/generate-key/<int:fid>", methods=["GET", "POST"])
def trustee_generate_key_form(fid):
    """TA_GenerateKey.jsp -> KeyBioIdentiry.jsp. The Trustee uploads
    a fingerprint; if it matches any owner's registered fingerprint,
    a new secret key is generated for the file (in both cloudserver
    and authorityfile) and the page returns to GenerateKey.jsp.
    Otherwise: 'Finger Print Mismatch, Please Provide Correct
    Finger Print!!'"""
    if _require("trustee"):
        return _require("trustee")
    if request.method == "POST":
        f = request.files.get("pic2")
        up_name = secure_filename(f.filename) if f and f.filename else ""
        up_bytes = f.read() if f and f.filename else b""
        owners = q("SELECT * FROM owner")
        ok = any(_fingerprint_matches(o["thumbname"], o["thumbimage"],
                                      up_name, up_bytes) for o in owners)
        if ok:
            return redirect(url_for("trustee_generate_key_direct",
                                    fid=fid))
        flash("Finger Print Mismatch, Please Provide Correct "
              "Finger Print!!")
        return render_template("biometric.html", role="trustee",
                               back=url_for("trustee_generate_key"),
                               fid=fid, action="trustee_generate_key_form")
    return render_template("biometric.html", role="trustee",
                           back=url_for("trustee_generate_key"), fid=fid,
                           action="trustee_generate_key_form")


@app.route("/trustee/generate-key-direct/<int:fid>")
def trustee_generate_key_direct(fid):
    """GenerateKey1.jsp - generates the secret key for a file
    directly (no fingerprint step). In the original this is what
    KeyBioIdentiry.jsp does after a matching fingerprint: it makes
    an RSA key pair and stores String.valueOf(public key bytes) as
    the sk. Here it stores a real random 12-character secret key
    in both cloudserver and authorityfile."""
    if _require("trustee"):
        return _require("trustee")
    sk = gen_secret_key()
    execute("UPDATE cloudserver SET sk=? WHERE id=?", (sk, fid))
    execute("UPDATE authorityfile SET sk=? WHERE id=?", (sk, fid))
    flash("Secret Key generated for file id %d: %s" % (fid, sk))
    return redirect(url_for("trustee_generate_key"))


@app.route("/trustee/attackers")
def trustee_attackers():
    """ViewAttackers.jsp - 'View All Attackers': Attacker Name,
    File Name, Secret Key Used, Date & Time."""
    if _require("trustee"):
        return _require("trustee")
    rows = q("SELECT * FROM attacker ORDER BY rowid")
    return render_template("attacker_list.html", rows=rows,
                           title="View All Attackers",
                           back="trustee_main", menu="trustee")


# ---------------------------------------------------------------- authority
# AAuthentication.jsp -> AuthorityMain.jsp. No login form in the
# original posts to AAuthentication.jsp (it is dead code in the
# original); it is kept here as a working login for the fixed
# `authority` account, opening the same Owner main page.

@app.route("/authority/login", methods=["GET", "POST"])
def authority_login():
    """AAuthentication.jsp - checks the `authority` table
    (authority / authority) and opens AuthorityMain.jsp."""
    if request.method == "POST":
        row = _fixed_login("authority",
                           request.form.get("userid", "").strip(),
                           request.form.get("pass", ""))
        if not row:
            return redirect(url_for("wronglogin"))
        session["role"] = "owner"
        session["username"] = row["name"]
        return redirect(url_for("owner_main"))
    return render_template("login.html", role="authority",
                           title="WELCOME TO OWNER LOGIN")


# ---------------------------------------------------------------- images

@app.route("/image/<kind>/<int:pid>")
def serve_image(kind, pid):
    """ownprofileimage.jsp / userprofileimage.jsp - serve the stored
    profile picture of an owner or a user."""
    table = "owner" if kind == "owner" else "user"
    row = q("SELECT image FROM %s WHERE id=?" % table, (pid,), one=True)
    data = bytes(row["image"]) if row and row["image"] else b""
    if not data:
        data = _seed_image_bytes("User.jpg")
    import io
    return send_file(io.BytesIO(data), mimetype="image/jpeg")


@app.route("/image/thumb/<kind>/<int:pid>")
def serve_thumb(kind, pid):
    """Serve the stored fingerprint (thumbimage) of an owner/user."""
    table = "owner" if kind == "owner" else "user"
    row = q("SELECT thumbimage, thumbname FROM %s WHERE id=?" % table,
            (pid,), one=True)
    data = bytes(row["thumbimage"]) if row and row["thumbimage"] else b""
    if not data:
        data = _seed_image_bytes("User.jpg")
    import io
    name = (row["thumbname"] or "fingerprint").lower()
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    return send_file(io.BytesIO(data), mimetype=mime)


# ---------------------------------------------------------------- start

_DB_READY = False


@app.before_request
def _ensure_db():
    """Create tables + seed data on the first request too, so the
    app also works when started with `flask run` or from Spyder
    without going through __main__."""
    global _DB_READY
    if not _DB_READY:
        init_db()
        _DB_READY = True


if __name__ == "__main__":
    with app.app_context():
        init_db()
    db_label = ("mysql %s@%s:%s/%s" % (config.MYSQL_USER,
                                       config.MYSQL_HOST,
                                       config.MYSQL_PORT, config.MYSQL_DB)
                if _is_mysql() else
                "SQLite %s" % os.path.join(BASE_DIR, config.SQLITE_FILE))
    print("Biometric-Based Secure Access Mechanism for Cloud Services "
          "(Python/Flask, converted from the real Java/JSP source)")
    print("Database:", db_label)
    print("Open http://127.0.0.1:5000")
    print("Demo logins - Owner: Raja/Raja | Client: Harish/Harish | "
          "Cloud Server: Server/Server | Trustee: AServer/AServer | "
          "Authority: authority/authority")
    if Fernet is None:
        print("WARNING: 'cryptography' is not installed - file content "
              "will be stored Base64-only. Run: pip install cryptography")
    app.run(host="127.0.0.1", port=5000, debug=True)
