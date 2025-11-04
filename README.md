# 学生语音识别系统

![系统架构图](https://via.placeholder.com/800x400?text=Student+Voice+Recognition+System+Architecture)

一个基于ESP32-S3硬件和Flask后端的实时学生语音互动识别系统，支持多设备管理和自动语音识别。

## 🌟 功能特性

- **实时语音识别**: 使用FunASR模型进行高精度中文语音识别
- **多设备管理**: 支持多个ESP32设备同时连接，每个设备绑定到特定学生
- **自动文件管理**: 每个学生拥有独立的音频文件夹，自动监控和处理新录音
- **Web管理界面**: 直观的Web界面进行学生管理、设备绑定和识别结果显示
- **设备自动发现**: 未绑定的设备上传音频时自动创建学生账户
- **Excel批量导入**: 支持通过Excel模板批量导入学生信息
- **灵活的文件清理**: 提供多种文件清理选项（单个学生、所有学生文件、完全清空）
- **随机颜色标识**: 每个学生自动分配独特的颜色标识便于区分

## 🚀 快速开始

### 环境要求

- **Python 3.7+** (后端服务)
- **Arduino IDE + ESP32开发板支持** (设备端)
- **FunASR语音识别库**
- **ESP32-S3开发板** (带I2S麦克风)

### 安装依赖

```bash
# 安装Python依赖
pip install flask funasr werkzeug pandas openpyxl

# ESP32开发环境
# 在Arduino IDE中安装ESP32开发板支持包
```

### 启动后端服务

```bash
# 基本启动（本地访问）
python src/app.py

# 允许外部访问（推荐用于ESP32连接）
python src/app.py --host 0.0.0.0 --port 5000

# 禁用文件监控功能（如不需要自动处理本地WAV文件）
python src/app.py --no-monitor

# 指定FunASR模型（默认: paraformer-zh）
python src/app.py --model paraformer-zh
```

### 启动参数说明

- `--host`: 服务器监听地址（默认: 127.0.0.1）
- `--port`: 服务器端口（默认: 5000）
- `--model`: FunASR模型名称（默认: paraformer-zh）
- `--no-monitor`: 禁用文件监控功能

### 配置ESP32设备

1. 编辑 `src/studentsASR.ino` 文件，修改以下配置：
   ```cpp
   // WiFi配置
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   
   // 服务器地址（替换为你的服务器IP）
   const char* serverUrl = "http://YOUR_SERVER_IP:5000/upload";
   
   // 设备唯一标识（每个设备必须不同）
   String deviceId = "ESP32_001";
   ```

2. 使用Arduino IDE将代码上传到ESP32设备

### 使用Web界面

1. 访问 `http://localhost:5000` 查看实时语音识别结果
2. 访问 `http://localhost:5000/students` 管理学生和设备绑定
3. 在学生管理页面添加学生并绑定对应的设备ID

## 📁 项目结构

```
├── platformio.ini          # PlatformIO项目配置
├── src/
│   ├── app.py             # Flask后端主程序
│   ├── studentsASR.ino    # ESP32设备固件代码
│   ├── students.json      # 学生数据存储（包含设备绑定信息）
│   ├── uploads/           # 音频文件存储目录
│   ├── templates/         # Web模板
│   │   ├── index.html     # 主页（识别结果显示）
│   │   └── students.html  # 学生管理页面
│   ├── ESP32_USAGE.md     # ESP32详细使用说明
│   └── asr_example.wav    # 语音识别示例音频
├── IFLOW.md               # 开发者上下文文档
└── README.md              # 本文件
```

## 📡 API接口

### 核心接口

- `POST /upload` - 设备上传音频文件（需`Device-Id`头部）
- `GET /api/messages` - 获取识别消息（最近50条）
- `GET /api/students` - 获取学生列表
- `GET /api/test` - 测试API接口连通性

### 学生管理接口

- `POST /api/students` - 添加学生（可选`device_id`参数）
- `PUT /api/students/<name>/color` - 更新学生颜色标识
- `PUT /api/students/<name>/device` - 更新学生设备绑定
- `DELETE /api/students/<name>` - 删除学生及对应文件夹

### 文件管理接口

- `DELETE /api/students/<name>/clear-files` - 清空指定学生文件夹内所有文件（保留学生记录）
- `DELETE /api/students/clear-all-files` - 清空所有学生文件夹内所有文件（保留学生记录和文件夹）
- `DELETE /api/students/clear-all` - 完全清空所有学生（删除学生记录、文件夹和所有文件）

### Excel导入接口

- `POST /api/import-students` - 从Excel文件导入学生信息
- `GET /api/excel-template` - 下载Excel导入模板

### 设备管理说明

- **设备绑定**: 设备ID信息直接存储在`students.json`文件中，无需单独的`devices.json`文件
- **自动创建**: 未绑定的设备上传音频时，系统自动创建以"设备_设备ID"命名的学生

## ⚙️ 硬件连接

ESP32-S3 I2S麦克风连接:
- **I2S_WS (LRCLK)**: GPIO 42
- **I2S_SD (DOUT)**: GPIO 17  
- **I2S_SCK (BCLK)**: GPIO 41
- **录音按钮**: GPIO 0 (接地触发)
- **LED指示灯**: GPIO 2

## 📝 使用流程

### 基本使用流程

1. 启动Flask后端服务
2. 配置并烧录ESP32设备固件
3. 通过Web界面添加学生并绑定设备ID
4. 按下ESP32按钮开始录音
5. 松开按钮或30秒后自动停止并上传
6. 在Web主页实时查看识别结果

### 批量管理流程

1. 访问学生管理页面 (`/students`)
2. 点击"下载模板"获取Excel导入模板
3. 在Excel中填写学生姓名和设备ID
4. 点击"导入学生"上传Excel文件
5. 系统自动验证并导入学生信息

### 文件管理流程

- **清理单个学生文件**: 在学生管理页面点击对应学生的"清空文件"按钮
- **清理所有学生文件**: 在学生管理页面点击"清空所有文件"按钮
- **完全重置系统**: 在学生管理页面点击"清空所有学生"按钮

## 🛠️ 故障排除

### 常见问题

**Q: ESP32无法连接到WiFi**
- 检查`studentsASR.ino`中的WiFi配置是否正确
- 确保WiFi网络在ESP32范围内

**Q: 音频文件上传失败**
- 检查服务器IP地址是否正确
- 确保后端服务正在运行且端口开放
- 验证防火墙设置

**Q: 语音识别结果不准确**
- 确保录音环境安静
- 检查音频格式是否为16kHz、16位、单声道WAV
- 考虑使用更适合的FunASR模型

### 支持格式

- **音频格式**: WAV (16kHz, 16位, 单声道)
- **文件大小**: 最大10MB
- **录音时长**: 最大30秒（可配置）

## 🤝 贡献指南

欢迎提交Issue和Pull Request！请遵循以下准则：

1. 保持代码风格一致
2. 添加必要的测试用例
3. 更新相关文档
4. 确保向后兼容性

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可。

---

**注意**: 本系统设计用于教育和实验目的，请确保在使用过程中遵守相关隐私和数据保护法规。