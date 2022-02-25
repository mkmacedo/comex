import os
import cv2
import re
from paddleocr import PPStructure, draw_structure_result, save_structure_res, PaddleOCR, draw_ocr
from LCS import lcs
from dictionaries import companies, listaCNPJ
import pytesseract

from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def runTesseractOCR(img_path):

    jsonResult = {}

    cnpjFlag = False
    flagVencimento = False
    flagValorTotal = False
    valorTotalCount = 0

    tempVencimento = ''

    nameLCS = 0

    poChoices = ['PO', 'NUMERO PEDIDO', 'NRO PEDIDO', 'ORDEM COMPRA']
    conChoices = ['NRO NOTA', 'NRO DA NOTA', 'NUMERO NOTA', 'NUMERO DA NOTA', 'NÚMERO NOTA', 'NÚMERO DA NOTA']
    vencimentoChoices = ['DATA', 'VENCIMENTO', 'DATA VENCIMENTO']
    valorChoices = ['VALOR NOTA', 'VALOR DA NOTA', 'VALOR TOTAL', 'TOTAL', 'TOTAL NOTA']

    img = cv2.imread(img_path)
    config_tesseract = '--oem 3  --psm 11'
    texto = pytesseract.image_to_string(img, config=config_tesseract)
    texto = texto.lower()

    tempResult = texto.split('\n')
    result =[]
    
    for r in tempResult:
        if r != '':
            result.append(r)
    print(result)

    for s in result:
        if fuzz.token_set_ratio(s.upper(), 'Nro da nota') > 80 or fuzz.token_set_ratio(s.lower(), 'con') > 80:
            if jsonResult.get('con') != None:
                if fuzz.token_set_ratio(s, 'Nro da nota') > fuzz.token_set_ratio(jsonResult.get('con'), 'Nro da nota'):
                    con = re.search(r'[a-zA-Z]*[0-9]+', s)
                    if con != None:
                        jsonResult['con'] = con.group()#s[s.find(':')+1:].strip()
            else:
                con = re.search(r'[a-zA-Z]*[0-9]+', s)
                if con != None:
                    jsonResult['con'] = con.group()#s[s.find(':')+1:].strip()

                
        #Razao Social
#            if fuzz.token_set_ratio(s, 'Razao Social') > 60 and fuzz.token_set_ratio(s, 'MERCK') < 80:
#                if jsonResult.get('nome') != None:
#                    if fuzz.token_set_ratio(s, 'Razao Social') > fuzz.token_set_ratio(jsonResult.get('nome'), 'Razao Social'):
#                        jsonResult['nome'] = s[s.find(':')+1:].strip()
#                else:
#                    jsonResult['nome'] = s[s.find(':')+1:].strip()

        #Razao Social
        for company in companies:
            n = fuzz.partial_ratio(s.upper(), company)
            tempLCS = lcs(s.upper(), company)
            if n > 90 and tempLCS > nameLCS:
                jsonResult['nome'] = company
                nameLCS = tempLCS


        #PO
        if fuzz.token_set_ratio(s, 'PO') > 80 or fuzz.token_set_ratio(s, 'NUMERO PEDIDO') > 80:
            if jsonResult.get('PO') != None:
                if fuzz.token_set_ratio(s, 'PO') > fuzz.token_set_ratio(jsonResult.get('PO'), 'PO'):
                    jsonResult['PO'] = s
                    po = re.search(r'[0-9]+', s)
                    if po != None:
                        jsonResult['PO'] = po.group()
                
            else:
                jsonResult['PO'] = s
                po = re.search(r'[0-9]+', s)
                if po != None:
                    jsonResult['PO'] = po.group()

        
        #VALOR
        if flagValorTotal == False:
            if process.extractOne(s.upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] > 80:
                flagValorTotal = True
                if jsonResult.get('valor') != None:
                    if fuzz.token_set_ratio(s, 'VALOR') > fuzz.token_set_ratio(jsonResult.get('valor'), 'VALOR'):
                        jsonResult['valor'] = s
                        if s.find('R$') != -1:
                            jsonResult['valor'] = s[s.find('R$'):].strip()

                else:
                    if s.find('R$') != -1:
                            jsonResult['valor'] = s[s.find('R$'):].strip()

        if flagValorTotal == True and valorTotalCount <= 5:
            valorTotalCount += 1
            if re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', s) != None:
                jsonResult['valor'] = re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', s).group()


        #Vencimento
        if process.extractOne(s.upper(), vencimentoChoices, scorer=fuzz.token_set_ratio)[1] > 85 > 80 or flagVencimento == True:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if fuzz.token_set_ratio(s.upper(), 'VENCIMENTO') > fuzz.token_set_ratio(tempVencimento, 'Vencimento') \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', s) != None:
                    tempVencimento = s
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', s)
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', s)
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()


        #nome
        for company in companies:
            if fuzz.token_set_ratio(s, company) > 80:
                jsonResult['nome'] = company



        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                if fuzz.token_set_ratio(s, num) > 90:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', num)
                    stringCNPJ = ''
                    for p in cnpj:
                        stringCNPJ += p
                    if fuzz.token_set_ratio(s, stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        break
    
    print('end of for loop \n')
    print(f'\nOutput tesseractReciboLocacao: {jsonResult} \n')

    return jsonResult


#res = runTesseractOCR('AGV_RL_0.jpg')
#print(res)