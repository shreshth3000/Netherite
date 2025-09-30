import setup_path
import airsim
import cv2 as cv
import numpy as np
import time
import keyboard
import os

# Create output directory for scans
out_dir = "lidar_logs"
os.makedirs(out_dir, exist_ok=True)

# Connect to AirSim
client = airsim.MultirotorClient()
client.enableApiControl(True, "Drone1")
client.armDisarm(True, "Drone1")
client.takeoffAsync(vehicle_name="Drone1").join()

# Movement speeds
speed = 15
vert_speed = 5
yaw_speed = 30

print("Controls: WASD=move, Up/Down=altitude, Left/Right=yaw, Esc=quit")

frame_id = 0
try:
    while True:
        # Default movement
        vx = vy = vz = yaw_rate = 0

        # Keyboard controls
        if keyboard.is_pressed("w"): vx = speed
        if keyboard.is_pressed("s"): vx = -speed
        if keyboard.is_pressed("a"): vy = -speed
        if keyboard.is_pressed("d"): vy = speed
        if keyboard.is_pressed("up"): vz = -vert_speed
        if keyboard.is_pressed("down"): vz = vert_speed
        if keyboard.is_pressed("left"): yaw_rate = -yaw_speed
        if keyboard.is_pressed("right"): yaw_rate = yaw_speed

        # Move drone
        client.moveByVelocityAsync(
            vx, vy, vz, duration=0.1,
            yaw_mode=airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate),
            vehicle_name="Drone1"
        )

        # Telemetry
        drone_state = client.getMultirotorState(vehicle_name="Drone1")
        altitude = -drone_state.kinematics_estimated.position.z_val
        velocity = drone_state.kinematics_estimated.linear_velocity.z_val
        print(f"Altitude: {altitude:.2f} m | Velocity: {velocity:.2f} m/s | "
              f"vx: {vx}, vy: {vy}, vz: {vz}, yaw_rate: {yaw_rate}")

        # LiDAR data
        lidarData =     client.getLidarData("Lidar1", "Drone1")
        if len(lidarData.point_cloud) >= 3:
            pts = np.array(lidarData.point_cloud, dtype=np.float32).reshape(-1, 3)

            # Transform into world coordinates
            pos = lidarData.pose.position
            orient = lidarData.pose.orientation
            q = [orient.w_val, orient.x_val, orient.y_val, orient.z_val]
            R = airsim.utils.to_rotation_matrix(q)
            pts_world = (pts @ R.T) + np.array([[pos.x_val, pos.y_val, pos.z_val]])

            np.save(os.path.join(out_dir, f"scan_{frame_id:05d}.npy"), pts_world)
            print(f"Saved scan {frame_id}, {pts_world.shape[0]} points")
            frame_id += 1

        responses = client.simGetImages([
            airsim.ImageRequest("BottomCamera", airsim.ImageType.Scene, False, False)
        ], vehicle_name="Drone1")

        if responses and responses[0].width != 0:
            img1d = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
            img_rgb = img1d.reshape(responses[0].height, responses[0].width, 3)
            img_rgb = cv.resize(img_rgb, (320, 240))  # resize smaller
            cv.imshow("Bottom Camera", img_rgb)

        if keyboard.is_pressed("esc"):
            print("ESC pressed. Exiting.")
            break
        if cv.waitKey(1) & 0xFF == ord('x'):
            print("'x' pressed in window. Exiting.")
            break

        time.sleep(0.05)

finally:
    print("Landing and closing connection...")
    client.landAsync(vehicle_name="Drone1").join()
    client.armDisarm(False, "Drone1")
    client.enableApiControl(False, "Drone1")
    cv.destroyAllWindows()
