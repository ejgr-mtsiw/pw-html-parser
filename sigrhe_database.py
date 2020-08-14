#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820

from datetime import datetime
from time import sleep
from sigrhe_contract import Contract
import psycopg2
from setup_config import config_parser
from setup_logger import logging

logger = logging.getLogger("db")


def get_database_connection():
    """Returns a valid database connection"""

    connection = None

    host, database, login, password = get_authentication_data()

    connection = psycopg2.connect(
        host=host, database=database, user=login, password=password
    )

    connection.set_client_encoding("UTF8")

    return connection


def get_all_contracts_ids(database):
    """Returns a list of all the contracts ids already in the database"""

    cursor = database.cursor()
    sql = "SELECT id FROM contracts WHERE expired = 0;"

    cursor.execute(sql)

    ids = cursor.fetchall()

    contracts_ids = [id[0] for id in ids]

    return contracts_ids


def get_authentication_data():
    """Reads authentication data from settings.ini file to avoid commiting
    user credentials to github"""

    host = config_parser.get("database", "host")
    database = config_parser.get("database", "database")
    login = config_parser.get("database", "login")
    password = config_parser.get("database", "password")

    return host, database, login, password


def add_new_contract(database, contract):
    """Inserts a new contract into the database"""

    cursor = database.cursor()

    sql = """INSERT INTO contracts
                (
                    id,
                    school_code,
                    school_name,
                    n_contract,
                    n_hours_per_week,
                    contract_end_date,
                    application_deadline,
                    recruitment_group,
                    county,
                    district,
                    class_project,
                    qualifications
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""

    data = (
        contract.id,
        contract.school_code,
        contract.school_name,
        contract.n_contract,
        contract.n_hours_per_week,
        contract.contract_end_date,
        contract.application_deadline,
        contract.recruitment_group,
        contract.county,
        contract.district,
        contract.class_project,
        contract.qualifications,
    )

    cursor.execute(sql, data)

    database.commit()


def mark_contract_as_expired(database, id):
    """Marks a contract as expired"""

    cursor = database.cursor()

    sql = """UPDATE contracts SET expired=%s WHERE id=%s;"""

    data = ("1", id)

    cursor.execute(sql, data)

    database.commit()
