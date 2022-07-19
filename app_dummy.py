import plots
import dash
import json
import dash_daq as daq
import dash_table as dt
import pandas as pd

from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


# Static collumn names to use when enriching data
CONFIG = {
    "cnames": {
        "orders": "Name",
        "clients": "Email",
        "revenue": "Total",
        "zip": "Billing Zip"
    }
}

# Links to get (http request) geojson files
url_counties = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName=cbs_gemeente_2017_gegeneraliseerd&outputFormat=json"
url_states = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=1.1.0&typeName=cbsgebiedsindelingen:cbs_provincie_2022_gegeneraliseerd&outputFormat=json"

options_dropdown = [
    {'label': 'Total orders', 'value': 'orders'},
    {'label': 'Total clients', 'value': 'clients'},
    {'label': 'Revenue', 'value': 'revenue'},
    {'label': 'Lifetime Value (LTV)', 'value': 'LTV'},
    {'label': 'Average Order Value (AOV)', 'value': 'AOV'}
]

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
                    id="options",
                    children=[
                        html.Div(
                            id="metric-buttons-container",
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
                        html.Div(
                            children=[html.Button('Update Figures', id='button_U')]
                        ),
                    ]
                ),

                html.Div(
                    id="marvelmap",
                    children=[
                        dcc.Graph(id='choropleth'),
                    ]
                ),
                html.Div(
                    id="marvelchart",
                    children=[
                        dcc.Graph(id='histogram')
                    ]
                ),
                dt.DataTable(id='datatable', sort_action="native"),
                dcc.Store(id="datasets", storage_type='session')
            ]
        )
    ]
)



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


###############################################################################
#                           APP (END)
###############################################################################



@app.callback(Output('datasets', 'data'),
              Input('button_U', 'n_clicks'),
              State('datasets', 'data'))
def load_data(n_clicks, datasets_json):
    if datasets_json is not None:
        raise PreventUpdate

    return plots.enrich_data([], [], url_states, url_counties, dummy_data=True)


@app.callback(Output('data-table', 'data'),
              Output('data-table', 'columns'),
              Output('histogram', 'figure'),
              Output('choropleth', 'figure'),
              Input('button_U', 'n_clicks'),
              State('datasets', 'data'),
              State('metric_selection', 'value'),
              State('region-selection', 'value'))
def update_figures(n_clicks, datasets_json, metric, region):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    if datasets_json is None or 'button_U' not in changed_id:
        raise PreventUpdate


    datasets = json.loads(datasets_json)
    df = pd.DataFrame.from_records(datasets[region])
    df.sort_values(metric, inplace=True, ascending=False)

    mmap = plots.generate_map(df, metric, region, url_states, url_counties)

    if region == 'Counties':
        df = df.reset_index(drop=True).iloc[:10]

    histogram = plots.generate_histogram(df, metric)
    data, columns = plots.generate_table(df)

    return data, columns, histogram, mmap


@app.callback(Output("metric_selection", "options"),
              Input("region-selection", "value"))
def update_dropdown(region):
    if region == 'Provinces':
        return options_dropdown + [
            {'label': 'Revenue relative to BBP of region', 'value': 'rev_BBP'},
            {'label': 'Clients per 100.000 population', 'value': 'clients_pop'}]
    else:
        return options_dropdown


if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8080)