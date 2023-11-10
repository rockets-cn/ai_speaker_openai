from openai import OpenAI
import os
from dotenv import load_dotenv
import pyaudio
import wave
import time
import audioop

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


# 采用 vox方式进行语音转换
def record_audio():
    # 录音参数
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    THRESHOLD = 500  # 定义声音激活的阈值
    #THRESHOLD = 900  # 定义声音激活的阈值
    SILENCE_LIMIT = 3  # 定义多少秒内低于阈值时停止录音
    WAVE_OUTPUT_FILENAME = "output.wav"  # 输出文件名
    # 初始化pyaudio
    p = pyaudio.PyAudio()

    # 打开录音流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("请开始说话...")

    # 用于存储块的数组
    frames = []
    silent_chunks = 0
    audio_started = False

    while True:
        # 读取最新的音频块
        data = stream.read(CHUNK)
        # 使用RMS来判断音量
        rms = audioop.rms(data, 2)

        # 如果音量超过阈值
        if rms > THRESHOLD:
            if not audio_started:
                print("开始录音...")
                audio_started = True
                silent_chunks = 0

            frames.append(data)

        elif audio_started:
            # 如果当前块的音量低于阈值，我们视为静默
            silent_chunks += 1
            frames.append(data)
            # 如果静默时间超过了设定的限度，则停止录音
            if silent_chunks > SILENCE_LIMIT * RATE / CHUNK:
                print("结束录音.")
                break
        else:
            print("等待声音...")

    # 停止并关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 保存音频数据
    wf = wave.open('output.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return WAVE_OUTPUT_FILENAME




def convert_audio_to_text(audio_file):
    audio_file = open(audio_file, "rb")

    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="text"
    )
    print("转换完成")

    return transcript

def generate_response(input_txt):
    response_text = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "user", 
             "content": input_txt}
        ]
    )
    print(response_text.choices[0].message)
    return response_text.choices[0].message.content

def convert_text_to_speech(input_tts):
    response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=input_tts,
    )

    response.stream_to_file("output2.mp3")

def play_audio():
    #播放语音
    os.system("mpg123 output2.mp3")

if __name__ == "__main__":
    while True:
        audio_file = record_audio()
        transcript = convert_audio_to_text(audio_file)
        input_txt = transcript
        input_tts = generate_response(input_txt)
        convert_text_to_speech(input_tts)
        play_audio()
        time.sleep(1)