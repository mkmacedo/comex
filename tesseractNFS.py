import cv2
import re
#from paddleocr import PPStructure, draw_structure_result, save_structure_res, PaddleOCR, draw_ocr
from dictionaries import companies, listaCNPJ, mapNameCNPJ

import pytesseract

from LCS import lcs

#from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#con
#vencimento
#nome
#valor
#po
#descricao


def runTesseractOCR(img_path):
    print('\nExecutando OCR tesseractNFS \n')
    cnpjFlag = False
    conFlag = False    
    flagNumNota = False
    flagValorTotal = False
    flagVencimento = False
    vencFlag = False
    flagNameFromCNPJ = False

    numNotaCount = 0
    valorTotalCount = 0
    vencimentoCount = 0

    nameLCS = 0

    tempVencimento = ''

    poChoices = ['PO', 'NUMERO PEDIDO', 'NRO PEDIDO', 'ORDEM COMPRA']
    conChoices = ['NRO NOTA', 'NRO DA NOTA', 'NUMERO NOTA', 'NUMERO DA NOTA', 'NÚMERO NOTA', 'NÚMERO DA NOTA']
    vencimentoChoices = ['DATA', 'VENCIMENTO', 'DATA VENCIMENTO']
    valorChoices = ['VALOR NOTA', 'VALOR DA NOTA', 'VALOR TOTAL']

    jsonResult = {}

    img = cv2.imread(img_path)
    config_tesseract = '--oem 3  --psm 11'
    texto = pytesseract.image_to_string(img, config=config_tesseract)
    texto = texto.lower()

    tempResult = texto.split('\n')
    result =[]
    
    for r in tempResult:
        if r != '':
            result.append(r)
    #print(result)

    #ocr = PaddleOCR(use_angle_cls=True, lang='en')

    #result = ocr.ocr(img_path, cls=True)

    for s in result:
        if flagNumNota == True:
            numNotaCount += 1

        #con
        if numNotaCount <= 4 and conFlag == False and flagNumNota == True:
            if re.match(r'[a-zA-Z]*[0-9]+', s) != None:
                con = re.match(r'[a-zA-Z]*[0-9]+', s).group()
                jsonResult['con'] = con
                conFlag = True


        if process.extractOne(s.upper(), conChoices, scorer=fuzz.partial_ratio)[1] > 80 and conFlag == False:
            flagNumNota = True

            if jsonResult.get('con') != None:
                if process.extractOne(s.upper(), conChoices, scorer=fuzz.partial_ratio)[1] \
                    > process.extractOne(str(jsonResult.get('con')).upper(), conChoices, scorer=fuzz.partial_ratio)[1]:
                    con = re.search(r'[a-zA-Z]*[0-9]+', s)
                    if con != None:
                        jsonResult['con'] = con.group()
                        conFlag = True
            else:
                con = re.search(r'[a-zA-Z]*[0-9]+', s)
                if con != None:
                    jsonResult['con'] = con.group()
                    conFlag = True

        
        #Razao Social
        if flagNameFromCNPJ == False:
            for company in companies:
                n = fuzz.partial_ratio(s.upper(), company)
                tempLCS = lcs(s.upper(), company)
                if n > 90 and tempLCS > nameLCS:
                    jsonResult['nome'] = company
                    nameLCS = tempLCS


        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                if fuzz.token_set_ratio(s, num) > 90:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    jsonResult['nome'] = mapNameCNPJ[num]
                    flagNameFromCNPJ = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', num)
                    stringCNPJ = ''
                    for p in cnpj:
                        stringCNPJ += p
                    if fuzz.token_set_ratio(s, stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        jsonResult['nome'] = mapNameCNPJ[num]
                        flagNameFromCNPJ = True
                        break


        #PO
        if process.extractOne(s.upper(), poChoices, scorer=fuzz.token_set_ratio)[1] > 80:
            if jsonResult.get('PO') != None:
                if process.extractOne(s.upper(), poChoices, scorer=fuzz.token_set_ratio) > process.extractOne(str(jsonResult.get('PO')).upper(), poChoices, scorer=fuzz.token_set_ratio):
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
            if process.extractOne(s.upper(), valorChoices, scorer=fuzz.partial_ratio)[1] > 80:
                if jsonResult.get('valor') != None:
                    if process.extractOne(s.upper(), valorChoices, scorer=fuzz.partial_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('valor')).upper(), valorChoices, scorer=fuzz.partial_ratio)[1]:
                        jsonResult['valor'] = s
                        valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', s)
                        if valor != None:
                            jsonResult['valor'] = valor.group()
                        elif s.find('R$') != -1:
                            jsonResult['valor'] = s[s.find('R$'):].strip()

                else:
                    valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', s)
                    if valor != None:
                        jsonResult['valor'] = valor.group()
                    elif s.find('R$') != -1:
                        jsonResult['valor'] = s[s.find('R$'):].strip()

        if fuzz.token_set_ratio(s.upper(), 'VALOR TOTAL') > 80 or fuzz.partial_ratio(s.upper(), 'VALOR TOTAL') > 80:
            flagValorTotal = True
            valorTotalCount = 0

        if flagValorTotal == True and valorTotalCount < 2 or (s.find('R$') != -1 and valorTotalCount < 4):
                valorTotalCount += 1
                if re.search(r'(?:[0-9]+\.?)+(?:,[0-9][0-9])?', s) != None:
                    jsonResult['valor'] = re.search(r'(?:[0-9]+\.?)+(?:,[0-9][0-9])?', s).group()


        #Vencimento
        if process.extractOne(s.upper(), vencimentoChoices, scorer=fuzz.partial_ratio)[1] > 85 and vencFlag == False:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if process.extractOne(s.upper(), vencimentoChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempVencimento.upper(), vencimentoChoices, scorer=fuzz.ratio)[1] \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', s) != None:
                    tempVencimento = s
                    jsonResult['vencimento'] = s
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', s)
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                jsonResult['vencimento'] = s
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', s)
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()

        if flagVencimento == True and vencFlag == False:
            vencimentoCount += 1
            if vencimentoCount <= 5:
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', s)
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()
            else:
                vencFlag = True
        
    print('end of for loop \n')

    print(f'\nOutput tesseractNFS: {jsonResult} \n')
    return jsonResult

#res = runTesseractOCR('mapa_faturamento_teste_0.jpg')
#print(res)