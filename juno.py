import json
import base64
import requests
import uuid

from decouple import config

JUNO_URL = config('JUNO_URL')
JUNO_TOKEN = config('JUNO_TOKEN')


class Charge(object):
    def __init__(self, description: str, references: list, amount: float, 
                dueDate: str, installments: int, maxOverdueDays: int, 
                paymentTypes: list, paymentAdvance: bool) -> None:

        self.description: str = description
        self.references: list = references
        self.amount: float = amount
        self.dueDate: str = dueDate
        self.installments: int = installments
        self.maxOverdueDays: int = maxOverdueDays
        self.paymentTypes: list = paymentTypes
        self.paymentAdvance: bool = paymentAdvance


class Billing(object):
    def __init__(self, name: str, document: str, 
                email: str, address:dict, birthDate: str, 
                notify: bool) -> None:

        self.name: str = name
        self.document: str = document
        self.email: str = email
        self.address: dict = address
        self.birthDate: str = birthDate
        self.notify: bool = notify

class JunoAPI(object):
    def __init__(self, charge: Charge, billing: Billing) -> None:
        self.charge: Charge = charge
        self.billing: Billing = billing

    def generate_charge_request(self):
        cobranca = dict(
            charge=vars(self.charge),
            billing=vars(self.billing)
        )

        url = f"{JUNO_URL}/api-integration/charges"
        
        headers = {
            'X-Api-Version': "2",
            'X-Resource-Token': JUNO_TOKEN,
            'Authorization': f'Bearer {JunoAPI.get_access_token()}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            url=url,
            data=json.dumps(cobranca),
            headers=headers
        )

        json_response = response.json()

        if response.status_code != 200:
            raise Exception(
                {
                    'status': json_response.get('status'),
                    'error': json_response.get('error'),
                    'details': json_response.get('details')
                }
            )

        return json_response
    
    @staticmethod
    def get_access_token() -> str:
        client_id = config('JUNO_CLIENT_ID')
        secret_id = config('JUNO_SECRET')

        cliente_secret = f"{client_id}:{secret_id}"

        cliente_secret_bytes = cliente_secret.encode('ascii')
        base64_bytes = base64.b64encode(cliente_secret_bytes)
        base64_message = base64_bytes.decode('ascii')

        url = f"{JUNO_URL}/authorization-server/oauth/token"
        data = dict(grant_type="client_credentials")
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64_message}'
        }


        response = requests.post(
            url=url,
            data=data,
            headers=headers
        )

        json_response = response.json()

        response.raise_for_status()

        return json_response.get('access_token')


    @staticmethod
    def list_overdue_charges():
        url = f"{JUNO_URL}/api-integration/charges?showDue=true&pageSize=100"
        
        headers = {
            'X-Api-Version': "2",
            'X-Resource-Token': JUNO_TOKEN,
            'Authorization': f'Bearer {JunoAPI.get_access_token()}'
        }

        response = requests.get(
            url=url,
            headers=headers
        )

        response.raise_for_status()
        
        return response.json()
    
    @staticmethod
    def list_not_paid_charges():
        url = f"{JUNO_URL}/api-integration/charges?showNotPaid=true&pageSize=100"
        
        headers = {
            'X-Api-Version': "2",
            'X-Resource-Token': JUNO_TOKEN,
            'Authorization': f'Bearer {JunoAPI.get_access_token()}'
        }

        response = requests.get(
            url=url,
            headers=headers
        )

        response.raise_for_status()
        
        return response.json()

charge = Charge(
    description="Produto de teste",
    references=[str(uuid.uuid4())],
    amount=50,
    dueDate="2021-12-19",
    installments=1,
    maxOverdueDays=7,
    paymentTypes=[
        'BOLETO',
        'CREDIT_CARD'
    ],
    paymentAdvance=False
)

billing = Billing(
    name="Fernando Gabriel Feitosa Leite",
    document="03780772019",
    email="fernandogfleite@gmail.com",
    address=dict(
        street="Rua Marinita Gouveia",
        number="15",
        complement="Quadra E",
        neighborhood="Massagueira",
        city="Marechal Deodoro",
        state="AL",
        postCode="57160000"
    ),
    birthDate="2003-07-24",
    notify=True
)

juno_api = JunoAPI(charge=charge, billing=billing)

try:
    with open('cobranca_criada.txt', 'w') as outfile:
        outfile.write("Cobrança criada: \n")
        json.dump(juno_api.generate_charge_request(), outfile)
    
    with open('cobrancas_vencidas.txt', 'w') as outfile:
        outfile.write("Cobranças vencidas: ")
        json.dump(juno_api.list_overdue_charges(), outfile)
    
    with open('cobrancas_nao_pagas.txt', 'w') as outfile:
        outfile.write("Cobranças não pagas: ")
        json.dump(juno_api.list_not_paid_charges(), outfile)

except Exception as error:
    with open('erros.txt', 'w') as outfile:
        outfile.write(f"Erros: {error}")
