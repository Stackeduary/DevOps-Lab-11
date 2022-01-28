# Read sampled data
# Classify - Average of hourly, daily and monthly data
# Insert the classfied data in influxdb

import pandas as pd
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
import sys
import numpy as np

# Get the variables
local_influxdb_name = sys.argv[1]
# Read sampled data
# Classify - Average of hourly, daily and monthly data
# Insert the classfied data in influxdb


local_influxdb_host = sys.argv[2]
print(local_influxdb_name,local_influxdb_host)

# client to extract data from data_source
data_sink = InfluxDBClient(
    host=local_influxdb_host,
    port=8086
)

data_sink.switch_database(local_influxdb_name)

# get preprocesed data
query = "select * from preprocessed"
df = pd.DataFrame(data_sink.query(query).get_points())

df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.set_index('time')


# Calculating AQI
# 1. Take rolling mean of 24h
df["pm10_avg"] = df.groupby("host")["pm10"].rolling(window = 24).mean().values

df["pm2_5_avg"] = df.groupby("host")["pm2_5"].rolling(window = 24).mean().values

def get_pm2_5subindex(x):
    if x <= 30:
        return x * 50 / 30
    elif x <= 60:
        return 50 + (x - 30) * 50 / 30
    elif x <= 90:
        return 100 + (x - 60) * 100 / 30
    elif x <= 120:
        return 200 + (x - 90) * 100 / 30
    elif x <= 250:
        return 300 + (x - 120) * 100 / 130
    elif x > 250:
        return 400 + (x - 250) * 100 / 130
    else:
        return 0

# Check for AQI boundaries

df["pm2_5_subindex"] = df["pm2_5_avg"].apply(lambda x: get_pm2_5subindex(x))

## PM10 Sub-Index calculation
def get_pm10subindex(x):
    if x <= 50:
        return x
    elif x <= 100:
        return x
    elif x <= 250:
        return 100 + (x - 100) * 100 / 150
    elif x <= 350:
        return 200 + (x - 250)
    elif x <= 430:
        return 300 + (x - 350) * 100 / 80
    elif x > 430:
        return 400 + (x - 430) * 100 / 80
    else:
        return 0

df["pm10_subindex"] = df["pm10_avg"].apply(lambda x: get_pm10subindex(x))

## AQI severeties
def get_AQI(x):
    if x <= 100:
        return "Good"
    elif x <= 150:
        return "Satisfactory"
    elif x <= 350:
        return "Moderate"
    elif x <= 400:
        return "Poor"
    elif x <= 550:
        return "Very Poor"
    elif x > 600:
        return "Severe"
    else:
        return np.NaN

df["Checks"] = (df["pm2_5_subindex"] > 0).astype(int) + \
                (df["pm10_subindex"] > 0).astype(int)
             

df["AQI"] = round(df[["pm2_5_subindex", "pm10_subindex"]].max(axis = 1))
df.loc[df["pm2_5_subindex"] + df["pm10_subindex"] <= 0, "AQI"] = np.NaN
df.loc[df.Checks <= 1, "AQI"] = np.NaN

df["AQI_calculated"] = df["AQI"].apply(lambda x: get_AQI(x))

print(df[~df.AQI.isna()].head(13))

data_client = DataFrameClient(
    host=local_influxdb_host,
    port=8086
)

# data_client.drop_database('AQI')
# data_client.create_database('AQI')
# data_client.switch_database('AQI')

data_client.drop_database('cluster')
data_client.create_database('cluster')
data_client.switch_database('cluster')


for group, dataframe in df.groupby(["host"]):
    dataframe = dataframe.reset_index()
    tags = {"host": group}
    fields = dataframe[["time","pm1_0", "pm2_5", "pm10","AQI","AQI_calculated"]]
    fields = fields.set_index("time")
    data_client.write_points(fields, 'AQI', tags, protocol="line")



# 1. read the data from influxdb running in the deployment VM
# 2. make the clusters

time_list = [0, 6, 12, 18, 23]
labels = ["Night", "Morning", "Afternoon", "Evening"]
pms = ["time", "pm1_0", "pm2_5", "pm10"]

session = pd.cut(df.time.dt.hour, time_list, labels, include_lowest=True)

df['time_interval'] = session
df['time_interval'] = df['time_interval'].astype(str)


# 3. insert the dataframe into Influxdb running in the deployment VM

dbname = cluster

for group, dataframe in df.groupby(['time_interval']):
    for host, df_ in dataframe.groupby(["host"]):
        df_ = df_.reset_index()
        tags = {
            "time_interval": group, 
            "host": host
            }
        fields = df_[pms]
        fields = fields.set_index("time")
        client.write_points(fields, 'cluster', tags, protocol='line')
        time.sleep(1)
