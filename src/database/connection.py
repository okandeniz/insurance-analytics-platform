"""
MySQL database connection utilities for the
Insurance Analytics Platform
"""

from __future__ import annotations

import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector.connection import MySQLConnection

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

def get_mysql_connection() -> MySQLConnection:
    """
    Create and return a connection to the project MySQL database.

    Database credentials are loaded from environment variables.
    """

    required_variables  = [
        "MYSQL_HOST",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE"
    ]

    missing_variables = [
        variable for variable in required_variables if not os.getenv(variable)
    ]

    if missing_variables:
        raise ValueError(
            "Missing required MySQL environment variables: "
            + ", ".join(missing_variables)
        )

    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )

    return connection