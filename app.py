import plots
import dash
import json
import dash_table as dt
import pandas as pd

from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


DUMMY_DATA = True

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

# with open("data/config.json", 'r') as file:
#     CONFIG.update(json.load(file))

app = dash.Dash(__name__)
server = app.server

###############################################################################
#                           APP (BEGIN)
###############################################################################
app.layout = html.Div(children=[
    html.Div(html.Img(src='assets/marvel_logo.png', style={'height':'20%', 'width':'20%'})),

    dcc.RadioItems(
        id='region_selection',
        options=[
            {'label': 'Provinces', 'value': 'Provinces'},
            {'label': 'Counties', 'value': 'Counties'}
        ],
        value='Provinces'
    ),

    html.Div([
        dcc.Dropdown(
        id='metric_selection',
        options=options_dropdown,
        value='clients'
    )
    ]),

    dcc.Upload(
        id='upload_data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    html.Button('Read data', id='button_data'),

    html.Button('Generate Figures', id='button_gen'),

    html.Div(children=[
        dcc.Graph(id='choropleth', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='histogram',
                  style={'width': '50%', 'display': 'inline-block'})],
        style={'backgroundColor': '#13265290'}
    ),
    dt.DataTable(id='data-table',
                 style_data = {
                    'color': 'black',
                    'backgroundColor': '#EFF4FA'
    },
                 style_header = {
                    'backgroundColor': '#13265290',
                    'fontWeight': 'bold'
    },
                 sort_action="native"
    ),

    dcc.Store(id="datasets", storage_type='session')

], style={'margin': 'auto', 'width': '80%'})

###############################################################################
#                           APP (END)
###############################################################################


@app.callback(Output('data-table', 'data'),
              Output('data-table', 'columns'),
              Output('histogram', 'figure'),
              Output('choropleth', 'figure'),
              Input('button_gen', 'n_clicks'),
              State('datasets', 'data'),
              State('metric_selection', 'value'),
              State('region_selection', 'value'))
def update_figures(n_clicks, datasets_json, metric, region):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    if not (datasets_json is not None and 'button_gen' in changed_id):
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


if DUMMY_DATA:
    @app.callback(Output('datasets', 'data'),
                Input('button_data', 'n_clicks'))
    def process_data(n_clicks):
        if not 'button_gen' in [p['prop_id'] for p in callback_context.triggered][0]:
            raise PreventUpdate

        return plots.enrich_data([], [], url_states, url_counties, DUMMY_DATA)
else:
    @app.callback(Output('datasets', 'data'),
                Input('button_data', 'n_clicks'),
                State('upload_data', 'contents'),
                State('upload_data', 'filename'))
    def process_data(n_clicks, list_of_contents, list_of_names):
        if not ('button_gen' in [p['prop_id'] for p in callback_context.triggered][0] or list_of_contents):
            raise PreventUpdate

        return plots.enrich_data(list_of_contents, list_of_names, url_states, url_counties)


@app.callback(Output("metric_selection", "options"),
    Input("region_selection", "value"))
def update_dropdown(region):
    if region == 'prov':
        return options_dropdown + [
            {'label': 'Revenue relative to BBP of region', 'value': 'rev_BBP'},
            {'label': 'Clients per 100.000 population', 'value': 'clients_pop'}]
    else:
        return options_dropdown


if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8080)