import utils
import pandas as pd
import requests as r
import geopandas as gpd
import base64
import io

from dash import html


# Adds missing province/state rows to dataframe
def add_missing_provinces(df, states):
    all_states = set([f['properties']['statnaam'] for f in states['features']])
    missing_states = list(all_states - set(df['state']))
    missing_rows_states = pd.DataFrame([[0, 0, 0, 0, 0, 0, 0, 0]] * len(missing_states),
                        index=missing_states,
                        columns=['orders', 'clients', 'revenue', 'LTV', 'AOV', 'clients_pop', 'rev_BBP'])
    missing_rows_states.index.name = 'state'

    df = df.append(missing_rows_states.reset_index()).reset_index(drop=True)

    return df


# Adds missing county/gemeente rows to dataframe
def add_missing_counties(df, counties):
    all_counties = set([f['properties']['statnaam'] for f in counties['features']])
    missing_counties = list(all_counties - set(df['county']))
    missing_rows_counties = pd.DataFrame([[0, 0, 0, 0]] * len(missing_counties),
                        index=missing_counties,
                        columns=['orders', 'clients', 'revenue', 'LTV'])
    missing_rows_counties.index.name = 'county'

    df = df.append(missing_rows_counties.reset_index()).reset_index(drop=True)

    return df


def get_province_data(df, states, CONFIG):
    df = get_regional_metrics('province', CONFIG['cnames'], df, utils.read_NL_data()).reset_index()
    df = add_missing_provinces(df, states)

    return df


def get_county_data(df, counties, CONFIG):
    df = get_regional_metrics('county', CONFIG['cnames'], df, utils.read_NL_data()).reset_index()
    df = add_missing_counties(df, counties)

    return df


def get_province_shapes(url_states):
    states = gpd.read_file(r.get(url_states).text)
    states['statnaam'].replace('Fryslân', 'Friesland', inplace=True)
    states = utils.change_crs(states)

    return states


def get_county_shapes(url_counties):
    counties = gpd.read_file(r.get(url_counties).text)
    counties = utils.change_crs(counties)

    return counties


def get_regional_metrics(level, cnames, client_data, data_NL):
    output = pd.DataFrame()
    reg_name = 0

    if level == 'province':
        reg_name = 'state'
        cname = 'state'

    elif level == 'county':
        reg_name = level
        cname = 'province_or_county'

    regions = [utils.zip_to_region(data_NL, r[cnames['zip']], cname) for _, r in client_data.iterrows()]
    client_data[reg_name] = regions
    client_data = client_data[client_data[reg_name] != 0].reset_index(drop=True)
    client_data = client_data[client_data['Billing Country'] == 'NL'].reset_index(drop=True)

    sep = utils.find_separator(client_data['Total'])

    if sep == ',':
        client_data['Total'] = client_data['Total'].apply(lambda x: float(str(x).replace(".", "").replace(",", ".")))

    output = calculate_metrics(client_data, output, data_NL, reg_name, cnames, level)

    return output


def calculate_metrics_province(output, data_NL):
    output['clients_pop'] = [data_NL[data_NL['state'] == p].iloc[0]['Population province']
                            for p, _ in output.iterrows()]
    output['clients_pop'] = [output['clients'][i] * 100000 / int(output['clients_pop'][i].replace('.', '')) for i in range(output.shape[0])]
    output['rev_BBP'] = [data_NL[data_NL['state'] == p].iloc[0]['BBP province']
                        for p, _ in output.iterrows()]
    output['rev_BBP'] = [output['revenue'][i] / int(output['rev_BBP'][i]) for i in range(output.shape[0])]\

    return output


def calculate_metrics(client_data, output, data_NL, reg_name, cnames, level):
    grp = client_data.groupby(by=reg_name, dropna=True)

    output['orders'] = grp.count()[cnames['orders']].astype(float)
    output['clients'] = grp.count()[cnames['clients']].astype(float)
    output['revenue'] = grp.sum()[cnames['revenue']]
    output['LTV'] = (output['revenue'] / output['clients']).round(decimals=2)
    output['AOV'] = (output['revenue'] / output['orders']).round(decimals=2)

    if level == "province":
        output = calculate_metrics_province(output, data_NL)

    return output


def parse_contents(contents, filename):
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            return pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            return pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
