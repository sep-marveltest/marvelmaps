import pandas as pd


FILE_DATA_NL = "data/data_NL.csv"

RANDSTAD = ['Amersfoort',
            'Utrecht',
            'Hilversum',
            'Amsterdam',
            'Haarlem',
            'Leiden',
            'Den Haag',
            'Rotterdam',
            'Dordrecht']


def read_NL_data():
    return pd.read_csv(FILE_DATA_NL)


def zip_to_region(data_NL, zip_, cname):
    try:
        row = data_NL.loc[data_NL['postal code'] == int(zip_)]

        return row[cname].values[0]
    except (KeyError, ValueError, IndexError):
        return 0


def get_regional_metrics(level, cnames, client_data, data_NL):
    output = pd.DataFrame()
    reg_name = 0

    if level == 'province':
        reg_name = 'state'
        cname = 'state'

    elif level == 'county':
        reg_name = level
        cname = 'province_or_county'

    regions = [zip_to_region(data_NL, r[cnames['zip']], cname) for _, r in client_data.iterrows()]

    client_data[reg_name] = regions
    client_data = client_data[client_data[reg_name] != 0].reset_index(drop=True)
    grp = client_data.groupby(by=reg_name, dropna=True)


    output['orders'] = grp.count()[cnames['orders']]
    output['clients'] = grp.count()[cnames['clients']]
    output['revenue'] = grp.sum()[cnames['revenue']]

    if level == "province":
        output['clients_pop'] = [data_NL[data_NL['state'] == p].iloc[0]['Population province']
                                for p, _ in output.iterrows()]
        output['clients_pop'] = [output['clients'][i] * 100000 / int(output['clients_pop'][i].replace('.', '')) for i in range(output.shape[0])]

        output['rev_BBP'] = [data_NL[data_NL['state'] == p].iloc[0]['BBP province']
                            for p, _ in output.iterrows()]
        output['rev_BBP'] = [output['revenue'][i] / int(output['rev_BBP'][i]) for i in range(output.shape[0])]

    elif level == "county":
        output['randstad'] = [True if c in RANDSTAD else False for c in output.index]

    return output
