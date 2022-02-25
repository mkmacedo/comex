from datetime import datetime
import traceback
import re

def getDias(dataEntrada, dataSaida):
    try:
        d1, m1, y1 = [int(x) for x in dataEntrada.split('/')]
        d2, m2, y2 = [int(x) for x in dataSaida.split('/')]

        date1 = datetime(y1, m1, d1)
        date2 = datetime(y2, m2, d2)


        dias = str(date2 - date1)
        d = re.search('[0-9]+', dias)
        if d != None:
            dias = eval(d.group())

        return dias
    except:
        print('Invalid datetime input')
        traceback.print_exc()
        return None

def getPeriodo(dataEntrada, dataSaida):
    try:
        if dataEntrada.find('/') != -1 or dataSaida.find('/') != -1:
            d1, m1, y1 = [int(x) for x in dataEntrada.split('/')]
            d2, m2, y2 = [int(x) for x in dataSaida.split('/')]
        elif dataEntrada.find('-') != -1 or dataSaida.find('-') != -1:
            d1, m1, y1 = [int(x) for x in dataEntrada.split('-')]
            d2, m2, y2 = [int(x) for x in dataSaida.split('-')]

        date1 = datetime(y1, m1, d1)
        date2 = datetime(y2, m2, d2)


        dias = str(date2 - date1)
        d = re.search('[0-9]+', dias)
        if d != None:
            dias = eval(d.group())

        l = lambda: 1 if dias % 7 > 0 else 0
        numPeriodos = dias // 7 + l()

        return numPeriodos
    except:
        print('Invalid datetime input')
        traceback.print_exc()
        return None

#17/08/2021 19/08/2021
print(getPeriodo('05-10-2021', '08-10-2021'))