import numpy as np
import trimesh
import json
import os
import gradio as gr
import tempfile

def place_obj(canvas, asset_obj, combined_scene, obj0_size=np.array([0, 0])):
    scene = asset_obj.load_glb_file()
    offset_x, offset_y = asset_obj.get_offset(obj0_size)
    for name, mesh in scene.geometry.items():
        # 使用单个缩放值创建缩放矩阵
        scale_matrix = trimesh.transformations.scale_matrix(
            asset_obj.scale,  # 直接使用单个缩放值
            [0, 0, 0]   # 缩放中心点
        )
        
        # 创建旋转矩阵（分别绕x、y、z轴旋转）
        rotation_x = trimesh.transformations.rotation_matrix(
            asset_obj.rotation[0], [1, 0, 0])
        rotation_y = trimesh.transformations.rotation_matrix(
            asset_obj.rotation[1], [0, 1, 0])
        rotation_z = trimesh.transformations.rotation_matrix(
            asset_obj.rotation[2], [0, 0, 1])
        
        # 创建平移矩阵（包含基础偏移和对象自身的平移）
        translation_matrix = trimesh.transformations.translation_matrix([
            asset_obj.translation[0]+offset_x,
            asset_obj.translation[1],
            asset_obj.translation[2]+offset_y
        ])
        
        # 组合所有变换矩阵（顺序：先缩放，再旋转，最后平移）
        transform = trimesh.transformations.concatenate_matrices(
            translation_matrix,
            rotation_z,
            rotation_y,
            rotation_x,
            scale_matrix
        )
        
        combined_scene.add_geometry(mesh, transform=transform)
    return combined_scene

def merge_glb_files(canvas):
    """
    合并多个GLB文件到同一个场景中，考虑每个对象的独立变换参数
    
    参数:
        asset_objects: AssetObject对象列表
    返回:
        combined_scene: 合并后的场景
    """

    combined_scene = trimesh.Scene()

    obj_dict = canvas.objects
    obj0 = None
    obj0_size = np.array([0, 0])
    if '(1, 1)' in obj_dict.keys():
        obj0 = obj_dict['(1, 1)']
        combined_scene = place_obj(combined_scene, obj0, combined_scene)
        obj0_size = obj0.get_mesh_size_scale()
    for key, value in obj_dict.items():
        combined_scene = place_obj(combined_scene, value, combined_scene, obj0_size)
    # for obj in canvas.objects.values():
    #     print(f"\n处理文件: {obj.get_path()}")
    #     scene = obj.load_glb_file()
        

    #     if scene is None:
    #         continue
            
    #     for name, mesh in scene.geometry.items():
    #         # 使用单个缩放值创建缩放矩阵
    #         scale_matrix = trimesh.transformations.scale_matrix(
    #             obj.scale,  # 直接使用单个缩放值
    #             [0, 0, 0]   # 缩放中心点
    #         )
            
    #         # 创建旋转矩阵（分别绕x、y、z轴旋转）
    #         rotation_x = trimesh.transformations.rotation_matrix(
    #             obj.rotation[0], [1, 0, 0])
    #         rotation_y = trimesh.transformations.rotation_matrix(
    #             obj.rotation[1], [0, 1, 0])
    #         rotation_z = trimesh.transformations.rotation_matrix(
    #             obj.rotation[2], [0, 0, 1])
            
    #         # 创建平移矩阵（包含基础偏移和对象自身的平移）
    #         translation_matrix = trimesh.transformations.translation_matrix([
    #             obj.translation[0],
    #             obj.translation[1],
    #             obj.translation[2]
    #         ])
            
    #         # 组合所有变换矩阵（顺序：先缩放，再旋转，最后平移）
    #         transform = trimesh.transformations.concatenate_matrices(
    #             translation_matrix,
    #             rotation_z,
    #             rotation_y,
    #             rotation_x,
    #             scale_matrix
    #         )
            
    #         combined_scene.add_geometry(mesh, transform=transform)
        
    
    return combined_scene

def load_and_render(canvas):

    combined_scene = merge_glb_files(canvas)
    return combined_scene




