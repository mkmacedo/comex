import cv2
import re
from paddleocr import PaddleOCR#, draw_structure_result, save_structure_res
from dictionaries import companies, listaCNPJ

#from PIL import Image
from fuzzywuzzy import fuzz
#from fuzzywuzzy import process


def runPaddleOCR(img_path, lg=None):
    print('\nExecutando OCR paddleDACTE \n')

    jsonResult = {}

    cnpjFlag = False
    flagVencimento = False
    valorTotal = False
    
    if lg != None:
        #table_engine = PPStructure(show_log=True, lang=lg)
        ocr = PaddleOCR(use_angle_cls=True)
        print('-> Argumento Idioma paddleDACTE:',lg,'\n')
    else:
        #table_engine = PPStructure(show_log=True)
        ocr = PaddleOCR(use_angle_cls=True, lang=lg)

    #save_folder = './output/table'
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(img_path, img)

    print(f'Inicio {img_path} ')
    result = ocr.ocr(img_path, cls=True)

    #result = table_engine(img)
    #save_structure_res(result, save_folder,os.path.basename(img_path).split('.')[0])

    for line in result:

        #con
        if fuzz.token_set_ratio(str(line[1][0]), 'Nro da nota') > 80 or fuzz.token_set_ratio(str(line[1][0]).lower(), 'con') > 80 or fuzz.partial_ratio(str(line[1][0]).lower(), 'numero') > 80:
            if jsonResult.get('con') != None:
                if fuzz.token_set_ratio(str(line[1][0]), 'Nro da nota') > fuzz.token_set_ratio(jsonResult.get('con'), 'Nro da nota'):
                    con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0]))
                    if con != None:
                        jsonResult['con'] = con.group()#str(line[1][0])[str(line[1][0]).find(':')+1:].strip()
            else:
                con = re.search(r'[a-zA-Z]*[0-9]+', str(line[1][0]))
                if con != None:
                    jsonResult['con'] = con.group()#str(line[1][0])[str(line[1][0]).find(':')+1:].strip()

                
        #Razao Social
        if fuzz.token_set_ratio(str(line[1][0]), 'Razao Social') > 60 and fuzz.token_set_ratio(str(line[1][0]), 'MERCK') < 80:
            if jsonResult.get('nome') != None:
                if fuzz.token_set_ratio(str(line[1][0]), 'Razao Social') > fuzz.token_set_ratio(jsonResult.get('nome'), 'Razao Social'):
                    jsonResult['nome'] = str(line[1][0])[str(line[1][0]).find(':')+1:].strip()
            else:
                jsonResult['nome'] = str(line[1][0])[str(line[1][0]).find(':')+1:].strip()


        #PO
        if fuzz.token_set_ratio(str(line[1][0]), 'PO') > 80 or fuzz.token_set_ratio(str(line[1][0]), 'NUMERO PEDIDO') > 80:
            if jsonResult.get('PO') != None:
                if fuzz.token_set_ratio(str(line[1][0]), 'PO') > fuzz.token_set_ratio(jsonResult.get('PO'), 'PO'):
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
        if fuzz.token_set_ratio(str(line[1][0]), 'VALOR') > 60:
            if jsonResult.get('valor') != None:
                if fuzz.token_set_ratio(str(line[1][0]), 'VALOR') > fuzz.token_set_ratio(jsonResult.get('valor'), 'VALOR'):
                    jsonResult['valor'] = str(line[1][0])
                    if str(line[1][0]).find('R$') != -1:
                        jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()

            else:
                if str(line[1][0]).find('R$') != -1:
                        jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()


        #Vencimento
        if fuzz.token_set_ratio(str(line[1][0]), 'Vencimento') > 80 or flagVencimento == True:
            flagVencimento = True
            if jsonResult.get('vencimento') != None:
                if fuzz.token_set_ratio(str(line[1][0]), 'Vencimento') > fuzz.token_set_ratio(jsonResult.get('vencimento'), 'Vencimento'):
                    #jsonResult['vencimento'] = str(line[1][0])
                    vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line[1][0])
                    if vencimento != None:
                        jsonResult['vencimento'] = vencimento.group()
            else:
                #jsonResult['vencimento'] = str(line[1][0])
                vencimento = re.search(r'[0-9]+/[0-9]+/[0-9]+', line[1][0])
                if vencimento != None:
                    jsonResult['vencimento'] = vencimento.group()


        #nome
        for company in companies:
            if fuzz.token_set_ratio(str(line[1][0]), company) > 80:
                jsonResult['nome'] = company

        if fuzz.token_set_ratio(str(line[1][0]), 'Valor Total') > 80:
            valorTotal = True

        if valorTotal == True:
            if str(line[1][0]).find('R$') != -1:
                        jsonResult['valor'] = str(line[1][0])[str(line[1][0]).find('R$'):].strip()


        #CNPJ
        if cnpjFlag == False:
            for num in listaCNPJ:
                if fuzz.token_set_ratio(str(line[1][0]), num) > 50:
                    jsonResult['CNPJ'] = num
                    cnpjFlag = True
                    break
                else:
                    cnpj = re.findall(r'[0-9]+', num)
                    stringCNPJ = ''
                    for s in cnpj:
                        stringCNPJ += s
                    if fuzz.token_set_ratio(str(line[1][0]), stringCNPJ) > 50:
                        jsonResult['CNPJ'] = num
                        cnpjFlag = True
                        break
    
    print('end of for loop \n')

    print(f'\nOutput paddleDACTE (lang={lg}): {jsonResult} \n')
    return jsonResult


#res = runPaddleOCR('FL_DACTE_0.jpg')
#print(res)