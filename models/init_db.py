"""Initializes the SQLAlchemy database instance that will be used in this app that the other SQLAlchemy models will reference."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()