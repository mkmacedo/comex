import cv2
import re
#from paddleocr import PPStructure, draw_structure_result, save_structure_res, PaddleOCR, draw_ocr
from dictionaries import companies, listaCNPJ, field_validation, mapNameCNPJ
import pytesseract

from LCS import lcs

#from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#con
#nome
#valor
#CNPJ
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def runTesseractOCR(img_path):
    print('\nExecutando OCR tesseractCustoFrete \n')
    cnpjFlag = False
    conFlag = False    
    flagNumNota = False
    flagValorTotal = False

    numNotaCount = 0
    valorTotalCount = 0

    regexValor = field_validation.get('valor')

    
    jsonResult = {}
    #table_engine = PPStructure(show_log=True, lang='en')
    nameLCS = 0

    poChoices = ['PO', 'NUMERO PEDIDO', 'NRO PEDIDO']
    conChoices = ['FATURA', 'PERIODO']
    valorChoices = ['VALOR NOTA', 'VALOR DA NOTA', 'VALOR TOTAL', 'VR.LIQUIDO', 'VR LIQUIDO', 'TOTAL GERAL', 'TOTAL']

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
    #print(result)


    for line in result:
        if flagNumNota == True:
            numNotaCount += 1

        #con

        if numNotaCount <= 7 and conFlag == False and flagNumNota == True:
            numNotaCount += 1
            slicedLine = str(line)[:str(line).find('|')]
            if re.match(r'[a-zA-Z]*[0-9]+', slicedLine) != None:
                con = re.match(r'[a-zA-Z]*[0-9]+', slicedLine).group()
                jsonResult['con'] = con
                conFlag = True


        if process.extractOne(str(line).upper(), conChoices, scorer=fuzz.token_set_ratio)[1] > 85 and conFlag == False:
            flagNumNota = True

            if jsonResult.get('con') != None:
                if process.extractOne(str(line).upper(), conChoices, scorer=fuzz.token_set_ratio)[1] \
                    > process.extractOne(str(jsonResult.get('con')).upper(), conChoices, scorer=fuzz.token_set_ratio)[1]:
                    slicedLine = str(line)[:str(line).find('|')]
                    con = re.search(r'[a-zA-Z]*[0-9]+', slicedLine)
                    if con != None:
                        jsonResult['con'] = con.group()#str(t[0])[str(t[0]).find(':')+1:].strip()
                        conFlag = True
            else:
                slicedLine = str(line)[:str(line).find('|')]
                con = re.search(r'[a-zA-Z]*[0-9]+', slicedLine)
                if con != None:
                    jsonResult['con'] = con.group()#str(t[0])[str(t[0]).find(':')+1:].strip()
                    conFlag = True

        
        #Razao Social
        if cnpjFlag == False:
            for company in companies:
                n = fuzz.partial_ratio(str(line), company)
                tempLCS = lcs(str(line), company)
                if n > 90 and tempLCS > nameLCS:
                    jsonResult['nome'] = company
                    nameLCS = tempLCS
        else:
            jsonResult['nome'] = mapNameCNPJ.get(jsonResult.get('CNPJ'))


        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                slicedNum = num[:num.find('/')]
                if fuzz.partial_ratio(str(line), slicedNum) > 90:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', slicedNum)
                    stringCNPJ = ''
                    for s in cnpj:
                        stringCNPJ += s
                    if fuzz.partial_ratio(str(line), stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        break


        #PO


        if process.extractOne(str(line).upper(), poChoices, scorer=fuzz.token_set_ratio)[1] > 60:
            if jsonResult.get('PO') != None:
                if process.extractOne(str(line).upper(), poChoices, scorer=fuzz.token_set_ratio) > process.extractOne(str(jsonResult.get('PO')).upper(), poChoices, scorer=fuzz.token_set_ratio):
                    jsonResult['PO'] = str(line)
                    po = re.search(r'[0-9]+', line)
                    if po != None:
                        jsonResult['PO'] = po.group()

                    
            else:
                jsonResult['PO'] = str(line)
                po = re.search(r'[0-9]+', str(line))
                if po != None:
                    jsonResult['PO'] = po.group()


        #VALOR
        if flagValorTotal == False:
            if fuzz.token_set_ratio(str(line).upper(), 'VALOR') > 80:
                if jsonResult.get('valor') != None:
                    if fuzz.token_set_ratio(str(line).upper(), 'VALOR') > fuzz.token_set_ratio(str(jsonResult.get('valor')).upper(), 'VALOR'):
                        jsonResult['valor'] = str(line)
                        if str(line).find('R$') != -1:
                            jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()

                else:
                    if str(line).find('R$') != -1:
                        jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()


        if process.extractOne(str(line).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] > 80:
            flagValorTotal = True

        if flagValorTotal == True and valorTotalCount <= 5:
            valorTotalCount += 1
            if re.search(regexValor, str(line)) != None:
                jsonResult['valor'] = re.search(regexValor, str(line)).group()
    
    print('end of for loop \n')

    print(f'\nOutput tesseractCustoFrete: {jsonResult} \n')
    return jsonResult

#res = runPaddleOCR('RelatórioFaturaAGV735_0.jpg', 'latin')
#res = runPaddleOCR('CustoFrete-FL_0.jpg')
#print(res)