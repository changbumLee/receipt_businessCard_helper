# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_app import MainApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainApp()
    main_win.show()
    sys.exit(app.exec_())