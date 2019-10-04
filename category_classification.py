import pandas as pd
import pickle
import re
from get_data import get_data
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
    #lister = string.split(' ')
    #lister = list(set(lister[:3]))

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
