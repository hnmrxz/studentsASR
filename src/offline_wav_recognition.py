import argparse
import wave
import numpy as np
import sys
from funasr import AutoModel

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

def recognize_wav_file(model, wav_file_path):
    """
    使用FunASR模型识别WAV文件中的语音
    """
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

def main():
    parser = argparse.ArgumentParser(description="离线WAV语音识别脚本")
    parser.add_argument("--wav_file", help="输入的WAV文件路径")
    parser.add_argument("--model", default="paraformer-zh", help="FunASR模型名称 (默认: paraformer-zh)")
    
    args = parser.parse_args()
    
    # 初始化FunASR模型
    print(f"正在加载模型: {args.model}")
    model = AutoModel(model=args.model, disable_update=True)
    print("模型加载完成")
    
    # 执行语音识别
    result = recognize_wav_file(model, args.wav_file)
    
    if result is None:
        print("识别失败")
        exit(1)
    else:
        print("识别完成")

if __name__ == "__main__":
    main()