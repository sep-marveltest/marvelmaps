# import plots
import requests
import dash
import dash_daq as daq
import dash_table as dt
import pandas as pd
import geopandas as gpd


from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


# Links to get (http request) geojson files
url_states = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=1.1.0&typeName=cbsgebiedsindelingen:cbs_provincie_2022_gegeneraliseerd&outputFormat=json"
url_counties = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName=cbs_gemeente_2017_gegeneraliseerd&outputFormat=json"

# Data with Shopify orders
df_orders = pd.read_csv('data/dummy_orders.csv')

gdf_states = gpd.read_file(requests.get(url_states).text)
gdf_counties = gpd.read_file(requests.get(url_counties).text)

app = dash.Dash(__name__)
server = app.server

###############################################################################
#                           APP (BEGIN)
###############################################################################

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
                            children="A short introduction about the project and why it is of value to the user. \
                            Disclaimer about privacy and safety of data being used. \
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
                                html.Button('Total orders', id='button-total-orders', n_clicks=0),
                                html.Button('Total clients', id='button-total-clients',  n_clicks=0),
                                html.Button('Revenue', id='button-revenue', n_clicks=0),
                                html.Button('Life Time Value', id='button-ltv', n_clicks=0),
                                html.Button('Average Order Value', id='button-aov', n_clicks=0),
                                html.Button('Clients per 100k pop', id='button-clients-100k', n_clicks=0)
                            ]
                        ),
                        daq.BooleanSwitch(id='region-switch', on=False),
                    ]
                ),

                html.Div(
                    id="marvelmap-container",
                    children=[
                        dcc.Graph(id='choropleth'),
                    ]
                ),
                html.Div(
                    id="marvelchart-container",
                    children=[
                        dcc.Graph(id='histogram')
                    ]
                ),
                html.Div(
                    id="datatable-container",
                    children=[
                        dt.DataTable(id='datatabel', sort_action="native"),
                    ]
                ),
                dcc.Store(id="datasets", storage_type='session')
            ]
        )
    ]
)


###############################################################################
#                           APP (END)
###############################################################################

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8080)





# Previous App



# app.layout = html.Div(children=[
#     html.Div(html.Img(src='assets/marvel_logo.png',
#                       style={'height':'20%', 'width':'20%'})),

#     dcc.RadioItems(
#         id='region-selection',
#         options=[
#             {'label': 'Provinces', 'value': 'Provinces'},
#             {'label': 'Counties', 'value': 'Counties'}
#         ],
#         value='Provinces'
#     ),

#     html.Div([
#         dcc.Dropdown(
#         id='metric_selection',
#         options=options_dropdown,
#         value='clients'
#     )
#     ]),

#     html.Button('Update Figures', id='button_U'),

#     html.H3('* Dummy Dataset *'),

#     html.Div(children=[
#         dcc.Graph(id='choropleth',
#                 style={'width': '50%', 'display': 'inline-block'}),
#         dcc.Graph(id='histogram',
#                   style={'width': '50%', 'display': 'inline-block'})],
#         style={'backgroundColor': '#13265290'}
#     ),
#     dt.DataTable(id='data-table',
#                  style_data = {
#                     'color': 'black',
#                     'backgroundColor': '#EFF4FA'
#     },
#                  style_header = {
#                     'backgroundColor': '#13265290',
#                     'fontWeight': 'bold'
#     },
#                  sort_action="native"
#     ),

#     dcc.Store(id="datasets", storage_type='session')

# ], style={'margin': 'auto', 'width': '80%'})