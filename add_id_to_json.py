import json
import os

def add_id_to_json_files(directory):
    # 获取所有json文件并按名称排序
    json_files = sorted([f for f in os.listdir(directory) if f.endswith('.json')])
    
    # 为每个文件添加id
    for index, filename in enumerate(json_files, start=1):
        file_path = os.path.join(directory, filename)
        
        # 读取json文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 添加id属性
        data['id'] = index
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f'已处理文件 {filename}，添加id: {index}')

# 执行脚本
add_id_to_json_files('./assets') 