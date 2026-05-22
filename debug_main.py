#!/usr/bin/env python3
"""
debug_main.py - Run this instead of main.py to see the actual crash error.
Place this in the same folder as main.py and run: python debug_main.py
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Catch ALL exceptions including those in Qt slots
def exception_hook(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("=" * 60)
    print("CRASH DETAILS:")
    print("=" * 60)
    print(error_msg)
    # Also write to a file so it's not lost
    with open("crash_log.txt", "w") as f:
        f.write(error_msg)
    print("Error saved to crash_log.txt")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = exception_hook

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

app = QApplication(sys.argv)
app.setFont(QFont("Segoe UI", 10))

# Patch Qt to also catch exceptions thrown inside slots
import traceback as tb
original_excepthook = sys.excepthook

try:
    from views.login_view import LoginView
    from controllers.auth_controller import AuthController

    login_view = LoginView()
    _auth_controller = AuthController(login_view)
    login_view.show()
    sys.exit(app.exec())

except Exception as e:
    print("=" * 60)
    print("STARTUP CRASH:")
    print("=" * 60)
    traceback.print_exc()
    with open("crash_log.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Error saved to crash_log.txt")
    input("Press Enter to exit...")