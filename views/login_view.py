"""
views/login_view.py
───────────────────
Login window UI only.
Controller (auth_controller.py) wires up the login button.

► TO ADD YOUR LOGO:
  1. Place your logo image inside the project folder (e.g. assets/logo.png)
  2. Find the comment  # ── LOGO ──  below
  3. Uncomment the QPixmap lines and update the file path.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont


_STYLE = """
QMainWindow, QWidget#bg { background: #16213e; }
QWidget#card  { background: #ffffff; border-radius: 16px; }
QLabel#brand  { color: #c0392b; font-size: 40px; font-weight: 900; letter-spacing: 8px; }
QLabel#tagline { color: #90cdf4; font-size: 14px; }
QLabel#welcome { color: #1a202c; font-size: 26px; font-weight: bold; }
QLabel#sub_lbl { color: #718096; font-size: 13px; }
QLabel#form_lbl { color: #4a5568; font-size: 12px; font-weight: 600; }
QLineEdit {
    border: 1.5px solid #e2e8f0; border-radius: 8px;
    padding: 10px 14px; font-size: 14px; color: #2d3748; background: #f8fafc;
}
QLineEdit:focus { border-color: #c0392b; background: white; }
QFrame#h_sep { background: #e2e8f0; max-height: 1px; }
QLabel#footer_lbl { color: #a0aec0; font-size: 11px; }
"""


class LoginView(QMainWindow):
    """Pure login UI — authentication handled by AuthController."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("STASH – Hotel Inventory Management System")
        self.setMinimumSize(940, 620)
        self.setStyleSheet(_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QWidget(); root.setObjectName("bg")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        # ── Left brand panel ──────────────────────────────────────────────────
        left = QWidget(); left.setStyleSheet("background:#0f3460;")
        ll = QVBoxLayout(left)
        ll.setAlignment(Qt.AlignmentFlag.AlignCenter); ll.setSpacing(10)

        brand = QLabel("STASH"); brand.setObjectName("brand")
        brand.setFont(QFont("Segoe UI", 42, QFont.Weight.Black))
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tagline = QLabel("Hotel Inventory Management System")
        tagline.setObjectName("tagline"); tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel("Centralised · Real-Time · Role-Based\n\nStreamlining hotel operations through\ndigital inventory control.")
        desc.setStyleSheet("color:#718096; font-size:12px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ll.addStretch()
        ll.addWidget(brand); ll.addWidget(tagline); ll.addSpacing(24); ll.addWidget(desc)
        ll.addStretch()
        outer.addWidget(left, 1)

        # ── Right login card ──────────────────────────────────────────────────
        right = QWidget(); right.setStyleSheet("background:#f0f2f5;")
        rl = QVBoxLayout(right); rl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget(); card.setObjectName("card"); card.setFixedWidth(390)
        cl = QVBoxLayout(card); cl.setContentsMargins(40, 36, 40, 36); cl.setSpacing(14)

        # ── LOGO ──────────────────────────────────────────────────────────────
        # Shows above the "Welcome Back!" text.
        # To use a real image file, replace the emoji with a QPixmap:
        #
        #   from PyQt6.QtGui import QPixmap
        #   self.logo_label.setPixmap(
        #       QPixmap("assets/logo.png").scaled(
        #           80, 80,
        #           Qt.AspectRatioMode.KeepAspectRatio,
        #           Qt.TransformationMode.SmoothTransformation,
        #       )
        #   )
        #   self.logo_label.setText("")   # clear placeholder emoji
        #
        self.logo_label = QLabel("🏨")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("font-size:52px;")
        self.logo_label.setFixedHeight(72)
        cl.addWidget(self.logo_label)
        # ─────────────────────────────────────────────────────────────────────

        welcome = QLabel("Welcome Back!")
        welcome.setObjectName("welcome")
        welcome.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Sign in to continue to STASH")
        sub.setObjectName("sub_lbl"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sep = QFrame(); sep.setObjectName("h_sep"); sep.setFrameShape(QFrame.Shape.HLine)

        lbl_e = QLabel("Company Email"); lbl_e.setObjectName("form_lbl")
        self.email_input = QLineEdit(); self.email_input.setPlaceholderText("Enter your email")

        lbl_p = QLabel("Password"); lbl_p.setObjectName("form_lbl")
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Enter your password")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Inline style on the button itself guarantees the colour is applied
        # regardless of parent widget stylesheet nesting in PyQt6.
        self.login_btn = QPushButton("Login")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setMinimumHeight(46)
        self.login_btn.setStyleSheet(
            "QPushButton{background-color:#c0392b;color:white;border:none;"
            "border-radius:8px;padding:12px;font-size:15px;font-weight:bold;}"
            "QPushButton:hover{background-color:#a93226;}"
            "QPushButton:pressed{background-color:#7b2419;}"
        )

        footer = QLabel("© 2025 STASH – Hotel Inventory Management System")
        footer.setObjectName("footer_lbl"); footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cl.addWidget(welcome); cl.addWidget(sub)
        cl.addSpacing(4); cl.addWidget(sep); cl.addSpacing(4)
        cl.addWidget(lbl_e); cl.addWidget(self.email_input)
        cl.addWidget(lbl_p); cl.addWidget(self.pw_input)
        cl.addSpacing(6); cl.addWidget(self.login_btn)
        cl.addSpacing(10); cl.addWidget(footer)

        rl.addWidget(card)
        outer.addWidget(right, 1)

    def get_email(self)    -> str: return self.email_input.text().strip()
    def get_password(self) -> str: return self.pw_input.text()
    def clear_password(self):      self.pw_input.clear()