def greater(rCurrentValue, rNewValue):
    r = rCurrentValue
    splitCurrentValue = rCurrentValue.split('.')
    splitNewValue = rNewValue.split('.')
    currentValue = ''
    newValue = ''
    for cSlice in splitCurrentValue:
        currentValue += cSlice
    comma = currentValue.find(',')
    if comma != -1:
        currentValue = currentValue[:comma]+'.'+currentValue[comma+1:]
    for nSlice in splitNewValue:
        newValue += nSlice
    comma = newValue.find(',')
    if comma != -1:
        newValue = newValue[:comma]+'.'+newValue[comma+1:]
    if eval(newValue) > eval(currentValue):
        r = rNewValue
    return r