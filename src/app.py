#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生语音识别系统 - Flask后端
上传WAV文件并返回识别结果
"""

import os
import wave
import json
import time
import threading
import argparse
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from funasr import AutoModel

# 配置
UPLOAD_FOLDER = 'uploads'
STUDENTS_FILE = 'students.json'
ALLOWED_EXTENSIONS = {'wav'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 创建应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局变量
model = None
students = []
recognized_messages = []
recognized_messages_lock = threading.Lock()

# 加载学生列表
def load_students():
    global students
    try:
        if os.path.exists(STUDENTS_FILE):
            with open(STUDENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容旧格式（字符串数组）和新格式（对象数组）
                if data and isinstance(data[0], str):
                    # 转换旧格式为新格式
                    students = []
                    for name in data:
                        students.append({
                            'name': name,
                            'color': generate_random_color()
                        })
                    save_students()  # 保存新格式
                else:
                    students = data
        else:
            students = []
    except Exception as e:
        print(f"加载学生列表失败: {e}")
        students = []



def generate_random_color():
    """生成随机的渐变色"""
    import random
    colors = [
        '#4a55e0', '#5a2a8a', '#d963d6', '#e03a57', '#2a8cf5', '#00c8d9',
        '#2ab85a', '#e55a85', '#ff6a7e', '#fdbfdf', '#76d6c2', '#b8e55a',
        '#ffcc99', '#f899c0', '#ff6a7e', '#fdbfdf', '#76d6c2', '#b8e55a'
    ]
    return random.choice(colors)

# 保存学生列表
def save_students():
    try:
        with open(STUDENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(students, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存学生列表失败: {e}")



# 确保学生文件夹存在
def ensure_student_folder(student_name):
    student_folder = os.path.join(UPLOAD_FOLDER, student_name)
    os.makedirs(student_folder, exist_ok=True)
    return student_folder

# 初始化学生数据
load_students()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_wav_file(file_path):
    """
    从WAV文件加载音频数据
    """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            # 验证音频格式
            if wav_file.getnchannels() != 1:
                raise ValueError("只支持单声道音频")
            if wav_file.getsampwidth() != 2:  # 16位音频
                raise ValueError("只支持16位深度音频")
            if wav_file.getframerate() != 16000:
                raise ValueError("只支持16kHz采样率音频")
            
            frames = wav_file.readframes(wav_file.getnframes())
            return frames
    except Exception as e:
        print(f"加载WAV文件失败: {e}")
        return None

def recognize_wav_file(wav_file_path):
    """
    使用FunASR模型识别WAV文件中的语音
    """
    global model
    try:
        # 加载WAV文件
        audio_data = load_wav_file(wav_file_path)
        if audio_data is None:
            return None
            
        print(f"正在处理文件: {wav_file_path}")
        
        # 使用模型进行识别
        result = model.generate(audio_data)
        text = result[0]['text'].replace(" ", "")
        print(f"识别结果: {text}")
        return text
        
    except Exception as e:
        print(f"语音识别错误: {e}")
        return None

@app.route('/')
def index():
    """主页 - 使用模板"""
    return app.send_static_file('index.html') if os.path.exists('static/index.html') else render_template('index.html')

@app.route('/students')
def students_page():
    """学生管理页面"""
    return render_template('students.html')



@app.route('/api/students', methods=['GET'])
def get_students():
    """获取学生列表"""
    return jsonify({'students': students})

@app.route('/api/students', methods=['POST'])
def add_student():
    """添加学生（可选绑定设备ID）"""
    global students
    try:
        data = request.get_json()
        student_name = data.get('name', '').strip()
        device_id = data.get('device_id', '').strip()
        
        if not student_name:
            return jsonify({'error': '学生姓名不能为空'}), 400
        
        # 检查学生是否已存在
        for student in students:
            if student['name'] == student_name:
                return jsonify({'error': '学生已存在'}), 400
        
        # 检查设备ID是否已存在（如果提供了设备ID）
        if device_id:
            for student in students:
                if student.get('device_id') == device_id:
                    return jsonify({'error': '设备ID已存在'}), 400
        
        # 添加新学生，包含随机颜色和设备ID
        new_student = {
            'name': student_name,
            'color': generate_random_color(),
            'device_id': device_id
        }
        students.append(new_student)
        save_students()
        ensure_student_folder(student_name)
        
        return jsonify({
            'success': True, 
            'message': '学生添加成功', 
            'student': new_student,
            'device_bound': bool(device_id)
        })
    except Exception as e:
        return jsonify({'error': f'添加失败: {str(e)}'}), 500

@app.route('/api/students/<student_name>', methods=['DELETE'])
def delete_student(student_name):
    """删除学生"""
    global students
    try:
        student_to_delete = None
        for student in students:
            if student['name'] == student_name:
                student_to_delete = student
                break
        
        if student_to_delete is None:
            return jsonify({'error': '学生不存在'}), 404
        
        # 删除学生文件夹及其内容
        student_folder = os.path.join(UPLOAD_FOLDER, student_name)
        if os.path.exists(student_folder):
            import shutil
            shutil.rmtree(student_folder)
        
        students.remove(student_to_delete)
        save_students()
        
        return jsonify({'success': True, 'message': '学生删除成功'})
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/students/<student_name>/color', methods=['PUT'])
def update_student_color(student_name):
    """更新学生颜色"""
    global students
    try:
        data = request.get_json()
        new_color = data.get('color', '').strip()
        
        if not new_color or not new_color.startswith('#') or len(new_color) != 7:
            return jsonify({'error': '无效的颜色格式'}), 400
        
        student_found = False
        for student in students:
            if student['name'] == student_name:
                student['color'] = new_color
                student_found = True
                break
        
        if not student_found:
            return jsonify({'error': '学生不存在'}), 404
        
        save_students()
        return jsonify({'success': True, 'message': '颜色更新成功'})
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """获取识别消息列表"""
    with recognized_messages_lock:
        return jsonify({'messages': recognized_messages[-50:]})  # 返回最近50条消息

@app.route('/api/test')
def test_api():
    """测试API接口"""
    return jsonify({'message': '语音识别系统运行正常'})

@app.route('/api/excel-template')
def download_excel_template():
    """下载Excel导入模板"""
    import io
    try:
        # 尝试导入pandas和openpyxl
        try:
            import pandas as pd
        except ImportError:
            return jsonify({'error': '缺少pandas库，请安装pandas和openpyxl'}), 500
        
        # 创建模板数据
        template_data = {
            '学生姓名': ['张三', '李四'],
            '设备ID': ['1', '2']
        }
        df = pd.DataFrame(template_data)
        
        # 创建内存中的Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='学生信息', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='学生导入模板.xlsx'
        )
    except Exception as e:
        return jsonify({'error': f'生成模板失败: {str(e)}'}), 500

@app.route('/api/import-students', methods=['POST'])
def import_students_from_excel():
    """从Excel文件导入学生"""
    global students
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '未提供Excel文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 检查文件扩展名
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': '只支持Excel文件(.xlsx, .xls)'}), 400
        
        # 尝试导入pandas
        try:
            import pandas as pd
        except ImportError:
            return jsonify({'error': '缺少pandas库，请安装pandas和openpyxl'}), 500
        
        # 读取Excel文件
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'读取Excel文件失败: {str(e)}'}), 400
        
        # 验证必需的列
        required_columns = ['学生姓名']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': f'Excel文件必须包含列: {", ".join(required_columns)}'}), 400
        
        imported_count = 0
        errors = []
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                student_name = str(row['学生姓名']).strip() if pd.notna(row['学生姓名']) else ''
                
                if not student_name:
                    errors.append(f'第{index + 2}行: 学生姓名不能为空')
                    continue
                
                # 检查学生是否已存在
                student_exists = False
                for existing_student in students:
                    if existing_student['name'] == student_name:
                        student_exists = True
                        break
                
                if student_exists:
                    errors.append(f'第{index + 2}行: 学生"{student_name}"已存在')
                    continue
                
                # 获取设备ID（如果存在）
                device_id = ''
                if '设备ID' in df.columns and pd.notna(row['设备ID']):
                    device_id = str(row['设备ID']).strip()
                
                # 检查设备ID是否已存在
                if device_id:
                    device_exists = False
                    for existing_student in students:
                        if existing_student.get('device_id') == device_id:
                            device_exists = True
                            break
                    if device_exists:
                        errors.append(f'第{index + 2}行: 设备ID"{device_id}"已存在')
                        continue
                
                # 添加新学生
                new_student = {
                    'name': student_name,
                    'color': generate_random_color(),
                    'device_id': device_id
                }
                students.append(new_student)
                ensure_student_folder(student_name)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'第{index + 2}行: 处理失败 - {str(e)}')
        
        # 保存学生列表
        save_students()
        
        result = {
            'success': True,
            'imported_count': imported_count,
            'total_rows': len(df),
            'message': f'成功导入{imported_count}个学生'
        }
        
        if errors:
            result['errors'] = errors
            result['message'] += f'，{len(errors)}行有错误'
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'导入失败: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_from_esp32():
    """处理ESP32设备上传的录音文件"""
    try:
        # 从请求头获取设备ID
        device_id = request.headers.get('Device-Id', '').strip()
        
        if not device_id:
            return jsonify({'error': '缺少Device-Id头部信息'}), 400
        
        # 根据设备ID查找对应的学生
        student_name = ""
        student_found = False
        for student in students:
            if student.get('device_id') == device_id:
                student_name = student['name']
                student_found = True
                break
        
        if not student_found:
            # 设备未绑定，使用设备ID作为学生姓名
            student_name = f"设备_{device_id}"
        
        # 确保学生存在
        student_exists = False
        for student in students:
            name = student['name'] if isinstance(student, dict) else student
            if name == student_name:
                student_exists = True
                break
        
        if not student_exists:
            # 自动创建新学生（无设备绑定）
            new_student = {
                'name': student_name,
                'color': generate_random_color(),
                'device_id': ""
            }
            students.append(new_student)
            save_students()
            print(f"自动创建新学生: {student_name}")
        
        # 确保学生文件夹存在
        student_folder = ensure_student_folder(student_name)
        
        # 处理文件上传
        if 'file' not in request.files:
            return jsonify({'error': '未提供文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免重名
            timestamp = str(int(time.time()))
            filename = f"esp32_{device_id}_{timestamp}.wav"
            
            filepath = os.path.join(student_folder, filename)
            file.save(filepath)
            
            # 立即进行语音识别
            result_text = recognize_wav_file(filepath)
            if result_text is not None:
                with recognized_messages_lock:
                    recognized_messages.append({
                        'student': student_name,
                        'text': result_text,
                        'timestamp': time.time(),
                        'filename': filename,
                        'source': 'esp32',
                        'device_id': device_id
                    })
                    if len(recognized_messages) > 100:
                        recognized_messages = recognized_messages[-100:]
            
            return jsonify({
                'success': True, 
                'message': '文件上传成功',
                'student': student_name,
                'filename': filename,
                'recognized_text': result_text,
                'device_id': device_id
            })
        else:
            return jsonify({'error': '不支持的文件格式'}), 400
            
    except Exception as e:
        print(f"ESP32上传处理错误: {e}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/students/<student_name>/device', methods=['PUT'])
def update_student_device(student_name):
    """更新学生设备绑定"""
    global students
    try:
        data = request.get_json()
        new_device_id = data.get('device_id', '').strip()
        
        # 查找学生
        student_found = False
        student_index = -1
        for i, student in enumerate(students):
            if student['name'] == student_name:
                student_found = True
                student_index = i
                break
        
        if not student_found:
            return jsonify({'error': '学生不存在'}), 404
        
        # 如果设置了新的设备ID，检查是否已存在
        if new_device_id:
            for i, student in enumerate(students):
                if student.get('device_id') == new_device_id and i != student_index:
                    return jsonify({'error': '设备ID已存在'}), 400
        
        # 更新设备ID
        students[student_index]['device_id'] = new_device_id
        save_students()
        
        return jsonify({'success': True, 'message': '设备绑定更新成功'})
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

def init_model(model_name="paraformer-zh"):
    """初始化FunASR模型"""
    global model
    print(f"正在加载模型: {model_name}")
    model = AutoModel(model=model_name, disable_update=True)
    print("模型加载完成")

# 监控线程相关变量
monitoring_thread = None
monitoring_active = False
processed_files = set()

def monitor_student_folders():
    """监控学生文件夹中的新WAV文件"""
    global monitoring_active, processed_files, students, recognized_messages
    
    while monitoring_active:
        try:
            # 获取所有学生文件夹（包括手动创建的）
            all_student_folders = []
            
            # 添加已注册的学生
            for student in students:
                student_name = student['name'] if isinstance(student, dict) else student
                student_folder = os.path.join(UPLOAD_FOLDER, student_name)
                if os.path.exists(student_folder):
                    all_student_folders.append(student_name)
            
            # 添加uploads目录下所有子文件夹（无论是否包含WAV文件）
            if os.path.exists(UPLOAD_FOLDER):
                for item in os.listdir(UPLOAD_FOLDER):
                    item_path = os.path.join(UPLOAD_FOLDER, item)
                    if os.path.isdir(item_path):
                        if item not in all_student_folders:
                            # 如果是新发现的学生文件夹，添加到学生列表
                            student_exists = False
                            for student in students:
                                name = student['name'] if isinstance(student, dict) else student
                                if name == item:
                                    student_exists = True
                                    break
                            
                            if not student_exists:
                                students.append({
                                    'name': item,
                                    'color': generate_random_color()
                                })
                                save_students()
                                print(f"发现新学生文件夹: {item}")
                            all_student_folders.append(item)
            
            # 监控所有学生文件夹
            for student_name in all_student_folders:
                student_folder = os.path.join(UPLOAD_FOLDER, student_name)
                if not os.path.exists(student_folder):
                    continue
                
                # 获取文件夹中所有WAV文件
                wav_files = []
                try:
                    for filename in os.listdir(student_folder):
                        if filename.lower().endswith('.wav'):
                            filepath = os.path.join(student_folder, filename)
                            wav_files.append((filepath, filename, os.path.getmtime(filepath)))
                except Exception as e:
                    print(f"读取文件夹失败 {student_folder}: {e}")
                    continue
                
                # 按修改时间排序，最新的在前面
                wav_files.sort(key=lambda x: x[2], reverse=True)
                
                # 处理所有未处理的文件
                for filepath, filename, mtime in wav_files:
                    file_key = filepath  # 使用完整文件路径作为唯一标识
                    if file_key not in processed_files:
                        try:
                            # 进行语音识别
                            result_text = recognize_wav_file(filepath)
                            if result_text is not None:
                                # 添加到消息列表
                                with recognized_messages_lock:
                                    recognized_messages.append({
                                        'student': student_name,
                                        'text': result_text,
                                        'timestamp': time.time(),
                                        'filename': filename
                                    })
                                    # 保持最多100条消息
                                    if len(recognized_messages) > 100:
                                        recognized_messages = recognized_messages[-100:]
                                
                                print(f"自动识别完成: {student_name} - {filename}")
                            
                            # 标记为已处理
                            processed_files.add(file_key)
                            
                        except Exception as e:
                            print(f"自动处理文件失败 {filepath}: {e}")
                            # 添加错误消息到识别结果
                            with recognized_messages_lock:
                                recognized_messages.append({
                                    'student': student_name,
                                    'text': f"[识别失败: {str(e)}]",
                                    'timestamp': time.time(),
                                    'filename': filename
                                })
                                # 保持最多100条消息
                                if len(recognized_messages) > 100:
                                    recognized_messages = recognized_messages[-100:]
                            processed_files.add(file_key)  # 避免重复尝试失败的文件
                
            time.sleep(2)  # 每2秒检查一次
            
        except Exception as e:
            print(f"监控线程错误: {e}")
            # 记录监控线程错误到消息列表
            try:
                with recognized_messages_lock:
                    recognized_messages.append({
                        'student': '系统',
                        'text': f"[监控错误: {str(e)}]",
                        'timestamp': time.time(),
                        'filename': 'monitor_error'
                    })
                    if len(recognized_messages) > 100:
                        recognized_messages = recognized_messages[-100:]
            except Exception as inner_e:
                print(f"记录监控错误失败: {inner_e}")
            time.sleep(5)

def start_monitoring():
    """启动监控线程"""
    global monitoring_thread, monitoring_active
    if monitoring_active:
        return
    
    monitoring_active = True
    monitoring_thread = threading.Thread(target=monitor_student_folders, daemon=True)
    monitoring_thread.start()
    print("开始监控学生文件夹...")

def stop_monitoring():
    """停止监控线程"""
    global monitoring_active
    monitoring_active = False
    if monitoring_thread:
        monitoring_thread.join(timeout=5)
    print("监控已停止")

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="学生语音识别Web系统")
    parser.add_argument("--model", default="paraformer-zh", help="FunASR模型名称 (默认: paraformer-zh)")
    parser.add_argument("--host", default="127.0.0.1", help="服务器主机地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="服务器端口 (默认: 5000)")
    parser.add_argument("--no-monitor", action="store_true", help="禁用文件监控功能")
    args = parser.parse_args()
    
    # 初始化模型
    init_model(args.model)
    
    # 启动监控（默认启用，除非指定 --no-monitor）
    if not args.no_monitor:
        start_monitoring()
    
    # 启动服务器
    print(f"启动服务器: http://{args.host}:{args.port}")
    try:
        app.run(host=args.host, port=args.port, debug=False)
    finally:
        if not args.no_monitor:
            stop_monitoring()