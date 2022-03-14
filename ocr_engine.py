#import cv2
from paddleocr import PaddleOCR
from dictionaries import companies, listaCNPJ, docHierarchy, docTypeMap, dict_document
from compareAmounts import greater
from LCS import lcs
import paddleNFS
import paddleReciboLocacao
import paddleFaturaDuplicata
import paddleNotaDebito
import paddleMinutaCalculo
import paddleCustoFrete
import paddleFaturaFrete
import tesseractNotaDebito
import tesseractFaturaFrete
import tesseractNFS
import tesseractReciboLocacao
import tesseractCustoFrete
import tesseractFaturaDuplicata
import tesseractMinutaCalculo
import paddleDetalhamentoNFS
import paddleCotacao

#from PIL import Image
from fuzzywuzzy import fuzz
#from fuzzywuzzy import process


def runPaddleOCR(img_path, docType=None):
    print('\nExecutando Paddle/tesseract lambda Pipeline \n')
    #docType = None
    docTypeList = list(docTypeMap.keys())
    #table_engine = PPStructure(show_log=True, lang='en')

    ocr = PaddleOCR(use_angle_cls=True, lang='en')

    result = ocr.ocr(img_path, cls=True)

    #img = cv2.imread(img_path)
    #result = table_engine(img)

    ocrModules = {
                'NFS': lambda : paddleNFS.runPaddleOCR(img_path),
                'mapa_faturamento': lambda : paddleNFS.runPaddleOCR(img_path, 'en'),
                'recibo_locacao': lambda : paddleReciboLocacao.runPaddleOCR(img_path),
                'fatura_duplicata': lambda : paddleFaturaDuplicata.runPaddleOCR(img_path),
                'nota_debito': lambda : paddleNotaDebito.runPaddleOCR(img_path),
                'minuta_calculo': lambda : paddleMinutaCalculo.runPaddleOCR(img_path),
                'custo_frete': lambda : paddleCustoFrete.runPaddleOCR(img_path)
                }

    ocrModules2 = {
                'NFS': [lambda : paddleNFS.runPaddleOCR(img_path), 
                        lambda : paddleNFS.runPaddleOCR(img_path, 'en'),
                        lambda : paddleNFS.runPaddleOCR(img_path, 'latin'),
                        lambda : tesseractNFS.runTesseractOCR(img_path)],
                'mapa_faturamento': [lambda : paddleNFS.runPaddleOCR(img_path, 'en'),
                                    lambda : paddleNFS.runPaddleOCR(img_path),
                                    lambda : paddleNFS.runPaddleOCR(img_path, 'latin'),
                                    lambda : tesseractNFS.runTesseractOCR(img_path)],
                'recibo_locacao': [lambda : paddleReciboLocacao.runPaddleOCR(img_path),
                                    lambda : paddleReciboLocacao.runPaddleOCR(img_path, 'en'),
                                    lambda : paddleReciboLocacao.runPaddleOCR(img_path, 'latin'),
                                    lambda : tesseractReciboLocacao.runTesseractOCR(img_path)],
                'fatura_duplicata': [lambda : paddleFaturaDuplicata.runPaddleOCR(img_path),
                                    lambda : paddleFaturaDuplicata.runPaddleOCR(img_path, 'en'),
                                    lambda : paddleFaturaDuplicata.runPaddleOCR(img_path, 'latin'),
                                    lambda : tesseractFaturaDuplicata.runTesseractOCR(img_path)],
                'nota_debito': [lambda : paddleNotaDebito.runPaddleOCR(img_path),
                                lambda : paddleNotaDebito.runPaddleOCR(img_path, 'en'),
                                lambda : paddleNotaDebito.runPaddleOCR(img_path, 'latin'),
                                lambda : tesseractNotaDebito.runTesseractOCR(img_path)],
                'minuta_calculo': [lambda : paddleMinutaCalculo.runPaddleOCR(img_path),
                                    lambda : paddleMinutaCalculo.runPaddleOCR(img_path, 'en'),
                                    lambda : paddleMinutaCalculo.runPaddleOCR(img_path, 'latin'),
                                    lambda : tesseractMinutaCalculo.runTesseractOCR(img_path)],
                'custo_frete': [lambda : paddleCustoFrete.runPaddleOCR(img_path, 'en'),
                                lambda : paddleCustoFrete.runPaddleOCR(img_path),
                                lambda : paddleCustoFrete.runPaddleOCR(img_path, 'latin'),
                                lambda : tesseractCustoFrete.runTesseractOCR(img_path)],
                'fatura_frete': [lambda : paddleFaturaFrete.runPaddleOCR(img_path), 
                                lambda : paddleFaturaFrete.runPaddleOCR(img_path, 'en'),
                                lambda : paddleFaturaFrete.runPaddleOCR(img_path, 'latin'),
                                lambda : tesseractFaturaFrete.runTesseractOCR(img_path)],
                'detalhamento_notafiscal': [lambda : paddleDetalhamentoNFS.runPaddleOCR(img_path, 'en'),
                                            lambda : paddleDetalhamentoNFS.runPaddleOCR(img_path),
                                            lambda : paddleDetalhamentoNFS.runPaddleOCR(img_path, 'latin'),
                                            lambda : tesseractNFS.runTesseractOCR(img_path)],
                'cotacao': [lambda : paddleCotacao.runPaddleOCR(img_path, 'en'),
                                            lambda : paddleCotacao.runPaddleOCR(img_path),
                                            lambda : paddleCotacao.runPaddleOCR(img_path, 'latin'),
                                            lambda : paddleCotacao.runTesseractOCR(img_path)]
                }

    if docType == None:
        maxLCS = 0
        maxHier = 0
        for line in result:
            for docName in docTypeList:
                if fuzz.token_set_ratio(line[1][0].lower(), docName) > 80:
                    lcsResult = lcs(line[1][0].upper(), docName.upper())
                    tempHier = docHierarchy[docTypeMap[docName]]
                    if lcsResult > maxLCS and tempHier > maxHier:
                        maxLCS = lcsResult
                        docType = docTypeMap[docName]
                        maxHier = tempHier

    print()

    if docType != None:
        jsonResult = {}
        if 'descricao' in dict_document.get(docType):
            jsonResult['descricao'] = 'None'
        if 'pesoBruto' in dict_document.get(docType):
            jsonResult['pesoBruto'] = 'None'
        flagBreak = False
        for f in ocrModules2[docType]:
            tempJsonResult = f()
            for info in dict_document[docType]:
                if info not in list(jsonResult.keys()) or jsonResult.get(info) == None:
                    if info in list(tempJsonResult.keys()):
                        jsonResult[info] = tempJsonResult[info]
                elif info == 'valor' and jsonResult.get('valor') != None:
                    tempValor = jsonResult['valor']
                    try:
                        tempValor = greater(jsonResult['valor'], tempJsonResult['valor'])
                    except:
                        pass
                    if jsonResult['valor'] != tempValor:
                        jsonResult['valor'] = tempValor
                    elif jsonResult.get('valor').find('.') == -1 and jsonResult.get('valor').find(',') == -1:
                        if tempJsonResult.get('valor') != None:
                             if tempJsonResult.get('valor').find('.') != -1 or tempJsonResult.get('valor').find(',') != -1:
                                 jsonResult['valor'] = tempJsonResult['valor']
                    elif tempJsonResult.get('valor') != None:
                        if tempJsonResult.get('valor').find('.') != -1 and tempJsonResult.get('valor').find(',') != -1:
                            if jsonResult.get('valor').find('.') == -1 or jsonResult.get('valor').find(',') == -1:
                                jsonResult['valor'] = tempJsonResult['valor']
                                flagBreak = True

            if len(jsonResult.keys()) >= len(dict_document[docType]):
                noneFlag = False
                for k in list(jsonResult.keys()):
                    if jsonResult[k] == None:
                        noneFlag == True
                if noneFlag == False and flagBreak == True:
                    break
        
        print(f'Output paddle_ocr_engine: {jsonResult} \n')
        return jsonResult

    else:
        print("\nDocumento nao identificado no paddle_ocr_engine \n")
        return {}

#print(runPaddleOCR('MapaF_AGv4.jpg'))
#print(runPaddleOCR('003.jpg'))
#runPaddleOCR('AGV_RL.jpg')
#print(runPaddleOCR('Diremadi.pdf_1.jpg'))
#runPaddleOCR('page0.jpg')
#print(runPaddleOCR('CustoFrete-FL_0.jpg'))


