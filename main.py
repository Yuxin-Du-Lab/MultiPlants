import os
import json
from canvas_manage import load_and_render
from assets_objects import AssetObject
from volcenginesdkarkruntime import Ark
import numpy as np
import gradio as gr
import tempfile

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
os.environ["ARK_API_KEY"] = "877c4dba-19fe-4246-928d-385146f9890d"

# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
    api_key=os.environ.get("ARK_API_KEY"),
)

class Canvas:
    def __init__(self, width=3, height=3, assets_json_paths=[]):
        self.width = width
        self.height = height
        self.canvas = np.ones((height, width)) * -1
        self.objects = {}
        self.assets_id2path = {}
        for asset_json_path in assets_json_paths:
            with open(asset_json_path, "r") as f:
                asset_info = json.load(f)
                self.assets_id2path[asset_info["id"]] = asset_json_path
        self.base_obj = None

    def add_asset(self, coor, asset_id):
        if asset_id == -1:
            self.delete_asset(coor)
            return
        new_key = len(self.objects.keys())
        # new asset object
        json_path = self.map_assets_id2path_json(asset_id)
        glb_path = json_path.replace('.json', '.glb')
        asset_object = AssetObject(glb_path)
        asset_object.set_canvas_key(new_key)
        asset_object.set_canvas_coor(coor)

        self.objects[str(coor)] = asset_object
        self.canvas[coor] = new_key
    
    def set_base_obj(self, asset_id):
        json_path = self.map_assets_id2path_json(asset_id)
        glb_path = json_path.replace('.json', '.glb')
        self.base_obj = AssetObject(glb_path)

    def delete_asset(self, coor):
        if str(coor) in self.objects.keys():
            self.objects.pop(str(coor))
            self.canvas[coor] = -1
        else:
            print(f"Warning: {coor} 位置没有元素")
        
    def get_canvas(self):
        return self.canvas
    
    def get_canvas_str(self):
        if len(self.objects) == 0:
            return "空。\n"

        canvas_str = ""
        for coor, obj in self.objects.items():
            canvas_str += str(coor) +';'+ str(obj.get_id()) + '\n'
        return canvas_str
    
    def map_assets_id2path_json(self, asset_id):
        return self.assets_id2path[asset_id]

    


def get_assets():
    assets_root = "/hpc2hdd/home/ydu709/code/RBM/assets"
    assets_paths = [os.path.join(assets_root, f) for f in os.listdir(assets_root) if f.endswith(".json")]
    #print(assets_paths)
    list_assets_info = []
    for asset_path in assets_paths:
        with open(asset_path, "r") as f:
            asset_info = json.load(f)
            list_assets_info.append(str(asset_info))
    # 将所有资产信息拼接成一个字符串
    assets_info_str = "; ".join(list_assets_info)
    
    return assets_info_str, assets_paths
    
def parse_assistant_output(assistant_system_output):
    elements = assistant_system_output.split("\n") 
    for element in elements:
        coor, asset_id = element.split(";")
        coor = coor.strip("()")
        coor = tuple(map(int, coor.split(",")))
        asset_id = int(asset_id)
        canvas.add_asset(coor, asset_id)
    
        
assets_info_str, assets_json_paths = get_assets()
system_prompt = "你是人工智能助手, 现在请你扮演一个盆景设计师，请你在一个俯视的3*3格子大小的画布上放置assets（用id代表该asset被放置在该格子中），下面是你可用的assets信息：" + assets_info_str
system_prompt += "\n请根据用户的需求，把这些assets放置在这个3*3的画布上，要求自然、协调、美观、合理。"
system_prompt += "\n每次放置新的元素时，从(0,0)开始，按行输出新元素索引和新元素的id，按如下模板进行打印，除此之外严禁有其他的输出，请在下面模板的三个{}中按顺序填入横坐标、纵坐标、新元素的id：({},{});{}"
system_prompt += "\n当你被要求修改画布中的元素时，请依然按照模板({},{});{}分行输出新元素的索引和新元素的id。如果用户要求删除元素，请输出({},{});-1"
# 创建一个列表来存储对话历史
messages_history = [
    {"role": "system", "content": system_prompt}
]
canvas = Canvas(assets_json_paths=assets_json_paths)
canvas.set_base_obj(1)

def chat_with_ai(user_input):
    # 将用户输入添加到对话历史
    messages_history.append({"role": "user", "content": user_input})
    
    # 发送包含完整对话历史的请求
    completion = client.chat.completions.create(
        model="doubao-1-5-pro-32k-250115",
        messages=messages_history
    )
    
    # 获取AI回复并添加到对话历史
    ai_response = completion.choices[0].message.content
    messages_history.append({"role": "assistant", "content": ai_response})
    
    return ai_response

def create_gradio_interface(canvas):
    """
    创建Gradio界面，集成3D场景展示和聊天功能
    """
    def chat_and_update(message, history):
        # 调用现有的chat_with_ai函数获取响应
        canvas_str = canvas.get_canvas_str()
        message = "当前画布状态：" + canvas_str + message
        response = chat_with_ai(message)
        print("AI助手:", response)
        # 解析响应并更新画布
        parse_assistant_output(response)
        if len(canvas.objects) == 0:
            return history, None, gr.update(visible=False)
        # 导出更新后的场景
        scene_file = export_scene()
        # 更新对话历史和3D模型显示
        history = history + [(message, response)]
        return history, scene_file, gr.update(visible=True)
    
    def export_scene():
        combined_scene = load_and_render(canvas)
        temp_file = tempfile.NamedTemporaryFile(suffix='.glb', delete=False)
        combined_scene.export(temp_file.name)
        return temp_file.name

    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column(scale=1):
                    chatbot = gr.Chatbot(label="对话历史")
                    msg = gr.Textbox(label="输入信息", interactive=True)
                    submit_btn = gr.Button("提交")
            
            with gr.Column(scale=2):
                gr.Markdown("# 3D模型展示")
                model_3d = gr.Model3D(
                    clear_color=[0.0, 0.0, 0.0, 0.0],
                    camera_position=[5, 5, 5],
                    value=None,
                    visible=False  # 初始设置为不可见
                )

        # 同时绑定文本框的submit事件和按钮的点击事件
        msg.submit(
            chat_and_update,
            [msg, chatbot],
            [chatbot, model_3d, model_3d]
        )
        submit_btn.click(
            chat_and_update,
            [msg, chatbot],
            [chatbot, model_3d, model_3d]
        )


    demo.launch(share=True)

if __name__ == "__main__":
    create_gradio_interface(canvas)

# 请你创建一个自然风光的盆景，有两棵树和一些草，没有其他元素