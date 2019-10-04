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

    #
    # with open('trans
    # Write to spreadsheet1actions.pickle', 'wb') as trans:
    #     pickle.dump(data, trans)
