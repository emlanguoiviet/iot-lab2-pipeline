import json
import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- CẤU HÌNH MQTT ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/lab2/manh_ptit/telemetry"

# --- CẤU HÌNH INFLUXDB 2.x ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "qd7K2D1qBPC5K34n0ERx_-kuIAeHVD9Svu53HIBbGIG8pByYZQqmhtwAEyJSKYQsULnj5INNZQ1awhs8AUZEHw=="
INFLUX_ORG = "ptit_iot"
INFLUX_BUCKET = "iot_raw"

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def validate_data(data):
    required_keys = ["device_id", "temperature", "humidity", "distance_cm"]
    for key in required_keys:
        if key not in data or data[key] is None:
            return False
    if not (-20 <= float(data["temperature"]) <= 85):
        return False
    if not (0 <= float(data["humidity"]) <= 100):
        return False
    if not (2 <= float(data["distance_cm"]) <= 400):
        return False
    return True

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(">> [MQTT] Ket noi Broker HiveMQ thanh cong!")
        client.subscribe(MQTT_TOPIC)
        print(f">> [MQTT] Dang lang nghe topic: {MQTT_TOPIC} ...\n")
    else:
        print(f">> [MQTT] Ket noi that bai, ma loi: {rc}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)

        if not validate_data(data):
            print(f"[LOAI BO] Du lieu ngoai khoang hop le: {payload_str}")
            return

        point = (
            Point("sensor_telemetry")
            .tag("device_id", str(data["device_id"]))
            .field("temperature", float(data["temperature"]))
            .field("humidity", float(data["humidity"]))
            .field("distance_cm", float(data["distance_cm"]))
            .field("sequence", int(data.get("sequence", 0)))
            .time(time.time_ns(), WritePrecision.NS)
        )

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(f"[DA GHI INFLUXDB] Seq: {data.get('sequence')} | Temp: {data['temperature']}C | Hum: {data['humidity']}% | Dist: {data['distance_cm']}cm")

    except Exception as e:
        print(f"[LOI XU LY]: {e}")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print(">> Dang khoi dong Collector...")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_forever()
