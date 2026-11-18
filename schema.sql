-- Biometric-Based Secure Access Mechanism for Cloud Services
-- SQLite schema. Tables and columns are exactly as in the original
-- DATABASE/Database.sql (database `Designing`), with SQLite types.
-- MySQL version: schema_mysql.sql
-- `transaction` is a reserved word in SQLite, so it is quoted.

CREATE TABLE IF NOT EXISTS attacker (
    user TEXT,
    fname TEXT,
    sk TEXT,
    dt TEXT
);

CREATE TABLE IF NOT EXISTS authority (
    name TEXT,
    pass TEXT
);

CREATE TABLE IF NOT EXISTS authorityfile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fname TEXT,
    ct TEXT,
    trapdoor TEXT,
    sk TEXT,
    rank INTEGER,
    dt TEXT,
    Access TEXT,
    user TEXT
);

CREATE TABLE IF NOT EXISTS cloud (
    name TEXT,
    pass TEXT
);

CREATE TABLE IF NOT EXISTS cloudserver (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fname TEXT,
    ct TEXT,
    trapdoor TEXT,
    sk TEXT,
    rank INTEGER,
    dt TEXT,
    Access TEXT,
    user TEXT
);

CREATE TABLE IF NOT EXISTS owner (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(45),
    password VARCHAR(255),
    email VARCHAR(45),
    mobile VARCHAR(45),
    address TEXT,
    dob VARCHAR(45),
    gender VARCHAR(45),
    pincode VARCHAR(45),
    status VARCHAR(45),
    image BLOB,
    thumbimage BLOB,
    thumbname TEXT
);

CREATE TABLE IF NOT EXISTS results (
    fname TEXT,
    tdelay TEXT,
    tpt TEXT
);

CREATE TABLE IF NOT EXISTS "transaction" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    fname TEXT,
    sk TEXT,
    task TEXT,
    dt TEXT
);

CREATE TABLE IF NOT EXISTS trustee (
    name TEXT,
    pass TEXT
);

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(45),
    password VARCHAR(255),
    email VARCHAR(45),
    mobile VARCHAR(45),
    address TEXT,
    dob VARCHAR(45),
    gender VARCHAR(45),
    pincode VARCHAR(45),
    status VARCHAR(45),
    image BLOB,
    thumbimage BLOB,
    thumbname TEXT
);
