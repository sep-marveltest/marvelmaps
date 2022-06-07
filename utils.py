import json
import pandas as pd


FILE_DATA_NL = "data/data_NL.csv"
CUR = "€"

# Reads static data of the Netherlands;
# - zip to region
# - BBP of region
# - Population of region
def read_NL_data():
    return pd.read_csv(FILE_DATA_NL)


# Converts a zipcode to region
def zip_to_region(data_NL, zip_, cname):
    try:
        row = data_NL.loc[data_NL['postal code'] == int(zip_)]

        return row[cname].values[0]
    except (KeyError, ValueError, IndexError):
        return 0


# Changes crs coding of geojson file
def change_crs(gdf):
    gdf = gdf.to_crs(epsg=4326)
    gdf.to_file('data/geojsfile.json', driver = 'GeoJSON')

    with open('data/geojsfile.json') as geofile:
        data = json.load(geofile)

    return data


# Add currency symbol to strings in passed columns
def add_currency(df, columns):
    for col in columns:
        df[col] = df[col].apply(lambda x: CUR + "{:.2f}".format(x))

    return df


# Determine which separator is used; comma or dot
def find_separator(column):
    for val in column:
        val = str(val)

        if '.' in val and ',' not in val:
            return '.'

        elif '.' not in val and ',' in val:
            return ','
