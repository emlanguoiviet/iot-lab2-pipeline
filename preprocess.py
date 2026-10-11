import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "qd7K2D1qBPC5K34n0ERx_-kuIAeHVD9Svu53HIBbGIG8pByYZQqmhtwAEyJSKYQsULnj5INNZQ1awhs8AUZEHw=="
INFLUX_ORG = "ptit_iot"
INFLUX_BUCKET = "iot_raw"

client = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)

print(">> 1. Dang lay du lieu thoi gian thuc moi nhat tu InfluxDB...")

# Truy van du lieu trong 30 phut gan nhat tu measurement 'telemetry'
query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -30m)
  |> filter(fn: (r) => r["_measurement"] == "telemetry")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"], desc: false)
'''

df = query_api.query_data_frame(query)

if df.empty:
    print(">> Khong tim thay du lieu. Hay kiem tra xem collector.py co dang ghi vao khong!")
    exit()

cols = ["_time", "temperature", "humidity", "distance_cm"]
df = df[[c for c in cols if c in df.columns]]
df.set_index("_time", inplace=True)
df.sort_index(inplace=True)

# 2. Noi suy va Rolling Mean
df_resampled = df.interpolate(method="time").ffill().bfill()
df_resampled["temperature_roll_mean"] = df_resampled["temperature"].rolling(window=3, min_periods=1).mean()
df_resampled["humidity_roll_mean"] = df_resampled["humidity"].rolling(window=3, min_periods=1).mean()

# 3. Tinh Delta
df_resampled["humidity_delta"] = df_resampled["humidity"].diff().fillna(0.0)

# 4. Chuan hoa Min-Max Scaling (dua ve khoang 0 - 1)
scaler = MinMaxScaler()
scaled_values = scaler.fit_transform(df_resampled[["temperature", "humidity"]])
df_resampled["temp_scaled"] = scaled_values[:, 0]
df_resampled["hum_scaled"] = scaled_values[:, 1]

# In 5 dong moi nhat
print("\n--- KET QUA TIEN XU LY (5 DONG MOI NHAT) ---")
print(df_resampled.tail(5))

# 5. Ghi nguoc lai vao measurement 'sensor_processed'
print("\n>> Dang ghi du lieu vao measurement 'sensor_processed'...")
points = []
for timestamp, row in df_resampled.iterrows():
    p = influxdb_client.Point("sensor_processed").time(timestamp)
    for col_name in df_resampled.columns:
        p.field(col_name, float(row[col_name]))
    points.append(p)

write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
print(">> GHI THANH CONG! Measurement 'sensor_processed' da san sang tren InfluxDB.")
