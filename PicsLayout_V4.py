import os
import math
from tkinter import Tk, filedialog, Button, Label, Entry, messagebox
from PIL import Image, ImageOps

# 提升 Pillow 的像素限制，允许处理非常大的图像
Image.MAX_IMAGE_PIXELS = None

def resample_image(image_path, output_path, max_size=4000):
    """重采样图片，使其长边为指定像素"""
    with Image.open(image_path) as img:
        width, height = img.size
        if width > height:
            new_width = max_size
            new_height = int((max_size / width) * height)
        else:
            new_height = max_size
            new_width = int((max_size / height) * width)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        img = img.convert('RGB')  # 转换为RGB格式
        img.save(output_path, 'JPEG', quality=95)  # 保存为8位JPEG

def add_border(image_path, output_path, border_size=4200):
    """等比例放大图片并添加白色边框，使其变为正方形（4200x4200）"""
    with Image.open(image_path) as img:
        img.thumbnail((border_size, border_size), Image.LANCZOS)  # 等比例缩放图片，使长边为4200
        # 计算边框大小以使图片居中
        delta_w = border_size - img.width
        delta_h = border_size - img.height
        border = (delta_w // 2, delta_h // 2)
        img_with_border = ImageOps.expand(img, border=border, fill='white')
        img_with_border = img_with_border.resize((border_size, border_size))
        img_with_border.save(output_path, 'JPEG', quality=95)  # 保存为8位JPEG

def create_collage(image_paths, output_path, border_size=4200):
    """创建正方形图片拼贴，不补全空白"""
    num_images = len(image_paths)
    # 计算需要的行和列数（不填充）
    grid_cols = math.ceil(math.sqrt(num_images))
    grid_rows = math.ceil(num_images / grid_cols)
    width, height = grid_cols * border_size, grid_rows * border_size

    collage = Image.new('RGB', (width, height), 'white')

    for index, image_path in enumerate(image_paths):
        row = index // grid_cols
        col = index % grid_cols
        with Image.open(image_path) as img:
            collage.paste(img, (col * border_size, row * border_size))

    collage.save(output_path, 'JPEG', quality=95)  # 保存为8位JPEG

def calculate_dynamic_border(grid_cols, min_border=200, max_border=1000):
    """根据拼图的列数动态计算边框大小"""
    # 长边图片数量为10时，边框为200像素，长边图片数量为2时，边框为1000像素
    if grid_cols >= 10:
        return min_border
    elif grid_cols <= 2:
        return max_border
    else:
        # 线性插值计算边框大小
        return int(min_border + (max_border - min_border) * (10 - grid_cols) / 8)

def add_final_border_and_resize(image_path, output_path, max_size=10000, border_size=200):
    """添加边框并调整拼贴图片的大小，使长边为10000像素"""
    with Image.open(image_path) as img:
        # 计算新的尺寸，使图片加上边框后的长边为10000像素
        width, height = img.size
        scale = (max_size - 2 * border_size) / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        img = img.resize((new_width, new_height), Image.LANCZOS)
        # 添加动态计算的白色边框
        img_with_border = ImageOps.expand(img, border=border_size, fill='white')
        img_with_border.save(output_path, 'JPEG', quality=95)

def process_images():
    """处理选中的图片并选择导出路径"""
    file_paths = filedialog.askopenfilenames(title='选择图片')
    if not file_paths:
        return

    # 限制选择图片的数量为 100
    if len(file_paths) > 100:
        messagebox.showerror("错误", "选择的图片数量不能超过 100 张。")
        return
    
    # 选择导出路径
    export_path = filedialog.askdirectory(title='选择导出路径')
    if not export_path:
        return
    
    # 获取导出的文件名前缀
    prefix = entry.get().strip()
    if not prefix:
        prefix = 'output'  # 默认前缀

    processed_images = []

    for image in file_paths:
        resampled_image = os.path.join(export_path, f"{prefix}_resampled_{os.path.basename(image)}")
        bordered_image = os.path.join(export_path, f"{prefix}_bordered_{os.path.basename(image)}")
        resample_image(image, resampled_image)
        add_border(resampled_image, bordered_image)
        processed_images.append(bordered_image)

    output_file = os.path.join(export_path, f"{prefix}_collage.jpg")
    create_collage(processed_images, output_file)

    # 动态计算最终输出图片的边框大小
    grid_cols = math.ceil(math.sqrt(len(processed_images)))
    dynamic_border_size = calculate_dynamic_border(grid_cols)
    final_output_file = os.path.join(export_path, f"{prefix}_collage_resampled_with_border.jpg")
    add_final_border_and_resize(output_file, final_output_file, border_size=dynamic_border_size)
    label.config(text=f"拼贴已成功创建: {final_output_file}")

# 创建 GUI
root = Tk()
root.title("图片排版工具")

label = Label(root, text="点击按钮选择图片进行处理")
label.pack(pady=10)

entry_label = Label(root, text="输出文件名前缀:")
entry_label.pack(pady=5)
entry = Entry(root)
entry.pack(pady=5)

button = Button(root, text="选择图片并处理", command=process_images)
button.pack(pady=20)

root.mainloop()
