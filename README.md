# IoT Lab 2: Thu thập, Lưu trữ và Tiền xử lý dữ liệu IoT (INT14149)

- Họ và tên: Lương Đức Mạnh
- Mã sinh viên: B23DCCN530
- Học phần: IoT và Ứng dụng (INT14149) - PTIT

## Kiến trúc hệ thống
ESP32 (Wokwi) -> HiveMQ Broker -> collector.py -> InfluxDB 2.x (iot_raw) -> preprocess.py -> InfluxDB 2.x (sensor_processed)

## Hướng dẫn chạy
1. Cài đặt thư viện: `pip install -r requirements.txt`
2. Chạy ESP32 trên Wokwi (mã nguồn tại `firmware/sketch.ino`).
3. Chạy thu thập dữ liệu: `python collector.py`
4. Chạy tiền xử lý dữ liệu: `python preprocess.py`
5. Chạy đo độ trễ: `python latency_eval.py`

## Kết quả đo độ trễ
- Mean Latency: 48.02 ms
- Jitter: 0.01 ms
