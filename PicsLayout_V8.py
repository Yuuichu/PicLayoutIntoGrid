import os
import math
from tkinter import Tk, filedialog, Button, Label, Entry, messagebox, StringVar, Frame, Scale, IntVar, Checkbutton, OptionMenu
from PIL import Image, ImageOps, ImageFile
import traceback
from tkinter.ttk import Progressbar, Notebook, Frame as TkFrame
import tempfile
import shutil
import concurrent.futures
import threading

# 设置PIL的块大小限制，减少内存占用
ImageFile.MAXBLOCK = 2 * 1024 * 1024  # 设置为2MB

# 提升 Pillow 的像素限制，允许处理非常大的图像
Image.MAX_IMAGE_PIXELS = None

# 全局变量存储水印图片路径
watermark_path = None

# 更新颜色预览函数
def update_color_preview(*args):
    """更新颜色预览框的背景色"""
    selected_color = color_var.get()
    color_preview.config(bg=selected_color)

# 选择水印图片函数
def select_watermark():
    """选择水印图片"""
    global watermark_path
    
    file_path = filedialog.askopenfilename(title='选择水印图片', 
                                          filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
    if not file_path:
        return
    
    watermark_path = file_path
    watermark_file_label.config(text=f"已选择: {os.path.basename(watermark_path)}")
    
    # 检查并提示
    if not watermark_path.lower().endswith('.png'):
        messagebox.showinfo("提示", "建议使用PNG格式的图片作为水印，以获得更好的透明效果。")

# 添加水印函数
def add_watermark(image_path, output_path, watermark_img_path, scale_percent=100, position_y_percent=95, position_x_percent=50):
    """
    给图片添加水印
    
    参数:
    - image_path: 原始图片路径
    - output_path: 输出图片路径
    - watermark_img_path: 水印图片路径
    - scale_percent: 水印缩放比例，默认100%
    - position_y_percent: 水印中心的垂直位置（图片高度的百分比），默认95%
    - position_x_percent: 水印中心的水平位置（图片宽度的百分比），默认50%（居中）
    """
    try:
        # 打开原始图片和水印图片
        with Image.open(image_path) as img, Image.open(watermark_img_path) as watermark:
            # 获取原始图片尺寸
            img_width, img_height = img.size
            
            # 水印缩放
            scale_factor = scale_percent / 100.0
            watermark_width = int(watermark.width * scale_factor)
            watermark_height = int(watermark.height * scale_factor)
            watermark = watermark.resize((watermark_width, watermark_height), Image.LANCZOS)
            
            # 计算水印位置（根据水平和垂直百分比）
            x = int((img_width * position_x_percent / 100) - (watermark_width / 2))
            y = int((img_height * position_y_percent / 100) - (watermark_height / 2))
            
            # 如果水印有透明通道，需要正确处理
            if watermark.mode in ('RGBA', 'LA') or (watermark.mode == 'P' and 'transparency' in watermark.info):
                # 创建一个与原图相同大小的透明图层
                watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                watermark_layer.paste(watermark, (x, y), watermark)
                
                # 如果原图没有透明通道，转换为RGBA
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 合并图层
                img = Image.alpha_composite(img, watermark_layer)
                img = img.convert('RGB')  # 转回RGB用于保存JPG
            else:
                # 如果水印没有透明通道，直接粘贴
                img.paste(watermark, (x, y))
            
            # 获取DPI设置
            dpi_value = int(dpi_var.get())
            
            # 保存结果
            img.save(output_path, 'JPEG', quality=95, optimize=True, dpi=(dpi_value, dpi_value))
            return True
    except Exception as e:
        error_msg = f"添加水印时出错: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return False

def resample_image(image_path, output_path, max_size=4000, status_var=None):
    """重采样图片，使其长边为指定像素"""
    try:
        # 尝试打开图片
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
            
            # 获取DPI设置
            dpi_value = int(dpi_var.get())
            
            img.save(output_path, 'JPEG', quality=95, optimize=True, dpi=(dpi_value, dpi_value))  # 使用设置的DPI值
            return True
    except Exception as e:
        # 捕获并显示错误信息
        error_msg = f"处理图片时出错: {os.path.basename(image_path)}\n错误: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return False

def add_border(image_path, output_path, border_size=4200, background_color='white', status_var=None):
    """等比例放大图片并添加自定义颜色边框，使其变为正方形"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail((border_size, border_size), Image.LANCZOS)  # 等比例缩放图片，使长边为设定值
            
            # 计算边框大小以使图片居中
            delta_w = border_size - img.width
            delta_h = border_size - img.height
            border = (delta_w // 2, delta_h // 2)
            
            img_with_border = ImageOps.expand(img, border=border, fill=background_color)
            img_with_border = img_with_border.resize((border_size, border_size))
            
            # 获取DPI设置
            dpi_value = int(dpi_var.get())
            
            img_with_border.save(output_path, 'JPEG', quality=95, optimize=True, dpi=(dpi_value, dpi_value))
            return True
    except Exception as e:
        error_msg = f"添加边框时出错: {os.path.basename(image_path)}\n错误: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return False

def process_single_image(image_path, temp_dir, resampling_size, border_size, background_color):
    """处理单张图片，包括重采样和添加边框"""
    try:
        # 处理当前图片到临时目录
        resampled_image = os.path.join(temp_dir, f"resampled_{os.path.basename(image_path)}")
        bordered_image = os.path.join(temp_dir, f"bordered_{os.path.basename(image_path)}")
        
        # 调用改进的函数并检查是否成功
        if resample_image(image_path, resampled_image, max_size=resampling_size):
            if add_border(resampled_image, bordered_image, border_size=border_size, background_color=background_color):
                return bordered_image
    except Exception as e:
        print(f"处理图片时出错: {os.path.basename(image_path)}\n错误: {str(e)}")
        print(traceback.format_exc())
    return None

def create_collage(image_paths, output_path, border_size=4200, background_color='white', status_var=None, chunk_size=2):
    """
    创建正方形图片拼贴，不补全空白，使用分块处理减少内存占用
    
    参数:
    - image_paths: 图像路径列表
    - output_path: 输出路径
    - border_size: 每个图像的边长
    - background_color: 背景颜色
    - status_var: 状态显示变量
    - chunk_size: 每次处理的图像行数
    """
    try:
        num_images = len(image_paths)
        if status_var:
            status_var.set(f"准备创建拼贴图 (共{num_images}张图片)...")
            root.update()
        
        # 计算需要的行和列数
        grid_cols = math.ceil(math.sqrt(num_images))
        grid_rows = math.ceil(num_images / grid_cols)
        width, height = grid_cols * border_size, grid_rows * border_size
        
        # 创建临时文件来存储中间结果
        temp_files = []
        
        # 按行分块处理
        for start_row in range(0, grid_rows, chunk_size):
            if status_var:
                status_var.set(f"正在处理第 {start_row+1}-{min(start_row+chunk_size, grid_rows)} 行 (共{grid_rows}行)...")
                root.update()
            
            # 计算当前块的行数
            end_row = min(start_row + chunk_size, grid_rows)
            current_rows = end_row - start_row
            
            # 创建当前块的画布
            chunk_height = current_rows * border_size
            chunk = Image.new('RGB', (width, chunk_height), background_color)
            
            # 填充当前块的图像
            for row_offset in range(current_rows):
                row = start_row + row_offset
                for col in range(grid_cols):
                    index = row * grid_cols + col
                    if index < num_images:  # 确保索引在有效范围内
                        if status_var:
                            status_var.set(f"正在处理图片 {index+1}/{num_images}...")
                            root.update()
                        try:
                            with Image.open(image_paths[index]) as img:
                                chunk.paste(img, (col * border_size, row_offset * border_size))
                        except Exception as e:
                            print(f"无法打开图片 {image_paths[index]}: {e}")
                            # 在错误位置放置背景色图像
                            blank = Image.new('RGB', (border_size, border_size), background_color)
                            chunk.paste(blank, (col * border_size, row_offset * border_size))
            
            # 保存当前块到临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_files.append(temp_file.name)
            
            # 获取DPI设置
            dpi_value = int(dpi_var.get())
            
            chunk.save(temp_file.name, 'JPEG', quality=95, optimize=True, dpi=(dpi_value, dpi_value))
            temp_file.close()
            
            # 释放内存
            del chunk
        
        # 如果只有一个临时文件，直接重命名为输出文件
        if len(temp_files) == 1:
            if status_var:
                status_var.set("正在保存最终拼贴图...")
                root.update()
            os.replace(temp_files[0], output_path)
        else:
            # 否则需要拼接所有临时文件
            if status_var:
                status_var.set("正在合并所有图像块...")
                root.update()
                
            # 创建最终输出图像
            with Image.new('RGB', (width, height), background_color) as final_collage:
                y_offset = 0
                for i, temp_file in enumerate(temp_files):
                    if status_var:
                        status_var.set(f"正在合并图像块 {i+1}/{len(temp_files)}...")
                        root.update()
                    
                    with Image.open(temp_file) as img:
                        final_collage.paste(img, (0, y_offset))
                        y_offset += img.height
                
                if status_var:
                    status_var.set("正在保存最终拼贴图...")
                    root.update()
                
                # 使用低内存模式保存
                dpi_value = int(dpi_var.get())
                final_collage.save(output_path, 'JPEG', quality=95, optimize=True, dpi=(dpi_value, dpi_value))
        
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass  # 忽略删除临时文件的错误
        
        return True
    except Exception as e:
        error_msg = f"创建拼贴图时出错: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return False

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

def add_final_border_and_resize(image_path, output_path, max_size=10000, border_size=200, background_color='white', status_var=None):
    """添加边框并调整拼贴图片的大小，使长边为10000像素"""
    try:
        if status_var:
            status_var.set(f"正在处理最终图像调整...")
            root.update()
            
        with Image.open(image_path) as img:
            # 计算新的尺寸，使图片加上边框后的长边为10000像素
            width, height = img.size
            scale = (max_size - 2 * border_size) / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)

            if status_var:
                status_var.set(f"正在调整图像大小...")
                root.update()
                
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            if status_var:
                status_var.set(f"正在添加边框...")
                root.update()
                
            # 添加动态计算的边框
            img_with_border = ImageOps.expand(img, border=border_size, fill=background_color)
            
            if status_var:
                status_var.set(f"正在保存最终图像...")
                root.update()
                
            # 获取DPI设置
            dpi_value = int(dpi_var.get())
            
            img_with_border.save(output_path, 'JPEG', quality=95, optimize=True, dpi=(dpi_value, dpi_value))
            return True
    except Exception as e:
        error_msg = f"处理最终图像时出错: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return False

def update_progress(progress_bar, progress_var, status_var, current, total, message=None):
    """更新进度条和状态信息"""
    progress_var.set(int((current / total) * 100))
    if message:
        status_var.set(message)
    root.update_idletasks()

def select_images():
    """选择图片并显示已选择的数量"""
    global selected_files
    
    file_paths = filedialog.askopenfilenames(title='选择图片', 
                                            filetypes=[("图片文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")])
    if not file_paths:
        return
    
    # 获取用户设置
    max_images = int(max_images_var.get())
    
    # 限制选择图片的数量
    if len(file_paths) > max_images:
        messagebox.showerror("错误", f"选择的图片数量不能超过 {max_images} 张。")
        return
    
    # 存储选择的文件路径
    selected_files = file_paths
    
    # 更新状态显示
    file_count_label.config(text=f"已选择 {len(selected_files)} 张图片")
    
    # 启用开始拼接按钮
    start_button.config(state="normal")

def process_images():
    """处理选中的图片并选择导出路径"""
    global selected_files, watermark_path
    
    if not selected_files or len(selected_files) == 0:
        messagebox.showerror("错误", "请先选择图片")
        return
    
    # 创建临时目录用于存储中间文件
    temp_dir = tempfile.mkdtemp(prefix="pic_layout_")
    
    # 选择导出路径
    export_path = filedialog.askdirectory(title='选择导出路径')
    if not export_path:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return
    
    # 获取导出的文件名前缀
    prefix = entry.get().strip()
    if not prefix:
        prefix = 'output'  # 默认前缀

    # 获取用户设置
    resampling_size = int(resampling_size_var.get())
    border_size = int(border_size_var.get())
    final_size = int(final_size_var.get())
    background_color = color_var.get()
    
    # 获取水印设置
    use_watermark = watermark_var.get()
    watermark_scale = int(watermark_scale_var.get())
    watermark_position_y = float(watermark_position_y_var.get())
    watermark_position_x = float(watermark_position_x_var.get())

    # 创建状态变量和进度条
    status_var = StringVar()
    progress_var = IntVar()
    
    # 创建一个框架来包含状态标签和进度条，便于后续移除
    status_frame = Frame(tab1)
    status_frame.pack(pady=5)
    
    status_label = Label(status_frame, textvariable=status_var)
    status_label.pack(pady=5)
    
    progress = Progressbar(status_frame, orient="horizontal", length=300, mode="determinate", variable=progress_var)
    progress.pack(pady=10)
    root.update()

    # 禁用按钮，防止重复点击
    select_button.config(state="disabled")
    start_button.config(state="disabled")
    status_var.set("正在处理图片...")
    
    # 使用线程池并行处理图片
    processed_images = []
    failed_images = []
    
    try:
        # 创建一个线程来处理图片，避免UI卡死
        def processing_thread():
            nonlocal processed_images, failed_images
            
            # 设置线程池中的工作线程数量
            max_workers = min(8, os.cpu_count() or 4)  # 使用CPU核心数，但最多8个
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 创建处理任务
                future_to_image = {
                    executor.submit(
                        process_single_image, 
                        image, 
                        temp_dir, 
                        resampling_size, 
                        border_size, 
                        background_color
                    ): image for image in selected_files
                }
                
                # 收集处理结果
                for i, future in enumerate(concurrent.futures.as_completed(future_to_image)):
                    image = future_to_image[future]
                    try:
                        result = future.result()
                        if result:
                            processed_images.append(result)
                        else:
                            failed_images.append(os.path.basename(image))
                    except Exception as e:
                        failed_images.append(os.path.basename(image))
                        print(f"处理图片时出错: {os.path.basename(image)}\n错误: {str(e)}")
                        print(traceback.format_exc())
                    
                    # 更新进度
                    update_progress(
                        progress, 
                        progress_var, 
                        status_var, 
                        i + 1, 
                        len(selected_files), 
                        f"处理进度: {i+1}/{len(selected_files)}"
                    )
            
            # 检查是否有成功处理的图片
            if len(processed_images) == 0:
                status_var.set("处理失败：没有成功处理任何图片")
                messagebox.showerror("处理错误", "没有成功处理任何图片")
                select_button.config(state="normal")
                start_button.config(state="disabled")
                status_frame.destroy()
                shutil.rmtree(temp_dir, ignore_errors=True)
                return
            
            status_var.set(f"正在创建拼贴图 ({len(processed_images)}/{len(selected_files)} 张图片处理成功)")
                
            try:
                # 设置临时拼贴图文件和最终输出文件
                temp_collage_file = os.path.join(temp_dir, "temp_collage.jpg")
                output_file = os.path.join(export_path, f"{prefix}_collage.jpg")
                final_output_file = os.path.join(export_path, f"{prefix}_collage_final.jpg")
                final_watermarked_file = os.path.join(export_path, f"{prefix}_collage_final_watermarked.jpg")
                
                # 使用状态变量调用改进后的create_collage函数
                if not create_collage(
                    processed_images, 
                    temp_collage_file, 
                    border_size=border_size, 
                    background_color=background_color,
                    status_var=status_var
                ):
                    messagebox.showerror("处理错误", "创建拼贴图失败")
                    select_button.config(state="normal")
                    start_button.config(state="disabled")
                    status_frame.destroy()
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return

                # 将临时拼贴图复制到输出目录
                shutil.copy2(temp_collage_file, output_file)

                # 动态计算最终输出图片的边框大小
                grid_cols = math.ceil(math.sqrt(len(processed_images)))
                dynamic_border_size = calculate_dynamic_border(grid_cols)
                
                # 添加边框并调整大小
                if not add_final_border_and_resize(
                    output_file, 
                    final_output_file, 
                    max_size=final_size, 
                    border_size=dynamic_border_size, 
                    background_color=background_color,
                    status_var=status_var
                ):
                    messagebox.showerror("处理错误", "添加最终边框失败")
                    select_button.config(state="normal")
                    start_button.config(state="disabled")
                    status_frame.destroy()
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return
                
                # 最终输出文件路径
                result_file = final_output_file
                
                # 如果启用水印且已选择水印图片，则添加水印
                if use_watermark and watermark_path:
                    status_var.set("正在添加水印...")
                    if add_watermark(
                        final_output_file,
                        final_watermarked_file,
                        watermark_path,
                        scale_percent=watermark_scale,
                        position_y_percent=watermark_position_y,
                        position_x_percent=watermark_position_x
                    ):
                        result_file = final_watermarked_file
                        status_var.set("水印添加成功")
                    else:
                        messagebox.showwarning("水印添加警告", "添加水印时出错，将使用无水印版本")
                        
                # 显示处理结果
                success_message = f"拼贴已成功创建: {os.path.basename(result_file)}"
                if failed_images:
                    success_message += f"\n处理失败的图片: {len(failed_images)}/{len(selected_files)}"
                
                status_var.set(success_message)
                result_label.config(text=f"拼贴已成功创建: {result_file}")
                messagebox.showinfo("处理完成", success_message)
                
            except Exception as e:
                error_msg = f"创建拼贴图时出错: {str(e)}"
                print(error_msg)
                print(traceback.format_exc())
                status_var.set(error_msg)
                messagebox.showerror("处理错误", error_msg)
            
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # 恢复按钮状态
            select_button.config(state="normal")
            start_button.config(state="disabled")
            
            # 清空已选择文件
            file_count_label.config(text="未选择图片")
            
            # 移除状态框架
            status_frame.destroy()
        
        # 启动处理线程
        threading.Thread(target=processing_thread, daemon=True).start()
        
    except Exception as e:
        error_msg = f"处理图片时出错: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        status_var.set(error_msg)
        messagebox.showerror("处理错误", error_msg)
        
        # 恢复按钮状态
        select_button.config(state="normal")
        start_button.config(state="disabled")
        
        # 移除状态框架
        status_frame.destroy()
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

# 全局变量存储选择的文件
selected_files = []

# 创建 GUI
root = Tk()
root.title("图片排版工具")
root.geometry("600x600")  # 增加窗口高度以适应新增的设置项

# 创建标签页控件
notebook = Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# 创建主页标签
tab1 = TkFrame(notebook)
notebook.add(tab1, text="主页")

# 创建设置标签
tab2 = TkFrame(notebook)
notebook.add(tab2, text="设置")

# 创建主页内容
main_frame = Frame(tab1)
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# 创建标题标签
title_label = Label(main_frame, text="图片排版工具", font=("黑体", 16, "bold"))
title_label.pack(pady=10)

# 创建说明标签
instruction_label = Label(main_frame, text="请先选择图片，然后点击开始拼接", font=("宋体", 10))
instruction_label.pack(pady=10)

# 创建一个框架来包含输入字段
entry_frame = Frame(main_frame)
entry_frame.pack(pady=10, fill="x")

entry_label = Label(entry_frame, text="输出文件名前缀:", font=("宋体", 10))
entry_label.pack(side="left", padx=5)
entry = Entry(entry_frame)
entry.pack(side="left", expand=True, fill="x", padx=5)
entry.insert(0, "output")  # 设置默认值

# 创建文件选择状态标签
file_count_label = Label(main_frame, text="未选择图片", font=("宋体", 9), fg="blue")
file_count_label.pack(pady=5)

# 创建按钮框架
button_frame = Frame(main_frame)
button_frame.pack(pady=10)

# 创建选择图片按钮
select_button = Button(button_frame, text="选择图片", command=select_images, 
                bg="#4CAF50", fg="white", font=("宋体", 10, "bold"),
                padx=15, pady=5)
select_button.pack(side="left", padx=10)

# 创建开始拼接按钮
start_button = Button(button_frame, text="开始拼接", command=process_images, 
                bg="#2196F3", fg="white", font=("宋体", 10, "bold"),
                padx=15, pady=5, state="disabled")
start_button.pack(side="left", padx=10)

# 创建结果标签
result_label = Label(main_frame, text="", font=("宋体", 9), wraplength=500)
result_label.pack(pady=10)

# 创建设置页内容
settings_frame = Frame(tab2)
settings_frame.pack(padx=20, pady=20, fill="both", expand=True)

# 创建设置标题
settings_title = Label(settings_frame, text="参数设置", font=("黑体", 14, "bold"))
settings_title.pack(pady=10)

# 最大图片数量设置
max_images_frame = Frame(settings_frame)
max_images_frame.pack(fill="x", pady=5)
max_images_label = Label(max_images_frame, text="最大图片数量:", width=15, anchor="w")
max_images_label.pack(side="left", padx=5)
max_images_var = StringVar(value="100")
max_images_entry = Entry(max_images_frame, textvariable=max_images_var, width=10)
max_images_entry.pack(side="left", padx=5)

# 重采样大小设置
resampling_frame = Frame(settings_frame)
resampling_frame.pack(fill="x", pady=5)
resampling_label = Label(resampling_frame, text="重采样大小:", width=15, anchor="w")
resampling_label.pack(side="left", padx=5)
resampling_size_var = StringVar(value="4000")
resampling_entry = Entry(resampling_frame, textvariable=resampling_size_var, width=10)
resampling_entry.pack(side="left", padx=5)
resampling_info = Label(resampling_frame, text="像素 (长边)", font=("宋体", 8))
resampling_info.pack(side="left", padx=5)

# 单图边框大小设置
border_frame = Frame(settings_frame)
border_frame.pack(fill="x", pady=5)
border_label = Label(border_frame, text="单图边框大小:", width=15, anchor="w")
border_label.pack(side="left", padx=5)
border_size_var = StringVar(value="4200")
border_entry = Entry(border_frame, textvariable=border_size_var, width=10)
border_entry.pack(side="left", padx=5)
border_info = Label(border_frame, text="像素", font=("宋体", 8))
border_info.pack(side="left", padx=5)

# 最终图像大小设置
final_frame = Frame(settings_frame)
final_frame.pack(fill="x", pady=5)
final_label = Label(final_frame, text="最终图像大小:", width=15, anchor="w")
final_label.pack(side="left", padx=5)
final_size_var = StringVar(value="10000")
final_entry = Entry(final_frame, textvariable=final_size_var, width=10)
final_entry.pack(side="left", padx=5)
final_info = Label(final_frame, text="像素 (长边)", font=("宋体", 8))
final_info.pack(side="left", padx=5)

# DPI设置
dpi_frame = Frame(settings_frame)
dpi_frame.pack(fill="x", pady=5)
dpi_label = Label(dpi_frame, text="图像DPI:", width=15, anchor="w")
dpi_label.pack(side="left", padx=5)
dpi_var = StringVar(value="300")
dpi_entry = Entry(dpi_frame, textvariable=dpi_var, width=10)
dpi_entry.pack(side="left", padx=5)
dpi_info = Label(dpi_frame, text="每英寸点数 (常用值: 72, 150, 300, 600)", font=("宋体", 8))
dpi_info.pack(side="left", padx=5)

# 背景颜色设置
color_frame = Frame(settings_frame)
color_frame.pack(fill="x", pady=5)
color_label = Label(color_frame, text="背景颜色:", width=15, anchor="w")
color_label.pack(side="left", padx=5)
color_var = StringVar(value="white")
color_options = ["white", "black", "grey", "lightgrey", "beige", "lightblue", "lightyellow"]
color_menu = OptionMenu(color_frame, color_var, *color_options)
color_menu.pack(side="left", padx=5)

# 添加颜色预览
color_preview_frame = Frame(color_frame)
color_preview_frame.pack(side="left", padx=10)
color_preview_label = Label(color_preview_frame, text="预览:", font=("宋体", 8))
color_preview_label.pack(side="left")
color_preview = Frame(color_preview_frame, width=30, height=20, bg="white", relief="solid", borderwidth=1)
color_preview.pack(side="left", padx=5)

# 添加水印相关设置
watermark_section = Frame(settings_frame)
watermark_section.pack(fill="x", pady=10)

watermark_section_label = Label(watermark_section, text="水印设置", font=("黑体", 12, "bold"))
watermark_section_label.pack(anchor="w", pady=5)

# 水印启用/禁用选项
watermark_enable_frame = Frame(watermark_section)
watermark_enable_frame.pack(fill="x", pady=5)
watermark_var = IntVar(value=0)
watermark_check = Checkbutton(watermark_enable_frame, text="启用水印", variable=watermark_var)
watermark_check.pack(side="left", padx=5)

# 选择水印图片按钮
watermark_select_button = Button(watermark_enable_frame, text="选择水印图片", command=select_watermark,
                              bg="#4CAF50", fg="white", font=("宋体", 9),
                              padx=10, pady=2)
watermark_select_button.pack(side="left", padx=10)

# 显示已选择的水印文件
watermark_file_label = Label(watermark_enable_frame, text="未选择水印图片", font=("宋体", 8), fg="blue")
watermark_file_label.pack(side="left", padx=5)

# 水印缩放比例
watermark_scale_frame = Frame(watermark_section)
watermark_scale_frame.pack(fill="x", pady=5)
watermark_scale_label = Label(watermark_scale_frame, text="水印缩放比例:", width=15, anchor="w")
watermark_scale_label.pack(side="left", padx=5)
watermark_scale_var = StringVar(value="100")
watermark_scale_entry = Entry(watermark_scale_frame, textvariable=watermark_scale_var, width=10)
watermark_scale_entry.pack(side="left", padx=5)
watermark_scale_info = Label(watermark_scale_frame, text="%", font=("宋体", 8))
watermark_scale_info.pack(side="left", padx=5)

# 水印垂直位置
watermark_position_y_frame = Frame(watermark_section)
watermark_position_y_frame.pack(fill="x", pady=5)
watermark_position_y_label = Label(watermark_position_y_frame, text="水印位置(垂直):", width=15, anchor="w")
watermark_position_y_label.pack(side="left", padx=5)
watermark_position_y_var = StringVar(value="95")
watermark_position_y_entry = Entry(watermark_position_y_frame, textvariable=watermark_position_y_var, width=10)
watermark_position_y_entry.pack(side="left", padx=5)
watermark_position_y_info = Label(watermark_position_y_frame, text="% (图片高度的百分比，95%表示底部)", font=("宋体", 8))
watermark_position_y_info.pack(side="left", padx=5)

# 水印水平位置
watermark_position_x_frame = Frame(watermark_section)
watermark_position_x_frame.pack(fill="x", pady=5)
watermark_position_x_label = Label(watermark_position_x_frame, text="水印位置(水平):", width=15, anchor="w")
watermark_position_x_label.pack(side="left", padx=5)
watermark_position_x_var = StringVar(value="50")
watermark_position_x_entry = Entry(watermark_position_x_frame, textvariable=watermark_position_x_var, width=10)
watermark_position_x_entry.pack(side="left", padx=5)
watermark_position_x_info = Label(watermark_position_x_frame, text="% (图片宽度的百分比，50%表示居中)", font=("宋体", 8))
watermark_position_x_info.pack(side="left", padx=5)

# 水印说明
watermark_info = Label(watermark_section, text="注意: 建议使用PNG格式的图片作为水印，以获得最佳透明效果。\n水印将被放置在最终拼贴图的指定位置。", 
                     font=("宋体", 9), fg="grey", wraplength=400)
watermark_info.pack(pady=5)

# 说明文本
settings_info = Label(settings_frame, text="注意: 较大的图像大小和处理数量会增加处理时间和内存占用。", 
                      font=("宋体", 9), fg="grey", wraplength=400)
settings_info.pack(pady=10)

# DPI说明文本
dpi_info_text = Label(settings_frame, text="DPI(每英寸点数)影响打印质量和物理尺寸，不影响屏幕显示效果。", 
                     font=("宋体", 9), fg="grey", wraplength=400)
dpi_info_text.pack(pady=5)

# 版权信息
copyright_label = Label(root, text="© Yuui's PicLayoutTool", font=("宋体", 8), fg="gray")
copyright_label.pack(side="bottom", pady=5)

# 颜色变化跟踪
color_var.trace_add("write", update_color_preview)

# 初始化颜色预览
update_color_preview()

root.mainloop()
