import cv2
import re
from paddleocr import PaddleOCR#, draw_structure_result, save_structure_res, draw_ocr
from dictionaries import companies, listaCNPJ

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
    ocr = PaddleOCR(use_angle_cls=True)
    if lg != None:
        #table_engine = PPStructure(show_log=True, lang=lg)
        ocr = PaddleOCR(use_angle_cls=True, lang=lg)
        print(lg)
    
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

        
        #Razao Social

        for company in companies:
            n = fuzz.partial_ratio(str(line[1][0]), company)
            tempLCS = lcs(str(line[1][0]), company)
            if n > 90 and tempLCS > nameLCS:
                jsonResult['nome'] = company
                nameLCS = tempLCS


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


        if process.extractOne(str(line[1][0]).upper(), valorChoices, scorer=fuzz.partial_ratio)[1] > 95:
            flagValorTotal = True

        if fuzz.token_set_ratio(str(line[1][0]).upper(), 'VALOR TOTAL') > 80:
            flagValorTotal = True

        if flagValorTotal == True and valorTotalCount <= 5:
            valorTotalCount += 1
            if str(line[1][0]).find('R$') != -1:
                jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()

            elif re.search(r'[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line[1][0])) != None:
                jsonResult['valor'] = re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line[1][0])).group()

        
        #CIF
        if flagCIF == False:
            if process.extractOne(str(line[1][0]).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] > 80:
                if jsonResult.get('valor') != None:
                    if process.extractOne(str(line[1][0]).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('valor')).upper(), cifChoices, scorer=fuzz.partial_ratio)[1]:
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


        if process.extractOne(str(line[1][0]).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] > 95:
            flagCIF = True

        if fuzz.token_set_ratio(str(line[1][0]).upper(), 'VALOR TOTAL') > 80:
            flagCIF = True

        if flagCIF == True and cifCount <= 5:
            cifCount += 1
            if str(line[1][0]).find('R$') != -1:
                jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()

            elif re.search(r'[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line[1][0])) != None:
                jsonResult['valor'] = re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line[1][0])).group()

        if fuzz.token_set_ratio(str(line[1][0]).upper(), 'CNTR') > 60:
            jsonResult['CNTR'] = str(line[1][0])

    print('end of for loop')

    print(f'Output paddleMinutaCalculo (lang={lg}): {jsonResult} \n')
    return jsonResult

#res = runPaddleOCR('LINE_NFS.jpg')
#print(res)