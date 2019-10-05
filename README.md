# Transaction Classification - Google Spreadsheet API

### Prerequisites

- Google OAuth() authentication
- Google spreadsheet ID with column for transaction description, account_name and transaction amount (defined as "read_range")
- Google spreadsheet ID with column as "write_range" for predictions.

![1570246494775](./img.png)



### Current State

Algorithm uses previous classifications to classify new transactions inputted into spreadsheet.

Currently utilises ridge regression on text and numeric features to classify new transactions into one of 43 personally defined categories at an accuracy of approximately 90%.



### Use 

Would require some adjustment for personal spreadsheets of other users but once configured running `main.py` daily or weekly will automatically classify new transactions.

My personal spreadsheet is automatically updated with new transactions daily using TillerHQ service and then my script is run subsequent to that to automatically classify new transactions.



### main.py calls other scripts

```python
from category_classification import create_model, prepare_data
from get_data import write_data, get_data
from sklearn.preprocessing import LabelBinarizer


def construct_json(series, range_):
    data_json = {'values': [series.tolist()],
                 'majorDimension': 'COLUMNS',
                 'range': range_}
    return data_json


def main(sheet_name, read_range, write_range, write_bool):
    data = get_data(ssid=sheet_name, range=read_range)
    # Prepare data
    features, target, empty_bool = prepare_data(data.copy())
    x_train = features[~empty_bool]
    x_test = features[empty_bool]

    # Encode target variable
    one_hot_encoder = LabelBinarizer()
    y_train = one_hot_encoder.fit_transform(target[~empty_bool])

    # Create statistical model
    model = create_model(x_train,
                         y_train,
                         model_type='ridge',
                         alpha_=0.5)

    # Predict and decode target
    preds = model.predict(x_test)
    preds = one_hot_encoder.inverse_transform(preds)

    # Update categories series and convert to json
    target.loc[target == ''] = preds
    updated_categories_json = construct_json(target, write_range)

    # Write to spreadsheet
    if write_bool:
        write_data(ssid=sheet_name,
                   range_=write_range,
                   value_input_option="RAW",
                   value_range_body=updated_categories_json)


if __name__ == '__main__':
    # The ID and range of spreadsheet.
    master_sheet = ''  # FILL with personal sheet ID

    # Set read/write range
    read = ''  # Fill with personal read range
    write = ''  # Fill with personal write range

    main(sheet_name=master_sheet,
         read_range=read,
         write_range=write,
         write_bool=True)
```



### get_data.py

```python
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
from re import sub
from pprint import pprint


def auth():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_data(ssid, range):
    creds = auth()
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=ssid,
                                range=range).execute()
    values = result.get('values', [])
    data = pd.DataFrame.from_records(values[1:])
    data.columns = [x.lower() for x in values[0]]

    convert_currency = lambda x: (float(sub(r'[^\d.]', '', x)))
    data.amount = data.amount.apply(convert_currency)
    data.rename({'account #': 'account'}, axis=1, inplace=True)
    data.drop(['amount processed', 'group', 'class', 'hide'], axis=1, inplace=True)
    return data


def write_data(ssid, range_, value_input_option, value_range_body):
    creds = auth()
    service = build('sheets', 'v4', credentials=creds)
    request = service.spreadsheets().values().update(spreadsheetId=ssid,
                                                     range=range_,
                                                     valueInputOption=value_input_option,
                                                     body=value_range_body)
    response = request.execute()
    pprint(response)


def request_body(ranges, rows):
    data_list = []

    for range_ in ranges:
        values_list = []
        if 'F' not in range_:
            if 'G' in range_:
                col = 2
            elif 'H' in range_:
                col = 3
            else:
                col = 5
            for i in range(rows):
                formula = "=VLOOKUP(D{}, Categories!A$2:E$100, {}, FALSE)".format(str(i+2), col)
                values_list.append([formula])
            data_list.append({"values": values_list,
                               "majorDimension": "ROWS",
                               "range": range_})
        else:
            for i in range(rows):
                formula = '=IF(L{}="Lily and Xavier", E{}/2, E{})'.format(str(i+2), str(i+2), str(i+2))
                # formula = "appro"
                values_list.append([formula])
            data_list.append({"values": values_list,
                               "majorDimension": "ROWS",
                               "range": range_})

    return {"data": data_list,
            "valueInputOption": "USER_ENTERED",
            "includeValuesInResponse": True}


# def update_batch(ssid, body):


if __name__ == '__main__':

    # If modifying these scopes, delete the file token.pickle.
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of spreadsheet.
    master_sheet = '' # FILL
    practice_sheet = '' # FILL
    copy_master_sheet = '' # FILL
    read_range = 'Transactions!C1:K'
    write_range = 'Transactions!D2:D'

    # PULL DATA
    # data = get_data(copy_master_sheet, read_range)
    # pprint(data.head())

    ranges = ["Transactions!F2:F4", "Transactions!G2:G4", "Transactions!H2:H4", "Transactions!I2:I4"]
    body = request_body(ranges, 3)
    pprint(body)

    creds = auth()
    service = build('sheets', 'v4', credentials=creds)

    request = service.spreadsheets().values().batchUpdate(spreadsheetId=copy_master_sheet, body=body)
    response = request.execute()

    pprint(response)
    pprint(body)
```



