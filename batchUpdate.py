
boolean = [True, True, True, False, False, False]

values_list = []
for i in range(len(boolean)):
    string = '=VLOOKUP(D{}, Categories!A$2:C$100,2,FALSE)'.format(str(i+2))
    values_list.append(string)

#print(values_list)


range_ = 'Transactions!G2:G'

data_list = [{'values': values_list,
             'majorDimension': 'COLUMNS',
             'range': range_}]

print(data_list)

batchBody = {'data': data_list, 
             'valueInputOption': 'USER_ENTERED', 
             'includeValuesInResponse': True}
batchBody
