#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820

from datetime import datetime
from time import sleep
from requests import Session, Request
from bs4 import BeautifulSoup
from sigrhe_contract import Contract
from setup_config import config_parser
from setup_logger import logging

logger = logging.getLogger("session")


def init_session():
    """Prepares the session used to communicate with the SIGHRE platform"""

    session = Session()

    # headers
    session.headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "pt-PT,pt;q=0.8,en-GB;q=0.6,en;q=0.4,en-US;q=0.2",
        "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/javascript, application/javascript, */*",
        "Referer": "https://sigrhe.dgae.mec.pt/openerp/menu?active=474&tzoffset=-60",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "sigrhe.dgae.mec.pt",
        "Origin": "https://sigrhe.dgae.mec.pt",
    }

    return session


def login_to_sigrhe(session):
    """Authenticate on the SIGRHE site"""

    now = datetime.now()
    time = now.strftime("%Y-%m-%dT%H:%M:%S.058Z")

    login, password = get_authentication_data()

    payload = {
        "login_action": "login",
        "db": "DUMMY",
        "user": login,
        "password": password,
    }

    request = Request(
        "POST",
        "https://sigrhe.dgae.mec.pt/?tzoffset=-60&dt=" + time,
        data=payload,
    )

    response = session.send(session.prepare_request(request))

    if response.status_code != 200:
        logger.critical("Login failed to SIGRHE")
        raise Exception("Login failed!")

    logger.info("Login successful to SIGRHE")

    return response


def get_contract_html(session):
    """Get the contract list from the SIGRHE page"""

    # I'm not sure we need all the items in the payload, but the list contains
    # all items sent in a 'normal' user request
    payload = {
        "_terp_model": "dgrhe_ce_12_horario",
        "_terp_state": "",
        "_terp_id": "False",
        "_terp_view_mode": "[u'tree',u'form']",
        "_terp_view_type": "tree",
        "_terp_view_id": "6676",
        "_terp_domain": "[('flag_bce','=','False'),('ano_letivo','=','2020/2021')]",
        "_terp_editable": "True",
        "_terp_limit": "-1",
        "_terp_offset": "0",
        "_terp_count": "0",
        "_terp_group_by_ctx": "[]",
        "_terp_filters_context": "",
        "_terp_action_id": "5455",
        "_terp_concurrency_info": "('dgrhe_ce_12_horario,297739','2020-08-07+15:37:35.010367')",
        "_terp_view_params/_terp_model": "dgrhe_ce_12_habilitacao",
        "_terp_view_params/_terp_id": "390841",
        "_terp_view_params/_terp_ids": "[390841]",
        "_terp_view_params/_terp_view_ids": "[False,False]",
        "_terp_view_params/_terp_view_mode": "[u'tree',u'form']",
        "_terp_parent_model": "dgrhe_ce_12_habilitacao",
        "_terp_parent_id": "390841",
        "_terp_parent_view_id": "8133",
        "_terp_source": "_terp_list",
    }

    request = Request(
        "POST",
        "https://sigrhe.dgae.mec.pt/openerp/listgrid/get",
        data=payload
    )

    response = session.send(session.prepare_request(request))

    if response.status_code != 200:
        raise Exception("Failed getting contract list!")

    # The response is html and we know the data we need is between the
    # only <tbody> ... </tbody> in the response
    start_table = response.text.find("<tbody>")
    end_table = response.text.find("</tbody>", start_table)

    html_data = response.text[start_table:end_table]

    # Strip uneeded characters
    html_data = (
        html_data.replace("\t", "")
        .replace("\n", "")
        .replace("\\t", "")
        .replace("\\n", "")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\\\", "\\")
        .replace("\\xc0", "À")
        .replace("\\xc1", "Á")
        .replace("\\xe1", "á")
        .replace("\\xe3", "ã")
        .replace("\\xe2", "â")
        .replace("\\xc9", "É")
        .replace("\\xe9", "é")
        .replace("\\xea", "ê")
        .replace("\\xcd", "Í")
        .replace("\\xed", "í")
        .replace("\\xd3", "Ó")
        .replace("\\xf3", "ó")
        .replace("\\xf5", "õ")
        .replace("\\xfa", "ú")
        .replace("\\xe7", "ç")
        .replace("\\xb4", "'")
        .replace("\\xaa", "ª")
        .replace("\\xba", "º")
    )

    # Convert \uxxxx bytes from javacript to utf-8 characters
    # https://www.webforefront.com/django/pythonbasics-text.html
    #html_data = bytes(html_data, "utf-8").decode("raw_unicode_escape")

    return html_data


