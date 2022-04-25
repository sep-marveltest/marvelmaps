import utils
import pandas as pd
import json
import requests as r
import geopandas as gpd
import base64
import io

from dash import html


def get_data(df, counties, states, CONFIG):
    prov_df = utils.get_regional_metrics('province', CONFIG['cnames'], df, utils.read_NL_data()).reset_index()
    cnty_df = utils.get_regional_metrics('county', CONFIG['cnames'], df, utils.read_NL_data()).reset_index()

    all_counties = set([f['properties']['statnaam'] for f in counties['features']])
    missing_counties = list(all_counties - set(cnty_df['county']))
    missing_rows_counties = pd.DataFrame([[0, 0, 0]] * len(missing_counties),
                        index=missing_counties,
                        columns=['orders', 'clients', 'revenue'])
    missing_rows_counties.index.name = 'county'

    all_states = set([f['properties']['statnaam'] for f in states['features']])
    missing_states = list(all_states - set(prov_df['state']))
    missing_rows_states = pd.DataFrame([[0, 0, 0, 0, 0, 0]] * len(missing_states),
                        index=missing_states,
                        columns=['orders', 'clients', 'revenue', 'clients_pop', 'rev_BBP'])
    missing_rows_states.index.name = 'state'

    prov_df = prov_df.append(missing_rows_states.reset_index()).reset_index(drop=True)
    cnty_df = cnty_df.append(missing_rows_counties.reset_index()).reset_index(drop=True)


    return prov_df, cnty_df


def change_crs(gdf):
    gdf = gdf.to_crs(epsg=4326)

    gdf.to_file('data/geojsfile.json', driver = 'GeoJSON')
    with open('data/geojsfile.json') as geofile:
        data = json.load(geofile) 

    return data


def get_shapes(url_states, url_counties):
    states = gpd.read_file(r.get(url_states).text)
    counties = gpd.read_file(r.get(url_counties).text)

    states['statnaam'].replace('Fryslân', 'Friesland', inplace=True)

    states = change_crs(states)
    counties = change_crs(counties)

    return states, counties


def parse_contents(contents, filename):
    _, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            return pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), thousands=',')
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            return pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
