# 学生语音识别系统 - IFLOW.md

## 项目概述

这是一个基于ESP32-S3硬件和Flask后端的**学生语音互动识别系统**。系统架构包含三个主要组件：

1. **ESP32-S3录音设备**: 作为学生端硬件，通过按钮触发录音，录制16kHz单声道WAV音频并通过WiFi上传到服务器
2. **Flask后端服务**: 接收音频文件，使用FunASR模型进行实时语音识别，并管理学生/设备绑定关系
3. **Web管理界面**: 提供学生管理、设备绑定和实时语音识别结果显示功能

> **注意**: 本文件为开发者上下文文档，用于iFlow CLI的项目理解和代码生成。用户应参考README.md获取使用说明。

## 核心功能

### 语音识别流程
- ESP32设备录制WAV格式音频（16kHz, 16位, 单声道）
- 通过HTTP POST上传到`/upload`接口，携带`Device-Id`头部
- 后端根据Device-Id映射到对应学生，进行语音识别
- 识别结果实时显示在Web界面的聊天消息区域

### 学生与设备管理
- **学生管理**: 添加/删除学生，为学生分配随机颜色标识
- **设备绑定**: 支持在添加学生时绑定设备ID，或单独为现有学生绑定设备
- **自动创建**: 未绑定的设备上传音频时，自动创建以"设备_设备ID"命名的学生

### 文件管理
- 每个学生对应一个独立文件夹（位于`uploads/`目录下）
- 系统自动监控学生文件夹中的新WAV文件并进行识别
- ESP32设备上传成功后自动删除本地文件以节省存储空间

## 项目结构

```
├── platformio.ini          # PlatformIO项目配置（ESP32-S3开发板）
├── src/
│   ├── app.py             # Flask后端主程序
│   ├── funasr.ino         # ESP32录音设备固件代码
│   ├── students.json      # 学生数据存储文件
│   ├── devices.json       # 设备绑定数据存储文件
│   ├── uploads/           # 学生音频文件存储目录
│   ├── templates/
│   │   ├── index.html     # 主页（语音识别结果显示）
│   │   └── students.html  # 学生管理页面（含设备绑定功能）
│   └── ESP32_USAGE.md     # ESP32设备使用说明文档
└── IFLOW.md               # 本说明文件
```

## 开发与部署

### 后端启动
```bash
# 基本启动（本地访问）
python src/app.py

# 允许外部访问
python src/app.py --host 0.0.0.0 --port 5000

# 禁用文件监控功能
python src/app.py --no-monitor
```

### ESP32配置
在`funasr.ino`中修改以下配置：
- `ssid` 和 `password`: WiFi网络凭据
- `serverUrl`: 后端服务器地址（格式：`http://IP:端口/upload`）
- `deviceId`: 设备唯一标识（每个ESP32设备必须不同）

### Web界面功能
- **主页 (`/`)**: 实时显示语音识别消息，按学生分组显示
- **学生管理 (`/students`)**: 
  - 添加学生（可同时绑定设备ID）
  - 为现有学生绑定/解绑设备
  - 修改学生颜色标识
  - 删除学生（同时删除对应文件夹）

## API接口

### 核心API
- `POST /upload` - ESP32设备上传音频文件（需`Device-Id`头部）
- `GET /api/messages` - 获取识别消息列表（最近50条）
- `GET /api/students` - 获取学生列表
- `POST /api/students` - 添加学生（可选`device_id`参数）
- `PUT /api/students/<name>/color` - 更新学生颜色
- `DELETE /api/students/<name>` - 删除学生

### 设备管理API
- `GET /api/devices` - 获取设备绑定列表
- `POST /api/devices` - 创建设备绑定（`device_id`, `student_name`）
- `DELETE /api/devices/<device_id>` - 删除设备绑定

## 技术栈

- **后端**: Python 3, Flask, FunASR（语音识别模型）
- **前端**: HTML5, CSS3, JavaScript（原生，无框架）
- **硬件**: ESP32-S3, I2S数字麦克风
- **部署**: PlatformIO（ESP32开发）, 标准Python环境（后端）

## 使用流程

1. 启动Flask后端服务
2. 配置并烧录ESP32设备固件
3. 通过Web界面添加学生并绑定对应的设备ID
4. ESP32设备录制语音并自动上传
5. 在主页实时查看语音识别结果