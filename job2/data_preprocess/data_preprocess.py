import pandas as pd
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
import sys

ds_host = sys.argv[4]
ds_name = sys.argv[3]
local_influxdb_name = sys.argv[1]
local_influxdb_host = sys.argv[2]

# client to extract data from data source
data_source = InfluxDBClient(host=ds_host, port=8087)

# Switch the database
data_source.switch_database(ds_name)
query = "select * from air_quality"

# read the dataframe
df = pd.DataFrame(data_source.query(query).get_points())
df["time"] = pd.to_datetime(df["time"], errors="coerce")
# df = df.set_index("time")

data_sink = DataFrameClient(host=local_influxdb_host, port=8086)

data_sink.drop_database(local_influxdb_name)
data_sink.create_database(local_influxdb_name)
data_sink.switch_database(local_influxdb_name)

for group, dataframe in df.groupby(['host']):
    tags = {'host': group}
    fields = dataframe[["time", "pm1_0", "pm2_5", "pm10"]]
    fields = fields.set_index("time")
    data_sink.write_points(fields, 'preprocessed', tags, protocol="line")
