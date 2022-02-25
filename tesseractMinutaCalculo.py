import cv2
import re
from dictionaries import companies, listaCNPJ
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
    cnpjFlag = False
    
    flagNumNota = False
    flagCIF = False
    flagValorTotal = False

    numNotaCount = 0
    valorTotalCount = 0
    cifCount = 0

    nameLCS = 0

    valorChoices = ['VALOR NOTA', 'VALOR DA NOTA', 'VALOR TOTAL']
    cifChoices = ['VALOR CIF']

    jsonResult = {}

    #table_engine = PPStructure(show_log=True)
    img = cv2.imread(img_path)
    config_tesseract = '--oem 3  --psm 11'
    texto = pytesseract.image_to_string(img, config=config_tesseract)
    texto = texto.lower()

    tempResult = texto.split('\n')
    result =[]
    
    for r in tempResult:
        if r != '':
            result.append(r)

    print(f'Inicio {img_path} ')
    #ocr = PaddleOCR(use_angle_cls=True, lang='en')

    #result = ocr.ocr(img_path, cls=True)

    for line in result:

        if flagNumNota == True:
            numNotaCount += 1

        
        #Razao Social

        for company in companies:
            n = fuzz.partial_ratio(str(line), company)
            tempLCS = lcs(str(line), company)
            if n > 90 and tempLCS > nameLCS:
                jsonResult['nome'] = company
                nameLCS = tempLCS


        #VALOR
        if flagValorTotal == False:
            if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] > 80:
                if jsonResult.get('valor') != None:
                    if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('valor')).upper(), valorChoices, scorer=fuzz.partial_ratio)[1]:
                        jsonResult['valor'] = str(line)
                        valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line))
                        if valor != None:
                            jsonResult['valor'] = valor.group()
                        elif str(line).find('R$') != -1:
                            jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()

                else:
                    valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line))
                    if valor != None:
                        jsonResult['valor'] = valor.group()
                    elif str(line).find('R$') != -1:
                        jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()


        if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] > 95:
            flagValorTotal = True

        if fuzz.token_set_ratio(str(line).upper(), 'VALOR TOTAL') > 80:
            flagValorTotal = True

        if flagValorTotal == True and valorTotalCount <= 5:
            valorTotalCount += 1
            if str(line).find('R$') != -1:
                jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()

            elif re.search(r'[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line)) != None:
                jsonResult['valor'] = re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line)).group()

        
        #CIF
        if flagCIF == False:
            if process.extractOne(str(line).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] > 80:
                if jsonResult.get('valor') != None:
                    if process.extractOne(str(line).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('valor')).upper(), cifChoices, scorer=fuzz.partial_ratio)[1]:
                        jsonResult['valor'] = str(line)
                        valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line))
                        if valor != None:
                            jsonResult['valor'] = valor.group()
                        elif str(line).find('R$') != -1:
                            jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()

                else:
                    valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line))
                    if valor != None:
                        jsonResult['valor'] = valor.group()
                    elif str(line).find('R$') != -1:
                        jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()


        if process.extractOne(str(line).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] > 95:
            flagCIF = True

        if fuzz.token_set_ratio(str(line).upper(), 'VALOR TOTAL') > 80:
            flagCIF = True

        if flagCIF == True and cifCount <= 5:
            cifCount += 1
            if str(line).find('R$') != -1:
                jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()

            elif re.search(r'[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line)) != None:
                jsonResult['valor'] = re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line)).group()

        if fuzz.token_set_ratio(str(line).upper(), 'CNTR') > 60:
            jsonResult['CNTR'] = str(line)

    print('end of for loop \n')

    print(f'Output paddleMinutaCalculo: {jsonResult} \n')
    return jsonResult

#res = runPaddleOCR('LINE_NFS.jpg')
#print(res)