
# encoding:utf-8
from subword_nmt import apply_bpe
import codecs
import requests
import base64
import sys
import jieba
import ctranslate2
import re

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QComboBox, QLabel, QMessageBox, QStatusBar, QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont,QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QComboBox, QLabel, QMessageBox, QStatusBar
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QTextEdit, QPushButton, QComboBox,
    QLabel, QMessageBox, QStatusBar, QVBoxLayout, QHBoxLayout, QFileDialog, QWidget
)
class TranslatorApp(QMainWindow):
    
   

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
        self.translate_button.clicked.connect(self.translate)
        self.segment_button.clicked.connect(self.segment)


        self.tab_widget.addTab(self.tab_translate, '文本翻译&分词')
        self.tab_widget.addTab(self.tab_ocr, 'OCR识图')
        self.tab_widget.addTab(self.tab_speech, '语音识别')

        


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
        combo_layout.addWidget(self.translate_button)

        translate_layout.addLayout(combo_layout)

        self.target_text = QTextEdit(tab)
        self.target_text.setFont(QFont("Arial", 14))
        self.target_text.setReadOnly(True)
        translate_layout.addWidget(self.target_text)

        # 创建右侧的分词区域
        segment_layout = QVBoxLayout()
        self.segment_button = QPushButton('分词', tab)
        segment_layout.addWidget(self.segment_button)

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

        translation = ' '.join(results[0].hypotheses[0])
        
        self.target_text.setPlainText(re.sub(r"@@|[']+", "", translation))
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
        #temp = '\' \''.join(self.word_list)
        
        self.segment_text.setPlainText('\' \''.join(self.word_list))
        return




    def create_ocr_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
       
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
    
        #self.source_text.setPlainText('\' \''.join(self.word_list))
        
        combo_layout = QHBoxLayout()
        self.ocr_translation_option = QComboBox(tab)
        self.ocr_translation_option.addItem("汉译英")
        self.ocr_translation_option.addItem("英译汉")
        combo_layout.addWidget(self.ocr_translation_option)

        #print(self.translation_option.currentText())


        self.ocr_translate_button = QPushButton('翻译', tab)
        self.ocr_translate_button.clicked.connect(self.ocr_direct_trans)
        combo_layout.addWidget(self.ocr_translate_button)

        ocr_translate_layout.addLayout(combo_layout)

        self.ocr_target_text = QTextEdit(tab)
        self.ocr_target_text.setFont(QFont("Arial", 14))
        self.ocr_target_text.setReadOnly(True)
        ocr_translate_layout.addWidget(self.ocr_target_text)

       

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
                print(text_result)
            else:
                # 如果response_json是一个列表，我们遍历列表并获取每个字典中的'words'值
                text_results = [item['words'] for item in response.json()['words_result']]
                #print(text_results)  # 打印结果，或者进行其他操作
                self.ocr_source_text.setPlainText('\' \''.join(text_results))

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

        # 语音识别按钮
        speech_button = QPushButton('开始录音', tab)
        speech_button.clicked.connect(self.start_speech_recognition)
        layout.addWidget(speech_button)



        audio_translate_layout = QVBoxLayout()
        self.audio_source_text = QTextEdit(tab)
        self.audio_source_text.setFont(QFont("Arial", 14))
        audio_translate_layout.addWidget(self.audio_source_text)
    
        #self.source_text.setPlainText('\' \''.join(self.word_list))
        
        combo_layout = QHBoxLayout()
        self.audio_translation_option = QComboBox(tab)
        self.audio_translation_option.addItem("汉译英")
        self.audio_translation_option.addItem("英译汉")
        combo_layout.addWidget(self.audio_translation_option)

        #print(self.translation_option.currentText())


        self.audio_translate_button = QPushButton('翻译', tab)
        self.audio_translate_button.clicked.connect(self.audio_direct_trans)
        combo_layout.addWidget(self.audio_translate_button)

        audio_translate_layout.addLayout(combo_layout)

        self.audio_target_text = QTextEdit(tab)
        self.audio_target_text.setFont(QFont("Arial", 14))
        self.audio_target_text.setReadOnly(True)
        audio_translate_layout.addWidget(self.audio_target_text)

       

        # 添加到主布局
        layout.addLayout(audio_translate_layout)  # 添加左侧布局
        tab.setLayout(layout)
        return tab

   

    def start_speech_recognition(self):
        # 开始语音识别逻辑
        pass

    def audio_direct_trans(self):
        pass






if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = TranslatorApp()
    sys.exit(app.exec_())



