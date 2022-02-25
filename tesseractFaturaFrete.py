import cv2
import re
#from paddleocr import PPStructure, draw_structure_result, save_structure_res, PaddleOCR, draw_ocr
from dictionaries import companies, listaCNPJ
import pytesseract

#from LCS import lcs

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
    print('\nExecutando OCR tessaractFaturaFrete \n')
    cnpjFlag = False
    conFlag = False    
    flagNumNota = False
    flagValorTotal = False
    flagVencimento = False
    vencFlag = False

    numNotaCount = 0
    valorTotalCount = 0
    vencimentoCount = 0

    nameLCS = 0

    tempVencimento = ''

    poChoices = ['PO', 'NUMERO PEDIDO', 'NRO PEDIDO', 'ORDEM COMPRA']
    conChoices = ['NRO NOTA', 'NRO DA NOTA', 'NUMERO NOTA', 'NUMERO DA NOTA', 'NÚMERO NOTA', 'NÚMERO DA NOTA']
    vencimentoChoices = ['DATA', 'VENCIMENTO', 'DATA VENCIMENTO']
    valorChoices = ['VALOR NOTA', 'VALOR DA NOTA', 'VALOR TOTAL', 'VR.LIQUIDO', 'VR LIQUIDO']

    jsonResult = {}

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

        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                if fuzz.token_set_ratio(str(line), num) > 90:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', num)
                    stringCNPJ = ''
                    for s in cnpj:
                        stringCNPJ += s
                    if fuzz.token_set_ratio(str(line), stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        break


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


        if fuzz.token_set_ratio(str(line).upper(), 'VR LIQUIDO') > 80 or fuzz.partial_ratio(str(line).upper(), 'VR LIQUIDO') > 80:
            flagValorTotal = True
            valorTotalCount = 0

        if flagValorTotal == True and valorTotalCount < 7 or (str(line).find('R$') != -1 and valorTotalCount < 7):
            valorTotalCount += 1
            if re.search(r'(?:[0-9]+\.?)+(?:,[0-9][0-9])?', str(line)) != None:
                value = str(line)
                value_split = value.split()
                value = ''
                for e in value_split:
                    value += e
                value = re.search(r'(?:[0-9]+\.?)+(?:,[0-9][0-9])?', value).group()
                if jsonResult.get('valor') == None:
                    jsonResult['valor'] = value
                else:
                    tmp_v = value
                    value = tmp_v
                    tmp_arr = tmp_v.split('.')
                    tmp_v = ''
                    for r in tmp_arr:
                        if ',' in r:
                            for c in r.split(','):
                                tmp_v += c
                        else:
                            tmp_v += r
                    
                    v_arr = jsonResult['valor'].split('.')
                    v = ''
                    for e in v_arr:
                        if ',' in e:
                            for c in e.split(','):
                                v += c 
                        else:
                            v += e
                    
                    if tmp_v.isnumeric() and v.isnumeric:
                        if eval(tmp_v) > eval(v):
                            jsonResult['valor'] = value


        #Vencimento
        if (process.extractOne(str(line).upper(), vencimentoChoices, scorer=fuzz.partial_ratio)[1] > 85 \
            or process.extractOne(str(line).upper(), vencimentoChoices, scorer=fuzz.token_set_ratio)[1] > 85) \
                and vencFlag == False:
            flagVencimento = True
            vencFlag = False
            if jsonResult.get('vencimento') != None:
                if process.extractOne(str(line).upper(), vencimentoChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempVencimento.upper(), vencimentoChoices, scorer=fuzz.ratio)[1] \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line)) != None:
                    tempVencimento = str(line)
                    jsonResult['vencimento'] = str(line)
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line))
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                jsonResult['vencimento'] = str(line)
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line)
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()

        if flagVencimento == True and vencFlag == False:
            vencimentoCount += 1
            if vencimentoCount <= 5:
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', str(line))
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()
            else:
                vencFlag = True
    
    print('end of for loop \n')

    print(f'\nOutput tesseractFaturaFrete: {jsonResult} \n')
    return jsonResult

#res = runTesseractOCR('bol_ccc_001904899_1.jpg')
#print(res)