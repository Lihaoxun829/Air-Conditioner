import paho.mqtt.client as mqtt
import json
import random
import time
from datetime import datetime, date
# -------------------Publisher:Monitor to APP-------------------------
client = mqtt.Client()
client.connect("broker.hivemq.com", 1883)
client.loop_start()

message_count = 0
max_messages = 5

print("[Monitor] Waiting for user to activate the smart air conditioner...\n")

while message_count < max_messages:
    user_input = input("Enter 'ON' to activate the smart air conditioner, or 'OFF' to deactivate the system: ").strip().upper()

    if user_input == "OFF":
        # Construct shutdown message
        today = str(date.today())
        current_time = datetime.now().strftime("%H:%M:%S")
        shutdown_msg = {
            "message": "User requested to shut down the system.",
            "temperature": "N/A",
            "ac_status": "OFF",
            "date": today,
            "time": current_time
        }
        # Publish shutdown message before exiting
        client.publish("smart_home/air_conditioner/report", json.dumps(shutdown_msg))
        print("[Monitor] Shutdown message sent to APP. Shutting down air conditioner...")
        time.sleep(1)  # Wait to ensure message delivery
        break

    elif user_input != "ON":
        print("Invalid input. Please enter 'ON' or 'OFF'.")
        continue

    # Generate temperature and construct normal status message
    temperature = random.randint(25, 40)
    today = str(date.today())
    current_time = datetime.now().strftime("%H:%M:%S")

    if temperature > 30:
        ac_status = "ON"
        message = f"Temperature is {temperature}°C, which is high. Air conditioner turned ON."
    else:
        ac_status = "OFF"
        message = f"Temperature is {temperature}°C, which is comfortable. Air conditioner remains OFF."

    data = {
        "message": message,
        "temperature": temperature,
        "ac_status": ac_status,
        "date": today,
        "time": current_time
    }

    # Publish the status message
    client.publish("smart_home/air_conditioner/report", json.dumps(data))
    print(f"[Monitor] Published message {message_count + 1}: {data}\n")

    message_count += 1
    time.sleep(1)

print("[Monitor] Finished or user exited. Disconnecting...")
client.loop_stop()
client.disconnect()

# -------------------Subscriber:APP to Monitor-------------------------
client = mqtt.Client()
running = True
connected = False
control_count = 0
max_control_messages = 5

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print("Air Conditioner connected to MQTT Broker.")
        client.subscribe("smart_home/user_to_ac")
        connected = True
    else:
        print("Connection failed with return code:", rc)

def on_message(client, userdata, msg):
    global running, control_count

    try:
        data = json.loads(msg.payload.decode("utf-8"))
        command_type = data.get("command")

        if command_type == "exit":
            print("[AC] Received exit command. Shutting down.")
            running = False
            return

        elif command_type == "get_temperature":
            temperature = random.randint(20, 50)
            print(f"[AC] Current room temperature generated: {temperature}°C")

            # Send temperature back to user
            response = {"temperature": temperature}
            client.publish("smart_home/ac_to_user/temperature", json.dumps(response))

        elif command_type == "control":
            print(f"[AC] Control command received:")
            print(f"  - Air conditioner status: {data['ac_status']}")
            print(f"  - Temperature: {data['temperature']}°C")
            print(f"  - Time: {data['date']} {data['time']}\n")

            control_count += 1
            if control_count >= max_control_messages:
                print(f"[AC] Received {max_control_messages} control commands. Shutting down.")
                running = False

        else:
            print("[AC] Unknown command received.")
            return

    except json.JSONDecodeError:
        print("Failed to decode incoming message.")

client.on_connect = on_connect
client.on_message = on_message

client.connect("broker.hivemq.com", 1883)
client.loop_start()

while not connected:
    time.sleep(0.1)

print("Air Conditioner is now listening for user commands...")

while running:
    time.sleep(0.1)

client.loop_stop()
client.disconnect()
print("Air Conditioner terminated.")









