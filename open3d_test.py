import open3d as o3d
from constants import *


pcd = o3d.io.read_point_cloud(OUTPUT_DIR + "pc.xyzrgb")

o3d.visualization.draw_geometries([pcd])

