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
from esocial import client

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
