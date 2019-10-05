# Transaction Classification - Google Spreadsheet API

#### Prerequisites

- Google OAuth() authentication
- Google spreadsheet ID with column for transaction description, account_name and transaction amount (defined as "read_range")
- Google spreadsheet ID with column as "write_range" for predictions.

![1570246494775](./1570246494775.png)



#### Current State

Algorithm uses previous classifications to classify new transactions inputted into spreadsheet.

Currently utilises ridge regression on text and numeric features to classify new transactions into one of 43 personally defined categories at an accuracy of approximately 90%.



#### Use 

Would require some adjustment for personal spreadsheets of other users but once configured running `main.py` daily or weekly will automatically classify new transactions.

My personal spreadsheet is automatically updated with new transactions daily using TillerHQ service and then my script is run subsequent to that to automatically classify new transactions.



