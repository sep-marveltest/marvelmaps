import plotly.express as px
from app import CONFIG
import data
import utils
import json
import numpy as np
import pandas as pd


# Function to generate plotly express choropleth
# Takes enriched data, list of locations, geojson and metric to plot
def choropleth(df, locations, geojson, metric):
    fig = px.choropleth_mapbox(df,
                               locations=locations,
                               color=metric,
                               geojson=geojson,
                               featureidkey = 'properties.statnaam',
                               mapbox_style="carto-positron",
                               color_continuous_scale=px.colors.sequential.Blues[1:],
                               center=dict(lon=5.2913, lat=52.1326),
                               zoom=6,
                               opacity=1)
    fig = fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig


# Generates a histogram from given data and selected metric
def generate_histogram(df, metric):
    if 'state' in df.columns:
        return px.histogram(df, x='state', y=metric)
    else:
        return px.histogram(df, x='county', y=metric)


# Takes uploaded contents and generates enriched data set
def enrich_data(list_of_contents, list_of_names, url_states, url_counties, dummy_data):
    datasets = {}

    if dummy_data:
        datasets['Provinces'] = pd.read_csv('data/dummy.csv')
        datasets['Counties'] = pd.read_csv('data/dummy.csv')
    else:
        datasets['Provinces'] = data.parse_contents(list_of_contents[0], list_of_names[0])
        datasets['Counties'] = data.parse_contents(list_of_contents[0], list_of_names[0])

    datasets['Provinces'][CONFIG['cnames']['zip']] = datasets['Provinces'][CONFIG['cnames']['zip']].apply(lambda z: str(z)[:4])
    states = data.get_province_shapes(url_states)
    datasets['Provinces'] = data.get_province_data(datasets['Provinces'], states, CONFIG)
    datasets['Provinces'] = datasets['Provinces'].astype({'orders': 'float64',
                                                          'clients': 'float64',
                                                          'revenue': 'float64',
                                                          'clients_pop': 'float64',
                                                          'rev_BBP': 'float64',
                                                          'AOV': 'float64',
                                                          'LTV': 'float64'})


    datasets['Counties'][CONFIG['cnames']['zip']] = datasets['Counties'][CONFIG['cnames']['zip']].apply(lambda z: str(z)[:4])
    counties = data.get_county_shapes(url_counties)
    datasets['Counties'] = data.get_county_data(datasets['Counties'], counties, CONFIG)
    datasets['Counties'] = datasets['Counties'].astype({'orders': 'float64',
                                                        'clients': 'float64',
                                                        'revenue': 'float64',
                                                        'AOV': 'float64',
                                                        'LTV': 'float64'})

    prov = [{k: v for k, v in x.items() if pd.notnull(v)} for x in datasets['Provinces'].to_dict('r')]
    cnty = [{k: v for k, v in x.items() if pd.notnull(v)} for x in datasets['Counties'].to_dict('r')]

    return json.dumps({'Provinces': prov, 'Counties': cnty})


# Generates a table parameters from given dataframe
def generate_table(df):
    df = utils.add_currency(df, ['revenue', 'LTV', 'AOV'])
    table_data = df.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df.columns]

    return table_data, table_columns


# Generates either province or county level choropleth map from passed dataframe
def generate_map(df, metric, region, url_states, url_counties):
    if region == 'Provinces':
        states = data.get_province_shapes(url_states)
        mmap = choropleth(df, 'state', states, metric)
    else:
        counties = data.get_county_shapes(url_counties)
        mmap = choropleth(df, 'county', counties, metric)

    return mmap
