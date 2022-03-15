
#Funcionamento: Se vira
#from m210 import fill_form
import traceback
#from icecream import ic

#from matplotlib.pyplot import flag
from pdf_splitter  import splitPDF
from convertPDF2JPG import convertPDF2Image
from api_client import API_Client
from dictionaries import docs_std_resolution, dict_document, dict_map, docTypeMap, docHierarchy, companies, listaCNPJ, mapLongShort, mapNameCNPJ, field_validation, manyPagesDocList, descriptionByNFSType
from ocr_engine import runPaddleOCR
from companyName import getCompanyName
from documentType import getDocType
from compareAmounts import greater
from ReadJson import printJson
from CurrencyFormat import switchValue
from Periodo import getPeriodo
import pytesseract
import numpy as np
import cv2 # OpenCV
import re
import json
import sys

from fuzzywuzzy import fuzz

#pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\Tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def getDocumentType(filename):
  img = cv2.imread(filename)
  #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

  config_tesseract = '--oem 3  --psm 11'
  texto = pytesseract.image_to_string(img, config=config_tesseract)
  texto = texto.lower()
  
  vetorResultado = re.findall(r'fatura.?duplicata|recibo de locação|nota fiscal de serviço|nota fiscal|corte na linha(?: de)?(?: baixo)?|banco|\
  nfs-e|nfs|fatura duplicata|nota fiscal eletronica de servicos e fatura|custo de frete|custo de frete|nota de debito|nota de débito|dacte|conferencia de faturas|duplicata|comprovante(?: de)? entrega', texto, flags=re.I)

  standardized_docs_list = []

  for v in vetorResultado:
    standardized_docs_list.append(docTypeMap[v])

  docPriority = 0
  doc = ''

  for d in standardized_docs_list:
    if docHierarchy[d] > docPriority:
      docPriority = docHierarchy[d]
      doc = d

  getTypeFunctions = [lambda: getDocType(filename), lambda: getDocType(filename, 'en'), 
    lambda: getDocType(filename, 'latin')]
  if doc == None or doc == '':
    for f in getTypeFunctions:
      if doc == None:
        doc = f()
      else:
        break
    
  elif doc == 'NFS':
    
    check = None 
    for f in getTypeFunctions:
      if check == None:
        check = f()
      else:
        break
    if check != doc and check != None:
      if docHierarchy[check] > docHierarchy[doc]:
        doc = check

  return doc


