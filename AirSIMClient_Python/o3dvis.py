import open3d as o3d
import numpy as np
import os
import time
from glob import glob

lidar_folder = "data/lidar"
refresh_secs = 0.5

def load_xyz_file(path):
    pts = np.loadtxt(path)
    pc = o3d.geometry.PointCloud()
    pc.points = o3d.utility.Vector3dVector(pts)
    return pc

def merge_clouds(filelist):
    pcs = [load_xyz_file(f) for f in filelist]
    if not pcs:
        return None
    merged = pcs[0]
    for pc in pcs[1:]:
        merged += pc
    return merged

vis = o3d.visualization.VisualizerWithKeyCallback()
vis.create_window("Live Digital Twin", width=625, height=625)
render_option = vis.get_render_option()
render_option.point_size = 1.0  

geom = None
prev_files = set()
should_quit = [False]

def stop(vis):
    print("Q pressed, quitting visualizer.")
    should_quit[0] = True
    return False

vis.register_key_callback(ord('q'), stop)
vis.register_key_callback(ord('Q'), stop)

print("Manipulation tips:")
print("- Use LEFT mouse to rotate")
print("- Hold SHIFT + LEFT mouse or use RIGHT mouse to pan")
print("- Mouse wheel to zoom")
print("- Press Q to quit the viewer")

while not should_quit[0]:
    filelist = sorted(glob(os.path.join(lidar_folder, "*.xyz")))
    if set(filelist) != prev_files:
        pc = merge_clouds(filelist)
        if pc:
            if geom:
                vis.remove_geometry(geom)
            geom = pc
            vis.add_geometry(geom)
            vis.get_view_control().set_lookat(pc.get_center())
            vis.get_view_control().set_zoom(0.7)  
        prev_files = set(filelist)
    vis.poll_events()
    vis.update_renderer()
    time.sleep(refresh_secs)

vis.destroy_window()
