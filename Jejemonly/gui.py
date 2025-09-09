import sys
import os
import warnings
import time
import threading

warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QFontDatabase, QFontMetrics, QPainterPath
from J3jemonly.jejemon_normalizer import JejemonNormalizer

class ProcessStep(QFrame):
    step_completed = pyqtSignal(int, str)
    process_finished = pyqtSignal()
    
    def __init__(self, title, icon_type, image_path=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_type = icon_type
        self.image_path = image_path
        self.setFixedSize(120, 120)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        self.pixmap = None
        self.highlighted = False
        self.text = ""
        self.normalizer = None
        self.processing_thread = None
        
        if self.image_path and os.path.exists(self.image_path):
            self.pixmap = QPixmap(self.image_path)

    def set_normalizer(self, normalizer):
        """Set the normalizer for text processing"""
        self.normalizer = normalizer

    def process_text_step(self, text, step_labels):
        """Process text through all normalization steps with delays"""
        if not self.normalizer:
            return
            
        def worker():
            try:
                # Step 1: Original text
                self.step_completed.emit(0, text)
                time.sleep(0.8)
                
                # Step 2: Punctuation evaluation
                result = self.normalizer.normalize_text(text) #type: ignore
                self.step_completed.emit(1, result['punctuation_evaluated'])
                time.sleep(0.8)
                
                # Step 3: Character replacement
                self.step_completed.emit(2, result['character_replaced'])
                time.sleep(0.8)
                
                # Step 4: Tokenization
                self.step_completed.emit(3, result['tokenized'])
                time.sleep(0.8)
                
                # Step 5: Normalization
                self.step_completed.emit(4, result['normalized'])
                time.sleep(0.5)
                
                self.process_finished.emit()
                
            except Exception as e:
                print(f"Error in processing: {e}")
                self.process_finished.emit()
        
        # Run in separate thread to prevent UI freezing
        self.processing_thread = threading.Thread(target=worker)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def update_text(self, text):
        self.text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        border_radius = 20
        border_width = 4 if self.highlighted else 2
        max_rect = rect.adjusted(border_width//2, border_width//2, -border_width//2, -border_width//2)
        
        if self.pixmap:
            img_ratio = self.pixmap.width() / self.pixmap.height()
            box_ratio = max_rect.width() / max_rect.height()
            if img_ratio > box_ratio:
                img_w = max_rect.width()
                img_h = int(img_w / img_ratio)
            else:
                img_h = max_rect.height()
                img_w = int(img_h * img_ratio)
            x = max_rect.left() + (max_rect.width() - img_w) // 2
            y = max_rect.top() + (max_rect.height() - img_h) // 2
            img_rect = QRect(x, y, img_w, img_h)
            path = QPainterPath()
            path.addRoundedRect(QRectF(img_rect), border_radius, border_radius)
            painter.save()
            painter.setClipPath(path)
            scaled_pixmap = self.pixmap.scaled(img_w, img_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(img_rect, scaled_pixmap)
            painter.restore()
            border_color = QColor(76, 175, 80) if self.highlighted else QColor(68, 68, 68)
            painter.setPen(QPen(border_color, border_width))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(img_rect), border_radius, border_radius)

        painter.setPen(QColor(255, 255, 255))
        parent = self.parent()
        if parent and hasattr(parent, 'bright_aura_font') and parent.bright_aura_font:
            font = QFont(parent.bright_aura_font, 10)
            painter.setFont(font)
            
        text_rect = QRectF(5, 85, self.width() - 10, 30)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)

class ArrowLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(5, 10, 25, 10)
        painter.drawLine(20, 5, 25, 10)
        painter.drawLine(20, 15, 25, 10)



class JejemonGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.normalizer = JejemonNormalizer()
        self.steps = []
        self.processing = False
        self.main_processor = None
        self.loadFonts()
        self.initUI()

    def loadFonts(self):
        font_dir = "assets/fonts"
        self.bright_aura_font = None
        self.super_adorable_font = None
        if os.path.exists(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    font_path = os.path.join(font_dir, font_file)
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                        if "bright" in font_file.lower() and "aura" in font_file.lower():
                            self.bright_aura_font = font_family
                        elif "super" in font_file.lower() and "adorable" in font_file.lower():
                            self.super_adorable_font = font_family

    def initUI(self):
        self.setWindowTitle("JEJEMONLY")
        self.setFixedSize(1100, 600)
        self.setStyleSheet("""
            QMainWindow {
                background: #27262c;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: rgba(60, 60, 60, 0.8);
                border: 2px solid #444;
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 15px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666;
            }
            QTextEdit {
                background-color: rgba(60, 60, 60, 0.8);
                border: 2px solid #444;
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 12px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)

        title_label = QLabel("JEJEMONLY")
        title_font = QFont(self.super_adorable_font, 45, QFont.Bold) if self.super_adorable_font else QFont("Arial", 36, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #FFD700;")
        layout.addWidget(title_label)
        layout.addSpacing(30)

        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(10)

        self.step_labels = []
        step_info = [
            ("Raw", "raw", "assets/images/step1.png"),
            ("Punctuation Evaluated", "clean", "assets/images/step2.png"),
            ("Character Replaced", "special", "assets/images/step3.png"),
            ("Tokenized", "tokenized", "assets/images/step4.png"),
            ("Normalized", "normalized", "assets/images/step5.png")
        ]
        for i, (title, icon_type, image_path) in enumerate(step_info):
            vbox = QVBoxLayout()
            vbox.setSpacing(5)
            step = ProcessStep(title, icon_type, image_path=image_path)
            step.set_normalizer(self.normalizer)  # Set the normalizer
            vbox.addWidget(step, alignment=Qt.AlignHCenter)
            self.steps.append(step)

            label = QLabel("")
            label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            label.setWordWrap(True)
            label.setFixedWidth(120)
            if self.bright_aura_font:
                label.setFont(QFont(self.bright_aura_font, 12))
            label.setStyleSheet("color: white;")
            vbox.addWidget(label)
            self.step_labels.append(label)
            steps_layout.addLayout(vbox)
            if i < len(step_info) - 1:
                arrow = ArrowLabel()
                steps_layout.addWidget(arrow)

        layout.addLayout(steps_layout)
        layout.addSpacing(10)

        io_layout = QHBoxLayout()
        io_layout.setSpacing(15)
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your jejemon text here...")
        if self.bright_aura_font:
            input_font = QFont(self.bright_aura_font, 12)
            self.input_field.setFont(input_font)
        self.input_field.returnPressed.connect(self.process_text)
        input_layout.addWidget(self.input_field)
        input_layout.addSpacing(20)
        self.process_btn = QPushButton("▶")
        self.process_btn.setFixedSize(50, 50)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border-radius: 25px;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        self.process_btn.clicked.connect(self.process_text)
        input_layout.addWidget(self.process_btn)
        io_layout.addLayout(input_layout)
        layout.addLayout(io_layout)

        copyright_label = QLabel("© 2025 JEJEMONLY. All Rights Reserved.")
        if self.bright_aura_font:
            copyright_font = QFont(self.bright_aura_font, 10)
            copyright_label.setFont(copyright_font)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px;")
        layout.addWidget(copyright_label)
        self.center()

    def center(self):
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def process_text(self):
        text = self.input_field.text().strip()
        if not text or self.processing:
            return
        
        self.processing = True
        self.process_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        
        # Clear previous results
        for step in self.steps:
            step.update_text("")
            step.highlighted = False
            step.update()
        for label in self.step_labels:
            label.setText("")
        
        # Use the first step as the main processor (they all have the same normalizer)
        self.main_processor = self.steps[0]
        self.main_processor.step_completed.connect(self.on_step_completed)
        self.main_processor.process_finished.connect(self.on_process_finished)
        
        # Start processing
        self.main_processor.process_text_step(text, self.step_labels)

    def on_step_completed(self, step_index, text):
        self.step_labels[step_index].setText(text) # Update the step display
        self.highlight_step(self.steps[step_index]) # Highlight the current step

    # Disconnect signals to prevent memory leaks
    def on_process_finished(self):
        if self.main_processor:
            self.main_processor.step_completed.disconnect()
            self.main_processor.process_finished.disconnect()
            self.main_processor = None
            
        self.processing = False
        self.process_btn.setEnabled(True)
        self.input_field.setEnabled(True)

    def highlight_step(self, step):
        step.highlighted = True
        step.update()
        QTimer.singleShot(600, lambda: self.unhighlight_step(step))

    def unhighlight_step(self, step):
        step.highlighted = False
        step.update()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = JejemonGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()