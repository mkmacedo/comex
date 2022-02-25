#import cv2
import re
from paddleocr import PaddleOCR#, PPStructure, draw_structure_result, save_structure_res, draw_ocr
from dictionaries import companies, listaCNPJ, field_validation, mapNameCNPJ

from LCS import lcs

#from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#con
#nome
#valor
#CNPJ



def runPaddleOCR(img_path, lg=None):
    print('\nExecutando OCR paddleCustoFrete \n')
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

#    try:
#        img = cv2.imread(img_path)
#        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#        cv2.imwrite(img_path, img)
#    except:
#        pass

    if lg == None:
        ocr = PaddleOCR(use_angle_cls=True)
    else:
        ocr = PaddleOCR(use_angle_cls=True, lang=lg)
        print('-> Argumento Idioma paddleCustoFrete:', lg, '\n')

    print(f'Inicio {img_path} ')
    result = ocr.ocr(img_path, cls=True)

    #print(f'Resultado apos excucao OCR Paddle: {result}\n')

    for line in result:
        if flagNumNota == True:
            numNotaCount += 1

        #con
        if numNotaCount <= 7 and conFlag == False and flagNumNota == True:
            numNotaCount += 1
            slicedLine = str(line[1][0])[:str(line[1][0]).find('|')]
            if re.match(r'[a-zA-Z]*[0-9]+', slicedLine) != None:
                con = re.match(r'[a-zA-Z]*[0-9]+', slicedLine).group()
                jsonResult['con'] = con
                conFlag = True


        if process.extractOne(str(line[1][0]).upper(), conChoices, scorer=fuzz.token_set_ratio)[1] > 85 and conFlag == False:
            flagNumNota = True

            if jsonResult.get('con') != None:
                if process.extractOne(str(line[1][0]).upper(), conChoices, scorer=fuzz.token_set_ratio)[1] \
                    > process.extractOne(str(jsonResult.get('con')).upper(), conChoices, scorer=fuzz.token_set_ratio)[1]:
                    slicedLine = str(line[1][0])[:str(line[1][0]).find('|')]
                    con = re.search(r'[a-zA-Z]*[0-9]+', slicedLine)
                    if con != None:
                        jsonResult['con'] = con.group()#str(t[0])[str(t[0]).find(':')+1:].strip()
                        conFlag = True
            else:
                slicedLine = str(line[1][0])[:str(line[1][0]).find('|')]
                con = re.search(r'[a-zA-Z]*[0-9]+', slicedLine)
                if con != None:
                    jsonResult['con'] = con.group()#str(t[0])[str(t[0]).find(':')+1:].strip()
                    conFlag = True

        
        #Razao Social
        if cnpjFlag == False:
            for company in companies:
                n = fuzz.partial_ratio(str(line[1][0]), company)
                tempLCS = lcs(str(line[1][0]), company)
                if n > 90 and tempLCS > nameLCS:
                    jsonResult['nome'] = company
                    nameLCS = tempLCS
        else:
            jsonResult['nome'] = mapNameCNPJ.get(jsonResult.get('CNPJ'))


        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                slicedNum = num[:num.find('/')]
                if fuzz.partial_ratio(str(line[1][0]), slicedNum) > 90:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', slicedNum)
                    stringCNPJ = ''
                    for s in cnpj:
                        stringCNPJ += s
                    if fuzz.partial_ratio(str(line[1][0]), stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        break


        #PO
        if process.extractOne(str(line[1][0]).upper(), poChoices, scorer=fuzz.token_set_ratio)[1] > 60:
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
            if fuzz.token_set_ratio(str(line[1][0]).upper(), 'VALOR') > 80:
                if jsonResult.get('valor') != None:
                    if fuzz.token_set_ratio(str(line[1][0]).upper(), 'VALOR') > fuzz.token_set_ratio(str(jsonResult.get('valor')).upper(), 'VALOR'):
                        jsonResult['valor'] = str(line[1][0])
                        if str(line[1][0]).find('R$') != -1:
                            jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()

                else:
                    if str(line[1][0]).find('R$') != -1:
                        jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()


        if process.extractOne(str(line[1][0]).upper(), valorChoices, scorer=fuzz.token_set_ratio)[1] > 80:
            flagValorTotal = True

        if flagValorTotal == True and valorTotalCount <= 5:
            valorTotalCount += 1
            if re.search(regexValor, str(line[1][0])) != None:
                jsonResult['valor'] = re.search(regexValor, str(line[1][0])).group()

    
    print('end of for loop \n')

    print(f'\nOutput paddleCustoFrete (lang={lg}): {jsonResult} \n')
    return jsonResult

#res = runPaddleOCR('RelatórioFaturaAGV735_1.jpg', 'en')
#res = runPaddleOCR('CustoFrete-FL_0.jpg', 'latin')
#print(res)