def isolate_field(image, x1, x2, y1, y2, coords: tuple):

  std_x, std_y = coords

  res_x = len(image[0])
  res_y = len(image)

  fator_x = std_x/res_x + 0.5
  fator_y = std_y/res_y + 0.5

  fator_x = int(fator_x)
  fator_y = int(fator_y)

  tlist = []

  for a in image:

    tlist2 = []
    for i in a:
      tlist2.append(i)
    tlist2 = tlist2[x1//fator_x:x2//fator_x]
    
    tlist.append(tlist2)

  tlist = tlist[y1//fator_y:y2//fator_y]
  image = np.array(tlist)

  return image


#Get contractor's name
def nomeFornecedor(filename, full_name=False):
  img = cv2.imread(filename)
  img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  #cv2.imwrite(filename, img)

  config_tesseract = '--oem 3  --psm 11'
  texto = pytesseract.image_to_string(img, config=config_tesseract)
  
  vetorResul = re.findall(r'MULTI RIO(?: OPERACOES)?(?: PORTUARIAS)?(?: S/A)?|MULTITERMINAIS|ICTSI(?: RIO)(?: BRASIL) TERMINAL 1 SA|DHL(?: GLOBAL)?(?: FORWARDING)?(?: \( BRAZIL\))?(?: LOGISTICS LTDA|KUEHNE(?:.)?NAGEL)?', texto, flags=re.I)
  if len(vetorResul) > 0:
    result = vetorResul[0].split(" ")
    company = result[0]
    
    if full_name == False:
      if company in list(mapLongShort.keys()):
        company = mapLongShort.get(company).split()[0]
      else:
        if company in list(mapLongShort.keys()):
          company = mapLongShort.get(company).split()
    print('NOME::::', company)
    return company.upper()

  else:
    company = getCompanyName(filename)
    if full_name == False and company != None:
      company = company.split()[0]
    print('NOME::::', company)
    return company



def getField(filename, company, field, document, params=None):

  image = cv2.imread(filename,0)
  if(field == 'nome'):
    image = cv2.blur(image, (3,3))

  if dict_map[company][document].get(field) == None:
    return ''

  x1, x2, y1, y2 = dict_map[company][document][field]

  info = isolate_field(image, x1, x2, y1, y2, docs_std_resolution[company][document])

  #if field == 'valor':
  #  cv2.imwrite('IMAGEMVALOR.jpg', info)

  #if field == 'con':
  #  cv2.imwrite('IMAGEMVALOR.jpg', info)

  #if field == 'PO':
  #  cv2.imwrite('IMAGEMVALOR.jpg', info)
  
  if params == None:
    texto = pytesseract.image_to_string(info)
  else:
    texto = pytesseract.image_to_string(info, config=params)

  if field == 'DI':
    if document == 'NFS':
      di = re.search(r'DI:? ?[0-9]+', texto)
      if di != None:
        di = re.search(r'[0-9]+', di.group())
        texto = di.group()
  elif field == 'valor':
    valor = re.search(r'(?:R$)? ?[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', texto)
    if valor == None:
      return ''
    else:
      return valor.group()

  return texto


def extract_data(filename, company, document):
  info = {}

  for field in dict_document[document]:
    info[field] = getField(filename, company, field, document, params='--oem 3  --psm 6')
    if info.get(field) != None:
      info[field] = info[field].strip()

    if field == 'nome':
      if company != None:
        if mapLongShort.get(company) != None:
          info[field] = mapLongShort[company]
      else:
        nameFuzzy = 0
        for c in companies:
          tempFuzzy = fuzz.token_set_ratio(str(info[field]).upper(), c)
          if tempFuzzy > nameFuzzy:
            info[field] = c
            nameFuzzy = tempFuzzy
    
    elif field == 'descricao' and document == 'NFS':
      if descriptionByNFSType.get(company) != None:
        desc = info.get(field)
        if desc != None:
          desc = descriptionByNFSType[company](desc)
          info[field] = desc

    #PO - NUMERIC    
    elif field == 'DI':
      s = re.match(r'[0-9]+', info[field])
      if s == None:
        info[field] = ''

    elif field == 'CNPJ':
      cnpj = re.search(r'[0-9][0-9]\.[0-9][0-9][0-9]\.[0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]-[0-9][0-9]', info[field])
      if cnpj != None:
        info[field] = cnpj.group()
      else:
        for num in listaCNPJ:
          if fuzz.token_set_ratio(info[field], num) > 75:
              info[field] = num
              break
          else:
              cnpj = re.findall(r'[0-9]+', num)
              stringCNPJ = ''
              for s in cnpj:
                  stringCNPJ += s
              if fuzz.token_set_ratio(info[field], stringCNPJ) > 75:
                  info[field] = num
                  break

    elif field == 'vencimento':
      vencimento = re.search(r'[0-9]+/[0-9]+(?:/[0-9]+)?', info[field])
      if vencimento != None:
        info[field] = vencimento.group()

    elif field == 'valor':
      valor = re.search(r'[0-9]+\.?[0-9]+(?:,[0-9][0-9])?', info[field])
      if valor == None:
        info[field] = valor

  return info


def run_ocr(filename, document, company):
  if company != None:
    #api_json = API_Client('https://wise.klink.ai/api/admin/list/planilhavalidacao/AGVLOGISTICA/494112').result
    centroCusto = None
    contaContabil = None
    """ for c in api_json:
      if c['razaoSocial'].upper() == company.upper():
        centroCusto = c['centroCusto']
        contaContabil = c['contaContabil']
        break """
    dados = extract_data(filename, company, document)
    if(centroCusto != None):
      dados['centro_custo'] = centroCusto

    if(contaContabil != None):
      dados['conta_contabil'] = contaContabil

    if dados.get('valor') != None:
      if dados.get('desconto') != None:
        dados['valorBruto'] = dados['valor'] - dados['desconto']
      else:
        dados['valorBruto'] = dados['valor']

    if(dados.get('descricao') != None):
      dados['descricao'] = re.sub('\n', ' ', dados['descricao'])

    dados['tipoDocumento'] = document

    res = dados

  else:
    res = extract_data(filename, None, document)

  #CNPJ
  if res.get('CNPJ') != None:
    m = mapNameCNPJ.get(res.get('CNPJ'))
    if m != res.get('nome') and m != None:
      res['nome'] = m

  return res


def writeOutputFile(jsonString, outputFile):
  outputString = json.dumps(jsonString)
  with open(outputFile, 'w') as f:
      f.write(outputString)
  return outputFile



def insert_data(filename, doctype, data: dict):
  #data['tipo_documento'] = doctype
  with open('registros.txt', 'a') as f:
    string = json.dumps(data)
    f.write(f'{filename}|{string}\n')


def runPipeline(file, docType, companyName):
  print('\nExecutando runPipeline \n')
  if docType in list(dict_document.keys()):
    print('\nConvertendo PDF para Imagem \n')
    try:
      imgFile = convertPDF2Image(file, docs_std_resolution[companyName][docType])
    except:
      imgFile = convertPDF2Image(file)

    print('\nPDF convertido para imagem com sucesso \n')

    if companyName in list(docs_std_resolution.keys()):
      try:
        print(f'Iniciando RUN_OCR em {imgFile} \n')
        out = run_ocr(imgFile, docType, companyName)
        print(f'RUN_OCR em {imgFile} finalizado \n')
        if out.get('tipoDocumento') == None:
          out['tipoDocumento'] = docType
        missedData = []

        print('Verificando informacoes extraidas')
        for info in dict_document[docType]:
          if (info in list(out.keys()) or out.get(info) != None) and field_validation.get(info) != None:
            temp = re.search(field_validation[info], str(out[info]))
            if temp != None:
              out[info] = temp.group()
            else:
              missedData.append(info)
          if info not in list(out.keys()) or out.get(info) == '':
            if info not in missedData:
              missedData.append(info)

        print(f'Dados não obtidos ou não validados: {missedData} \n')
        if len(missedData) > 0:
          print('Iniciando Paddle Pipeline \n')
          supJson = runPaddleOCR(imgFile, docType)
          #print('Paddle Json:',supJson)

        for e in missedData:
          out[e] = supJson.get(e)

        if 'valor' not in missedData and len(missedData) > 0:
          if out.get('valor') != None and supJson.get('valor') != None:
            try:
              out['valor'] = greater(out['valor'], supJson['valor'])
            except:
              pass

        insert_data(imgFile, docType, out)
        print()
      except Exception as e:
        traceback.print_exc()
        try:
          print(f'Iniciando Paddle Pipeline em {imgFile} \n')
          out = runPaddleOCR(imgFile, docType)

          #insert_data(imgFile, docType, out)
          print()
        except:
          traceback.print_exc()
          print('Unable to read file. \n')
          out = {}
          return out#, pageOutputName
      finally:
        print('Validando informações extraidas')
        for info in dict_document[docType]:
          if (info in list(out.keys()) or out.get(info) != None) and field_validation.get(info) != None:
            temp = re.search(field_validation[info], str(out[info]))
            if temp != None:
              out[info] = temp.group()
            else:
              out[info] = None
        
        if docType in ['detalhamento_notafiscal', 'minuta_calculo']:
          if out.get('dataEntrada') != None and out.get('dataSaida') != None:
            p = getPeriodo(out.get('dataEntrada'), out.get('dataSaida'))
            if p != None:
              out['periodo'] = p
        print('SAIDA PIPELINE:', out, '\n')
        return out#, pageOutputName

    else:
      print(f'Nome do fornecedor não identificado em {imgFile} \n')
      infoList = dict_document.get(str(docType))
      if companyName == None or 'nome' not in infoList:
        if docType == 'custo_frete':
          try:
            print(f'Iniciando RUN_OCR em {imgFile} \n')
            out = run_ocr(imgFile, docType, companyName)
            print(f'RUN_OCR em {imgFile} finalizado \n')

            if out.get('tipoDocumento') == None:
              out['tipoDocumento'] = docType
            missedData = []
            print('Verificando informacoes extraidas')
            for info in dict_document[docType]:
              if info in list(out.keys()) or out.get(info) != None:
                temp = re.search(field_validation[info], out[info])
                if temp != None:
                  out[info] = temp.group()
                else:
                  missedData.append(info)
              if info not in list(out.keys()) or out.get(info) == '':
                if info not in missedData:
                  missedData.append(info)

            print(f'Dados não obtidos ou não validados: {missedData} \n')
            if len(missedData) > 0:
              print('Iniciando Paddle Pipeline \n')
              supJson = runPaddleOCR(imgFile, docType)
            #print('Paddle Json:', file)
            for e in missedData:
              out[e] = supJson.get(e)

            if 'valor' not in missedData and len(missedData) > 0:
              if out.get('valor') != None and supJson.get('valor') != None:
                try:
                  out['valor'] = greater(out['valor'], supJson['valor'])
                except:
                  pass

            #insert_data(imgFile, docType, out)
            print()
          except Exception as e:
            traceback.print_exc()
            try:
              print(f'Iniciando Paddle Pipeline em {imgFile} \n')
              out = runPaddleOCR(imgFile, docType)
              if out.get('tipoDocumento') == None:
                out['tipoDocumento'] = docType

              #insert_data(imgFile, docType, out)
              print()
            except:
              traceback.print_exc()
              print('Unable to read file. \n')
              return {}#, pageOutputName
          finally:
            print('Validando informações extraidas')
            for info in dict_document[docType]:
              if (info in list(out.keys()) or out.get(info) != None) and field_validation.get(info) != None:
                temp = re.search(field_validation[info], str(out[info]))
                if temp != None:
                  out[info] = temp.group()
                else:
                  out[info] = None

            if docType in ['detalhamento_notafiscal', 'minuta_calculo']:
              if out.get('dataEntrada') != None and out.get('dataSaida') != None:
                p = getPeriodo(out.get('dataEntrada'), out.get('dataSaida'))
                if p != None:
                  out['periodo'] = p
            print('SAIDA PIPELINE:', out,'\n')
            return out#, pageOutputName
          
        else:
          print('Unable to retrieve document type in', file,'\n')

  else:
    print(file,'is not a valid document \n')





pdf_file = sys.argv[1]
outputFileName = sys.argv[2]
print(f'\nDividindo páginas do PDF {pdf_file} \n')
splitted_files = splitPDF(pdf_file)
print(f'Páginas a serem lidas: {splitted_files} \n')

docTypeAnchor = None
companyNameAnchor = None
flagSameDocument = False
initPage = 0
finalPage = 0
#currentOutputFile = outputFileName

print(f' Iniciando leitura do arquivo {pdf_file} \n')

result = {}
resultArray = []
for file in splitted_files:
  print(f' Convertendo pagina {file} para imagem \n')
  jpgFile = convertPDF2Image(file)

  print(f' Buscando Nome do Fornecedor \n')
  companyName = nomeFornecedor(jpgFile)
  if companyName != None and companyNameAnchor == None:
    companyNameAnchor = companyName
  else:
    companyName = companyNameAnchor

  print(f' Buscando Tipo de Documento \n')
  docType = getDocumentType(jpgFile)
  if docType != None:
    if docType != docTypeAnchor:
        docTypeAnchor = docType
    flagSameDocument = False

    try:
      if companyName == None:
        companyName = companyNameAnchor

      print(f' Executando OCR Pipeline para {file} \n')
      out = runPipeline(file, docType, companyNameAnchor)
      if out.get('tipoDocumento') == result.get('tipoDocumento') and out.get('tipoDocumento') in manyPagesDocList:
        if out.get('valor') not in [None, ''] and result.get('valor') in [None, '']:
          if len(resultArray) > 0:
            resultArray[-1]['valor'] = out['valor']
        if out.get('valor') not in [None, ''] and result.get('valor') not in [None, '']:
          try:
            result['valor'] = switchValue(result, out)
            result['valor'] = greater(result['valor'], out['valor'])
          except:
            pass
        resultArray[-1]['paginaFinal'] = finalPage

      else:
        result = out
        if len(result) > 0:
          initPage = finalPage
          result['paginaInicial'] = initPage
          result['paginaFinal'] = finalPage
          resultArray.append(result)
      #writeOutputFile(result, docOutputFile)
      #currentOutputFile = docOutputFile
      #count += 1

    except:
      traceback.print_exc()
      print('Unable to retrieve company name or document type in', file, '\n')
    finally:
      finalPage += 1
  
  else:
    flagSameDocument = True
    docType = docTypeAnchor
    companyName = companyNameAnchor
    try:
      print(f' Executando OCR Pipeline para {file} \n')
      out = runPipeline(file, docType, companyName)

      for key in list(out.keys()):
        if result.get(key) == None:
          result[key] = out[key]
        elif out.get('valor') not in [None, ''] and result.get('valor') not in [None, '']:
          try:
            result['valor'] = switchValue(result, out)
            result['valor'] = greater(result['valor'], out['valor'])
          except:
            pass

      if len(resultArray) > 0:
          for key in list(result.keys()):
              if resultArray[-1].get(key) == None:
                  resultArray[-1][key] = result[key]
          resultArray[-1]['paginaFinal'] = finalPage
      elif len(result) > 0:
          initPage = finalPage
          result['paginaInicial'] = initPage
          result['paginaFinal'] = finalPage 
          resultArray.append(result)
      #writeOutputFile(result, docOutputFile)
    except:
      traceback.print_exc()
      print('Invalid Page \n')
    #count += 1
    finally:
      finalPage += 1

ret = {
    'return': resultArray
    }

outputFileNameName = outputFileName+'.json'
generatedJson = writeOutputFile(ret, outputFileName)
print('Json Array: \n')
printJson(generatedJson)

  









