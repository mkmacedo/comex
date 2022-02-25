from typing import Container

#from icecream import ic 

dias = 28

def getNumPeriodos(dias):
    l = lambda: 1 if dias % 7 > 0 else 0
    numPeriodos = dias // 7 + l()
    return numPeriodos

variaveisPeriodoC20 = {}
variaveisPeriodoC40 = {}

valoresPorPeriodo20 = [{'percent': 0.0041, 'min': 1611.22},
                    {'percent': 0.0076, 'min': 1384.42},
                    {'percent': 0.0140, 'min': 1522.87},
                    {'percent': 0.0180, 'min': 1675.16}]

valoresPorPeriodo40 = [{'percent': 0.0041, 'min': 1741.44},
                    {'percent': 0.0076, 'min': 1527.68},
                    {'percent': 0.0140, 'min': 1680.45},
                    {'percent': 0.0180, 'min': 1848.48}]

for i in range(len(valoresPorPeriodo20)):
    variaveisPeriodoC20[i + 1] = valoresPorPeriodo20[i]
       
for i in range(len(valoresPorPeriodo40)):
    variaveisPeriodoC40[i + 1] = valoresPorPeriodo40[i]
        


def calculo(cif, **kwargs):
    container = kwargs.get("container")
    dias = kwargs.get("dias")
    numPeriodos = getNumPeriodos(dias)
    quantContainer = kwargs.get("quantContainer")
    variaveisPeriodo = {}
    variaveisPeriodo['20'] = kwargs.get("variaveisPeriodoC20")
    variaveisPeriodo['40'] = kwargs.get("variaveisPeriodoC40")
    
    formula = lambda x, y, z: x*y if(x*y/quantContainer > z ) else z*quantContainer

    res = 0
    for i in range(numPeriodos):
        if i + 1 <= 4:
            #res += formula(cif, variaveisPeriodo[container][i + 1]['percent'], variaveisPeriodo[container][i + 1]['min'])
            yield formula(cif, variaveisPeriodo[container][i + 1]['percent'], variaveisPeriodo[container][i + 1]['min'])
        else:
            #res += formula(cif, variaveisPeriodo[container][4]['percent'], variaveisPeriodo[container][4]['min'])
            yield formula(cif, variaveisPeriodo[container][4]['percent'], variaveisPeriodo[container][4]['min'])

    return res

for r in (calculo(1689043.88, container='40', dias=dias, quantContainer=1, variaveisPeriodoC20=variaveisPeriodoC20, variaveisPeriodoC40=variaveisPeriodoC40)):
    print(r)
          
