# Database settings for the Biometric-Based Secure Access Mechanism
# for Cloud Services app (Python / Flask version, converted from the
# REAL Java/JSP source the user shared on 2026-11-11).
#
# HOW TO CHOOSE:
#   * MySQL (default for THIS project) - the user has MySQL / MySQL
#     Workbench. The app creates the `Designing` database and its
#     tables by itself on first run (schema_mysql.sql), or you can run
#     schema_mysql.sql in Workbench first. Set DB_TYPE = "mysql" (the
#     default below) and MYSQL_PASSWORD to YOUR OWN MySQL root password.
#   * SQLite (fallback) - no setup at all. The app creates app.db
#     itself. Set DB_TYPE = "sqlite" if you have no MySQL server.
#
# The database name is `Designing` - exactly as in the original
# project: connect.jsp uses jdbc:mysql://localhost:3306/Designing and
# DATABASE/Database.sql starts with "create database Designing;".
# (The nested Design_of_bio_metric sub-project inside the same zip
# uses a different database, `multi_user` - see README.md section 9.)
#
# SECURITY: change MYSQL_PASSWORD to YOUR OWN MySQL root password
# (the one you set when you installed MySQL / in MySQL Workbench).
# "root" below is only the original project's style of default. Do not
# share this file publicly with your real password in it.

import os

# "mysql" (default here) or "sqlite" (lower-case; anything else falls
# back to mysql for this project, because the user has MySQL)
DB_TYPE = os.environ.get("DB_TYPE", "mysql").strip().lower()

# SQLite settings (only used when DB_TYPE = "sqlite")
SQLITE_FILE = os.environ.get("SQLITE_FILE", "app.db")

# MySQL settings (only used when DB_TYPE = "mysql")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "root")
MYSQL_DB = os.environ.get("MYSQL_DB", "Designing")

# Flask secret key for the login session cookie. Change this to any
# random text of your own if you show the project to other people.
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "biometric-designing-demo-key")
