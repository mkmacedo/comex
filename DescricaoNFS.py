import re
def getCleanDescriptionType1(description):
    resArray = []
    splittedString = description.split('\n')
    for line in splittedString:
        if re.search(r'[0-9]+\.[0-9]+\.[0-9]+', line):
            resArray.append(line.strip())
    res = ''
    for r in resArray:
        res += str(r)+'\n'
    return res.strip()
