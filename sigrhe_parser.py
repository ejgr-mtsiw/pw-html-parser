#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820

from datetime import datetime
from time import sleep
from requests import Session, Request
import configparser
from bs4 import BeautifulSoup
from sigrhe_contract import Contract


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
        # TODO: Log this!
        raise Exception("Login failed!")

    print("We're in!")

    return response


def get_contract_html(session):
    """Get the contract list from the SIGRHE page"""

    # I'm not sure we need all the items in the payload, but the list contains
    # all items sent in a 'normal' user request
    payload = {
        "_terp_search_domain": "None",
        "_terp_filter_domain": "[]",
        "_terp_search_data": "",
        "_terp_notebook_tab": "0",
        "_terp_string": "Horários",
        "_terp_model": "dgrhe_ce_12_horario",
        "_terp_state": "",
        "_terp_id": "False",
        "_terp_ids": "",
        "_terp_view_ids": "[1872, False]",
        "_terp_view_mode": "[u'tree', u'form']",
        "_terp_view_type": "tree",
        "_terp_view_id": "1872",
        "_terp_domain": "[('flag_bce', '=', 'False'), ('ano_letivo', '=', '2019/2020')]",
        "_terp_context": "{'lang': u'pt_PT', 'tz': False, 'active_model': 'ir.ui.menu', 'department_id': False, 'disabled_states': ('naocomprovado', 'finalizacao', 'anulado_reg', 'deleted', 'anulado', 'anulado_conc', 'usado_rr', 'usado_bce', 'enviado_bce', 'enviado_ce', 'enviado_rr', 'rejeitado_rr1', 'rejeitado_bce', 'anulado_rr', 'anulado_bce', 'denunciado', 'naoapre', 'naousado_rr', 'naousado_rr1', 'naousado_rr2', 'naousado_bce', 'valido_waiting'), 'disabled_$flag_cand_subm': (True,), 'disabled_$ano_letivo': ('2019/2020', '2016/2017', '2015/2016', '2014/2015', '2013/2014', '2012/2013'), 'client': 'web', 'active_ids': [], 'disable_cache': True, 'active_id': False}",
        "_terp_editable": "True",
        "_terp_limit": "-1",
        "_terp_offset": "0",
        "_terp_count": "0",
        "_terp_group_by_ctx": "[]",
        "_terp_filters_context": "",
        "_terp_action_id": "2920",
        "_terp_concurrency_info": "",
        "_terp_source": "_terp_list",
        "callback": "jsonp1533584920784",
    }

    request = Request(
        "POST", "https://sigrhe.dgae.mec.pt/openerp/listgrid/get",
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
    html_data = html_data.replace("\t", "").replace("\n", "").replace("\\t", "").replace(
        "\\n", "").replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')

    # Convert \uxxxx bytes from javacript to utf-8 characters
    # https://www.webforefront.com/django/pythonbasics-text.html
    html_data = bytes(html_data, 'utf-8').decode('raw_unicode_escape')

    return html_data


def get_authentication_data():
    """Reads authentication data from settings.ini file to avoid commiting
    user credentials to github"""

    config_parser = configparser.RawConfigParser()
    config_file_path = r'settings.ini'
    config_parser.read(config_file_path)

    sigrhe_login = config_parser.get('sigrhe', 'login')
    sigrhe_password = config_parser.get('sigrhe', 'password')

    return sigrhe_login, sigrhe_password


def parse_html_data(html_data):
    """Iterates over each tr element in the tree and
    returns an array of contracts"""

    contracts = []

    soup = BeautifulSoup(html_data, "lxml")

    for tr in soup.find_all("tr", class_='grid-row'):
        contract = get_new_contract(tr)
        if contract:
            contracts.append(contract)

    return contracts


def get_new_contract(tr):
    """Parses a BeautifulSoup tr element and
    builds an object with the data we need"""

    contract = None

    try:
        id = int(tr['record'])
        if (id <= 0):
            return None

        school_code = tr.find(attrs={"name": "codigo"})["value"]
        school_name = tr.find(attrs={"name": "entidade_id"}).string
        n_contract = tr.find(attrs={"name": "num_horario"})["value"]
        n_hours_per_week = tr.find(attrs={"name": "num_horas"})["value"]
        contract_end_date = tr.find(
            attrs={"name": "data_fim_colocacao"})["value"]
        application_deadline = tr.find(
            attrs={"name": "data_final_candidatura"})["value"]
        county = tr.find(attrs={"name": "concelho"})["value"]
        district = tr.find(attrs={"name": "distrito"})["value"]

        group_span = tr.find(attrs={"name": "grupo_recrutamento_id"})
        if group_span['value'] == "False":
            recruitment_group = "T. E."
        else:
            recruitment_group = group_span.string[:3]

        contract = Contract(
            id,
            int(school_code),
            str(school_name),
            int(n_contract),
            int(n_hours_per_week),
            str(contract_end_date),
            str(application_deadline),
            str(recruitment_group),
            str(county),
            str(district),
            "",
            "")
        return contract
    except:
        # TODO: Log this!
        return None


def get_contract_details(session, id):
    """ Get the extra details for a contract"""

    payload = {"model": "dgrhe_ce_12_horario",
               "id": id,
               "domain": "[('flag_bce', '=', 'False'), ('ano_letivo', '=', '2019/2020')]"
               }

    request = Request('GET',
                      "https://sigrhe.dgae.mec.pt/openerp/form/view",
                      params=payload
                      )

    response = session.send(session.prepare_request(request))

    if response.status_code != 200:
        # TODO: Log this!
        print('Failed getting offer discipline! [' + str(id) + ']')
        return None

    try:
        soup = BeautifulSoup(response.text, "lxml")
        class_project = soup.find(attrs={"id": "disciplina_projeto"})['value']
        qualifications = soup.find(attrs={"id": "curso_habilitacao"})['value']
        return class_project, qualifications
    except:
        return None


def get_contract_list(session):

    contracts = []

    try:
        # authenticate on the SIGRHE site
        login_to_sigrhe(session)

        # get contract data
        html_data = get_contract_html(session)
        contracts = parse_html_data(html_data)
    except Exception as detail:
        # TODO: Log this!
        print("Error: " + detail)

    return contracts
