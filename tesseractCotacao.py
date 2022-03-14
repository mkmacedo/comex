import cv2
import re
from paddleocr import PaddleOCR#, draw_structure_result, save_structure_res, draw_ocr
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


def runTesseractOCR(img_path, lg=None):
    cnpjFlag = False
    
    flagNumNota = False
    flagCIF = False
    flagValorTotal = False

    numNotaCount = 0
    valorTotalCount = 0
    cifCount = 0

    nameLCS = 0

    valorChoices = ['VALOR TOTAL']
    cifChoices = ['VALOR CIF']

    jsonResult = {}

    #table_engine = PPStructure(show_log=True)
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #cv2.imwrite('aaaaaaaaaaaa.jpg', img)
    config_tesseract = '--oem 3  --psm 11'
    texto = pytesseract.image_to_string(img, config=config_tesseract)
    texto = texto.lower()

    tempResult = texto.split('\n')
    result =[]

    for r in tempResult:
        if r != '':
            result.append(r)
    #ocr = PaddleOCR(use_angle_cls=True, lang='en')

    #result = ocr.ocr(img_path, cls=True)
    listaPeriodos = []

    for line in result:
        print(line)
        if re.search(r"de ?[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9] ?a ?[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]", line) != None:
            periodo = re.search(r"de ?[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9] ?a ?[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]", line).group()
            listaPeriodos.append(periodo)

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
            if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] > 80:
                if jsonResult.get('valor') != None:
                    if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('valor')).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1]:
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


        if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] > 95:
            flagValorTotal = True
            valorTotalCount = 0

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
                if jsonResult.get('CIF') != None:
                    if process.extractOne(str(line).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] \
                        > process.extractOne(str(jsonResult.get('CIF')).upper(), cifChoices, scorer=fuzz.partial_ratio)[1]:
                        jsonResult['CIF'] = str(line)
                        valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line))
                        if valor != None:
                            jsonResult['CIF'] = valor.group()
                        elif str(line).find('R$') != -1:
                            jsonResult['CIF'] = str(line)[str(line).find('R$'):].strip()

                else:
                    valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', str(line))
                    if valor != None:
                        jsonResult['CIF'] = valor.group()
                    elif str(line).find('R$') != -1:
                        jsonResult['CIF'] = str(line)[str(line).find('R$'):].strip()


        if process.extractOne(str(line).upper(), cifChoices, scorer=fuzz.partial_ratio)[1] > 95:
            flagCIF = True

        if fuzz.token_set_ratio(str(line).upper(), 'VALOR CIF') > 80:
            flagCIF = True

        if flagCIF == True and cifCount <= 5:
            cifCount += 1
            if str(line).find('R$') != -1:
                jsonResult['CIF'] = str(line)[str(line).find('R$'):].strip()

            elif re.search(r'[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line)) != None:
                jsonResult['CIF'] = re.search(r'(?:R$ ?)?[0-9]+(?:\.[0-9]+)?,[0-9][0-9]', str(line)).group()

        if fuzz.token_set_ratio(str(line).upper(), 'CNTR') > 60:
            jsonResult['CNTR'] = str(line)

        #DI
        if fuzz.ratio("DI", str(line).upper()) > 80 or fuzz.token_set_ratio("DI", str(line).upper()) > 95 or re.search(r"DI ?[0-9]+", str(line)) != None:
            print("DI", str(line))
            if jsonResult.get('DI') != None:
                if fuzz.ratio("DI", str(line).upper()) > fuzz.ratio("DI", str(jsonResult.get("DI"))) :
                    jsonResult['DI'] = str(line)
                    di = re.search(r'[0-9]+', line)
                    if di != None:
                        jsonResult['DI'] = di.group()

                    
            else:
                jsonResult['DI'] = str(line)
                di = re.search(r'[0-9]+', str(line))
                if di != None:
                    jsonResult['DI'] = di.group()



    print('end of for loop')

    if len(listaPeriodos) > 0:
        listaDatas = re.findall(r"[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]", listaPeriodos[-1])
        if len(listaDatas) > 0:
            jsonResult["dataEntrada"] = listaDatas[0]
            jsonResult["dataSaida"] = listaDatas[-1]


    print(f'Output paddleMinutaCalculo (lang={lg}): {jsonResult} \n')
    return jsonResult

#res = runPaddleOCR('Minuta DI 211911396-2_page-0001 (1)(1).jpg', 'en')
#print(res)