import cv2
import re
from paddleocr import PaddleOCR
from dictionaries import companies, listaCNPJ, mapNameCNPJ

from LCS import lcs

#from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#con
#dataEntrada
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
    flagDataEntrada = False
    flagDataSaida = True
    vencFlag = False
    flagNameFromCNPJ = False

    numNotaCount = 0
    valorTotalCount = 0
    dataEntradaCount = 0
    dataSaidaCount = 0

    nameLCS = 0

    tempdataEntrada = ''
    tempdataSaida = ''


    conChoices = ['NRO NOTA', 'NRO DA NOTA', 'NUMERO NOTA', 'NUMERO DA NOTA', 'NÚMERO NOTA', 'NÚMERO DA NOTA']
    dataEntradaChoices = ['ENTRADA', 'DATA DE ENTRADA']
    dataSaidaChoices = ['DT HR ATRACACAO NAVIO', 'ATRACACAO NAVIO', 'DT HR ATRACACAO']
    valorChoices = ['VALOR TOTAL', 'TOTAL']

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


        #dataEntrada
        if process.extractOne(str(line[1][0]).upper(), dataEntradaChoices, scorer=fuzz.partial_ratio)[1] > 85 and vencFlag == False:
            flagDataSaida = True
            if jsonResult.get('dataEntrada') != None:
                if process.extractOne(str(line[1][0]).upper(), dataSaidaChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempDataSaida.upper(), dataEntradaChoices, scorer=fuzz.ratio)[1] \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0])) != None:
                    tempdataEntrada = str(line[1][0])
                    jsonResult['dataEntrada'] = str(line[1][0])
                    dataEntrada = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                    if dataEntrada != None:
                        jsonResult['dataEntrada'] = dataEntrada.group()
            else:
                jsonResult['dataEntrada'] = str(line[1][0])
                dataEntrada = re.search(r'[0-9]+/[0-9]+/[0-9]+', line[1][0])
                if dataEntrada != None:
                    jsonResult['dataEntrada'] = dataEntrada.group()

        if flagDataEntrada == True and vencFlag == False:
            dataEntradaCount += 1
            if dataEntradaCount <= 5:
                dataEntrada = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                if dataEntrada != None:
                    jsonResult['dataEntrada'] = dataEntrada.group()
            else:
                vencFlag = True
        

        #dataSaida
        if process.extractOne(str(line[1][0]).upper(), dataSaidaChoices, scorer=fuzz.partial_ratio)[1] > 85 and vencFlag == False:
            flagDataSaida = True
            if jsonResult.get('dataSaida') != None:
                if process.extractOne(str(line[1][0]).upper(), dataSaidaChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempDataSaida.upper(), dataSaidaChoices, scorer=fuzz.ratio)[1] \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0])) != None:
                    tempDataSaida = str(line[1][0])
                    jsonResult['dataSaida'] = str(line[1][0])
                    dataSaida = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                    if dataSaida != None:
                        jsonResult['dataSaida'] = dataSaida.group()
            else:
                jsonResult['dataSaida'] = str(line[1][0])
                dataSaida = re.search(r'[0-9]+/[0-9]+/[0-9]+', line[1][0])
                if dataSaida != None:
                    jsonResult['dataSaida'] = dataSaida.group()

        if flagDataSaida == True and vencFlag == False:
            dataSaidaCount += 1
            if dataSaidaCount <= 5:
                dataSaida = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line[1][0]))
                if dataSaida != None:
                    jsonResult['dataEntrada'] = dataSaida.group()
            else:
                vencFlag = True
    print('end of for loop \n')

    print(f'\nOutput paddleNFS (lang={lg}): {jsonResult} \n')
    return jsonResult

res = runPaddleOCR('DETNF500218_0.jpg')
print(res)