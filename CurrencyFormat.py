def switchValue(jsonResult, tempJsonResult):

    if jsonResult.get('valor').find('.') == -1 and jsonResult.get('valor').find(',') == -1:
        if tempJsonResult.get('valor') != None:
                if tempJsonResult.get('valor').find('.') != -1 or tempJsonResult.get('valor').find(',') != -1:
                    jsonResult['valor'] = tempJsonResult['valor']

    elif tempJsonResult.get('valor').find('.') != -1 and tempJsonResult.get('valor').find(',') != -1:
        if jsonResult.get('valor').find('.') == -1 or jsonResult.get('valor').find(',') == -1:
            jsonResult['valor'] = tempJsonResult['valor']
    return jsonResult['valor']