import requests
import json
import dash
import pandas as pd
import geopandas as gpd
import plotly.express as px
import dash_daq as daq

from dash import dash_table
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


DEBUG = True


# Change GeoPandas GeoDataFrame to GeoJSON
def gdf_to_geojson(gdf):
    gdf = gdf.to_crs(epsg=4326)
    gdf.to_file('data/geojsonfile.json', driver = 'GeoJSON')

    with open('data/geojsonfile.json') as geofile:
        data = json.load(geofile)

    return data


# Add currency symbol to strings in passed columns
def add_currency(df, columns):
    for col in columns:
        df[col] = df[col].apply(lambda x: "€" + "{:.2f}".format(float(x)))

    return df


# Generates table parameters from given dataframe
def generate_table(df_in):
    df_out = pd.DataFrame(df_in, copy=True)
    df_out = add_currency(df_out,
                         ['Gross sales', 'Net sales', 'Life Time Value'])
    table_data = df_out.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df_out.columns]

    return table_data, table_columns


# Read dummy Shopify order dataset
orders_df = pd.read_csv("data/dummy_orders.csv", low_memory=False)

# Filter out everything outside of NL
orders_df = orders_df[orders_df['Shipping Country'] == "NL"]

# Group by order name and customer email
orders_df = (orders_df.groupby(by=['Name', 'Email', 'Shipping Zip'])
                      .sum()
                      .reset_index())

# Turn Dutch postcode to just the digits:
# 1054BD --> 1054
orders_df['Shipping Zip'] = orders_df['Shipping Zip'].apply(lambda z: str(z)[:4])

# Read regional data of the Netherlands and cast zip codes to strings
nl_regional_df = pd.read_csv("data/data_NL.csv", delimiter=',', thousands='.')
nl_regional_df['postal code'] = nl_regional_df['postal code'].astype(str)
nl_regional_df

# Merge order data with regional data
pd.set_option('display.max_columns', None)
merge = orders_df.merge(
    nl_regional_df,
    left_on='Shipping Zip',
    right_on='postal code')

# Group the merged data by states and re-organise to get metrics
df_states = (merge.groupby(by=['state', 'Population province', 'BBP province'])
                  .agg({'Lineitem quantity': 'sum',
                        'Lineitem price'   : 'sum',
                        'Lineitem discount': 'sum',
                        'Tax 1 Value'      : 'sum',
                        'Name'             : 'count',
                        'Email'            : 'count'
                   })
                  .reset_index()
                  .rename(columns={'state'              : 'State',
                                   'Lineitem quantity'  : 'Products',
                                   'Lineitem price'     : 'Gross sales',
                                   'Lineitem discount'  : 'Discounts',
                                   'Tax 1 Value'        : 'Taxes',
                                   'Name'               : 'Orders',
                                   'Email'              : 'Customers',
                                   'Population province': 'State population',
                                   'BBP province'       : 'State BBP'}))

# Add net sales metrics for each state
df_states['Net sales'] = (df_states['Gross sales']
                          - df_states['Discounts']
                          - df_states['Taxes'])
df_states['Life Time Value'] = (df_states['Net sales'] / df_states['Customers'])
df_states = df_states.round(2)

# Reorder columns for beter datatable reading
df_states = df_states[[
    'State',
    'Orders',
    'Products',
    'Gross sales',
    'Net sales',
    'Life Time Value'
]]

# Group the merged data by counties and re-organise to get metrics
df_counties = (merge.groupby(by=['province_or_county'])
                    .agg({'Lineitem quantity': 'sum',
                          'Lineitem price'   : 'sum',
                          'Lineitem discount': 'sum',
                          'Tax 1 Value'      : 'sum',
                          'Name'             : 'count',
                          'Email'            : 'count'})
                    .reset_index()
                    .rename(columns={'province_or_county' : 'County',
                                     'Lineitem quantity'  : 'Products',
                                     'Lineitem price'     : 'Gross sales',
                                     'Lineitem discount'  : 'Discounts',
                                     'Tax 1 Value'        : 'Taxes',
                                     'Name'               : 'Orders',
                                     'Email'              : 'Customers'}))

# Add net sales metrics for each county
df_counties['Net sales'] = (df_counties['Gross sales']
                            - df_counties['Discounts']
                            - df_counties['Taxes'])
df_counties['Life Time Value'] = (df_counties['Net sales'] / df_counties['Customers'])
df_counties.round(2)

# Reorder columns for beter datatable reading
df_counties = df_counties[[
    'County',
    'Orders',
    'Products',
    'Gross sales',
    'Net sales',
    'Life Time Value'
]]

# Urls to use HTTP GET requests to for regional shapefiles of the Netherlands
url_states = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=1.1.0&typeName=cbsgebiedsindelingen:cbs_provincie_2022_gegeneraliseerd&outputFormat=json"
url_counties = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName=cbs_gemeente_2017_gegeneraliseerd&outputFormat=json"

# Read shape file for states of the Netherlands and convert to geojson
gdf_shapes_states = gpd.read_file(requests.get(url_states).text)
gdf_shapes_states['statnaam'].replace('Fryslân', 'Friesland', inplace=True)
geojson_states = gdf_to_geojson(gdf_shapes_states)

