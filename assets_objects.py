import json
import trimesh
import numpy as np
import os

# -1.57079633

class AssetObject:
    def __init__(self, glb_path):
        self.glb_path = glb_path
        self.json_path = glb_path.replace('.glb', '.json')
        self.config = json.load(open(self.json_path))
        # 将scale简化为单个值
        
        self.rotation = [0.0, 0.0, 0.0]  # 绕x, y, z轴的旋转（弧度）
        self.translation = [0.0, 0.0, 0.0]  # x, y, z平移
        self.scene = None
        self.canvas_key = None
        self.canvas_coor = None
        self.offset = [0.0, 0.0]
        self.base_size = 1.0
        self.scale = self.base_size / max(self.get_mesh_size())
        self.init_transform()

    def set_canvas_key(self, canvas_key):
        self.canvas_key = canvas_key
    
    def set_canvas_coor(self, canvas_coor):
        self.canvas_coor = canvas_coor

    def load_glb_file(self):

        if self.scene is None:
            print(f"Loading GLB file: {self.glb_path}")
            self.scene = trimesh.load(self.glb_path)

        return self.scene

    def init_transform(self):
        if 'rotation' in self.config:
            self.set_rotation(self.config['rotation'])

        if 'translation' in self.config:
            scaled_translation = [x * self.scale for x in self.config['translation']]
            self.set_translation(scaled_translation)
    
    def get_mesh_size(self):
        # 打印场景中每个mesh的尺寸
        if self.scene is None:
            self.load_glb_file()
        print("场景中mesh的尺寸信息:")
        sizes = []
        for name, mesh in self.scene.geometry.items():
            bounds = mesh.bounds
            size = bounds[1] - bounds[0]  # 最大边界减去最小边界得到尺寸
            print(f"Mesh '{name}' 的尺寸: {size}")
            sizes.append(size)

        # 计算每个size数组中x和y的乘积（忽略z轴）
        volumes = [size[0] * size[1] for size in sizes]
        # 返回乘积最大的size数组的x和y值
        max_size = sizes[np.argmax(volumes)]
        return np.array(max_size[:2])  # 只返回x和y值
    
    def get_mesh_size_scale(self):
        return self.get_mesh_size() * self.scale

    def get_offset(self, obj0_size=np.array([0, 0])):
        return np.array([0, 0])
        # 现在get_mesh_size()只返回x和y值
        x, y = self.get_mesh_size_scale() / 2
        x_base, y_base = obj0_size / 2
        offset = np.array([0, 0])
        if self.canvas_coor == (1, 1):
            offset = np.array([0, 0])
        elif self.canvas_coor == (1, 2):
            offset = np.array([0, y_base+y])
        elif self.canvas_coor == (2, 1):
            offset = np.array([x_base+x, 0])
        elif self.canvas_coor == (2, 2):
            offset = np.array([x_base+x, y_base+y])
        elif self.canvas_coor == (0, 0):
            offset = -np.array([x_base+x, y_base+y])
        elif self.canvas_coor == (0, 1):
            offset = -np.array([x_base+x, 0])
        elif self.canvas_coor == (1, 0):
            offset = -np.array([0, y_base+y])
        elif self.canvas_coor == (0, 2):
            offset = np.array([-(x_base+x), y_base+y])
        elif self.canvas_coor == (2, 0):
            offset = np.array([x_base+x, -(y_base+y)])
        else:
            raise ValueError(f"Invalid canvas coordinate: {self.canvas_coor}")
        return offset

    def get_id(self):
        return self.config['id']

    def get_path(self):
        return self.glb_path

    def set_scale(self, scale):
        # 现在scale是一个数值而不是列表
        self.scale = scale

    def set_rotation(self, rotation):
        self.rotation = rotation

    def set_translation(self, translation):
        self.translation = translation

if __name__ == "__main__":
    asset_root = "/hpc2hdd/home/ydu709/code/RBM/assets"
    assets_glb_paths = [os.path.join(asset_root, f) for f in os.listdir(asset_root) if f.endswith('.glb')]
    for asset_glb_path in assets_glb_paths:
        asset_object = AssetObject(asset_glb_path)
        asset_object.load_glb_file()
        print(asset_object.get_mesh_size_scale())