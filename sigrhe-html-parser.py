#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820

import sigrhe_parser
import sigrhe_database
from sigrhe_contract import Contract

# the session used to communicate with our API
# api_session = Session()

try:
    sigrhe_session = sigrhe_parser.init_session()
    contracts = sigrhe_parser.get_contract_list(sigrhe_session)

    db_connection = sigrhe_database.get_database_connection()
    existing_contract_ids = sigrhe_database.get_all_contracts_ids(
        db_connection)

    for contract in contracts:
        # check if contract already exists
        if contract.id in existing_contract_ids:
            # remove it from the list
            # TODO: Log this!
            existing_contract_ids.remove(contract.id)
            print("Already exists: "+str(contract.id))
        else:
            # if it's new get extra details
            contract.class_project, contract.qualifications = sigrhe_parser.get_contract_details(
                sigrhe_session, contract.id)

            # add it to our system
            # TODO: Log this!
            print("Adding: "+str(contract.id))
            sigrhe_database.add_new_contract(db_connection, contract)

    # TODO: mark the remaining existing_contract_ids as expired

except Exception as detail:
    # TODO: Log this!
    print(detail)
