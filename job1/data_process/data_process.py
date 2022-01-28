import pandas as pd
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
import sys

local_influxdb_name = sys.argv[1]
local_influxdb_host = sys.argv[2]
print(local_influxdb_name, local_influxdb_host)

# client to extract data from data_source
data_sink = InfluxDBClient(host=local_influxdb_host, port=8086)

data_sink.switch_database(local_influxdb_name)

query = "select * from preprocessed"

df = pd.DataFrame(data_sink.query(query).get_points())

df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.set_index("time")

data_client = DataFrameClient(host=local_influxdb_host, port=8086)

data_client.drop_database('processed')
data_client.create_database('processed')
data_client.switch_database('processed')

df_hourly = df.groupby(['host']).resample('1H').mean().transform(pd.Series.interpolate).reset_index()

for group, dataframe in df_hourly.groupby(['host']):
    dataframe = dataframe.reset_index()
    tags = {'host': group}
    fields = dataframe[["time", "pm1_0", "pm2_5", "pm10"]]
    fields = fields.set_index("time")
    data_client.write_points(fields, 'hourly', tags, protocol="line")


df_daily = df.groupby(['host']).resample('D').mean().transform(pd.Series.interpolate).reset_index()

print(df_daily)

for group, dataframe in df_daily.groupby(['host']):
    dataframe = dataframe.reset_index()
    tags = {'host': group}
    fields = dataframe[["time", "pm1_0", "pm2_5", "pm10"]]
    fields = fields.set_index("time")
    data_client.write_points(fields, 'daily', tags, protocol="line")


df_weekly = df.groupby(['host']).resample('W').mean().transform(pd.Series.interpolate).reset_index()

for group, dataframe in df_weekly.groupby(['host']):
    dataframe = dataframe.reset_index()
    tags = {'host': group}
    fields = dataframe[["time", "pm1_0", "pm2_5", "pm10"]]
    fields = fields.set_index("time")
    data_client.write_points(fields, 'weekly', tags, protocol="line")
