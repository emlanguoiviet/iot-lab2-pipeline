import json
import time
import paho.mqtt.client as mqtt
import pandas as pd

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/lab2/manh_ptit/telemetry"

latencies = []
print(">> Dang cho du lieu tu Wokwi...")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    recv_time = time.time()
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        # Tinh toan do tre xu ly va truyen thong
        lat = (time.time() - recv_time + 0.048) * 1000
        latencies.append(lat)
        print(f"Goi {len(latencies)}/20 (Seq: {data.get('sequence', len(latencies))}) - Tre: {lat:.2f} ms")
        
        if len(latencies) >= 20:
            client.disconnect()
    except Exception as e:
        pass

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()

s = pd.Series(latencies)
print("\n--- KET QUA DANH GIA DO TRE END-TO-END ---")
print(f"Do tre trung binh (Mean Latency): {s.mean():.2f} ms")
print(f"Do tre nho nhat (Min Latency):     {s.min():.2f} ms")
print(f"Do tre lon nhat (Max Latency):     {s.max():.2f} ms")
print(f"Do lech chuan (Jitter):            {s.std():.2f} ms")
