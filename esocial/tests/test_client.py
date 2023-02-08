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
import pytest
import requests

from esocial import client

from esocial.tests import ws_factory

def test_client_target():
    target_tests = [
        ('tests', 'tests'),
        ('production', 'production'),
        ('1', 'production'),
        ('2', 'tests'),
        (1, 'production'),
        (2, 'tests')
    ]
    for t in target_tests:
        ws = client.WSClient(target=t[0])
        assert ws.target == t[1], 'Expected target {}. Got {}'.format(t[1], ws.target)


def test_client_connect():
    # This test is only for the https transport, once the connection will fail because of the
    # self signed certificate and non-authorized entity
    ws = ws_factory()
    with pytest.raises(requests.exceptions.HTTPError) as exception_info:
        wsdl_client = ws.connect(ws.esocial_send_url())
    assert '403 Client Error: Forbidden for url' in str(exception_info)
    # wsdl_client.wsdl.dump()
