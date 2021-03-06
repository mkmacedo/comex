import cv2
from paddleocr import PaddleOCR
from dictionaries import companies
from LCS import lcs
from lsCommonSegment import longestSubsequenceCommonSegment
import pytesseract

from fuzzywuzzy import fuzz

def getCompanyName(img_path, lg=None):
    print('\nExecutando companyName.getCompanyName \n')
    companyName = None

    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(img_path, img)

    if lg == None:
        ocr = PaddleOCR(use_angle_cls=True)
    else:
        ocr = PaddleOCR(use_angle_cls=True, lang=lg)

    result = ocr.ocr(img_path, cls=True)

    maxLCS = 0
    maxFuzz = 0
    for line in result:
        for company in companies:
            splitCompany = company.split()
            splitString = str(line[1][0]).split()
            newCompany = ''
            newString = ''
            for c in splitCompany:
                newCompany += c
            for d in splitString:
                newString += d
            tempFuzzTokenSetRatio = fuzz.token_set_ratio(newString.upper(), newCompany)
            tempFuzzPartialRatio = fuzz.partial_ratio(newString.upper(), newCompany)
            
            if tempFuzzTokenSetRatio > 87 or tempFuzzPartialRatio > 87:
                lcsResult = longestSubsequenceCommonSegment(5, str(line[1][0]), company)
                if lcsResult > maxLCS and str(line[1][0]) != 'GKO FRETE':
                    if tempFuzzTokenSetRatio > maxFuzz or tempFuzzPartialRatio > maxFuzz:
                        #print(company, str(line[1][0]), lcsResult, max(tempFuzzTokenSetRatio, tempFuzzPartialRatio))
                        companyName = company
                        maxFuzz = max(tempFuzzTokenSetRatio, tempFuzzPartialRatio)
                        maxLCS = lcsResult

    if companyName != None:
        print(f'\n{img_path} -> Nome do fornecedor idenficiado: {companyName} (Paddle) \n')
        return companyName
    
    else:

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

        maxLCS = 0
        maxFuzz = 0
        for line in result:
            print(line)
            for company in companies:
                splitCompany = company.split()
                splitString = str(line).split()
                newCompany = ''
                newString = ''
                for c in splitCompany:
                    newCompany += c
                for d in splitString:
                    newString += d
                tempFuzzTokenSetRatio = fuzz.token_set_ratio(newString.upper(), newCompany)
                tempFuzzPartialRatio = fuzz.partial_ratio(newString.upper(), newCompany)
                
                if tempFuzzTokenSetRatio > 87 or tempFuzzPartialRatio > 87:
                    lcsResult = longestSubsequenceCommonSegment(5, str(line), company)
                    if lcsResult > maxLCS and str(line) != 'GKO FRETE':
                        if tempFuzzTokenSetRatio > maxFuzz or tempFuzzPartialRatio > maxFuzz:
                            #print(company, str(line[1][0]), lcsResult, max(tempFuzzTokenSetRatio, tempFuzzPartialRatio))
                            companyName = company
                            maxFuzz = max(tempFuzzTokenSetRatio, tempFuzzPartialRatio)
                            maxLCS = lcsResult

        if companyName != None:
            print(f'\n{img_path} -> Nome do fornecedor idenficiado: {companyName} (Paddle) \n')
            return companyName


        return None


#print(getCompanyName('Diremadi_0.pdf'))
#print(getCompanyName('NF500218Boleto_0.jpg'))