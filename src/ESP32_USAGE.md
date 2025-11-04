# ESP32学生录音设备使用说明（简化版）

## 系统架构

- **ESP32-S3设备**: 作为学生端录音工具，按下按钮开始录音，松开或30秒后自动停止
- **Flask后端**: 接收录音文件，进行语音识别，并管理学生和设备绑定
- **Web界面**: 查看识别结果和管理学生/设备

## 硬件连接

ESP32-S3 I2S麦克风连接:
- I2S_WS (LRCLK): GPIO 42
- I2S_SD (DOUT): GPIO 17  
- I2S_SCK (BCLK): GPIO 41
- 录音按钮: GPIO 0 (接地触发)
- LED指示灯: GPIO 2

## 软件配置流程

### 1. 配置ESP32代码

编辑 `esp32_recorder.ino` 文件，修改以下参数：
```cpp
// WiFi配置 - 烧录前手动修改
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// 服务器配置 - 烧录前手动修改  
const char* serverUrl = "http://YOUR_SERVER_IP:5000/upload";

// 设备信息 - 烧录前手动修改 deviceId（每个设备不同）
String deviceId = "ESP32_001";
```

### 2. 上传ESP32代码

使用Arduino IDE打开 `esp32_recorder.ino`，上传到ESP32设备。

### 3. 启动后端服务

```bash
python app.py --host 0.0.0.0 --port 5000
```

### 4. 管理学生和设备绑定

通过Web界面或API管理学生和设备绑定：

**添加学生时绑定设备**:
- 在学生管理页面添加学生时，可以同时指定设备ID
- 系统会自动创建设备绑定关系

**单独绑定设备**:
- 通过设备管理API手动绑定设备ID到学生

## 功能特性

### ESP32端功能
- 按钮触发录音（支持消抖）
- 最大录音时间30秒（可配置）
- 录音时LED亮起
- 自动连接WiFi
- 生成标准WAV格式文件
- 通过HTTP POST上传到服务器（只发送Device-Id）
- 上传成功后自动删除本地文件节省空间

### 后端功能
- 根据Device-Id映射到对应学生
- 自动创建学生文件夹
- 实时语音识别
- 设备绑定管理API
- 支持未绑定设备自动创建学生（以"设备_设备ID"命名）

## API接口

### 设备上传接口
- **URL**: `/upload`
- **Method**: POST (multipart/form-data)
- **Headers**: `Device-Id`: 设备唯一标识
- **Response**: JSON格式的成功/错误信息

### 学生管理API
- `POST /api/students` - 添加学生（可选device_id参数）
- 其他学生管理接口保持不变

### 设备管理API
- `GET /api/devices` - 获取设备列表
- `POST /api/devices` - 添加设备绑定  
- `DELETE /api/devices/<device_id>` - 删除设备绑定

## 注意事项

1. **WiFi配置**: 所有ESP32设备使用相同的WiFi配置
2. **服务器地址**: 所有ESP32设备使用相同的服务器地址
3. **设备ID**: 每个ESP32设备必须有唯一的deviceId
4. **SD卡**: ESP32需要安装SD卡用于临时存储录音文件
5. **音频格式**: 系统只支持16kHz、16位、单声道WAV格式

## 部署流程

1. 配置好后端服务器和网络
2. 为每个ESP32设备修改deviceId并烧录代码
3. 通过Web界面添加学生并绑定对应的设备ID
4. 设备即可自动上传录音到对应学生文件夹