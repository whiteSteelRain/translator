
# encoding:utf-8
from subword_nmt import apply_bpe
import codecs
import requests
import base64
import sys
import jieba
import ctranslate2
import re
import wave
import pyaudio
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QComboBox, QLabel, QMessageBox, QStatusBar, QSpacerItem
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QIcon, QFont,QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QComboBox, QLabel, QMessageBox, QStatusBar
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QTextEdit, QPushButton, QComboBox,
    QLabel, QMessageBox, QStatusBar, QVBoxLayout, QHBoxLayout, QFileDialog, QWidget
)
from functools import partial



# 定义录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024



from PyQt5.QtCore import QThread, pyqtSignal

class TranslatorApp(QMainWindow,QThread):
    
   

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('翻译器')
        self.setGeometry(200, 100, 800, 600)



        self.tab_widget = QTabWidget(self)
        self.tab_ocr = self.create_ocr_tab()
        self.tab_speech = self.create_speech_tab()
        self.tab_translate = self.create_translate_tab()

        tab_bar = self.tab_widget.tabBar()
        tab_bar.setMinimumSize(500, 100)  # 设置标签的最小宽度和高度
        
        #self.segment_button.clicked.connect(self.segment)


        self.tab_widget.addTab(self.tab_translate, '文本翻译&分词')
        self.tab_widget.addTab(self.tab_ocr, 'OCR识图')
        self.tab_widget.addTab(self.tab_speech, '语音识别')

        
        self.tab_widget.currentChanged.connect(self.onTabChange)

        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(self.tab_widget)
        central_widget.setLayout(central_layout)

        self.setCentralWidget(central_widget)

        # 添加状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)




      

        # 显示窗口
        self.show()

    def onTabChange(self):
        self.source_text.clear()
        self.segment_text.clear()
        self.target_text.clear()
        #self.ocr_source_text.clear()
        #self.ocr_target_text.clear()
        self.translation_option.clear()

    def create_translate_tab(self):
        
        tab = QWidget()
        layout = QHBoxLayout(tab)  # 使用水平布局

        # 创建左侧的翻译区域
        translate_layout = QVBoxLayout()
        self.source_text = QTextEdit(tab)
        self.source_text.setFont(QFont("Arial", 14))
        translate_layout.addWidget(self.source_text)

        # 创建翻译选项和按钮
        combo_layout = QHBoxLayout()
        self.translation_option = QComboBox(tab)
        self.translation_option.addItem("汉译英")
        self.translation_option.addItem("英译汉")
        combo_layout.addWidget(self.translation_option)

        print(self.translation_option.currentText())

        
        self.translate_button = QPushButton('翻译', tab)
        self.translate_button.clicked.connect(partial(self.Fs_Translate,self.source_text))
        combo_layout.addWidget(self.translate_button)

        translate_layout.addLayout(combo_layout)

        self.target_text = QTextEdit(tab)
        self.target_text.setFont(QFont("Arial", 14))
        self.target_text.setReadOnly(True)
        translate_layout.addWidget(self.target_text)

        # 创建右侧的分词区域
        segment_layout = QVBoxLayout()
        #self.segment_button = QPushButton('分词', tab)
        #segment_layout.addWidget(self.segment_button)

        self.segment_text = QTextEdit(tab)
        self.segment_text.setFont(QFont("Arial", 14))
        self.segment_text.setReadOnly(True)
        segment_layout.addWidget(self.segment_text)

        # 添加到主布局
        layout.addLayout(translate_layout)  # 添加左侧布局
        layout.addLayout(segment_layout)    # 添加右侧布局

        tab.setLayout(layout)
        








        return tab


    def translate(self):
        if (self.word_list is None):
            # 如果为空，弹出警告框
            QMessageBox.warning(self, '警告', '请先进行分词')
            return
        
        if(self.translation_option.currentText() == "汉译英"):
            translator = ctranslate2.Translator("en_zh_cmodel/", device="cpu")
        else:
            translator = ctranslate2.Translator("zh_en_cmodel/", device="cpu")

        results = translator.translate_batch([list(self.word_list)])

        translation = ''.join(results[0].hypotheses[0])
        print(translation)
        #self.target_text.setPlainText(re.sub(r"@@|[']+", "", translation))
        self.target_text.setPlainText(re.sub(r'@@\s*|\s*@+(?=\s*$)', '', translation))
        return

    def segment(self):

        raw = self.source_text.toPlainText()

        if not raw.strip():
            # 如果为空，弹出警告框
            QMessageBox.warning(self, '警告', '请输入要翻译的文本！')
            return
        if(self.translation_option.currentText() == "汉译英"):
            jieba.load_userdict('en2zh_data/dict.zh.txt')
            words = jieba.cut(raw)
        else:
              # 加载BPE规则
            with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
                bpe = apply_bpe.BPE(f)
                # 加载词汇表
            words = bpe.segment_tokens(raw.split())

        
        self.word_list = list(words)  # 直接将分词结果转换成列表并赋值
        self.segment_text.setPlainText('\' \''.join(self.word_list))
        return

    def Fs_Translate(self,source):
        '''通过fairseq翻译的模块,输入raw,输出分词结果,翻译结果'''
        raw = source.toPlainText()
        if not raw.strip():
            # 如果为空，弹出警告框
            QMessageBox.warning(self, '警告', '请输入要翻译的文本！')
            return
        
        print(self.translation_option.currentText())


        if(self.translation_option.currentText() == "汉译英"):
            jieba.load_userdict('en2zh_data/dict.zh.txt')
            words = jieba.cut(raw)
        else:
              # 加载BPE规则
            with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
                bpe = apply_bpe.BPE(f)
                # 加载词汇表
            words = bpe.segment_tokens(raw.split())

        
        word_list = list(words)  # 直接将分词结果转换成列表并赋值
        #segment_text.setPlainText('\' \''.join(word_list))
        if(self.translation_option.currentText() == "汉译英"):
            translator = ctranslate2.Translator("en_zh_cmodel/", device="cpu")
        else:
            translator = ctranslate2.Translator("zh_en_cmodel/", device="cpu")

        results = translator.translate_batch([list(word_list)])
        translation = ' '.join(results[0].hypotheses[0])

        target = re.sub(r"@@|[']+", "", translation)

        self.segment_text.setPlainText('\' \''.join(word_list))
        self.target_text.setPlainText(target)
        
        print(self.target_text.toPlainText())
        return

    def create_ocr_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        #print(self.target_text.toPlainText())
        # OCR图片展示
        self.ocr_image_label = QLabel(tab)
        #self.ocr_image_label.setPixmap(QPixmap(":/images/placeholder.png"))
        layout.addWidget(self.ocr_image_label)

        # 选择图片按钮
        self.ocr_button = QPushButton('选择图片', tab)
        self.ocr_button.clicked.connect(self.open_image_dialog)
        layout.addWidget(self.ocr_button)

        self.rec_button = QPushButton('开始识别', tab)
        self.rec_button.clicked.connect(self.rec_img)
        layout.addWidget(self.rec_button)

        ocr_translate_layout = QVBoxLayout()
        self.ocr_source_text = QTextEdit(tab)
        self.ocr_source_text.setFont(QFont("Arial", 14))
        ocr_translate_layout.addWidget(self.ocr_source_text)

        combo_layout = QHBoxLayout()
        self.translation_option = QComboBox(tab)
        self.translation_option.addItem("汉译英")
        self.translation_option.addItem("英译汉")
        combo_layout.addWidget(self.translation_option)


        self.ocr_translate_button = QPushButton('翻译', tab)
        
        combo_layout.addWidget(self.ocr_translate_button)

        ocr_translate_layout.addLayout(combo_layout)

        

        self.target_text = QTextEdit(tab)
        self.target_text.setFont(QFont("Arial", 14))
        self.target_text.setReadOnly(True)
        ocr_translate_layout.addWidget(self.target_text)

        print(self.target_text.toPlainText())

        self.ocr_translate_button.clicked.connect(partial(self.Fs_Translate,self.ocr_source_text))
        # 添加到主布局
        layout.addLayout(ocr_translate_layout)  # 添加左侧布局
        tab.setLayout(layout)
        return tab

    def open_image_dialog(self):
        # 打开图片选择对话框
        image_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg)    ")
        if image_path:
            # 将图片显示在标签上
            #print(image_path)
            self.image_path = image_path
            pixmap = QPixmap(image_path)
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
            print (response.json())
            if 'words' in response.json():
                text_result = response.json()['words']
                print("hello")
            else:
                # 如果response_json是一个列表，我们遍历列表并获取每个字典中的'words'值
                text_results = [item['words'] for item in response.json()['words_result']]
                #print(text_results)  # 打印结果，或者进行其他操作
                self.ocr_source_text.setPlainText(' '.join(text_results))

    def ocr_direct_trans(self):
        raw = self.ocr_source_text.toPlainText()
        if not raw.strip():
            # 如果为空，弹出警告框
            QMessageBox.warning(self, '警告', '请输入要翻译的文本！')
            return
        

        if(self.ocr_translation_option.currentText() == "汉译英"):
            jieba.load_userdict('en2zh_data/dict.zh.txt')
            words = jieba.cut(raw)
        else:
            
              # 加载BPE规则
            with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
                bpe = apply_bpe.BPE(f)
                # 加载词汇表
            

            words = bpe.segment_tokens(raw.split())

        
        self.ocr_word_list = list(words)  # 直接将分词结果转换成列表并赋值
        #self.seg = '\' \''.join(self.word_list)


        if(self.ocr_translation_option.currentText() == "汉译英"):
            translator = ctranslate2.Translator("en_zh_cmodel/", device="cpu")
        else:
            translator = ctranslate2.Translator("zh_en_cmodel/", device="cpu")

        results = translator.translate_batch([list(self.ocr_word_list)])

        translation = ' '.join(results[0].hypotheses[0])
        target = re.sub(r"@@|[']+", "", translation)

        self.ocr_target_text.setPlainText(target)

        
        return

    def create_speech_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        #初始化变量
        self.is_recording = False
        self.stream = None
        self.frames = []
        self.audio = pyaudio.PyAudio()

        # 语音识别按钮
        self.speech_button = QPushButton('实时录音', tab)
        self.speech_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.speech_button)

        self.upload_button = QPushButton('上传本地录音文件',tab)
        self.upload_button.clicked.connect(self.upload_record)
        layout.addWidget(self.upload_button)


        #识别结果输出框
        audio_translate_layout = QVBoxLayout()
        self.audio_source_text = QTextEdit(tab)
        self.audio_source_text.setFont(QFont("Arial", 14))
        audio_translate_layout.addWidget(self.audio_source_text)
    
        
        #汉英选择框
        combo_layout = QHBoxLayout()
        self.audio_translation_option = QComboBox(tab)
        self.audio_translation_option.addItem("汉译英")
        self.audio_translation_option.addItem("英译汉")
        combo_layout.addWidget(self.audio_translation_option)

      

        #翻译按钮
        self.audio_translate_button = QPushButton('翻译', tab)
        self.audio_translate_button.clicked.connect(self.audio_translation)
        combo_layout.addWidget(self.audio_translate_button)

        audio_translate_layout.addLayout(combo_layout)


        #目标文本输出
        self.audio_target_text = QTextEdit(tab)
        self.audio_target_text.setFont(QFont("Arial", 14))
        self.audio_target_text.setReadOnly(True)
        audio_translate_layout.addWidget(self.audio_target_text)

       
        # 创建定时器，用于定期检查录音状态
        #为什么这里用计时器不用循环呢？

        #如果这里用循环，CPU全部集中在读数据流上，无暇应对你的”取消录制”操作，图形化界面会卡死
            #故采用定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_recording)
        self.timer.start(10) 



        # 添加到主布局
        layout.addLayout(audio_translate_layout)  # 添加左侧布局
        tab.setLayout(layout)
        return tab

    def upload_record(self):
        audio_path, _ = QFileDialog.getOpenFileName(self, "选择音频", "", "音频文件 (*.wav *.pcm *.m4a)    ")
        self.send_to_api(audio_path=audio_path)

    def toggle_recording(self):
        #切换开和关
        if self.is_recording:
            self.is_recording = False
            self.speech_button.setText('开始录音')
            self.speech_button.setStyleSheet("background-color: white; ")
            #self.record_button.setIcon(QIcon(':/icons/record.png'))  # 回到初始图标
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
            self.start_recording()

    
    def send_to_api(self,audio_path):
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode()

        # 计算音频数据的字节数
        audio_len = len(audio_data)

        url = "https://vop.baidu.com/server_api"

        payload = json.dumps({
            "format": "pcm",
            "rate": 16000,
            "channel": 1,
            "cuid": "26tQ2f03yoRZSF5tD3OUnOappYUVGMo4",
            "token": "24.fc06dd924c3eb4655b17ab7c4d0d6666.2592000.1718203866.282335-70265727",
            "dev_pid"	: 1537,
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

                self.audio_source_text.setPlainText("".join(text))
            else:
                print("未识别到有效内容")


            
            
        else:
            print("请求失败，状态码：", response.status_code)

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
        

    def audio_translation(self):
        pass






if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = TranslatorApp()
    sys.exit(app.exec_())



