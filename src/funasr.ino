#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>
#include <SPIFFS.h>

// WiFi配置 - 烧录前手动修改
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// 服务器配置 - 烧录前手动修改
const char* serverUrl = "http://YOUR_SERVER_IP:5000/upload";

// I2S配置 (ESP32-S3)
#define I2S_WS 42
#define I2S_SD 17
#define I2S_SCK 41
#define I2S_PORT I2S_NUM_0
#define I2S_SAMPLE_RATE 16000
#define I2S_BITS_PER_SAMPLE 16
#define I2S_BUFFER_SIZE 1024

// 按钮配置
#define RECORD_BUTTON_PIN 0
#define LED_PIN 2

// 设备信息 - 烧录前手动修改 deviceId
String deviceId = "ESP32_001";  // 设备唯一标识，每个设备不同

// 录音状态
bool isRecording = false;
File wavFile;
unsigned long recordingStartTime = 0;
const unsigned long maxRecordingTime = 30000; // 最大录音时间30秒

// WAV文件头结构
struct WAVHeader {
  char riff[4] = {'R', 'I', 'F', 'F'};
  uint32_t chunkSize = 0;
  char wave[4] = {'W', 'A', 'V', 'E'};
  char fmt[4] = {'f', 'm', 't', ' '};
  uint32_t subChunk1Size = 16;
  uint16_t audioFormat = 1;
  uint16_t numChannels = 1;
  uint32_t sampleRate = I2S_SAMPLE_RATE;
  uint32_t byteRate = I2S_SAMPLE_RATE * 2;
  uint16_t blockAlign = 2;
  uint16_t bitsPerSample = I2S_BITS_PER_SAMPLE;
  char data[4] = {'d', 'a', 't', 'a'};
  uint32_t subChunk2Size = 0;
};

WAVHeader wavHeader;

void setup() {
  Serial.begin(115200);
  
  // 初始化LED和按钮
  pinMode(LED_PIN, OUTPUT);
  pinMode(RECORD_BUTTON_PIN, INPUT_PULLUP);
  
  // 初始化SPIFFS (板载Flash)
  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS初始化失败");
    return;
  }
  
  // 连接WiFi
  connectToWiFi();
  
  // 初始化I2S
  i2s_config_t i2sConfig = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = (i2s_bits_per_sample_t)I2S_BITS_PER_SAMPLE,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = I2S_BUFFER_SIZE,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  
  i2s_pin_config_t pinConfig = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  
  i2s_driver_install(I2S_PORT, &i2sConfig, 0, NULL);
  i2s_set_pin(I2S_PORT, &pinConfig);
  
  Serial.println("ESP32录音设备初始化完成");
  Serial.println("按下按钮开始录音...");
}

void loop() {
  // 检测按钮按下（低电平触发）
  if (digitalRead(RECORD_BUTTON_PIN) == LOW && !isRecording) {
    delay(50); // 消抖
    if (digitalRead(RECORD_BUTTON_PIN) == LOW) {
      startRecording();
    }
  }
  
  // 录音过程中检查是否超时或按钮再次按下
  if (isRecording) {
    if (millis() - recordingStartTime > maxRecordingTime || digitalRead(RECORD_BUTTON_PIN) == LOW) {
      stopRecording();
      uploadFile();
    }
  }
  
  delay(10);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("连接WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi连接成功");
  Serial.print("IP地址: ");
  Serial.println(WiFi.localIP());
}

void startRecording() {
  isRecording = true;
  recordingStartTime = millis();
  
  // 创建WAV文件名
  String filename = "/recording_" + String(millis()) + ".wav";
  wavFile = SPIFFS.open(filename.c_str(), FILE_WRITE);
  
  if (!wavFile) {
    Serial.println("无法创建录音文件");
    isRecording = false;
    return;
  }
  
  // 写入WAV头（稍后更新文件大小）
  wavFile.write((uint8_t*)&wavHeader, sizeof(wavHeader));
  
  digitalWrite(LED_PIN, HIGH);
  Serial.println("开始录音...");
}

void stopRecording() {
  if (!isRecording) return;
  
  isRecording = false;
  digitalWrite(LED_PIN, LOW);
  
  // 停止I2S
  i2s_stop(I2S_PORT);
  
  // 更新WAV文件头
  uint32_t dataSize = wavFile.size() - sizeof(wavHeader);
  wavHeader.subChunk2Size = dataSize;
  wavHeader.chunkSize = sizeof(wavHeader) - 8 + dataSize;
  
  // 重写文件头
  wavFile.seek(0);
  wavFile.write((uint8_t*)&wavHeader, sizeof(wavHeader));
  wavFile.close();
  
  Serial.println("录音结束");
}

void uploadFile() {
  // 获取最新录音文件
  File root = SPIFFS.open("/");
  File latestFile;
  unsigned long latestTime = 0;
  
  while (true) {
    File file = root.openNextFile();
    if (!file) break;
    
    if (file.name()[0] == '.' || !strstr(file.name(), ".wav")) {
      file.close();
      continue;
    }
    
    if (file.getLastWrite() > latestTime) {
      if (latestFile) latestFile.close();
      latestFile = file;
      latestTime = file.getLastWrite();
    } else {
      file.close();
    }
  }
  root.close();
  
  if (!latestFile) {
    Serial.println("未找到录音文件");
    return;
  }
  
  // 上传文件
  if (uploadAudioFile(latestFile.name())) {
    Serial.println("文件上传成功");
    // 删除本地文件以节省空间
    SPIFFS.remove(latestFile.name());
  } else {
    Serial.println("文件上传失败");
  }
  
  latestFile.close();
}

bool uploadAudioFile(const char* filename) {
  File file = SPIFFS.open(filename);
  if (!file) {
    Serial.println("无法打开文件进行上传");
    return false;
  }
  
  // 读取整个文件到内存（注意：ESP32内存有限，大文件可能有问题）
  size_t fileSize = file.size();
  uint8_t* fileBuffer = (uint8_t*)malloc(fileSize);
  if (!fileBuffer) {
    Serial.println("内存不足，无法分配文件缓冲区");
    file.close();
    return false;
  }
  
  file.read(fileBuffer, fileSize);
  file.close();
  
  HTTPClient http;
  http.begin(serverUrl);
  
  // 设置请求头
  http.addHeader("Device-Id", deviceId.c_str());
  
  // 发送POST请求（HTTPClient会自动处理multipart）
  int httpResponseCode = http.POST(fileBuffer, fileSize);
  http.end();
  
  free(fileBuffer);
  
  return httpResponseCode == 200;
}