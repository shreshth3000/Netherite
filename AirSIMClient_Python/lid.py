import airsim
import numpy as np
import cv2 as cv
import time

client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True, "Drone1")
client.armDisarm(True, "Drone1")

print("Taking off...")
client.takeoffAsync(vehicle_name="Drone1").join()
client.moveToZAsync(-5, 2, vehicle_name="Drone1").join()  


waypoints=[
  (-17, -3, -5), (-17, -1, -5), (-17, 1, -5), (-17, 3, -5),
  (-15, 3, -5), (-15, 1, -5), (-15, -1, -5), (-15, -3, -5),
  (-13, -3, -5), (-13, -1, -5), (-13, 1, -5), (-13, 3, -5),

  (-14, 0, -5), (-14, 2, -5), (-14, -2, -5),

  (-11, -3, -5), (-11, -1, -5), (-11, 1, -5), (-11, 3, -5),
  (-9, 3, -5), (-9, 1, -5), (-9, -1, -5), (-9, -3, -5),
  (-7, -3, -5), (-7, -1, -5), (-7, 1, -5), (-7, 3, -5),

  (-8, 2, -5), (-8, 0, -5), (-8, -2, -5),

  (-3, -3, -5), (-3, -1, -5), (-3, 1, -5), (-3, 3, -5),+
  (0, 3, -5), (0, 1, -5), (0, -1, -5), (0, -3, -5),
  (3, -3, -5), (3, -1, -5), (3, 1, -5), (3, 3, -5),

  (4, 2, -5), (4, 0, -5), (4, -2, -5),

  (7, -3, -5), (7, -1, -5), (7, 1, -5), (7, 3, -5),

  (11, 2, -5), (11, 0, -5), (11, -2, -5),

  (15, -3, -5), (15, -1, -5), (15, 1, -5), (15, 3, -5),
  (17, 3, -5), (17, 1, -5), (17, -1, -5), (17, -3, -5)
]


for wp in waypoints:
    print(f"Flying to {wp}...")
    client.moveToPositionAsync(wp[0], wp[1], wp[2], velocity=3, vehicle_name="Drone1").join()

    for _ in range(10):  
        lidarData = client.getLidarData("Lidar1", "Drone1")
        if len(lidarData.point_cloud) >= 3:
            pts = np.array(lidarData.point_cloud, dtype=np.float32).reshape(-1, 3)
            img = np.zeros((500, 500, 3), dtype=np.uint8)
            for x, y, z in pts:
                xi = int(250 + x * 5) % 500
                yi = int(250 + y * 5) % 500
                img[yi, xi] = (255, 255, 255)
            cv.imshow("LiDAR Feed (2D)", img)

        responses = client.simGetImages([
            airsim.ImageRequest("BottomCamera", airsim.ImageType.Scene, False, False)
        ], vehicle_name="Drone1")
        if responses and responses[0].width != 0:
            img1d = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
            img_rgb = img1d.reshape(responses[0].height, responses[0].width, 3)
            img_small = cv.resize(img_rgb, (320, 240))
            cv.imshow("Bottom Camera", img_small)

        if cv.waitKey(1) & 0xFF == 27: 
            break
        time.sleep(0.1)


print("Landing...")
client.landAsync(vehicle_name="Drone1").join()
client.armDisarm(False, "Drone1")
client.enableApiControl(False, "Drone1")
cv.destroyAllWindows()
