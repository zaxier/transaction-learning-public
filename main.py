from category_classification import create_model, prepare_data
from get_data import write_data, get_data
from sklearn.preprocessing import LabelBinarizer


def construct_json(series, range_):
    data_json = {'values': [series.tolist()],
                 'majorDimension': 'COLUMNS',
                 'range': range_}
    return data_json


def main(sheet_name, write_bool):
    data = get_data(ssid=copy_master_sheet, range=read)
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
    master_sheet = '' # FILL with personal sheet ID
    copy_master_sheet = '' # FILL with personal sheet ID

    # Set read/write range
    read = '' # Fill with personal read range
    write_range = '' # Fill with personal write range

    main(copy_master_sheet, True)

