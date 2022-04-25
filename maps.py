from numpy import histogram
import plotly.express as px
import data


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
                               opacity=1
                               )
    fig = fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig


def generate_histogram(df, metric):
    if 'state' in df.columns:
        x = 'state'
    else:
        x = 'county'

    fig = px.histogram(df, x=x, y=metric)

    return fig


def generate_figures(list_of_contents, list_of_names, metric, region, CONFIG, url_states, url_counties):
    df = data.parse_contents(list_of_contents[0], list_of_names[0])

    df[CONFIG['cnames']['zip']] = df[CONFIG['cnames']['zip']].apply(lambda z: str(z)[:4])

    states, counties = data.get_shapes(url_states, url_counties)
    prov_df, cnty_df = data.get_data(df, counties, states, CONFIG)

    if metric != 'randstad':
        prov_df[metric] = prov_df[metric].astype(float)

    if region == 'prov':
        df = prov_df
        locations = 'state'
        geojson = states
    else:
        df = cnty_df
        locations = 'county'
        geojson = counties


    mmap = choropleth(df, locations, geojson, metric)
    histogram = generate_histogram(df, metric)
    table_data = df.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df.columns]

    return mmap, histogram, table_data, table_columns
