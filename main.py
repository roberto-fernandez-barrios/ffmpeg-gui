# main.py

import sys
from PyQt6.QtWidgets import QApplication
from ffmpeg_gui import FFmpegGUI

def main():
    app = QApplication(sys.argv)
    window = FFmpegGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
