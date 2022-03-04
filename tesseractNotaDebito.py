import cv2
import re
import pytesseract
from dictionaries import companies, listaCNPJ, mapNameCNPJ
from LCS import lcs

from PIL import Image
from fuzzywuzzy import fuzz
from fuzzywuzzy import process



def runTesseractOCR(img_path):

    jsonResult = {}

    cnpjFlag = False
    flagVencimento = False
    valorTotal = False
    flagNameFromCNPJ = False
    vencFlag = True

    vencimentoChoices = ['DATA', 'VENCIMENTO', 'DATA VENCIMENTO', 'DATA DE VENCIMENTO']

    nameLCS = 0
    
    #save_folder = './output/table'
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    config_tesseract = '--oem 3  --psm 11'
    texto = pytesseract.image_to_string(img, config=config_tesseract)
    texto = texto.lower()

    tempResult = texto.split('\n')
    result =[]
    
    for r in tempResult:
        if r != '':
            result.append(r)
    print(result)
    print(f'Inicio {img_path} ')

    for line in result:
        i = 0
        #con
        if i < 5:
            if re.match(r'[0-9]+', str(line)) != None:
                con = re.match(r'[0-9]+', str(line)).group()
                jsonResult['con'] = con


        if fuzz.token_set_ratio(str(line), 'Nro da nota') > 60:
            if jsonResult.get('con') != None:
                if fuzz.token_set_ratio(str(line), 'Nro da nota') > fuzz.token_set_ratio(jsonResult.get('con'), 'Nro da nota'):
                    con = re.search(r'[a-zA-Z]*[0-9]+', str(line))
                    if con != None:
                        jsonResult['con'] = con.group()#str(line)[str(line).find(':')+1:].strip()
            else:
                con = re.search(r'[a-zA-Z]*[0-9]+', str(line))
                if con != None:
                    jsonResult['con'] = con.group()#str(line)[str(line).find(':')+1:].strip()

                
        #Razao Social
        if fuzz.token_set_ratio(str(line), 'Razao Social') > 60 and fuzz.token_set_ratio(str(line), 'MERCK') < 80:
            if jsonResult.get('nome') != None:
                if fuzz.token_set_ratio(str(line), 'Razao Social') > fuzz.token_set_ratio(jsonResult.get('nome'), 'Razao Social'):
                    jsonResult['nome'] = str(line)[str(line).find(':')+1:].strip()
            else:
                jsonResult['nome'] = str(line)[str(line).find(':')+1:].strip()



        #if fuzz.token_set_ratio(str(line), 'Numero Nota') > 50:
            #print(line, fuzz.token_set_ratio(str(line), 'Numero Nota'))
            #print()
            #if jsonResult.get('con') != None:
                #if fuzz.token_set_ratio(str(line), 'Numero Nota') > fuzz.token_set_ratio(jsonResult.get('con'), 'Numero Nota'):
                    #jsonResult['con'] = str(line)
            #else:
                #jsonResult['con'] = str(line)


        #PO
        if fuzz.token_set_ratio(str(line), 'PO') > 80 or fuzz.token_set_ratio(str(line), 'NUMERO PEDIDO') > 80:
            if jsonResult.get('PO') != None:
                if fuzz.token_set_ratio(str(line), 'PO') > fuzz.token_set_ratio(jsonResult.get('PO'), 'PO'):
                    jsonResult['PO'] = str(line)
                    po = re.search(r'[0-9]+', line)
                    if po != None:
                        jsonResult['PO'] = po.group()
                    #po = re.match(r'[0-9]+', str(line))
                    #if po != None:
                        #po = po.group()
                        #jsonResult['PO'] = po #str(line)                    
            else:
                jsonResult['PO'] = str(line)
                po = re.search(r'[0-9]+', str(line))
                if po != None:
                    jsonResult['PO'] = po.group()
                #if po != None:
                    #po = po.group()
                    #jsonResult['PO'] = po #str(line)

        
        #VALOR
        if fuzz.token_set_ratio(str(line), 'VALOR') > 60:
            if jsonResult.get('valor') != None:
                if fuzz.token_set_ratio(str(line), 'VALOR') > fuzz.token_set_ratio(jsonResult.get('valor'), 'VALOR'):
                    jsonResult['valor'] = str(line)
                    if str(line).find('R$') != -1:
                        jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()

            else:
                if str(line).find('R$') != -1:
                        jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()


        #Vencimento
        if fuzz.token_set_ratio(str(line), 'Vencimento') > 80 or flagVencimento == True:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if fuzz.token_set_ratio(str(line), 'Vencimento') > fuzz.token_set_ratio(jsonResult.get('vencimento'), 'Vencimento'):
                    #jsonResult['vencimento'] = str(line)
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line)
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                #jsonResult['vencimento'] = str(line)
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line)
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()

            
        #Vencimento
        if process.extractOne(line.upper(), vencimentoChoices, scorer=fuzz.partial_ratio)[1] > 85 and vencFlag == False:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if process.extractOne(line.upper(), vencimentoChoices, scorer=fuzz.ratio)[1] > process.extractOne(tempVencimento.upper(), vencimentoChoices, scorer=fuzz.ratio)[1] \
                    and re.search(r'[0-9]+/[0-9]+/[0-9]+', line) != None:
                    tempVencimento = line
                    jsonResult['vencimento'] = line
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line)
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                jsonResult['vencimento'] = line
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line)
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


        #nome
        if flagNameFromCNPJ == False:
            for company in companies:
                n = fuzz.partial_ratio(line.upper(), company)
                tempLCS = lcs(line.upper(), company)
                if n > 90 and tempLCS > nameLCS:
                    jsonResult['nome'] = company
                    nameLCS = tempLCS

        if fuzz.token_set_ratio(str(line), 'Valor Total') > 80:
            valorTotal = True

        if valorTotal == True:
            if str(line).find('R$') != -1:
                        jsonResult['valor'] = str(line)[str(line).find('R$'):].strip()


        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                if fuzz.token_set_ratio(str(line), num) > 90:
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
                    if fuzz.token_set_ratio(str(line), stringCNPJ) > 90:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        jsonResult['nome'] = mapNameCNPJ[num]
                        flagNameFromCNPJ = True
                        break


    
    print('end of for loop \n')
    print(f'\nOutput tesseractNotaDebito: {jsonResult} \n')

    return jsonResult


res = runTesseractOCR('20FS137029A_0.jpg')
print(res)