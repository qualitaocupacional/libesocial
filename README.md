# LIBeSocial

Biblioteca em Python para lidar com os processos do [eSocial](https://www.gov.br/esocial/pt-br):

- Validação dos XML's dos eventos;
- Comunicação com o Webservices do eSocial para envio e consulta de lotes;
- Assinatura dos XML's (e conexão com o webservices) com certificado tipo `A1`.

Apesar desta biblioteca ter sido desenvolvida para lidar especialmente com os eventos de SST (Saúde e Segurança do Trabalho), nada impede que ela possa ser utilizada para enviar/validar quaisquer dos eventos disponíveis no projeto eSocial.

No momento só é possível utilizar assinaturas do tipo `A1` em arquivos no formato `PKCS#12` (geralmente arquivos com extensão `.pfx` ou `.p12`).

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

ide_transmissor = {
    'tpInsc': 1,
    'nrInsc': '43210987654321' # CNPJ/CPF completo (com 14/11 dígitos)
}

esocial_ws = esocial.client.WSClient(
    pfx_file='caminho/para/o/arquivo/certificado/A1',
    pfx_passw='senha do arquivo de certificado',
    employer_id=ide_empregador,
    # Se o transmissor é o próprio empregador, não precisa informar o "sender_id"
    sender_id=ide_transmissor,
)

evento1_grupo1 = esocial.xml.load_fromfile('evento1.xml')
evento2_grupo1 = esocial.xml.load_fromfile('evento2.xml')

# Adicionando eventos ao lote. O evento já vai ser assinado usando o certificado fornecido e validado contra o XSD do evento
evento1_id, evento1_assinado = esocial_ws.add_event(evento1_grupo1)
evento2_id, evento2_assinado = esocial_ws.add_event(evento2_grupo1)

result = esocial_ws.send(group_id=1)

# result vai ser um Element object
#<Element {http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0}eSocial at 0x>
print(esocial.xml.dump_tostring(result, xml_declaration=False, pretty_print=True))
```

**Consultando o resultado do processamento de um Lote**

```python
import esocial.xml
import esocial.client

ide_empregador = {
    'tpInsc': 1,
    'nrInsc': '12345678901234' # CNPJ/CPF completo (com 14/11 dígitos)
}

ide_transmissor = {
    'tpInsc': 1,
    'nrInsc': '43210987654321' # CNPJ/CPF completo (com 14/11 dígitos)
}

esocial_ws = esocial.client.WSClient(
    pfx_file='caminho/para/o/arquivo/certificado/A1',
    pfx_passw='senha do arquivo de certificado',
    employer_id=ide_empregador,
    # Se o transmissor é o próprio empregador, não precisa informar o "sender_id"
    sender_id=ide_transmissor,
)

# De posse do número do protocolo de envio
response = esocial_ws.retrieve('1.2.202109.0000000000000000001')

# response vai ser um Element object
#<Element {http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0}eSocial at 0x>
print(esocial.xml.dump_tostring(result, xml_declaration=False, pretty_print=True))
```

Para obter algumas informações relevantes da resposta, use o método **decode_response(response)**:

```python
import esocial.xml
import json

response_decoded = esocial.xml.decode_response(response)

print(json.dumps(response_decoded.toDict(), indent=4))
```
**Exemplo de Saída**

```json
{
    "status": {
        "ocorrencias": [],
        "cdResposta": "201",
        "descResposta": "Lote processado com sucesso."
    },
    "lote": {
        "dhRecepcao": "2021-10-04T11:45:44.16",
        "versaoAplicativoRecepcao": "0.1.105",
        "protocoloEnvio": "1.1.202110.0000000000011111111"
    },
    "eventos": [
        {
            "id": "ID1123456780000002021100411454300001",
            "processamento": {
                "ocorrencias": [],
                "cdResposta": "201",
                "descResposta": "Sucesso.",
                "versaoAppProcessamento": "13.3.1",
                "dhProcessamento": "2021-10-04T11:45:50.923"
            },
            "recibo": {
                "nrRecibo": "1.1.0000000000111111111",
                "hash": "GeGBSm+RjCxk53xh1oLQ22FDIR2Je3SQ6emcYGDm0Bo="
            }
        },
        {
            "id": "ID1123456780000002021100411454300002",
            "processamento": {
                "ocorrencias": [],
                "cdResposta": "201",
                "descResposta": "Sucesso.",
                "versaoAppProcessamento": "13.3.1",
                "dhProcessamento": "2021-10-04T11:45:51.56"
            },
            "recibo": {
                "nrRecibo": "1.1.0000000000111111112",
                "hash": "EqjMGQU5vPfT1qu24HIO/yn06DrLwA5IFJKP04mNedE="
            }
        },
        {
            "id": "ID1123456780000002021100411454300003",
            "processamento": {
                "ocorrencias": [],
                "cdResposta": "201",
                "descResposta": "Sucesso.",
                "versaoAppProcessamento": "13.3.1",
                "dhProcessamento": "2021-10-04T11:45:52.243"
            },
            "recibo": {
                "nrRecibo": "1.2.0000000000111111113",
                "hash": "Lf9tQsGezML23RmWQYQg4Y+qzwn9BDAtyfyGiMfadfE="
            }
        },
        {
            "id": "ID1123456780000002021100411454300004",
            "processamento": {
                "ocorrencias": [],
                "cdResposta": "201",
                "descResposta": "Sucesso.",
                "versaoAppProcessamento": "13.3.1",
                "dhProcessamento": "2021-10-04T11:45:52.9"
            },
            "recibo": {
                "nrRecibo": "1.1.0000000000111111114",
                "hash": "zp8AJYm0uOoNTW+2oQEitCm0f6tIK8LbxqT8+Jel4rg="
            }
        }
    ]
}
```

O retorno vai ser um objeto do tipo [**DotMap**](https://github.com/drgrib/dotmap), que pode ser acessado assim:
```python
print(response_decoded.status.cdResposta, '-', response_decoded.status.descResposta)
for evt in response_decoded.eventos:
    print('ID:', evt.id)
    print('Recibo:', evt.recibo.nrRecibo)
    print('-'*10)

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

Se por algum motivo você precisar assinar algum arquivo XML separadamente, pode usar as funções utilitárias da LIBeSocial. Lembrando que o método "**add_event(xml_element)**" já faz a assinatura do evento antes de adicioná-lo ao lote.

```python
import esocial.xml
import esocial.utils

cert_data = esocial.utils.pkcs12_data('my_cert_file.pfx', 'my password')
evt2220 = esocial.xml.load_fromfile('S2220.xml')

# Assina o XML com os algoritmos descritos na documentação do eSocial
evt2220_signed = esocial.xml.sign(evt2220, cert_data)

```

**Validando um evento**

```python
import esocial.xml

evt2220 = esocial.xml.load_fromfile('S2220.xml')
try:
    esocial.xml.XMLValidate(evt2220).validate()
except esocial.xml.XMLValidateError as e:
    print('O XML do evento S-2220 é inválido!')
    print(e)
    for err in e.errors:
        print(' ->', err)
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

# Certificados do ICP-Brasil no lado cliente

De acordo com o [manual do desenvolvedor do eSocial, versão 1.10](https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/manualorientacaodesenvolvedoresocialv1-10.pdf) (página 114), é necessário instalar a cadeia de certificação do eSocial para poder utilizar os *Webservices*. Que são:

**Raiz**

**[AC - Primeiro Nível](http://acraiz.icpbrasil.gov.br/credenciadas/RFB/v2/p/AC_Secretaria_da_Receita_Federal_do_Brasil_v3.crt)**

**[AC - Segundo Nível](http://acraiz.icpbrasil.gov.br/credenciadas/RFB/v2/Autoridade_Certificadora_do_SERPRO_RFB_SSL.crt)**

Primeiro, o manual está desatualizado, sendo que os servidores do eSocial estão utilizando a versão 10 do certificado **Raiz** do ICP-Brasil:

[Raiz v10](http://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv10.crt)

Segundo, utilizando a **LIBeSocial** não há necessidade de instalar nenhum desses certificados na máquina que vai enviar os eventos. Os respectivos certificados já estão "agrupados" no arquivo "**serpro_full_chain.pem**" na pasta **certs** que acompanha a **LIBeSocial**.

Entretando, certificados expiram e/ou são trocados. Se necessário, para criar um novo arquivo com a cadeia de certificados novos, após baixar os devidos arquivos `.crt` (que devem estar no formato *PEM*), é só concatenar os arquivos em um único. Exemplo em Linux/Unix:

```
$ cat ICP-Brasilv10.crt AC_Secretaria_da_Receita_Federal_do_Brasil_v3.crt Autoridade_Certificadora_do_SERPRO_RFB_SSL.crt > novo_arquivo_certificados.pem
```

E informar esse arquivo ao instanciar o cliente *esocial*:

```python
import esocial.client

esocial_ws = esocial.client.WSClient(
    pfx_file='caminho/para/o/arquivo/certificado/A1',
    pfx_passw='senha do arquivo de certificado',
    employer_id=ide_empregador,
    target='production',
    ca_file='/caminho/para/novo_arquivo_certificados.pem',
)

...

```

# Requisitos

A LIBeSocial requer as seguintes bibliotecas Python:

- **requests** >= 2.26.0
- **lxml** >= 4.6.3
- **zeep** >=4.1.0
- **signxml** >= 2.8.2
- **pyOpenSSL** < 19
- **six** >= 1.11.0

# Licença

A LIBeSocial é um projeto de código aberto, desenvolvido pelo departamento de
Pesquisa e Desenvolvimento e Tecnologia da Informação da [Qualitá Segurança e Saúde Ocupacional](https://qualitamais.com.br)
e está licenciada pela [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0).