### category_classification.py

```python
import pandas as pd
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, Ridge


def preprocess_desc(string):
    if ' - Visa Purchase - ' in string:
        string = re.match(r'.+(?= - Visa Purchase - )', string).group()

    elif string.startswith('Visa-') or string.startswith('VISA-'):
        string = string[5:]
        temp = re.match(r'.+(?= (\w+|\w+.+\w+)#)', string)
        if not temp == None:
            string = temp.group()

    if 'Internal Transfer' in string:
        string = 'internal_transfer'

    if 'rent X 2w' in string:
        string = 'rent_x'

    if string.startswith('uber'):
        if 'trip' or 'Trip' in string:
            string = 'uber_trip'

    else:
        pass
    string = re.sub(r' *[Pp]aypal \*', '', string)
    string = re.sub(r'[xX]?[xX]\d+', '', string)
    string = string.replace('Receipt', '')
    string = re.sub(r'( A[Uu]\W)|( A[uU]$)', ' ', string)
    string = re.sub(r'\d*\w*(\d+|\w+)\d+\w+', '', string)
    string = re.sub(r'(\d-)?\d+/\d+(/\d{2})?', 'DATEXX', string)
    string = re.sub(r'-', ' ', string)
    string = re.sub(r'[,]', '', string)
    string = re.sub(r'google\*', 'google ', string)
    string = re.sub(r'microsoft\*', 'microsoft ', string)
    string = re.sub(r'( x )|( x$)', '', string)
    string = re.sub(r'   *', ' ', string)
    string = re.sub(r'(\.)|(\')', '', string)
    string = re.sub(r'[\*/]', '', string)
    string = re.sub(r' Value Date:?', '', string)
    string = re.sub(r'Ac ', '', string)
    string = re.sub(r' to ', ' ', string)
    string = re.sub(r'([Pp][Tt][Yy])|([Ll][Tt][Dd])', '', string)
    string = re.sub(r'[Tt]he ', ' ', string)
    string = string.strip()
    string = re.sub(r'   *', ' ', string)
    string = string.lower()

    return string


def vectorize_description(series):
    # process -> vectorize -> return pd.DataFrame
    processed_description = series.apply(preprocess_desc)
    tfidf_matrix = TfidfVectorizer().fit_transform(processed_description)
    vector_df = pd.DataFrame(tfidf_matrix.toarray())

    return vector_df


def prepare_data(data):
    # Extract features from data
    features = vectorize_description(data.description)
    features['account_factor'] = data.account.factorize()[0]
    features['amount'] = data.amount
    tfidf_width = features.shape[1]

    # Extract target from data
    target = data.category

    # Split data
    empty_bool = data.category == ''
    x_train = features[~empty_bool]
    x_test = features[empty_bool]

    return features, target, empty_bool


def create_model(features_, target_, model_type, alpha_=None):
    if model_type == 'lr':
        model = LinearRegression().fit(features_, target_)
    elif model_type == 'ridge':
        model = Ridge(alpha=alpha_).fit(features_, target_)
    else:
        raise ValueError("model_type must be valid: ['lr', 'ridge']")

    return model


if __name__ == '__main__':
    with open('transactions.pickle', 'rb') as trans:
        data = pickle.load(trans)
    print(data.columns)
    features = vectorize_description(data, 'description')
    target = encode_column(data['category'])
    print(len(features))
    not_empty = features[data['category'] != '']
    print(len(not_empty))
```

