# LIBeSocial

Biblioteca em Python para lidar com os processos do [eSocial](https://portal.esocial.gov.br):

- Validação dos XML's dos eventos;
- Comunicação com o Webservices do eSocial para envio e consulta de lotes;
- Assinatura dos XML's (e conexão com o webservices) com certificado tipo `A1`.

Apesar desta biblioteca ter sido desenvolvida para lidar especialmente com os eventos de SST (Saúde e Segurança do Trabalho), nada impede que ela possa ser utilizada para enviar/validar quaisquer dos eventos disponíveis no projeto eSocial.

No momento só é possível utilizar assinaturas do tipo `A1` em arquivos no formato `PKCS#12` (geralmente arquivos com extensão `.pfx` ou `.p12`).

# Documentação

Um manual de utilização está sendo feito em https://qualitaocupacional.com.br/libesocial/

# Instalação

PyPi:
```
pip install libesocial
```

A versão mais recente diretamente do repositório:

```
pip install https://github.com/qualitaocupacional/libesocial/archive/master.zip
```

Ou você pode clonar este repositório:
```
git clone https://github.com/qualitaocupacional/libesocial
```

Entrar na pasta do repositório recém clonado:
```
> cd libesocial
> python setup.py install
```
# Uso básico

**Montando um Lote e transmitindo para o eSocial**

```python
import esocial.xml
import esocial.client

ide_empregador = {
    'tpInsc': 1,
    'nrInsc': '12345678901234' # CNPJ/CPF completo (com 14/11 dígitos)
}

esocial_ws = esocial.client.WSClient(
    pfx_file='caminho/para/o/arquivo/certificado/A1',
    pfx_passw='senha do arquivo de certificado',
    employer_id=ide_empregador,
    sender_id=ide_empregador
)

evento1_grupo1 = esocial.xml.load_fromfile('evento1.xml')
evento2_grupo1 = esocial.xml.load_fromfile('evento2.xml')

# Adicionando eventos ao lote
esocial_ws.add_event(evento1_grupo1)
esocial_ws.add_event(evento2_grupo1)

result = esocial_ws.send(group_id=1)

# result vai ser um Element object
#<Element {http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0}eSocial at 0x>
print(esocial.xml.dump_tostring(result))
```

Por padrão, o webservice de envio/consulta de lotes é o de "**Produção Restrita**", para enviar para o ambiente de "**Produção Empresas**", onde as coisas são para valer:

```python
import esocial.client

esocial_ws = esocial.client.WSClient(
    pfx_file='caminho/para/o/arquivo/certificado/A1',
    pfx_passw='senha do arquivo de certificado',
    employer_id=ide_empregador,
    sender_id=ide_empregador,
    target='production'
)

...

```


**Assinando um evento**

```python
import esocial.xml
import esocial.utils

cert_data = esocial.utils.pkcs12_data('my_cert_file.pfx', 'my password')
evt2220 = esocial.xml.load_fromfile('S2220.xml')

# Signing using the signature algorithms from eSocial documentation
evt2220_signed = esocial.xml.sign(evt2220, cert_data)

```

**Validando um evento**

```python
import esocial.xml

evt2220 = esocial.xml.load_fromfile('S2220.xml')
try:
    esocial.xml.XMLValidate(evt2220).validate()
except AssertionError as e:
    print('O XML do evento S-2220 é inválido!')
    print(e)
```
ou
```python
import esocial.xml

evt2220 = esocial.xml.load_fromfile('S2220.xml')
xmlschema = esocial.xml.XMLValidate(evt2220)
if xmlschema.isvalid():
    print('XML do evento é válido! :-D.')
else:
    print('O XML do evento S-2220 é inválido!')
    print(str(xmlschema.last_error))
```

**OBSERVAÇÃO**: Até o presente momento (*15/05/2018*), a [SignXML](https://github.com/XML-Security/signxml),
versão **2.5.2** que está no [PyPi](https://pypi.org/project/signxml) não está alinhada com a versão mais
atual da [Cryptography](https://pypi.org/project/cryptography):

```
(...)/site-packages/signxml/__init__.py:370: CryptographyDeprecationWarning: signer and verifier have been deprecated. Please use sign and verify instead.
  signer = key.signer(padding=PKCS1v15(), algorithm=hash_alg)

```
Isso não atrapalha o funcionamento da **LIBeSocial**, mas é um aviso de que no futuro essa
função não vai mais funcionar. Você pode instalar a mesma versão **2.5.2** da **SignXML** diretamente do
repositório oficial, onde esta *issue* já foi corrigida:
```
pip install https://github.com/XML-Security/signxml/archive/master.zip
```

# Requisitos

A LIBeSocial requer as seguintes bibliotecas Python:

- **requests** >= 2.7.0
- **lxml** >= 4.2.1
- **zeep** >= 2.5.0
- **pyOpenSSL** >= 17.5.0
- **signxml** >= 2.5.2
- **six** >= 1.11.0

# Licença

A LIBeSocial é um projeto de código aberto, desenvolvido pelo departamento de
Pesquisa e Desenvolvimento e Tecnologia da Informação da [Qualitá Segurança e Saúde Ocupacional](https://qualitaocupacional.com.br)
e está licenciada pela [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0).
