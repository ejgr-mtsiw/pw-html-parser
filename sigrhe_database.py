#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820

from datetime import datetime
from time import sleep
import configparser
from sigrhe_contract import Contract
import mysql.connector
from setup_logger import logging

logger = logging.getLogger('db')

def get_database_connection():
    """Returns a valid database connection"""

    connection = None

    host, database, login, password = get_authentication_data()

    connection = mysql.connector.connect(
        host=host,
        database=database,
        user=login,
        passwd=password,
        charset = 'utf8'
    )

    return connection


def get_all_contracts_ids(database):
    """Returns a list of all the contracts ids already in the database"""

    cursor = database.cursor()
    sql = "SELECT id FROM contracts WHERE `expired` = 0;"

    cursor.execute(sql)

    ids = cursor.fetchall()

    contracts_ids = [id[0] for id in ids]

    return contracts_ids


def get_authentication_data():
    """Reads authentication data from settings.ini file to avoid commiting
    user credentials to github"""

    config_parser = configparser.RawConfigParser()
    config_file_path = r'settings.ini'
    config_parser.read(config_file_path)

    host = config_parser.get('database', 'host')
    database = config_parser.get('database', 'database')
    login = config_parser.get('database', 'login')
    password = config_parser.get('database', 'password')

    return host, database, login, password


def add_new_contract(database, contract):
    """Inserts a new contract into the database"""

    cursor = database.cursor()

    sql = '''INSERT INTO `contracts` SET
                `id`=%s,
                `school_code`=%s,
                `school_name`=%s,
                `n_contract`=%s,
                `n_hours_per_week`=%s,
                `contract_end_date`=%s,
                `application_deadline`=%s,
                `recruitment_group`=%s,
                `county`=%s,
                `district`=%s,
                `class_project`=%s,
                `qualifications`=%s;'''

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
        contract.qualifications
    )

    cursor.execute(sql, data)

    database.commit()

def mark_contract_as_expired(database, id):
    """Marks a contract as expired"""

    cursor = database.cursor()

    sql = '''UPDATE `contracts` SET
                `expired`=%s
            WHERE
                `id`=%s;'''

    data = (
        "1",
        id
    )

    cursor.execute(sql, data)

    database.commit()