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
import os
import datetime

import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

import esocial

from esocial import xml
from esocial.utils import (
    format_xsd_version,
    pkcs12_data,
    encrypt_pem_file,
)

import zeep
from zeep import xsd
from zeep.transports import Transport

from lxml import etree


here = os.path.abspath(os.path.dirname(__file__))
serpro_ca_bundle = os.path.join(here, 'certs', 'serpro_full_chain.pem')


class CustomHTTPSAdapter(HTTPAdapter):

    def __init__(self, ctx_options=None):
        self.ctx_options = ctx_options
        super(CustomHTTPSAdapter, self).__init__()

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        if self.ctx_options is not None:
            context.load_verify_locations(self.ctx_options.get('cafile'))
            with encrypt_pem_file(self.ctx_options.get('cert_data'), self.ctx_options.get('key_passwd')) as pem:
                context.load_cert_chain(pem.name, password=self.ctx_options.get('key_passwd'))
        kwargs['ssl_context'] = context
        return super(CustomHTTPSAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context()
        if self.ctx_options is not None:
            context.load_verify_locations(cafile=self.ctx_options.get('cafile'))
            with encrypt_pem_file(self.ctx_options.get('cert_data'), self.ctx_options.get('key_passwd')) as pem:
                context.load_cert_chain(pem.name, password=self.ctx_options.get('key_passwd'))
        kwargs['ssl_context'] = context
        return super(CustomHTTPSAdapter, self).proxy_manager_for(*args, **kwargs)


class WSClient(object):

    def __init__(self, pfx_file=None, pfx_passw=None, employer_id=None, sender_id=None,
                 ca_file=serpro_ca_bundle, target=esocial._TARGET, esocial_version=esocial.__esocial_version__):
        self.ca_file = ca_file
        self.pfx_passw = pfx_passw
        if pfx_file is not None:
            self.cert_data = pkcs12_data(pfx_file, pfx_passw)
        else:
            self.cert_data = None
        self.batch = []
        self.event_ids = []
        self.max_batch_size = 50
        self.employer_id = employer_id
        self.sender_id = sender_id or employer_id
        # self.target = target
        self.esocial_version = esocial_version
        self._set_target(target)

    def connect(self, url):
        transport_session = requests.Session()
        transport_session.mount(
            'https://',
            CustomHTTPSAdapter(
                ctx_options={
                    'cert_data': self.cert_data,
                    'key_passwd': self.pfx_passw,
                    'cafile': self.ca_file
                }
            )
        )
        ws_transport = Transport(session=transport_session)
        return zeep.Client(
            url,
            transport=ws_transport
        )

    def _set_target(self, target):
        str_target = str(target)
        if str_target in esocial._TARGET_TPAMB:
            self.target = esocial._TARGET_TPAMB[str_target]
        else:
            self.target = str_target
    
    def _check_nrinsc(self, employer_id):
        if employer_id.get('use_full') or employer_id.get('tpInsc') == 2:
            return employer_id['nrInsc']
        return employer_id['nrInsc'][:8]

    def _event_id(self):
        id_prefix = 'ID{}{:0<14}{}'.format(
            self.employer_id.get('tpInsc'),
            self._check_nrinsc(self.employer_id),
            datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        )
        self.event_ids.append(id_prefix)
        Q = self.event_ids.count(id_prefix)
        return '{}{:0>5}'.format(id_prefix, Q)

    def clear_batch(self):
        self.batch = []
        self.event_ids = []

    def add_event(self, event, gen_event_id=False):
        if not isinstance(event, etree._ElementTree):
            raise ValueError('Not an ElementTree instance!')
        if not (self.employer_id and self.sender_id and self.cert_data):
            raise Exception('In order to add events to a batch, employer_id, sender_id, pfx_file and pfx_passw are needed!')
        if len(self.batch) < self.max_batch_size:
            if gen_event_id:
                event_id = self._event_id()
                # Normally, the element with Id attribute is the first one
                event.getroot().getchildren()[0].set('Id', event_id)
            # Signing...
            event_signed = xml.sign(event, self.cert_data)
            # Validating
            xml.XMLValidate(event_signed).validate()
            # Adding the event to batch
            self.batch.append(event_signed)
            return (event_id, event_signed)
        raise Exception('More than {} events per batch is not permitted!'.format(self.max_batch_size))

    def _xsd(self, which):
        version = format_xsd_version(esocial.__xsd_versions__[which]['version'])
        xsd_file = esocial.__xsd_versions__[which]['xsd'].format(version)
        xsd_file = os.path.join(here, 'xsd', xsd_file)
        return xml.xsd_fromfile(xsd_file)

    def validate_envelop(self, which, envelop):
        xmlschema = self._xsd(which)
        element_test = envelop
        if not isinstance(envelop, etree._ElementTree):
            element_test = etree.ElementTree(envelop)
        xml.XMLValidate(element_test, xsd=xmlschema, esocial_version=self.esocial_version).validate()

    def _make_send_envelop(self, group_id):
        version = format_xsd_version(esocial.__xsd_versions__['send']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/lote/eventos/envio/v{}'.format(version)
        batch_envelop = xml.XMLHelper('eSocial', xmlns=xmlns)
        batch_envelop.add_element(None, 'envioLoteEventos', grupo=str(group_id))
        batch_envelop.add_element('envioLoteEventos', 'ideEmpregador')
        batch_envelop.add_element(
            'envioLoteEventos/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
        )
        batch_envelop.add_element(
            'envioLoteEventos/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
        )
        batch_envelop.add_element('envioLoteEventos', 'ideTransmissor')
        batch_envelop.add_element(
            'envioLoteEventos/ideTransmissor',
            'tpInsc',
            text=str(self.sender_id['tpInsc']),
        )
        batch_envelop.add_element(
            'envioLoteEventos/ideTransmissor',
            'nrInsc',
            text=str(self.sender_id['nrInsc']),
        )
        batch_envelop.add_element('envioLoteEventos', 'eventos')
        for event in self.batch:
            # Getting the Id attribute
            event_tag = event.getroot()
            event_id = event_tag.getchildren()[0].get('Id')
            # Adding the event XML
            event_root = batch_envelop.add_element(
                'envioLoteEventos/eventos',
                'evento',
                Id=event_id,
            )
            event_root.append(event_tag)
        return batch_envelop.root

    def send(self, group_id=1, clear_batch=True):
        batch_to_send = self._make_send_envelop(group_id)
        self.validate_envelop('send', batch_to_send)
        # If no exception, batch XML is valid
        url = esocial._WS_URL[self.target]['send']
        ws = self.connect(url)
        # ws.wsdl.dump()
        BatchElement = ws.get_element('ns1:EnviarLoteEventos')
        result = ws.service.EnviarLoteEventos(BatchElement(loteEventos=batch_to_send))
        del ws
        if clear_batch:
            self.clear_batch()
        # Result is a lxml Element object
        return result

    def _make_retrieve_envelop(self, protocol_number):
        version = format_xsd_version(esocial.__xsd_versions__['retrieve']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v{}'.format(version)
        envelop_h = xml.XMLHelper('eSocial', xmlns=xmlns)
        envelop_h.add_element(None, 'consultaLoteEventos')
        envelop_h.add_element('consultaLoteEventos', 'protocoloEnvio', text=str(protocol_number))
        return envelop_h.root

    def retrieve(self, protocol_number):
        batch_to_search = self._make_retrieve_envelop(protocol_number)
        self.validate_envelop('retrieve', batch_to_search)
        # if no exception, protocol XML is valid
        url = esocial._WS_URL[self.target]['retrieve']
        ws = self.connect(url)
        # ws.wsdl.dump()
        SearchElement = ws.get_element('ns1:ConsultarLoteEventos')
        result = ws.service.ConsultarLoteEventos(SearchElement(consulta=batch_to_search))
        del ws
        return result

    def _make_employer_events_ids_evelop(self, params):
        version = format_xsd_version(esocial.__xsd_versions__['view_employer_event_id']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v{}'.format(version)
        envelop_h = xml.XMLHelper('eSocial', xmlns=xmlns)
        envelop_h.add_element(None, 'consultaIdentificadoresEvts')
        envelop_h.add_element('consultaIdentificadoresEvts', 'ideEmpregador')
        envelop_h.add_element(
            'consultaIdentificadoresEvts/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
        )
        envelop_h.add_element(
            'consultaIdentificadoresEvts/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
        )
        envelop_h.add_element('consultaIdentificadoresEvts', 'consultaEvtsEmpregador')
        envelop_h.add_element(
            'consultaIdentificadoresEvts/consultaEvtsEmpregador',
            'tpEvt',
            text=str(params.get('tpEvt')),
        )
        envelop_h.add_element(
            'consultaIdentificadoresEvts/consultaEvtsEmpregador',
            'perApur',
            text=str(params.get('perApur')),
        )
        return xml.sign(etree.ElementTree(envelop_h.root), self.cert_data)
    
    def get_employer_events_ids(self, params):
        signed_envelop = self._make_employer_events_ids_evelop(params)
        self.validate_envelop('view_employer_event_id', signed_envelop)
        url = esocial._WS_URL_DOWN[self.target]['send']
        ws = self.connect(url)
        result = ws.service.ConsultarIdentificadoresEventosEmpregador(consultaEventosEmpregador=signed_envelop.getroot())
        del ws
        return result
    
    def _make_table_events_ids_evelop(self, params):
        version = format_xsd_version(esocial.__xsd_versions__['view_table_event_id']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/consulta/identificadores-eventos/tabela/v{}'.format(version)
        envelop_h = xml.XMLHelper('eSocial', xmlns=xmlns)
        envelop_h.add_element(None, 'consultaIdentificadoresEvts')
        envelop_h.add_element('consultaIdentificadoresEvts', 'ideEmpregador')
        envelop_h.add_element(
            'consultaIdentificadoresEvts/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
        )
        envelop_h.add_element(
            'consultaIdentificadoresEvts/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
        )
        envelop_h.add_element('consultaIdentificadoresEvts', 'consultaEvtsTabela')
        envelop_h.add_element(
            'consultaIdentificadoresEvts/consultaEvtsTabela',
            'tpEvt',
            text=str(params.get('tpEvt')),
        )
        for p in ('chEvt', 'dtIni', 'dtFim'):
            if params.get(p):
                envelop_h.add_element(
                    'consultaIdentificadoresEvts/consultaEvtsTabela',
                    p,
                    text=str(params.get(p)),
                )
        return xml.sign(etree.ElementTree(envelop_h.root), self.cert_data)
    
    def get_table_events_ids(self, params):
        signed_envelop = self._make_table_events_ids_evelop(params)
        self.validate_envelop('view_table_event_id', signed_envelop)
        url = esocial._WS_URL_DOWN[self.target]['send']
        ws = self.connect(url)
        result = ws.service.ConsultarIdentificadoresEventosTabela(consultaEventosTabela=signed_envelop.getroot())
        del ws
        return result

    def _make_employee_events_ids_envelop(self, params):
        version = format_xsd_version(esocial.__xsd_versions__['view_employee_event_id']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/consulta/identificadores-eventos/trabalhador/v{}'.format(version)
        envelop_h = xml.XMLHelper('eSocial', xmlns=xmlns)
        envelop_h.add_element(None, 'consultaIdentificadoresEvts')
        envelop_h.add_element('consultaIdentificadoresEvts', 'ideEmpregador')
        envelop_h.add_element(
            'consultaIdentificadoresEvts/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
        )
        envelop_h.add_element(
            'consultaIdentificadoresEvts/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
        )
        envelop_h.add_element('consultaIdentificadoresEvts', 'consultaEvtsTrabalhador')
        for p in ('cpfTrab', 'dtIni', 'dtFim'):
            envelop_h.add_element(
                'consultaIdentificadoresEvts/consultaEvtsTrabalhador',
                p,
                text=str(params.get(p)),
            )
        return xml.sign(etree.ElementTree(envelop_h.root), self.cert_data)
    
    def get_employee_events_ids(self, params):
        signed_envelop = self._make_employee_events_ids_envelop(params)
        self.validate_envelop('view_employee_event_id', signed_envelop)
        url = esocial._WS_URL_DOWN[self.target]['send']
        ws = self.connect(url)
        result = ws.service.ConsultarIdentificadoresEventosTrabalhador(consultaEventosTrabalhador=signed_envelop.getroot())
        del ws
        return result

    def _make_download_id_envelop(self, ids):
        version = format_xsd_version(esocial.__xsd_versions__['event_download_id']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/download/solicitacao/id/v{}'.format(version)
        envelop_h = xml.XMLHelper('eSocial', xmlns=xmlns)
        envelop_h.add_element(None, 'download')
        envelop_h.add_element('download', 'ideEmpregador')
        envelop_h.add_element(
            'download/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
        )
        envelop_h.add_element(
            'download/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
        )
        envelop_h.add_element('download', 'solicDownloadEvtsPorId')
        for str_id in ids:
            envelop_h.add_element('download/solicDownloadEvtsPorId', 'id', text=str(str_id))
        # Signing
        return xml.sign(etree.ElementTree(envelop_h.root), self.cert_data)

    def download_events_by_id(self, ids):
        if ids and isinstance(ids, list):
            signed_envelop = self._make_download_id_envelop(ids)
            self.validate_envelop('event_download_id', signed_envelop)
            url = esocial._WS_URL_DOWN[self.target]['download']
            ws = self.connect(url)
            result = ws.service.SolicitarDownloadEventosPorId(solicitacao=signed_envelop.getroot())
            del ws
            return result
        raise ValueError('Parameter is not a List')

    def _make_download_receipt_envelop(self, n_protocols):        
        version = format_xsd_version(esocial.__xsd_versions__['event_download_receipt']['version'])
        xmlns = 'http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v{}'.format(version)
        envelop_h = xml.XMLHelper('eSocial', xmlns=xmlns)
        envelop_h.add_element(None, 'download')
        envelop_h.add_element('download', 'ideEmpregador')
        envelop_h.add_element(
            'download/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
        )
        envelop_h.add_element(
            'download/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
        )
        envelop_h.add_element('download', 'solicDownloadEventosPorNrRecibo')
        for str_id in n_protocols:
            envelop_h.add_element('download/solicDownloadEventosPorNrRecibo', 'nrRec', text=str(str_id))
        # Signing
        return xml.sign(etree.ElementTree(envelop_h.root), self.cert_data)

    def download_events_by_receipt(self, n_protocols):
        if n_protocols and isinstance(n_protocols, list):
            signed_envelop = self._make_download_receipt_envelop(n_protocols)
            self.validate_envelop('event_download_receipt', signed_envelop)
            url = esocial._WS_URL_DOWN[self.target]['download']
            ws = self.connect(url)
            result = ws.service.SolicitarDownloadEventosPorNrRecibo(solicitacao=signed_envelop.getroot())
            del ws
            return result
        raise ValueError('Parameter is not a List')
