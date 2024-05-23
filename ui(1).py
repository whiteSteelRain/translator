import base64
import requests
import sys
import wave
import pyaudio
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QComboBox, QLabel, QMessageBox, QStatusBar,
                            QSpacerItem, QMainWindow, QTabWidget, QFileDialog,QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QTimer
from PyQt5.QtGui import QIcon, QFont,QPixmap
import gradio_client
from gradio_client import Client
import socket



FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

class TranslationThread(QThread):#文本处理和翻译线程
    translation_finished = pyqtSignal(str,str)  # 定义一个信号，用于发送翻译结果
    tokenization_finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.source_text = ""
        self.mode = ""
        self.target_text = ""
        self.target_text2 = ""
        self.source_tokenized_text = ""
        self.running = True

    def input_text(self, text):
        self.source_text = text

    def input_mode(self, mode):  
        self.mode = mode

    def run(self):
        while self.running:
            self.mutex.lock()
            if self.source_text:  # 检查是否有待翻译的文本
                try:
                # 执行翻译操作
                    client = Client("Dy3257/translate")
                
                    result = client.predict(
		                source_text=self.source_text,
		                mode=self.mode,
		                api_name="/predict"
                    )
                except Exception as e:
                    self.translation_finished.emit("Error", str(e))
                    self.mutex.unlock()
                    #self.stop()
                    break  # 退出循环，停止线程
                self.target_text,self.target_text2,self.source_tokenized_text = result
                self.tokenization_finished.emit(self.source_tokenized_text)  #发送分词结果信号
                self.translation_finished.emit(self.target_text, self.target_text2)  # 发送翻译结果信号
                self.source_text = ""
            self.mutex.unlock()

    def stop(self):
        self.running = False
        #self.mutex.lock()
        #self.mutex.unlock()
        self.wait(5000)  # 等待线程安全结束
        print("已结束")

class TranslatorApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.mode = "汉译英"
        self.source_text = ""
        self.ocr_source_text = ""
        self.stt_source_text = ""
        self.source_tokens = ""
        self.target_text = ""
        self.target_text2 = ""
        self.ocr_target_text = ""
        self.ocr_target_text2 = ""
        self.stt_target_text = ""
        self.stt_target_text2 = ""
        self.translate_idle = True
        self.tab_num = 1

        self.connection_status = "网络状态未知"

        # 创建翻译线程实例
        self.translation_thread = TranslationThread()
        # 连接线程的信号以更新UI
        self.translation_thread.translation_finished.connect(self.text_output)
        self.translation_thread.tokenization_finished.connect(self.token_output)
        # 启动线程
        self.translation_thread.start()
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle('translater')
        self.setGeometry(1400, 500, 800, 600)#窗口整体位置及大小

        self.tab_widget = QTabWidget(self)#设置标签
        self.tab_ocr = self.create_ocr_tab()
        self.tab_speech = self.create_speech_tab()
        self.tab_translate = self.create_translate_tab()

        tab_bar = self.tab_widget.tabBar()
        tab_bar.setMinimumSize(500, 40)  # 设置标签的最小宽度和高度

        self.tab_widget.addTab(self.tab_translate, '文本翻译&分词')
        self.tab_widget.addTab(self.tab_ocr, 'OCR识图')
        self.tab_widget.addTab(self.tab_speech, '语音识别')

        central_widget = QWidget(self) #设置主体
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(self.tab_widget)
        central_widget.setLayout(central_layout)

        self.setCentralWidget(central_widget)

        
        # 创建定时器
        self.timer = QTimer(self)  # 创建一个定时器对象
        self.timer.timeout.connect(self.text_input)  # 连接定时器的timeout信号到translate方法
        self.timer.start(1000)  # 设置定时器时间间隔为1000毫秒（1秒）

        #网络连接状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 添加一个永久显示的标签
        self.status_label = QLabel(self.connection_status)
        self.status_bar.addPermanentWidget(self.status_label, 1)

        # 添加一个按钮，用于更新状态信息
        self.update_button = QPushButton("重试Retry", self)
        self.update_button.clicked.connect(self.check_connection)
        self.status_bar.addPermanentWidget(self.update_button, 3)

        # 显示窗口
        self.show()

    def check_connection(self):
        if(self.check_proxy()):
            self.connection_status = "网络已连接"
            print("网络已连接")
        else:
            self.connection_status = "网络未连接，请配置网络or代理服务器"
            print("网络未连接")
        self.status_label.setText(self.connection_status)

    def check_proxy(self,timeout=5):
            try:
                # 尝试向Hugging Face服务器发送一个GET请求
                requests.get('https://www.huggingface.co', timeout=timeout)
                return True
            except requests.exceptions.RequestException:
                pass
            return False

    def create_translate_tab(self):#文本翻译页
        
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建上方输入区域
        input_layout = QHBoxLayout()
        input_layoutL = QVBoxLayout()
        combo_layout = QHBoxLayout()
        self.source_text_input_title = QLabel("输入文字：")
        combo_layout.addWidget(self.source_text_input_title)
        # 创建翻译选项
        self.translate_option1 = QPushButton('汉译英', tab)  # 初始显示为“汉译英”
        self.translate_option1.clicked.connect(self.change_translate_option)  # 连接信号到槽函数
        combo_layout.addWidget(self.translate_option1)
        input_layoutL.addLayout(combo_layout)

        self.source_text_input = QTextEdit(tab)
        self.source_text_input.setFont(QFont("Arial", 12))
        input_layoutL.addWidget(self.source_text_input)
        
        input_layout.addLayout(input_layoutL)

        input_layoutR = QVBoxLayout()
        
        # 创建分词结果输出框
        self.tokenize_output_title = QLabel("分词结果：")
        input_layoutR.addWidget(self.tokenize_output_title)
        self.tokenize_output = QTextEdit(tab)
        self.tokenize_output.setFont(QFont("Arial", 12))
        self.tokenize_output.setReadOnly(True)
        input_layoutR.addWidget(self.tokenize_output)
        
        input_layout.addLayout(input_layoutR)

        # 创建下方输出区域
        output_layout = QHBoxLayout()
        output_layoutL = QVBoxLayout()
        
        # 创建目标语言输出框
        self.target_text_output_title = QLabel("翻译结果1：")
        output_layoutL.addWidget(self.target_text_output_title)
        self.target_text_output = QTextEdit(tab)
        self.target_text_output.setFont(QFont("Arial", 12))
        self.target_text_output.setReadOnly(True)
        output_layoutL.addWidget(self.target_text_output)

        output_layout.addLayout(output_layoutL)

        output_layoutR = QVBoxLayout()
        
        # 创建目标语言输出框2
        self.target_text2_output_title = QLabel("翻译结果2：")
        output_layoutR.addWidget(self.target_text2_output_title)
        self.target_text2_output = QTextEdit(tab)
        self.target_text2_output.setFont(QFont("Arial", 12))
        self.target_text2_output.setReadOnly(True)
        output_layoutR.addWidget(self.target_text2_output)

        output_layout.addLayout(output_layoutR)

        # 添加到主布局
        layout.addLayout(input_layout)  # 添加左侧布局
        layout.addLayout(output_layout)    # 添加右侧布局

        tab.setLayout(layout)

        return tab
    
    def create_ocr_tab(self):#识图翻译页
        tab = QWidget()
        layout = QVBoxLayout(tab)
       
        # OCR图片展示
        self.ocr_image_label = QLabel(tab)
        layout.addWidget(self.ocr_image_label)

        combo_layoutH = QHBoxLayout()
        # 选择图片按钮
        self.ocr_button = QPushButton('选择图片', tab)
        self.ocr_button.clicked.connect(self.open_image_dialog)
        combo_layoutH.addWidget(self.ocr_button)
        #开始识别按钮
        self.rec_button = QPushButton('开始识别', tab)
        self.rec_button.clicked.connect(self.rec_img)
        combo_layoutH.addWidget(self.rec_button)
        
        layout.addLayout(combo_layoutH)

        combo_layoutM = QHBoxLayout()
        self.ocr_source_text_input_title = QLabel("识别文字：")
        combo_layoutM.addWidget(self.ocr_source_text_input_title)
        # 创建翻译选项
        self.translate_option2 = QPushButton('汉译英', tab)  # 初始显示为“汉译英”
        self.translate_option2.clicked.connect(self.change_translate_option)  # 连接信号到槽函数
        combo_layoutM.addWidget(self.translate_option2)
        
        layout.addLayout(combo_layoutM)
        
        #识别文字文本框
        self.ocr_source_text_input = QTextEdit(tab)
        self.ocr_source_text_input.setFont(QFont("Arial", 12))
        layout.addWidget(self.ocr_source_text_input)
        
        combo_layoutL = QHBoxLayout()
        combo_layoutLL = QVBoxLayout()
        #翻译结果1
        self.ocr_target_text_output_title = QLabel("翻译结果1：")
        combo_layoutLL.addWidget(self.ocr_target_text_output_title)
        self.ocr_target_text_output = QTextEdit(tab)
        self.ocr_target_text_output.setFont(QFont("Arial", 12))
        self.ocr_target_text_output.setReadOnly(True)
        
        combo_layoutLL.addWidget(self.ocr_target_text_output)
        combo_layoutL.addLayout(combo_layoutLL)
        
        combo_layoutLR = QVBoxLayout()
        #翻译结果2
        self.ocr_target_text2_output_title = QLabel("翻译结果2：")
        combo_layoutLR.addWidget(self.ocr_target_text2_output_title)
        self.ocr_target_text2_output = QTextEdit(tab)
        self.ocr_target_text2_output.setFont(QFont("Arial", 12))
        self.ocr_target_text2_output.setReadOnly(True)
        
        combo_layoutLR.addWidget(self.ocr_target_text2_output)
        combo_layoutL.addLayout(combo_layoutLR)
        layout.addLayout(combo_layoutL)

        tab.setLayout(layout)
        return tab

    def create_speech_tab(self):#语音翻译页
        tab = QWidget()
        layout = QVBoxLayout(tab)

        #初始化变量
        self.is_recording = False
        self.stream = None
        self.frames = []
        self.audio = pyaudio.PyAudio()

        combo_layoutH = QHBoxLayout()
        self.stt_source_text_input_title = QLabel("识别文字：")
        combo_layoutH.addWidget(self.stt_source_text_input_title)
        # 创建翻译选项
        self.translate_option3 = QPushButton('汉译英', tab)  # 初始显示为“汉译英”
        self.translate_option3.clicked.connect(self.change_translate_option)  # 连接信号到槽函数
        combo_layoutH.addWidget(self.translate_option3)
        
        # 语音识别按钮
        self.speech_button = QPushButton('开始录音', tab)
        self.speech_button.clicked.connect(self.toggle_recording)
        combo_layoutH.addWidget(self.speech_button)
        
        upload_button = QPushButton('上传录音', tab)
        upload_button.clicked.connect(self.upload_record)
        combo_layoutH.addWidget(upload_button)
        
        layout.addLayout(combo_layoutH)
        #语音识别文本框
        self.stt_source_text_input = QTextEdit(tab)
        self.stt_source_text_input.setFont(QFont("Arial", 12))
        layout.addWidget(self.stt_source_text_input)
        
        combo_layoutL = QHBoxLayout()
        combo_layoutLL = QVBoxLayout()
        #翻译结果1
        self.stt_target_text_output_title = QLabel("翻译结果1：")
        combo_layoutLL.addWidget(self.stt_target_text_output_title)
        self.stt_target_text_output = QTextEdit(tab)
        self.stt_target_text_output.setFont(QFont("Arial", 12))
        self.stt_target_text_output.setReadOnly(True)
        combo_layoutLL.addWidget(self.stt_target_text_output)
        combo_layoutL.addLayout(combo_layoutLL)

        combo_layoutLR = QVBoxLayout()
        #翻译结果2
        self.stt_target_text2_output_title = QLabel("翻译结果2：")
        combo_layoutLR.addWidget(self.stt_target_text2_output_title)
        self.stt_target_text2_output = QTextEdit(tab)
        self.stt_target_text2_output.setFont(QFont("Arial", 12))
        self.stt_target_text2_output.setReadOnly(True)
        combo_layoutLR.addWidget(self.stt_target_text2_output)
        combo_layoutL.addLayout(combo_layoutLR)

        layout.addLayout(combo_layoutL)
        
        # 创建定时器，用于定期检查录音状态
        #为什么这里用计时器不用循环呢？

        #如果这里用循环，CPU全部集中在读数据流上，无暇应对你的”取消录制”操作，图形化界面会卡死
        #故采用定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_recording)
        self.timer.start(10) 

        # 添加到主布局
        tab.setLayout(layout)
        return tab
    
    def toggle_recording(self):
        #切换开和关
        if self.is_recording:
            self.is_recording = False
            self.speech_button.setText('开始录音')
            self.speech_button.setStyleSheet("background-color: white; ")
            self.stream.stop_stream()
            self.stream.close()
            print("录制结束.")
            with wave.open('temp.wav', 'wb') as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(self.audio.get_sample_size(FORMAT))
                wav_file.setframerate(RATE)
                wav_file.writeframes(b''.join(self.frames))
            print("音频保存完毕.")
            QMessageBox.information(self, "录制完成", "音频录制完成，准备发送到百度语音识别API。")
            self.send_to_api('temp.wav')
        else:
            self.frames = []
            self.start_recording()
            
    def start_recording(self):
        # 开始录制ing：
        if not self.is_recording:
        
            self.is_recording = True
            # 更新按钮状态，再按就是停止录音
            self.speech_button.setText("停止录音")
            self.speech_button.setStyleSheet("background-color: red; color: white;")

            # 打开流录制音频
            self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,  frames_per_buffer=CHUNK)
            print("正在录制音频...")

            #这之后，timer每次检测条件满足，timer就开始了录

    def check_recording(self):
        
        if self.is_recording:
           try:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            self.frames.append(data)
           except Exception as e:
            print(e)
            self.is_recording = False
            

    def upload_record(self):
        audio_path, _ = QFileDialog.getOpenFileName(self, "选择音频", "", "音频文件 (*.wav *.pcm *.m4a)    ")
        if audio_path :
            self.send_to_api(audio_path=audio_path)
            

    def send_to_api(self,audio_path):
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode()

        # 计算音频数据的字节数
        audio_len = len(audio_data)

        url = "https://vop.baidu.com/server_api"

        dev_pid = 1537
        if self.mode == "英译汉":
            dev_pid = 1737
        else :
            dev_pid = 1537

        payload = json.dumps({
            "format": "pcm",
            "rate": 16000,
            "channel": 1,
            "cuid": "26tQ2f03yoRZSF5tD3OUnOappYUVGMo4",
            "token": "24.fc06dd924c3eb4655b17ab7c4d0d6666.2592000.1718203866.282335-70265727",
            "dev_pid"	: dev_pid,
            "speech": audio_base64,
            "len": audio_len
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        # 检查响应状态码
        if response.status_code == 200:
            # 解析返回的JSON数据
            result = json.loads(response.text)
            # 提取识别结果
            text = result.get("result", [])
            if text:
                print("识别结果：", "".join(text))

                self.stt_source_text_input.setPlainText("".join(text))
            else:
                print("未识别到有效内容")
        else:
            print("请求失败，状态码：", response.status_code)

   
    def open_image_dialog(self):
        # 打开图片选择对话框
        image_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg)    ")
        if image_path:
            # 将图片显示在标签上
            #print(image_path)
            self.image_path = image_path
            pixmap = QPixmap(image_path)
            # 检查图片是否超过限制尺寸
            MAX_WIDTH = 1200  # 举例：最大宽度为300像素
            MAX_HEIGHT = 800  # 举例：最大高度为200像素
        
            if pixmap.width() > MAX_WIDTH or pixmap.height() > MAX_HEIGHT:
                # 调整图片尺寸以适应限制
                new_size = pixmap.size()
                if pixmap.width() > MAX_WIDTH:
                    scale_ratio = MAX_WIDTH / float(pixmap.width())
                    new_size *= scale_ratio
                if pixmap.height() > MAX_HEIGHT:
                    scale_ratio = MAX_HEIGHT / float(pixmap.height())
                    new_size *= scale_ratio
            
                # 保持宽高比缩放图片
                new_pixmap = pixmap.scaled(new_size, Qt.KeepAspectRatio)

                # 设置标签的图片
                self.ocr_image_label.setPixmap(new_pixmap)
            else:
                # 直接显示原始图片
                self.ocr_image_label.setPixmap(pixmap)

    def rec_img(self):
        '''
        通用文字识别（高精度版）
        '''

        request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
        # 二进制方式打开图片文件
        f = open(str(self.image_path), 'rb')
        img = base64.b64encode(f.read())

        params = {"image":img}
        access_token = '24.5c22507e562c2c4606516b99677ab63e.2592000.1717916413.282335-68876272'
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        if response:
            #print (response.json())
            if 'words' in response.json():
                text_result = response.json()['words']
                #print(text_result)
            else:
                # 如果response_json是一个列表，我们遍历列表并获取每个字典中的'words'值
                text_results = [item['words'] for item in response.json()['words_result']]
                #print(text_results)  # 打印结果，或者进行其他操作
                self.ocr_source_text_input.setPlainText(' '.join(text_results))


    def change_translate_option(self):
        if self.mode == "汉译英":
            self.translate_option1.setText("英译汉")
            self.translate_option2.setText("英译汉")
            self.translate_option3.setText("英译汉")
            self.mode = "英译汉"
            self.source_text = ""
            self.ocr_source_text = ""
            self.stt_source_text = ""
        else :
            self.translate_option1.setText("汉译英")
            self.translate_option2.setText("汉译英")
            self.translate_option3.setText("汉译英")
            self.mode = "汉译英"
            self.source_text = ""
            self.ocr_source_text = ""
            self.stt_source_text = ""

    def text_input(self):
        text1 = self.source_text_input.toPlainText()
        text2 = self.ocr_source_text_input.toPlainText()
        text3 = self.stt_source_text_input.toPlainText()
        if (self.source_text != text1) and self.translate_idle :
            self.translate_idle = False
            self.source_text = text1
            self.tab_num = 1
            self.translation_thread.input_text(self.source_text)
            self.translation_thread.input_mode(self.mode)
        elif (self.ocr_source_text != text2) and self.translate_idle :
            self.translate_idle = False
            self.ocr_source_text = text2
            self.tab_num = 2
            self.translation_thread.input_text(self.ocr_source_text)
            self.translation_thread.input_mode(self.mode)
        elif (self.stt_source_text != text3) and self.translate_idle :
            self.translate_idle = False
            self.stt_source_text = text3
            self.tab_num = 3
            self.translation_thread.input_text(self.stt_source_text)
            self.translation_thread.input_mode(self.mode)
    
    def token_output(self, source_tokens):
        if(self.tab_num == 1):
            self.source_tokens = source_tokens
            self.tokenize_output.setPlainText(self.source_tokens)

    def text_output(self, target_text, target_text2):
        if(target_text == 'Error'):
            QMessageBox.critical(self, 'Error', target_text2)
            self.translation_thread.stop()
        else:
            self.translate_idle = True
            if(self.tab_num == 1) :
                self.target_text = target_text
                self.target_text_output.setPlainText(self.target_text)
                self.target_text2 = target_text2
                self.target_text2_output.setPlainText(self.target_text2)
            elif(self.tab_num == 2) :
                self.ocr_target_text = target_text
                self.ocr_target_text_output.setPlainText(self.ocr_target_text)
                self.ocr_target_text2 = target_text2
                self.ocr_target_text2_output.setPlainText(self.ocr_target_text2)
            elif(self.tab_num == 3) :
                self.stt_target_text = target_text
                self.stt_target_text_output.setPlainText(self.stt_target_text)
                self.stt_target_text2 = target_text2
                self.stt_target_text2_output.setPlainText(self.stt_target_text2)

    def closeEvent(self, event):
        # 关闭窗口时停止翻译线程
        self.translation_thread.stop()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = TranslatorApp()
    sys.exit(app.exec_())
