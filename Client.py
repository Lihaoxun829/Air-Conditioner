import paho.mqtt.client as mqtt
import json
from datetime import date, datetime
import time
#------------------------Subscriber:Monitor to APP---------------------------
message_count = 0
max_messages = 5
connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print("APP connected to MQTT Broker")
        client.subscribe("smart_home/air_conditioner/report")
        connected = True
    else:
        print("Connection failed with return code:", rc)

def on_message(client, userdata, msg):
    global message_count
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        print(f"[APP] Message {message_count + 1} received from air conditioner:\n")
        print(f"  - Temperature: {data['temperature']}°C")
        print(f"  - Air Conditioner Status: {data['ac_status']}")
        print(f"  - Time: {data['date']} {data['time']}\n")

        message_count += 1
        if message_count >= max_messages:
            print("APP received 5 messages. Exiting...")
            client.loop_stop()
            client.disconnect()

    except json.JSONDecodeError:
        print("Failed to decode message")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("broker.hivemq.com", 1883)
print("APP is waiting for air conditioner messages...\n")

client.loop_start()

# Wait for connection
while not connected:
    time.sleep(0.1)

# Stay alive until disconnected
while client.is_connected():
    time.sleep(0.1)
#------------------------Publisher:APP to Monitor---------------------------
client = mqtt.Client()
temperature_received = False
current_temperature = None
command_count = 0
max_commands = 5
connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print("APP connected to MQTT Broker.")
        client.subscribe("smart_home/ac_to_user/temperature")
        connected = True
    else:
        print("Connection failed with return code:", rc)

def on_message(client, userdata, msg):
    global temperature_received, current_temperature
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        current_temperature = data["temperature"]
        temperature_received = True
    except json.JSONDecodeError:
        print("Failed to decode temperature message.")

client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883)
client.loop_start()

# Wait for MQTT connection
while not connected:
    time.sleep(0.1)

print("APP started. You can control the air conditioner.")

while command_count < max_commands:
    choice = input("Enter 1 to continue, or 0 to exit: ")

    if choice == "0":
        exit_msg = {"command": "exit"}
        client.publish("smart_home/user_to_ac", json.dumps(exit_msg))
        print("[APP] Sent exit command. Exiting...")
        break

    elif choice == "1":
        # Request temperature from AC
        temperature_received = False
        client.publish("smart_home/user_to_ac", json.dumps({"command": "get_temperature"}))
        print("[APP] Requested current temperature. Waiting for response...")

        # Wait until temperature is received
        while not temperature_received:
            time.sleep(0.1)

        # Step 2: Show temperature and ask control decision
        print(f"Current room temperature: {current_temperature}°C")
        status_input = input("Enter 1 to turn ON the air conditioner, or 0 to turn it OFF: ")
        ac_status = "ON" if status_input == "1" else "OFF"
        today = str(date.today())
        now = datetime.now().strftime("%H:%M:%S")

        control_msg = {
            "command": "control",
            "ac_status": ac_status,
            "temperature": current_temperature,
            "date": today,
            "time": now
        }

        client.publish("smart_home/user_to_ac", json.dumps(control_msg))
        print(f"[APP] Sent control command: {control_msg}\n")

        command_count += 1
        time.sleep(1)

    else:
        print("Invalid input. Please enter 1 or 0.")

client.loop_stop()
client.disconnect()
print("APP terminated.")





