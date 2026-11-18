-- Biometric-Based Secure Access Mechanism for Cloud Services
-- MySQL schema. Tables and columns are exactly as in the original
-- DATABASE/Database.sql (database `Designing`).
-- Run in MySQL Workbench, or let app.py run it on first start.
-- SQLite version: schema.sql

CREATE DATABASE IF NOT EXISTS `Designing`;
USE `Designing`;

CREATE TABLE IF NOT EXISTS `attacker` (
    `user` text,
    `fname` text,
    `sk` text,
    `dt` text
);

CREATE TABLE IF NOT EXISTS `authority` (
    `name` text,
    `pass` text
);

CREATE TABLE IF NOT EXISTS `authorityfile` (
    `id` int(11) NOT NULL auto_increment,
    `fname` text,
    `ct` text,
    `trapdoor` text,
    `sk` text,
    `rank` int(11) default NULL,
    `dt` text,
    `Access` text,
    `user` text,
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `cloud` (
    `name` text,
    `pass` text
);

CREATE TABLE IF NOT EXISTS `cloudserver` (
    `id` int(11) NOT NULL auto_increment,
    `fname` text,
    `ct` text,
    `trapdoor` text,
    `sk` text,
    `rank` int(11) default NULL,
    `dt` text,
    `Access` text,
    `user` text,
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `owner` (
    `id` int(11) NOT NULL auto_increment,
    `username` varchar(45) default NULL,
    `password` varchar(255) default NULL,
    `email` varchar(45) default NULL,
    `mobile` varchar(45) default NULL,
    `address` text,
    `dob` varchar(45) default NULL,
    `gender` varchar(45) default NULL,
    `pincode` varchar(45) default NULL,
    `status` varchar(45) default NULL,
    `image` longblob,
    `thumbimage` longblob,
    `thumbname` text,
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `results` (
    `fname` text,
    `tdelay` text,
    `tpt` text
);

CREATE TABLE IF NOT EXISTS `transaction` (
    `id` int(11) NOT NULL auto_increment,
    `user` text,
    `fname` text,
    `sk` text,
    `task` text,
    `dt` text,
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `trustee` (
    `name` text,
    `pass` text
);

CREATE TABLE IF NOT EXISTS `user` (
    `id` int(11) NOT NULL auto_increment,
    `username` varchar(45) default NULL,
    `password` varchar(255) default NULL,
    `email` varchar(45) default NULL,
    `mobile` varchar(45) default NULL,
    `address` text,
    `dob` varchar(45) default NULL,
    `gender` varchar(45) default NULL,
    `pincode` varchar(45) default NULL,
    `status` varchar(45) default NULL,
    `image` longblob,
    `thumbimage` longblob,
    `thumbname` text,
    PRIMARY KEY (`id`)
);
