# gui/main_app.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTabWidget, QLineEdit, QFormLayout, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from api.openai_api import analyze_image_with_gpt
from db.db_handler import DBHandler
from utils.file_handler import save_uploaded_image

# 분석 작업을 위한 스레드
class AnalysisThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        result = analyze_image_with_gpt(self.image_path)
        self.finished.emit(result)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("영수증/명함 자동 정리기")
        self.setGeometry(100, 100, 800, 600)

        self.db_handler = DBHandler()
        self.current_analysis_result = None
        self.current_image_path = None

        # 메인 위젯 및 레이아웃 설정
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # 탭 위젯 설정
        self.tabs = QTabWidget()
        self.upload_tab = QWidget()
        self.history_tab = QWidget()
        self.tabs.addTab(self.upload_tab, "정보 추출")
        self.tabs.addTab(self.history_tab, "저장 내역")
        self.layout.addWidget(self.tabs)

        self.setup_upload_tab()
        self.setup_history_tab()

        self.tabs.currentChanged.connect(self.on_tab_change)

    # 메모를 입력받는 QLineEdit이 이미 생성됨.
    def setup_upload_tab(self):
        layout = QHBoxLayout(self.upload_tab)

        # 왼쪽: 이미지 업로드 및 표시
        left_layout = QVBoxLayout()
        self.upload_button = QPushButton("이미지 업로드")
        self.upload_button.clicked.connect(self.upload_image)
        self.image_label = QLabel("업로드된 이미지가 여기에 표시됩니다.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(350, 350)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        left_layout.addWidget(self.upload_button)
        left_layout.addWidget(self.image_label)
        layout.addLayout(left_layout)

        # 오른쪽: 분석 결과 및 저장
        right_layout = QVBoxLayout()
        self.status_label = QLabel("이미지를 업로드 해주세요.")
        self.result_form_layout = QFormLayout()

        # 영수증/명함 필드 (초기엔 숨김)
        self.receipt_fields = self.create_form_fields(['상호명', '총액', '거래일시'])
        self.card_fields = self.create_form_fields(['이름', '회사', '직책', '전화번호', '이메일'])
        self.memo_field = QLineEdit()
        self.result_form_layout.addRow("메모:", self.memo_field)

        self.save_button = QPushButton("결과 저장")
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setEnabled(False)

        right_layout.addWidget(self.status_label)
        right_layout.addLayout(self.result_form_layout)
        right_layout.addWidget(self.save_button)
        right_layout.addStretch()
        layout.addLayout(right_layout)

    # def create_form_fields(self, labels):
    #     fields = {label: QLineEdit() for label in labels}
    #     for label, field_widget in fields.items():
    #         self.result_form_layout.addRow(f"{label}:", field_widget)
    #         field_widget.parent().setVisible(False) # 부모인 QLayoutWidget을 숨김
    #     return fields
        # 이 부분이 수정/추가되었습니다.
    def toggle_form_visibility(self, fields, visible):
        for field_widget in fields.values():
            # QFormLayout에서 필드 위젯에 해당하는 라벨을 찾습니다.
            label_widget = self.result_form_layout.labelForField(field_widget)
            if label_widget:
                label_widget.setVisible(visible)
            field_widget.setVisible(visible)

    def create_form_fields(self, labels):
        fields = {label: QLineEdit() for label in labels}
        for label, field_widget in fields.items():
            self.result_form_layout.addRow(f"{label}:", field_widget)
        return fields
    
    def setup_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        
        # 영수증 내역
        layout.addWidget(QLabel("영수증 저장 내역"))
        self.receipt_table = QTableWidget()
        self.receipt_table.setColumnCount(6)
        self.receipt_table.setHorizontalHeaderLabels(['ID', '상호명', '총액', '거래일시', '메모', '저장일시'])
        self.receipt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.receipt_table)

        # 명함 내역
        layout.addWidget(QLabel("명함 저장 내역"))
        self.card_table = QTableWidget()
        self.card_table.setColumnCount(8)
        self.card_table.setHorizontalHeaderLabels(['ID', '이름', '회사', '직책', '전화번호', '이메일', '메모', '저장일시'])
        self.card_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.card_table)
        
    def on_tab_change(self, index):
        # "저장 내역" 탭이 선택되면
        if index == 1:
            self.load_history()

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "이미지 파일 선택", "", "Image files (*.jpg *.jpeg *.png)")
        if file_path:
            self.current_image_path = save_uploaded_image(file_path) # 파일 복사 및 경로 저장
            
            pixmap = QPixmap(self.current_image_path)
            self.image_label.setPixmap(pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.status_label.setText("이미지 분석 중... 잠시만 기다려주세요.")
            self.save_button.setEnabled(False)
            
            # 분석 스레드 실행
            self.analysis_thread = AnalysisThread(self.current_image_path)
            self.analysis_thread.finished.connect(self.on_analysis_finished)
            self.analysis_thread.start()

    def on_analysis_finished(self, result):
        self.current_analysis_result = result
        self.status_label.setText("분석 완료! 내용을 확인하고 저장하세요.")
        self.update_result_form(result)
        self.save_button.setEnabled(True)

    # def update_result_form(self, result):
    #     # 모든 필드 숨기기
    #     for field in self.receipt_fields.values():
    #         field.parent().setVisible(False)
    #     for field in self.card_fields.values():
    #         field.parent().setVisible(False)
        
    #     if result.get('type') == 'receipt':
    #         data = result.get('data', {})
    #         self.receipt_fields['상호명'].setText(data.get('store_name', ''))
    #         self.receipt_fields['총액'].setText(data.get('total_amount', ''))
    #         self.receipt_fields['거래일시'].setText(data.get('transaction_date', ''))
    #         for field in self.receipt_fields.values():
    #             field.parent().setVisible(True)

    #     elif result.get('type') == 'business_card':
    #         data = result.get('data', {})
    #         self.card_fields['이름'].setText(data.get('name', ''))
    #         self.card_fields['회사'].setText(data.get('company', ''))
    #         self.card_fields['직책'].setText(data.get('title', ''))
    #         self.card_fields['전화번호'].setText(data.get('phone', ''))
    #         self.card_fields['이메일'].setText(data.get('email', ''))
    #         for field in self.card_fields.values():
    #             field.parent().setVisible(True)
    #     else:
    #         QMessageBox.warning(self, "분석 실패", f"이미지 분석에 실패했습니다. (오류: {result.get('data', {}).get('message', '알 수 없음')})")
    #         self.status_label.setText("분석 실패. 다른 이미지를 시도해주세요.")
    # 이 부분이 수정되었습니다.
    def update_result_form(self, result):
        self.toggle_form_visibility(self.receipt_fields, False)
        self.toggle_form_visibility(self.card_fields, False)
        
        if result.get('type') == 'receipt':
            data = result.get('data', {})
            self.receipt_fields['상호명'].setText(data.get('store_name', ''))
            self.receipt_fields['총액'].setText(data.get('total_amount', ''))
            self.receipt_fields['거래일시'].setText(data.get('transaction_date', ''))
            self.toggle_form_visibility(self.receipt_fields, True)

        elif result.get('type') == 'business_card':
            data = result.get('data', {})
            self.card_fields['이름'].setText(data.get('name', ''))
            self.card_fields['회사'].setText(data.get('company', ''))
            self.card_fields['직책'].setText(data.get('title', ''))
            self.card_fields['전화번호'].setText(data.get('phone', ''))
            self.card_fields['이메일'].setText(data.get('email', ''))
            self.toggle_form_visibility(self.card_fields, True)
        else:
            QMessageBox.warning(self, "분석 실패", f"이미지 분석에 실패했습니다. (오류: {result.get('data', {}).get('message', '알 수 없음')})")
            self.status_label.setText("분석 실패. 다른 이미지를 시도해주세요.")

    # 사용자가 이 memofiled에 입력한 내용을 가져와 데이터 베이스에 함께 저장.
    def save_data(self):
        if not self.current_analysis_result or not self.current_image_path:
            QMessageBox.warning(self, "저장 실패", "분석된 데이터가 없습니다.")
            return

        memo = self.memo_field.text()
        result_type = self.current_analysis_result.get('type')

        try:
            if result_type == 'receipt':
                data_to_save = {
                    'store_name': self.receipt_fields['상호명'].text(),
                    'total_amount': self.receipt_fields['총액'].text(),
                    'transaction_date': self.receipt_fields['거래일시'].text(),
                    'memo': memo,
                    'image_path': self.current_image_path
                }
                self.db_handler.save_receipt(data_to_save)
            elif result_type == 'business_card':
                data_to_save = {
                    'name': self.card_fields['이름'].text(),
                    'company': self.card_fields['회사'].text(),
                    'title': self.card_fields['직책'].text(),
                    'phone': self.card_fields['전화번호'].text(),
                    'email': self.card_fields['이메일'].text(),
                    'memo': memo,
                    'image_path': self.current_image_path
                }
                self.db_handler.save_business_card(data_to_save)
            else:
                raise ValueError("알 수 없는 데이터 타입")
            
            QMessageBox.information(self, "저장 완료", "데이터가 성공적으로 저장되었습니다.")
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"데이터 저장 중 오류가 발생했습니다: {e}")

    # def clear_form(self):
    #     self.image_label.setText("업로드된 이미지가 여기에 표시됩니다.")
    #     self.status_label.setText("이미지를 업로드 해주세요.")
    #     self.memo_field.clear()
        
    #     # 모든 폼 필드 초기화 및 숨기기
    #     for field in self.receipt_fields.values():
    #         field.clear()
    #         field.parent().setVisible(False)
    #     for field in self.card_fields.values():
    #         field.clear()
    #         field.parent().setVisible(False)

    #     self.current_analysis_result = None
    #     self.current_image_path = None
    #     self.save_button.setEnabled(False)
        # 이 부분이 수정되었습니다.
    def clear_form(self):
        self.image_label.setText("업로드된 이미지가 여기에 표시됩니다.")
        self.status_label.setText("이미지를 업로드 해주세요.")
        self.memo_field.clear()
        
        for field in self.receipt_fields.values():
            field.clear()
        for field in self.card_fields.values():
            field.clear()
        
        self.toggle_form_visibility(self.receipt_fields, False)
        self.toggle_form_visibility(self.card_fields, False)

        self.current_analysis_result = None
        self.current_image_path = None
        self.save_button.setEnabled(False)


    def load_history(self):
        # 영수증 내역 로드
        self.receipt_table.setRowCount(0)
        receipts = self.db_handler.get_all_receipts()
        for row_num, row_data in enumerate(receipts):
            self.receipt_table.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                self.receipt_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
        
        # 명함 내역 로드
        self.card_table.setRowCount(0)
        cards = self.db_handler.get_all_business_cards()
        for row_num, row_data in enumerate(cards):
            self.card_table.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                self.card_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))