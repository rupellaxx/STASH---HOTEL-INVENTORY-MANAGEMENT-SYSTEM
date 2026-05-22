"""
views/message_dialog.py
───────────────────────
Rich message detail popup with inline reply capability.
Used by Admin, Owner, and Department message pages.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFrame, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont, QColor

from views.styles import APP_STYLE


_DIALOG_STYLE = APP_STYLE + """
QDialog { background: #ffffff; }

QWidget#msg_header {
    background: #16213e;
    border-radius: 10px 10px 0 0;
}
QLabel#avatar_lbl {
    background: #c0392b;
    color: white;
    font-size: 22px;
    font-weight: bold;
    border-radius: 24px;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}
QLabel#sender_name  { color: #ffffff; font-size: 15px; font-weight: bold; }
QLabel#sender_role  { color: #90cdf4; font-size: 11px; }
QLabel#msg_date     { color: #a0aec0; font-size: 11px; }
QLabel#msg_subject  { color: #1a202c; font-size: 17px; font-weight: bold; }
QLabel#msg_category {
    color: #c0392b; background: #fdecea;
    border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;
}
QTextEdit#msg_body {
    border: none;
    background: #f8fafc;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    color: #2d3748;
    line-height: 1.6;
}
QFrame#reply_frame {
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    background: white;
}
QTextEdit#reply_input {
    border: none;
    font-size: 13px;
    color: #2d3748;
    background: transparent;
}
QPushButton#send_reply_btn {
    background: #c0392b; color: white;
    border: none; border-radius: 7px;
    padding: 9px 22px; font-size: 13px; font-weight: bold;
}
QPushButton#send_reply_btn:hover { background: #922b21; }
QPushButton#close_btn {
    background: #edf2f7; color: #4a5568;
    border: none; border-radius: 7px;
    padding: 9px 18px; font-size: 13px;
}
QPushButton#close_btn:hover { background: #e2e8f0; }
"""


class MessageDetailDialog(QDialog):
    """
    Full-featured message viewer with:
      • Sender avatar (initial)
      • Subject, category badge, timestamp
      • Scrollable message body
      • Inline reply editor + Send Reply button
    """
    reply_sent = pyqtSignal(int, str)   # (recipient_id, body_text)

    def __init__(self, msg: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.msg          = msg
        self.current_user = current_user

        self.setWindowTitle(f"Message – {msg.get('title', 'No Subject')}")
        self.setMinimumSize(560, 520)
        self.setStyleSheet(_DIALOG_STYLE)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget(); header.setObjectName("msg_header")
        header.setMinimumHeight(90)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 18, 20, 18)
        hl.setSpacing(14)

        sender_name = self.msg.get("sender_name", "Unknown")
        initial     = sender_name[0].upper() if sender_name else "?"

        avatar = QLabel(initial); avatar.setObjectName("avatar_lbl")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))

        info_col = QVBoxLayout(); info_col.setSpacing(2)
        lbl_name = QLabel(sender_name);        lbl_name.setObjectName("sender_name")
        lbl_role = QLabel(f"→ {self.msg.get('recipient_name', '')}  ·  {self.msg.get('category','General')}")
        lbl_role.setObjectName("sender_role")
        lbl_date = QLabel(str(self.msg.get("created_at", ""))[:16])
        lbl_date.setObjectName("msg_date")
        info_col.addWidget(lbl_name)
        info_col.addWidget(lbl_role)
        info_col.addWidget(lbl_date)

        hl.addWidget(avatar)
        hl.addLayout(info_col, 1)
        root.addWidget(header)

        # ── Body area ─────────────────────────────────────────────────────────
        body_container = QWidget()
        body_container.setStyleSheet("background:white;")
        bl = QVBoxLayout(body_container)
        bl.setContentsMargins(24, 20, 24, 16)
        bl.setSpacing(14)

        # Subject row
        subj_row = QHBoxLayout(); subj_row.setSpacing(10)
        subj_lbl = QLabel(self.msg.get("title") or "(No Subject)")
        subj_lbl.setObjectName("msg_subject")
        subj_lbl.setWordWrap(True)
        cat_badge = QLabel(self.msg.get("category", "General").upper())
        cat_badge.setObjectName("msg_category")
        cat_badge.setFixedHeight(22)
        subj_row.addWidget(subj_lbl, 1)
        subj_row.addWidget(cat_badge)
        bl.addLayout(subj_row)

        sep = QFrame(); sep.setObjectName("h_sep")
        sep.setFrameShape(QFrame.Shape.HLine)
        bl.addWidget(sep)

        # Message body
        body_edit = QTextEdit(); body_edit.setObjectName("msg_body")
        body_edit.setPlainText(self.msg.get("body") or "")
        body_edit.setReadOnly(True)
        body_edit.setMinimumHeight(120)
        bl.addWidget(body_edit)

        # ── Reply section ─────────────────────────────────────────────────────
        reply_lbl = QLabel("Reply")
        reply_lbl.setStyleSheet(
            "font-size:13px; font-weight:600; color:#2d3748;"
        )
        bl.addWidget(reply_lbl)

        reply_frame = QFrame(); reply_frame.setObjectName("reply_frame")
        rf_lo = QVBoxLayout(reply_frame)
        rf_lo.setContentsMargins(12, 10, 12, 10)
        rf_lo.setSpacing(8)

        self.reply_input = QTextEdit(); self.reply_input.setObjectName("reply_input")
        self.reply_input.setPlaceholderText(
            f"Reply to {self.msg.get('sender_name', '')}…"
        )
        self.reply_input.setMaximumHeight(90)
        rf_lo.addWidget(self.reply_input)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        self.send_btn  = QPushButton("✉️  Send Reply")
        self.send_btn.setObjectName("send_reply_btn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._send_reply)
        btn_row.addWidget(self.send_btn)
        rf_lo.addLayout(btn_row)
        bl.addWidget(reply_frame)

        # ── Close button ──────────────────────────────────────────────────────
        close_row = QHBoxLayout(); close_row.addStretch()
        close_btn = QPushButton("Close"); close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        bl.addLayout(close_row)

        root.addWidget(body_container, 1)

    # ── Slot ──────────────────────────────────────────────────────────────────
    def _send_reply(self):
        text = self.reply_input.toPlainText().strip()
        if not text:
            return
        # Determine reply-to: if I'm the recipient, reply to sender; else to recipient
        sender_id    = self.msg.get("sender_id")
        recipient_id = self.msg.get("recipient_id")
        reply_to_id  = (
            sender_id
            if self.current_user["id"] == recipient_id
            else recipient_id
        )
        self.reply_sent.emit(reply_to_id, text)
        self.reply_input.clear()
        self.accept()