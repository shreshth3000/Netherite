import airsim
import time

client = airsim.MultirotorClient()
connected = False
for i in range(10):
    try:
        client.confirmConnection()
        connected = True
        print("Connected to AirSim client.")
        break
    except Exception as e:
        print("Connection failed, retrying...")
        time.sleep(1)

if not connected:
    print("Could not connect to AirSim server. Make sure UE simulator is running.")
    exit(1)
