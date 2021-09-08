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
import six
import tempfile
import contextlib

from OpenSSL import crypto

from cryptography.hazmat.primitives import serialization

def format_xsd_version(str_version):
    chars_to_transform = '.-'
    result_version = str_version
    for c in chars_to_transform:
        result_version = result_version.replace(c, '_')
    return result_version


def normalize_text(text):
    _chars = {
        u'>' : u'&gt;',
        u'<' : u'&lt;',
        u'&' : u'&amp;',
        u'"' : u'&quot;',
        u'\'': u'&apos;'
    }
    for c in _chars:
        text = text.replace(c, _chars[c])
    return text


def pkcs12_data(cert_file, password):
    if six.PY3:
        password = password.encode('utf-8')
    with open(cert_file, 'rb') as fp:
        content_pkcs12 = crypto.load_pkcs12(fp.read(), password)
    pkey = content_pkcs12.get_privatekey()
    cert_X509 = content_pkcs12.get_certificate()
    key_str = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
    cert_str = crypto.dump_certificate(crypto.FILETYPE_PEM, cert_X509)
    return {
        'key_str': key_str,
        'cert_str': cert_str,
        'key': pkey,
        'cert': cert_X509,
    }

@contextlib.contextmanager
def encrypt_pem_file(cert_data, cert_pass):
    crypto_key = cert_data['key'].to_cryptography_key()
    pem_pvkey_bytes = crypto_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(cert_pass.encode('utf-8'))
    )
    fp = tempfile.NamedTemporaryFile('w')
    fp.write(cert_data['cert_str'].decode('utf-8'))
    fp.write(pem_pvkey_bytes.decode('utf-8'))
    fp.flush()
    try:
        yield fp
    finally:
        fp.close()
