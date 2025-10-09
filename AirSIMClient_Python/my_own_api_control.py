import setup_path
import airsim
import cv2 as cv
import numpy as np
import time
import keyboard
import os
from scipy.spatial.transform import Rotation as R
os.makedirs("data", exist_ok=True)
os.makedirs("data/images", exist_ok=True)
os.makedirs("data/lidar", exist_ok=True)

client = airsim.MultirotorClient()
client.enableApiControl(True)
client.armDisarm(True)
client.takeoffAsync().join()

speed = 15
vert_speed = 5
yaw_speed = 30
frame_idx = 0

print("Controls: WASD=move, Up/Down=altitude, Left/Right=yaw, Esc=quit")

try:
    while True:
        vx = vy = vz = yaw_rate = 0

        if keyboard.is_pressed("w"):
            vx = speed
        if keyboard.is_pressed("s"):
            vx = -speed
        if keyboard.is_pressed("a"):
            vy = -speed
        if keyboard.is_pressed("d"):
            vy = speed
        if keyboard.is_pressed("up"):
            vz = -vert_speed
        if keyboard.is_pressed("down"):
            vz = vert_speed
        if keyboard.is_pressed("left"):
            yaw_rate = -yaw_speed
        if keyboard.is_pressed("right"):
            yaw_rate = yaw_speed

        client.moveByVelocityAsync(
            vx, vy, vz, duration=0.1,
            yaw_mode=airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate)
        )
        
        drone_state = client.getMultirotorState()
        pos = drone_state.kinematics_estimated.position
        quat = drone_state.kinematics_estimated.orientation
        position_global = np.array([pos.x_val, pos.y_val, pos.z_val])
        rotation_global = R.from_quat([quat.x_val, quat.y_val, quat.z_val, quat.w_val])

        altitude = -pos.z_val
        velocity = drone_state.kinematics_estimated.linear_velocity.z_val

        print(f"Frame {frame_idx} | Altitude: {altitude:.2f} m | Velocity: {velocity:.2f} m/s | vx: {vx}, vy: {vy}, vz: {vz}, yaw_rate: {yaw_rate}")

        # Get lidar
        lidarData = client.getLidarData("Lidar1")
        timestamp = int(time.time() * 1000)
        if lidarData.point_cloud and len(lidarData.point_cloud) >= 3:
            pts = np.array(lidarData.point_cloud, dtype=np.float32).reshape(-1, 3)
            pts_rotated = rotation_global.apply(pts)         
            pts_global = pts_rotated + position_global     
            pts_global[:,2] = -pts_global[:,2]
            lidar_filename = f"data/lidar/scan_{frame_idx:05d}_{timestamp}.xyz" if frame_idx%20==0 else None
            if lidar_filename is not None: 
                np.savetxt(lidar_filename, pts_global)
            #img_lidar = np.zeros((500, 500, 3), dtype=np.uint8)
           # for x, y, z in pts_global:
           #     xi = int(250 + x * 5) % 500
          #      yi = int(250 + y * 5) % 500
          #      img_lidar[yi, xi] = (255, 255, 255)
            #cv.putText(img_lidar, f'Altitude: {altitude:.2f} m', (10, 30),
             #          cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            #cv.imshow("LiDAR Feed", img_lidar)

        responses = client.simGetImages([
            airsim.ImageRequest("BottomCamera", airsim.ImageType.Scene, False, False)
        ], vehicle_name="Drone1")
#
       # if responses and responses[0].width != 0:
         #   img1d = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
            #img_rgb = img1d.reshape(responses[0].height, responses[0].width, 3)
            #img_rgb = cv.resize(img_rgb, (320, 240))  # resize smaller
            #image_filename = f"data/images/frame_{frame_idx:05d}_{timestamp}.png"
            #cv.imwrite(image_filename, img_rgb)
            #cv.imshow("Bottom Camera", img_rgb)

        frame_idx += 1

        if keyboard.is_pressed("esc"):
            print("ESC pressed. Exiting.")
            break

        if cv.waitKey(1) & 0xFF == ord('x'):
            print("'x' pressed in window. Exiting.")
            break

        time.sleep(0.05)

finally:
    print("Landing and closing connection...")
    client.landAsync().join()
    client.armDisarm(False)
    client.enableApiControl(False)
    cv.destroyAllWindows()
