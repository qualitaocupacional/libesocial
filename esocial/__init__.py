# Copyright 2018, Qualita Seguranca e Saude Ocupacional. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""eSocial Library

Module with functions and classes to validate and sign eSocial XML events and
access eSocial government webservices to send and retrieve events batchs.
"""
__version__ = '0.1.1'

__esocial_version__ = 'S-1.1'

__xsd_versions__ = {
    'send': {
        'version': '1.1.1',
        'xsd': 'EnvioLoteEventos-v{}.xsd',
    },
    'retrieve': {
        'version': '1.0.0',
        'xsd': 'ConsultaLoteEventos-v{}.xsd',
    },
    'send_return': {
        'version': '1.1.0',
        'xsd': 'RetornoEnvioLoteEventos-v{}.xsd',
    },
    'event_return': {
        'version': '1.2.1',
        'xsd': 'RetornoEvento-v{}.xsd'
    },
    'process_return': {
        'version': '1.3.0',
        'xsd': 'RetornoProcessamentoLote-v{}.xsd',
    },
    # new on 1.5 - Communication Package
    'view_employer_event_id': {
        'version': '1.0.0',
        'xsd': 'ConsultaIdentificadoresEventosEmpregador-v{}.xsd'
    },
    'view_table_event_id': {
        'version': '1.0.0',
        'xsd': 'ConsultaIdentificadoresEventosTabela-v{}.xsd'
    },
    'view_employee_event_id': {
        'version': '1.0.0',
        'xsd': 'ConsultaIdentificadoresEventosTrabalhador-v{}.xsd'
    },
    'view_event_id_return':{
        'version': '1.0.0',
        'xsd': 'RetornoConsultaIdentificadoresEventos-v{}.xsd'
    },
    'event_download_id':{
        'version': '1.0.0',
        'xsd': 'SolicitacaoDownloadEventosPorId-v{}.xsd'
    },
    'event_download_receipt':{
        'version': '1.0.0',
        'xsd': 'SolicitacaoDownloadEventosPorNrRecibo-v{}.xsd'
    },
    'event_download_return':{
        'version': '1.0.0',
        'xsd': 'RetornoSolicitacaoDownloadEventos-v{}.xsd'
    },
}

_TARGET = 'tests'

_WS_URL = {
    'tests': {
        'send': 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        'retrieve': 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },

    'production': {
        'send': 'https://webservices.envio.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
        'retrieve': 'https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc?wsdl',
    },
}

_WS_URL_DOWN = {
    'tests': {
        'send': 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc?wsdl',
        'download': 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc?wsdl',
    },
    'production': {
        'send': 'https://webservices.download.esocial.gov.br/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc?wsdl',
        'download': 'https://webservices.download.esocial.gov.br/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc?wsdl',
    },
}

_TARGET_TPAMB = {
    '1': 'production',
    '2': 'tests'
}