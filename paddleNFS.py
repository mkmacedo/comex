import cv2
import re
from paddleocr import PaddleOCR#, draw_structure_result, save_structure_res, PaddleOCR, draw_ocr
from dictionaries import companies, listaCNPJ, mapNameCNPJ

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

def runPaddleOCR(img_path, lg=None):
    print('\nExecutando OCR paddleNSF \n')
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

    #table_engine = PPStructure(show_log=True)
    ocr = PaddleOCR(use_angle_cls=True)
    if lg != None:
        #table_engine = PPStructure(show_log=True, lang=lg)
        ocr = PaddleOCR(use_angle_cls=True, lang=lg)
        print('-> Argumento Idioma paddleNFS:', lg, '\n')
    
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(img_path, img)

    print(f'Inicio {img_path} ')
    result = ocr.ocr(img_path, cls=True)

    #ocr = PaddleOCR(use_angle_cls=True, lang='en')

    #result = ocr.ocr(img_path, cls=True)

    for line in result:
        print(line[1][0])
        if flagNumNota == True:
            numNotaCount += 1

        #con
        if numNotaCount <= 10 and conFlag == False and flagNumNota == True:
            if re.match(r'[a-zA-Z]*[0-9]+', str(line[1][0])) != None:
                con = re.match(r'[a-zA-Z]*[0-9]+', str(line[1][0])).group()
                jsonResult['con'] = con
                conFlag = True


        if process.extractOne(str(line[1][0]).upper(), conChoices, scorer=fuzz.partial_ratio)[1] > 80:
            flagNumNota = True

            if jsonResult.get('con') != None:
                if process.extractOne(str(line[1][0]).upper(), conChoices, scorer=fuzz.partial_ratio)[1] \
                    > process.extractOne(str(jsonResult.get('con')).upper(), conChoices, scorer=fuzz.partial_ratio)[1] and conFlag == False:
                    con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0]))
                    if con != None:
                        jsonResult['con'] = con.group()#str(line[1][0])[str(line[1][0]).find(':')+1:].strip()
                        conFlag = True
            else:
                con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0]))
                if con != None:
                    jsonResult['con'] = con.group()#str(line[1][0])[str(line[1][0]).find(':')+1:].strip()
                    conFlag = True

        
        #Razao Social
        if flagNameFromCNPJ == False:
            for company in companies:
                n = fuzz.partial_ratio(str(line[1][0]).upper(), company)
                tempLCS = lcs(str(line[1][0]).upper(), company)
                if n > 90 and tempLCS > nameLCS:
                    jsonResult['nome'] = company
                    nameLCS = tempLCS


        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                if fuzz.token_set_ratio(str(line[1][0]), num) > 90:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    jsonResult['nome'] = mapNameCNPJ[num]
                    flagNameFromCNPJ = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', num)
                    stringCNPJ = ''
                    for s in cnpj:
                        stringCNPJ += s
                    if fuzz.token_set_ratio(str(line[1][0]), stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        jsonResult['nome'] = mapNameCNPJ[num]
                        flagNameFromCNPJ = True
                        break


        #PO
        if process.extractOne(str(line[1][0]).upper(), poChoices, scorer=fuzz.token_set_ratio)[1] > 80:
            if jsonResult.get('PO') != None:
                if process.extractOne(str(line[1][0]).upper(), poChoices, scorer=fuzz.token_set_ratio) > process.extractOne(str(jsonResult.get('PO')).upper(), poChoices, scorer=fuzz.token_set_ratio):
                    jsonResult['PO'] = str(line[1][0])
                    po = re.search(r'[0-9]+', line[1][0])
                    if po != None:
                        jsonResult['PO'] = po.group()

                    
            else:
                jsonResult['PO'] = str(line[1][0])
                po = re.search(r'[0-9]+', str(line[1][0]))
                if po != None:
                    jsonResult['PO'] = po.group()


        #VALOR
        if flagValorTotal == False:
            if process.extractOne(str(line[1][0]).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] > 80:
                if jsonResult.get('valor') != None:
                    if process.extractOne(str(line[1][0]).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('valor')).upper(), valorChoices, scorer=fuzz.partial_ratio)[1]:
                        jsonResult['valor'] = str(line[1][0])
                        valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line[1][0]))
                        if valor != None:
                            jsonResult['valor'] = valor.group()
                        elif str(line[1][0]).find('R$') != -1:
                            jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()

                else:
                    valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line[1][0]))
                    if valor != None:
                        jsonResult['valor'] = valor.group()
                    elif str(line[1][0]).find('R$') != -1:
                        jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()


        if fuzz.token_set_ratio(str(line[1][0]).upper(), 'VALOR TOTAL') > 80 or fuzz.partial_ratio(str(line[1][0]).upper(), 'VALOR TOTAL') > 80:
            flagValorTotal = True
            valorTotalCount = 0

        if flagValorTotal == True and valorTotalCount < 2 or (str(line[1][0]).find('R$') != -1 and valorTotalCount < 4):
            valorTotalCount += 1
            if re.search(r'(?:[0-9]+\.?)+(?:,[0-9][0-9])?', str(line[1][0])) != None:
                jsonResult['valor'] = re.search(r'(?:[0-9]+\.?)+(?:,[0-9][0-9])?', str(line[1][0])).group()


        #Vencimento
        if process.extractOne(str(line[1][0]).upper(), vencimentoChoices, scorer=fuzz.partial_ratio)[1] > 85 and vencFlag == False:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if process.extractOne(str(line[1][0]).upper(), vencimentoChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempVencimento.upper(), vencimentoChoices, scorer=fuzz.ratio)[1] \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0])) != None:
                    tempVencimento = str(line[1][0])
                    jsonResult['vencimento'] = str(line[1][0])
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                jsonResult['vencimento'] = str(line[1][0])
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line[1][0])
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()

        if flagVencimento == True and vencFlag == False:
            vencimentoCount += 1
            if vencimentoCount <= 5:
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()
            else:
                vencFlag = True
        
    print('end of for loop \n')

    print(f'\nOutput paddleNFS (lang={lg}): {jsonResult} \n')
    return jsonResult

#res = runPaddleOCR('aéreoNFSDHL.jpg')
#print(res)