# Read shape file for counties of the Netherlands and convert to geojson
gdf_shapes_counties = gpd.read_file(requests.get(url_counties).text)
geojson_counties = gdf_to_geojson(gdf_shapes_counties)

# Colormap for choropleth
map_cmap = px.colors.sequential.Blues[1:]

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.Div(
                    id="description-container",
                    children=[
                        html.H1(
                            id="title",
                            children="MarvelMaps"),
                        html.P(
                            id="description",
                            children="A short introduction about the project \
                            and why it is of value to the user. Disclaimer \
                            about privacy and safety of data being used. \
                            First step, upload your data ->"
                        )
                    ]
                ),
                html.Div(
                    id="logo-container",
                    children=[
                        html.H1(
                            children="Marveltest Logo"
                        )
                    ]
                )
            ]
        ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="options-container",
                    children=[
                        html.Div(
                            id="metric-buttons",
                            children=[
                                html.Button(
                                    'Orders',
                                    id='button-orders',
                                    className='metric-button',
                                    n_clicks=0),
                                html.Button(
                                    'Gross sales',
                                    id='button-gross',
                                    className='metric-button',
                                    n_clicks=0),
                                html.Button(
                                    'Net Sales',
                                    id='button-net',
                                    className='metric-button',
                                    n_clicks=0),
                                html.Button(
                                    'Products',
                                    id='button-products',
                                    className='metric-button',
                                    n_clicks=0),
                                html.Button(
                                    'Life Time Value',
                                    id='button-ltv',
                                    className='metric-button',
                                    n_clicks=0)
                            ]
                        ),
                        daq.BooleanSwitch(
                            id='region-is-states-switch',
                            on=True),
                    ]
                ),

                html.Div(
                    id="marvelmap-container",
                    children=[
                        dcc.Graph(id='choropleth'),
                    ],
                ),
                html.Div(
                    id="marvelchart-container",
                    children=[
                        dcc.Graph(id='histogram')
                    ]
                ),
                html.Div(
                    id="data-table-container",
                    children=[
                        dash_table.DataTable(
                            id='data-table',
                            sort_action="native",
                            fixed_rows={'headers': True},
                            style_table={'height': 400} ),
                    ]
                ),
                dcc.Store(id="datasets", storage_type='session')
            ]
        )
    ]
)


@app.callback(
    [
        Output('choropleth', 'figure'),
        Output('histogram', 'figure'),
        Output('data-table', 'data'),
        Output('data-table', 'columns')
    ],
    [
        Input('region-is-states-switch', 'on'),
        Input('button-orders', 'n_clicks'),
        Input('button-gross', 'n_clicks'),
        Input('button-net', 'n_clicks'),
        Input('button-products', 'n_clicks'),
        Input('button-ltv', 'n_clicks')
    ]
)
def display_figures(region_is_states, btn1, btn2, btn3, btn4, btn5):
    # Get last pressed button id
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    # Set metric to last pressed button
    if 'button-orders' in changed_id:
        metric = 'Orders'
    elif 'button-gross' in changed_id:
        metric = 'Gross sales'
    elif 'button-net' in changed_id:
        metric = 'Net sales'
    elif 'button-products' in changed_id:
        metric = 'Products'
    elif 'button-ltv' in changed_id:
        metric = 'Life Time Value'
    elif 'region-is-states-switch' in changed_id:
        # Metric set to Orders when regions are switched
        metric = 'Orders'
    else:
        raise PreventUpdate

    if DEBUG:
        app.logger.info(f"Metric selection button pressed: {metric}")

    # Depending on the region switch determine the args for the figures
    if region_is_states:
        df_states_sorted = df_states.sort_values(by=[metric], ascending=False)

        # Arguments for figures on state level
        choropleth_args = {
            'data_frame': df_states_sorted,
            'locations': 'State',
            'geojson': geojson_states}
        histogram_args = {
            'data_frame': df_states_sorted,
            'x': 'State'
        }
        table_data, table_columns = generate_table(df_states_sorted)
    else:
        df_counties_sorted = df_counties.sort_values(by=[metric], ascending=False)

        # Arguments for figures on county level
        choropleth_args = {
            'data_frame': df_counties_sorted,
            'locations': 'County',
            'geojson': geojson_counties}
        histogram_args = {
            'data_frame': df_counties_sorted[:10],
            'x': 'County'
        }
        table_data, table_columns = generate_table(df_counties_sorted)

    # Create choropleth using args set by app options
    map = px.choropleth_mapbox(**choropleth_args,
                               color=metric,
                               featureidkey = 'properties.statnaam',
                               mapbox_style="carto-positron",
                               color_continuous_scale=map_cmap,
                               center=dict(lon=5.2913, lat=52.1326),
                               zoom=5.5)
    map = map.update_layout(margin={'l': 40, 'b': 40,'t': 10, 'r': 0},
                            hovermode='closest')

    # Create histogram using metric and region
    his = px.histogram(**histogram_args, y=metric)
    his = his.update_layout(yaxis_title=metric)

    return map, his, table_data, table_columns


if __name__ == '__main__':
    app.run_server(debug=DEBUG, host="0.0.0.0", port=8080)
