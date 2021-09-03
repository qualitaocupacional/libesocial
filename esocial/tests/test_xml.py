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

import esocial

from esocial import xml
from esocial import client
from esocial.utils import pkcs12_data

here = os.path.dirname(os.path.abspath(__file__))
there = os.path.dirname(os.path.abspath(esocial.__file__))


def test_S2220_xml():
    evt2220 = xml.load_fromfile(os.path.join(here, 'xml', 'S-2220-v{}.xml'.format(esocial.__esocial_version__)))
    xml.XMLValidate(evt2220).validate()


def test_xml_sign():
    evt2220_not_signed = xml.load_fromfile(os.path.join(here, 'xml', 'S-2220-v{}-not_signed.xml'.format(esocial.__esocial_version__)))
    xmlschema = xml.XMLValidate(evt2220_not_signed)
    isvalid = xmlschema.isvalid()
    assert (not isvalid), str(xmlschema.last_error)

    # Test signing
    cert_data = pkcs12_data(
        cert_file=os.path.join(there, 'certs', 'libesocial-cert-test.pfx'),
        password='cert@test'
    )
    evt2220_signed = xml.sign(evt2220_not_signed, cert_data)
    xml.XMLValidate(evt2220_signed).validate()


def test_xml_send_batch():
    evt2220 = xml.load_fromfile(os.path.join(here, 'xml', 'S-2220-v{}-not_signed.xml'.format(esocial.__esocial_version__)))
    employer_id = {
        'tpInsc': 2,
        'nrInsc': '12345678901234'
    }
    ws = client.WSClient(
        pfx_file=os.path.join(there, 'certs', 'libesocial-cert-test.pfx'),
        pfx_passw='cert@test',
        employer_id=employer_id,
        sender_id=employer_id
    )
    ws.add_event(evt2220)
    batch_to_send = ws._make_send_envelop(1)
    ws.validate_envelop('send', batch_to_send)

def test_xml_retrieve_batch():
    ws = client.WSClient()
    protocol_number = 'A.B.YYYYMM.NNNNNNNNNNNNNNNNNNN'
    batch_to_retrieve = ws._make_retrieve_envelop(protocol_number)
    ws.validate_envelop('retrieve', batch_to_retrieve)
