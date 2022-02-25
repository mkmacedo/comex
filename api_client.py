import requests
#import sys

#param = sys.argv[1]

class API_Client():
    def __init__(self, url):
        self.url = url
        self.result = self.connect()

    def connect(self):

        json = requests.get(self.url).json()

        return json

#a = API_Client('https://wise.klink.ai/api/admin/find/fornecedor/tenant/merck').result
#print(a[0]['centroCusto'],a[0]['contaContabil'])