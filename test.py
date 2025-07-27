import paho.mqtt.client as mqtt

# Broker MQTT
BROKER = "192.168.100.223"
PORT = 1883
TOPIC = "sensor/data"

# Fungsi callback ketika terhubung ke broker
def on_connect(client, userdata, flags, rc):
    print(f"Terhubung ke broker dengan status: {rc}")
    # Subscribe ke topik setelah terhubung
    client.subscribe(TOPIC)

# Fungsi callback ketika menerima pesan
def on_message(client, userdata, msg):
    print(f"Pesan diterima dari topik {msg.topic}: {msg.payload.decode()}")

# Membuat client MQTT
client = mqtt.Client()

# Set callback untuk koneksi dan pesan
client.on_connect = on_connect
client.on_message = on_message

# Menghubungkan ke broker
client.connect(BROKER, PORT, 60)

# Menjalankan loop untuk mendengarkan pesan
client.loop_forever()
