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
from esocial.utils import pkcs12_data

from zeep import (
    Client,
    xsd
)
from zeep.transports import Transport

from lxml import etree


here = os.path.abspath(os.path.dirname(__file__))
serpro_ca_bundle = os.path.join(here, 'certs', 'serpro_chain_full.pem')


class CustomHTTPSAdapter(HTTPAdapter):

    def __init__(self, ctx_options=None):
        self.ctx_options = ctx_options
        super(CustomHTTPSAdapter, self).__init__()

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        if self.ctx_options is not None:
            # Probably there is a better (pythonic) way to setting this up
            context._ctx.use_certificate(self.ctx_options.get('cert'))
            context._ctx.use_privatekey(self.ctx_options.get('key'))
            context._ctx.load_verify_locations(self.ctx_options.get('cafile'))
        kwargs['ssl_context'] = context
        return super(CustomHTTPSAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context()
        if self.ctx_options is not None:
            context._ctx.use_certificate(self.ctx_options.get('cert'))
            context._ctx.use_privatekey(self.ctx_options.get('key'))
            context._ctx.load_verify_locations(self.ctx_options.get('cafile'))
        kwargs['ssl_context'] = context
        return super(CustomHTTPSAdapter, self).proxy_manager_for(*args, **kwargs)


class WSClient(object):

    def __init__(self, employer_id=None, sender_id=None, pfx_file=None, pfx_passw=None,
                 ca_file=serpro_ca_bundle, target=esocial._TARGET):
        self.ca_file = ca_file
        if pfx_file is not None:
            self.cert_data = pkcs12_data(pfx_file, pfx_passw)
        else:
            self.cert_data = None
        self.batch = []
        self.event_ids = []
        self.max_batch_size = 50
        self.employer_id = employer_id
        self.sender_id = sender_id
        self.target = target

    def _connect(self, url):
        transport_session = requests.Session()
        transport_session.mount(
            'https://',
            CustomHTTPSAdapter(
                ctx_options={
                    'cert': self.cert_data['cert'],
                    'key': self.cert_data['key'],
                    'cafile': self.ca_file
                }
            )
        )
        ws_transport = Transport(session=transport_session)
        return Client(
            url,
            transport=ws_transport
        )

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

    def add_event(self, event):
        if not isinstance(event, etree._ElementTree):
            raise ValueError('Not an ElementTree instance!')
        if not (self.employer_id and self.sender_id and self.cert_data):
            raise Exception('In order to add events to a batch, employer_id, sender_id, pfx_file and pfx_passw is needed!')
        if len(self.batch) < self.max_batch_size:
            # Normally, the element with Id attribute is the first one
            event.getroot().getchildren()[0].set('Id', self._event_id())
            # Signing...
            event_signed = xml.sign(event, self.cert_data)
            # Validating
            xml.XMLValidate(event_signed).validate()
            # Adding the event to batch
            self.batch.append(event_signed)
        else:
            raise Exception('More than {} events per batch is not permitted!'.format(self.max_batch_size))

    def _make_send_envelop(self, group_id):
        xmlns = 'http://www.esocial.gov.br/schema/lote/eventos/envio/v{}'
        version = esocial.__xsd_versions__['send']['version'].replace('.', '_')
        xmlns = xmlns.format(version)
        nsmap = {None: xmlns}
        batch_envelop = xml.create_root_element('eSocial', ns=nsmap)
        xml.add_element(batch_envelop, None, 'envioLoteEventos', grupo=str(group_id), ns=nsmap)
        xml.add_element(batch_envelop, 'envioLoteEventos', 'ideEmpregador', ns=nsmap)
        xml.add_element(
            batch_envelop,
            'envioLoteEventos/ideEmpregador',
            'tpInsc',
            text=str(self.employer_id['tpInsc']),
            ns=nsmap,
        )
        xml.add_element(
            batch_envelop,
            'envioLoteEventos/ideEmpregador',
            'nrInsc',
            text=str(self._check_nrinsc(self.employer_id)),
            ns=nsmap
        )
        xml.add_element(batch_envelop, 'envioLoteEventos', 'ideTransmissor', ns=nsmap)
        xml.add_element(
            batch_envelop,
            'envioLoteEventos/ideTransmissor',
            'tpInsc',
            text=str(self.sender_id['tpInsc']),
            ns=nsmap
        )
        xml.add_element(
            batch_envelop,
            'envioLoteEventos/ideTransmissor',
            'nrInsc',
            text=str(self.sender_id['nrInsc']),
            ns=nsmap
        )
        xml.add_element(batch_envelop, 'envioLoteEventos', 'eventos', ns=nsmap)
        for event in self.batch:
            # Getting the Id attribute
            event_tag = event.getroot()
            event_id = event_tag.getchildren()[0].get('Id')
            # Adding the event XML
            event_root = xml.add_element(
                batch_envelop,
                'envioLoteEventos/eventos',
                'evento',
                Id=event_id,
                ns=nsmap
            )
            event_root.append(event_tag)
        return batch_envelop

    def _make_retrieve_envelop(self, protocol_number):
        xmlns = 'http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v{}'
        version = esocial.__xsd_versions__['retrieve']['version'].replace('.', '_')
        xmlns = xmlns.format(version)
        nsmap = {None: xmlns}
        envelop = xml.create_root_element('eSocial', ns=nsmap)
        xml.add_element(envelop, None, 'consultaLoteEventos', ns=nsmap)
        xml.add_element(envelop, 'consultaLoteEventos', 'protocoloEnvio', text=str(protocol_number), ns=nsmap)
        return envelop

    def _xsd(self, which):
        version = esocial.__xsd_versions__[which]['version'].replace('.', '_')
        xsd_file = esocial.__xsd_versions__[which]['xsd'].format(version)
        xsd_file = os.path.join(here, 'xsd', xsd_file)
        return xml.xsd_fromfile(xsd_file)

    def validate_envelop(self, which, envelop):
        xmlschema = self._xsd(which)
        element_test = envelop
        if not isinstance(envelop, etree._ElementTree):
            element_test = etree.ElementTree(envelop)
        xml.XMLValidate(element_test, xsd=xmlschema).validate()

    def send(self, group_id=1):
        batch_to_send = self._make_send_envelop(group_id)
        self.validate_envelop('send', batch_to_send)
        # If no exception, batch XML is valid
        url = esocial._WS_URL[self.target]['send']
        ws = self._connect(url)
        # ws.wsdl.dump()
        BatchElement = ws.get_element('ns1:EnviarLoteEventos')
        result = ws.service.EnviarLoteEventos(BatchElement(loteEventos=batch_to_send))
        del ws
        # Result is a lxml Element object
        return result

    def retrieve(self, protocol_number):
        batch_to_search = self._make_retrieve_envelop(protocol_number)
        self.validate_envelop('retrieve', batch_to_search)
        # if no exception, protocol XML is valid
        url = esocial._WS_URL[self.target]['retrieve']
        ws = self._connect(url)
        # ws.wsdl.dump()
        SearchElement = ws.get_element('ns1:ConsultarLoteEventos')
        result = ws.service.ConsultarLoteEventos(SearchElement(consulta=batch_to_search))
        del ws
        return result
