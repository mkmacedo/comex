import cv2
#import re
from paddleocr import PaddleOCR#,PPStructure , draw_structure_result, save_structure_res, draw_ocr
from dictionaries import companies, listaCNPJ, docHierarchy, docTypeMap
from LCS import lcs

#from PIL import Image
from fuzzywuzzy import fuzz


def getDocType(img_path, lg=None):
    print('\nExecutando documentType.getDocType \n')
    docType = None
    docTypeList = list(docTypeMap.keys())

    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(img_path, img)

    if lg == None:
        ocr = PaddleOCR(use_angle_cls=True)
    else:
        ocr = PaddleOCR(use_angle_cls=True, lang='en')

    result = ocr.ocr(img_path, cls=True)

    #img = cv2.imread(img_path)
    #result = table_engine(img)

    maxLCS = 0
    maxHier = 0
    for line in result:
        
        for docName in docTypeList:
            if fuzz.token_set_ratio(line[1][0].lower(), docName) > 80:
                lcsResult = lcs(line[1][0], docName)
                tempHier = docHierarchy[docTypeMap[docName]]
                if lcsResult > maxLCS and tempHier > maxHier:
                    maxLCS = lcsResult
                    docType = docTypeMap[docName]
                    maxHier = tempHier

    if docType != None:
        print(f'\n{img_path} -> Tipo de documento identificado: {docType} (Paddle) \n')
        return docType
    else:
        print('Tipo de Documento não identificado...\n')
        return None

#print(getDocType('MapaF_AGv4.jpg', 'en'))
#runPaddleOCR('003.jpg')
#runPaddleOCR('AGV_RL.jpg')
#runPaddleOCR('Diremadi.pdf_1.jpg')
#getDocType('Notas/FATCCC001751938.jpg')
#getDocType('Diremadi_1.jpg')


