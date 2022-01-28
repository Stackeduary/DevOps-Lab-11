import pandas as pd
from influxdb import InfluxDBClient
import os
import glob
import sys

dbname = "cluster"
# dbname = "datasource_3"
client = InfluxDBClient(host=172.17.91.132, port=8086)

# check for existing databases
client.drop_database(dbname)
client.create_database(dbname)
client.switch_database(dbname)

path = os.getcwd()
csv_files = glob.glob(os.path.join(path, "*.csv"))

for f in csv_files:
    csvReader = pd.read_csv(f)

    for row_index, row in csvReader.iterrows():
        tags = row[3]
        json_body = [{
            "measurement": "air_quality",
            "time": row[2],
            "tags": {
                "host": tags
            },
            "fields": {
                "lat": row[4],
                "long": row[5],
                "pm1_0": row[6],
                "pm2_5": row[7],
                "pm10": row[8]
            }
        }]
        print(json_body)
        client.write_points(json_body)