def get_authentication_data():
    """Reads authentication data from settings.ini file to avoid commiting
    user credentials to github"""

    sigrhe_login = config_parser.get("sigrhe", "login")
    sigrhe_password = config_parser.get("sigrhe", "password")

    return sigrhe_login, sigrhe_password


def parse_html_data(html_data):
    """Iterates over each tr element in the tree and
    returns an array of contracts"""

    contracts = []

    soup = BeautifulSoup(html_data, "lxml")

    for tr in soup.find_all("tr", class_="grid-row"):
        contract = get_new_contract(tr)
        if contract:
            contracts.append(contract)

    return contracts


def get_new_contract(tr):
    """Parses a BeautifulSoup tr element and
    builds an object with the data we need"""

    contract = None

    try:
        id = int(tr["record"])
        if id <= 0:
            return None

        #school_code = tr.find(attrs={"name": "codigo"})["value"]
        school_name = tr.find(attrs={"name": "entidade_id"}).string
        n_contract = tr.find(attrs={"name": "num_horario"})["value"]
        n_hours_per_week = tr.find(attrs={"name": "num_horas"})["value"]
        contract_end_date = tr.find(attrs={"name": "data_fim_colocacao"})["value"]
        application_deadline = tr.find(attrs={"name": "data_final_candidatura"})["value"]
        county = tr.find(attrs={"name": "concelho"})["value"]
        district = tr.find(attrs={"name": "distrito"})["value"]

        group_span = tr.find(attrs={"name": "grupo_recrutamento_id"})
        if group_span["value"] == "False":
            recruitment_group = "T. E."
        else:
            recruitment_group = group_span.string[:3]

        contract = Contract(
            id,
            0,
            str(school_name),
            int(n_contract),
            int(n_hours_per_week),
            str(contract_end_date),
            str(application_deadline),
            str(recruitment_group),
            str(county),
            str(district),
            "",
            "",
        )
        return contract
    except:
        logger.error("Unable to parse %s" % tr)
        return None


def get_contract_details(session, id):
    """ Get the extra details for a contract"""

    payload = {
        "model": "dgrhe_ce_12_horario",
        "id": id,
        "domain": "[('flag_bce', '=', 'False'), ('ano_letivo', '=', '2020/2021')]",
    }

    request = Request(
        "GET",
        "https://sigrhe.dgae.mec.pt/openerp/form/view",
        params=payload
    )

    response = session.send(session.prepare_request(request))

    if response.status_code != 200:
        logger.critical("Unable to get details for contract %s" % id)
        return None

    try:
        soup = BeautifulSoup(response.text, "lxml")

        school_code = soup.find(attrs={"id": "codigo"})["value"]
        class_project = soup.find(attrs={"id": "disciplina_projeto"})["value"]
        qualifications = soup.find(attrs={"id": "curso_habilitacao"})["value"]
        return school_code, class_project, qualifications
    except:
        logger.critical(
            "Unable to parse details for contract %s: %s" % (id, response.text)
        )
        return None


def get_contract_list(session):

    contracts = []

    # authenticate on the SIGRHE site
    login_to_sigrhe(session)

    # get contract data
    html_data = get_contract_html(session)
    contracts = parse_html_data(html_data)

    return contracts
