#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820

import sigrhe_parser
import sigrhe_database
from sigrhe_contract import Contract
from time import sleep
from setup_logger import logger

try:
    sigrhe_session = sigrhe_parser.init_session()
    contracts = sigrhe_parser.get_contract_list(sigrhe_session)
    logger.info("Found %s contracts" % len(contracts))

    db_connection = sigrhe_database.get_database_connection()
    existing_contract_ids = sigrhe_database.get_all_contracts_ids(db_connection)

    for contract in contracts:
        # check if contract already exists
        if contract.id in existing_contract_ids:
            # remove it from the list
            existing_contract_ids.remove(contract.id)
        else:
            # if it's new get extra details
            (
                contract.class_project,
                contract.qualifications,
            ) = sigrhe_parser.get_contract_details(sigrhe_session, contract.id)

            if contract.class_project == None:
                logger.critical(
                    "Could not retrieve details for contract %s" % contract.id
                )
            else:
                # add it to our system
                sigrhe_database.add_new_contract(db_connection, contract)
                logger.info("Adding: %s" % contract.id)

            # let's sleep between requests to avoid being flagged as DOS attack
            sleep(5)

    # Mark the remaining existing_contract_ids as expired
    for id in existing_contract_ids:
        sigrhe_database.mark_contract_as_expired(db_connection, id)
        logger.info("[%s] marked as expired" % id)

except Exception as detail:
    logger.critical(str(detail))
