import maps
import dash
import json
import base64
import dash_table as dt

from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


CONFIG = {}

url_counties = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName=cbs_gemeente_2017_gegeneraliseerd&outputFormat=json"
url_states = "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=1.1.0&typeName=cbsgebiedsindelingen:cbs_provincie_2022_gegeneraliseerd&outputFormat=json"

options_dropdown = [
    {'label': 'Total orders', 'value': 'orders'},
    {'label': 'Total clients', 'value': 'clients'},
    {'label': 'Revenue', 'value': 'revenue'}
]

with open("data/config.json", 'r') as file:
    CONFIG.update(json.load(file))

# image_filename = 'data/Marveltest_Logo_DarkBlue (1).png' # replace with your own image
# encoded_image = base64.b64encode(open(image_filename, 'rb').read())

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
            {'label': 'Provinces', 'value': 'prov'},
            {'label': 'Counties', 'value': 'cnty'}
        ],
        value='prov'
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

    html.Button('Generate Map', id='button_gen'),

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
                 sort_action="native")
], style={'margin': 'auto', 'width': '80%'})

###############################################################################
#                           APP (END)
###############################################################################


@app.callback(Output('choropleth', 'figure'),
              Output('histogram', 'figure'),
              Output('data-table', 'data'),
              Output('data-table', 'columns'),
              Input('button_gen', 'n_clicks'),
              State('upload_data', 'contents'),
              State('upload_data', 'filename'),
              State('metric_selection', 'value'),
              State('region_selection', 'value'))
def update_output(n_clicks, list_of_contents, list_of_names, metric, region):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    if 'button_gen' in changed_id and list_of_contents is not None:
        return maps.generate_figures(list_of_contents, list_of_names, metric, region, CONFIG, url_states, url_counties)

    elif 'button_gen' in changed_id:
        print('Upload file first')

    raise PreventUpdate


# @app.callback(Output("", "options"),
#               Input("", "value"))
# def update_histogram_ordering():


@app.callback(
    Output("metric_selection", "options"), 
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