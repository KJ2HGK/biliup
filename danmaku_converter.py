import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog
import os

# 修改后的 ASS 头部（关键：添加了正确的 Position 和对齐）
ASS_HEADER = '''[Script Info]
Title: Douyin Danmaku
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1280
PlayResY: 720
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Roll,Microsoft YaHei,25,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,0,0,7,10,10,10,1
Style: Top,Microsoft YaHei,25,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,0,0,8,10,10,10,1
Style: Bottom,Microsoft YaHei,25,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,0,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02}:{s:05.2f}"

def parse_color(color_str):
    color = int(color_str)
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return f"&H00{b:02X}{g:02X}{r:02X}&"  # ASS 使用 BGR 顺序，透明度 00

# 管理 Y 轴位置，避免重叠
class DanmakuScheduler:
    def __init__(self):
        self.layers = []  # 每层最后结束时间
        self.y_positions = []  # 每层对应的 Y 坐标

    def get_position(self, start, duration, height=30, margin=10):
        end = start + duration
        for i, layer_end in enumerate(self.layers):
            if start >= layer_end:
                self.layers[i] = end
                return self.y_positions[i]
        # 新增一层
        y = len(self.layers) * height + margin
        self.layers.append(end)
        self.y_positions.append(y)
        return y

def convert_xml_to_ass(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    base_name = os.path.splitext(xml_path)[0]
    ass_path = base_name + ".ass"

    scheduler = DanmakuScheduler()

    with open(ass_path, 'w', encoding='utf-8-sig') as f:
        f.write(ASS_HEADER)

        for d in root.findall('d'):
            p = d.get('p')
            if not p:
                continue
            params = p.split(',')
            if len(params) < 8:
                continue

            time_offset = float(params[0])
            mode = int(params[1])           # 1=滚动, 4=底部, 5=顶部
            fontsize = int(params[2])
            color = parse_color(params[3])
            text = d.text or ''
            if not text.strip():
                continue

            start = time_offset
            style = "Roll"

            if mode == 4:
                style = "Bottom"
                end = start + 4
            elif mode == 5:
                style = "Top"
                end = start + 4
            else:
                # 滚动弹幕：根据文本长度动态计算速度
                text_width = len(text) * fontsize * 0.6  # 估算宽度
                roll_duration = max(8, text_width / 100 * 2)  # 至少 8 秒，长文本更久
                end = start + roll_duration

                # 获取不重叠的 Y 坐标
                y = scheduler.get_position(start, roll_duration)
                x1, x2 = 1280, -text_width
                move_tag = f"{{\\move({x1},{y},{x2},{y})}}"
                text = f"{move_tag}{{\\fs{fontsize}}}{{\\c{color}}}{text}"
                f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},Roll,,0,0,0,,{text}\n")
                continue  # 跳过通用写入

            # 处理顶部/底部弹幕
            if mode == 5:
                text = f"{{\\an8}}{{\\fs{fontsize}}}{{\\c{color}}}{text}"
            else:
                text = f"{{\\an2}}{{\\fs{fontsize}}}{{\\c{color}}}{text}"

            f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},{style},,,0,0,0,,{text}\n")

    print(f"✅ 已生成弹幕文件: {ass_path}")

def main():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="选择抖音弹幕 XML 文件",
        filetypes=[("XML files", "*.xml")]
    )
    if file_path:
        convert_xml_to_ass(file_path)
    else:
        print("❌ 未选择文件")

if __name__ == "__main__":
    main()
