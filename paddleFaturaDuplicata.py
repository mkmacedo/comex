import cv2
import re
from paddleocr import PaddleOCR#, draw_structure_result, save_structure_res, PaddleOCR, draw_ocr
from dictionaries import companies, listaCNPJ, field_validation, mapNameCNPJ
from LCS import lcs

#from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def runPaddleOCR(img_path, lg=None):
    print('\nExecutando OCR paddleFaturaDuplicata \n')
    
    jsonResult = {}

    poChoices = ['PO', 'NUMERO PEDIDO', 'NRO PEDIDO', 'ORDEM COMPRA', 'NR PEDIDO']
    conChoices = ['NRO NOTA', 'NRO DA NOTA', 'NUMERO NOTA', 'NUMERO DA NOTA', 'NÚMERO NOTA', 'NÚMERO DA NOTA', 'NUMERO ORDEM', 'NÚMERO ORDEM', 'N DOCUMENTO']
    vencimentoChoices = ['DATA', 'VENCIMENTO', 'DATA VENCIMENTO']
    valorChoices = ['VALOR NOTA', 'VALOR DA NOTA', 'VALOR TOTAL', 'VALOR DO DOCUMENTO']

    cnpjFlag = False
    conFlag = False    
    flagNumNota = False
    flagValorTotal = False
    flagVencimento = False
    vencFlag = False
    valorFlag = False
    poFlag = False
    flagNameFromCNPJ = False

    numNotaCount = 0
    valorTotalCount = 0
    vencimentoCount = 0

    nameLCS = 0

    tempVencimento = ''
    
    if lg == None:
        #table_engine = PPStructure(show_log=True)
        ocr = PaddleOCR(use_angle_cls=True)
    else:
        #table_engine = PPStructure(show_log=True, lang=lg)
        ocr = PaddleOCR(use_angle_cls=True, lang=lg)
        print('-> Argumento Idioma paddleFaturaDuplicata:',lg,'\n')

    #img = cv2.imread(img_path)
    #result = table_engine(img)

    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(img_path, img)

    print(f'Inicio {img_path} ')
    result = ocr.ocr(img_path, cls=True)

    for line in result:

        #con
        if numNotaCount <= 5 and conFlag == False and flagNumNota == True:
            numNotaCount += 1
            if re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0])) != None:
                con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0])).group()
                c = jsonResult.get('con')
                if c != None:
                    if len(con) > len(c):
                        jsonResult['con'] = con
                else:
                    jsonResult['con'] = con

        if process.extractOne(str(line[1][0]).upper(), conChoices, scorer=fuzz.token_set_ratio)[1] > 80 and conFlag == False:
            flagNumNota = True
            conFlag = False
            numNotaCount = 0
            if jsonResult.get('con') != None:
                if process.extractOne(str(line[1][0]).upper(), conChoices, scorer=fuzz.partial_ratio)[1] \
                    > process.extractOne(str(jsonResult.get('con')).upper(), conChoices, scorer=fuzz.partial_ratio)[1] \
                    and re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0])) != None:

                    con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0]))
                    if con != None:
                        jsonResult['con'] = con.group()
            else:
                con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0]))
                if con != None:
                    jsonResult['con'] = con.group()

                
        #Razao Social
        if flagNameFromCNPJ == False:
            for company in companies:
                n = fuzz.partial_ratio(str(line[1][0]), company)
                tempLCS = lcs(str(line[1][0]), company)
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
        fuzzPO = process.extractOne(str(line[1][0]).upper(), poChoices, scorer=fuzz.partial_ratio)[1]
        if fuzzPO > 85 and poFlag == False:
            if jsonResult.get('PO') != None:                    
                jsonResult['PO'] = str(line[1][0])
                po = re.search(r'[0-9]+', line[1][0])
                if po != None:
                    jsonResult['PO'] = po.group()
                    poFlag = True
                    
            else:
                jsonResult['PO'] = str(line[1][0])
                po = re.search(r'[0-9]+', str(line[1][0]))
                if po != None:
                    jsonResult['PO'] = po.group()
                    poFlag = True


        #Valor
        if valorTotalCount <= 5 and flagValorTotal == True and valorFlag == False:
            valorTotalCount += 1

            if re.match(field_validation['valor'], str(line[1][0])) != None:
                valor = re.match(field_validation['valor'], str(line[1][0])).group()
                jsonResult['valor'] = valor
                valorFlag = True

        if process.extractOne(str(line[1][0]).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] > 80:
            flagValorTotal = True
            valorTotalCount = 0
            if jsonResult.get('valor') != None:
                if process.extractOne(str(line[1][0]).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] \
                    > process.extractOne(str(jsonResult.get('valor')).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] \
                    and re.search(field_validation['valor'], str(line[1][0])) != None:

                    valor = re.search(field_validation['valor'], str(line[1][0]))
                    if valor != None:
                        jsonResult['valor'] = valor.group()
            else:
                valor = re.search(field_validation['valor'], str(line[1][0]))
                if valor != None:
                    jsonResult['valor'] = valor.group()


        #Vencimento            
        if process.extractOne(str(line[1][0]).upper(), vencimentoChoices, scorer=fuzz.token_set_ratio)[1] > 55 or flagVencimento == True:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if process.extractOne(str(line[1][0]).upper(), vencimentoChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempVencimento.upper(), vencimentoChoices, scorer=fuzz.ratio)[1]\
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0])) != None:
                    tempVencimento = str(line[1][0])

                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:

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


        if fuzz.token_set_ratio(str(line[1][0]), 'Valor Total') > 80:
            flagValorTotal = True

        if flagValorTotal == True:
            if str(line[1][0]).find('R$') != -1:
                        jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()

    
    print('end of for loop \n')

    print(f'\nOutput paddleFaturaDuplicata (lang={lg}): {jsonResult} \n')
    return jsonResult


#res = runPaddleOCR('PastaTestes1/FaturaDuplicata2-AGV_0.jpg', 'en')
#print(res)