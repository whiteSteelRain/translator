import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap

class ImageUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        # 创建一个垂直布局
        layout = QVBoxLayout()
        
        # 创建一个按钮，点击后弹出文件选择对话框
        self.uploadButton = QPushButton('上传图片', self)
        self.uploadButton.clicked.connect(self.chooseImage)
        layout.addWidget(self.uploadButton)
        
        # 创建一个标签，用于显示图片
        self.imageLabel = QLabel(self)
        layout.addWidget(self.imageLabel)
        
        # 设置布局
        self.setLayout(layout)
        
        # 设置窗口标题和初始大小
        self.setWindowTitle('图片上传示例')
        self.setGeometry(100, 100, 300, 200)
    
    def chooseImage(self):
        # 弹出文件选择对话框，选择图片文件
        image_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg)")
        if image_path:
            # 将图片显示在标签上
            pixmap = QPixmap(image_path)
            self.imageLabel.setPixmap(pixmap)

def main():
    app = QApplication(sys.argv)
    ex = ImageUploader()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()