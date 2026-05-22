"""
controllers/auth_controller.py
──────────────────────────────
Connects LoginView ↔ UserModel.
Handles login validation and routes the user to the correct window.
"""

from PyQt6.QtWidgets import QMessageBox
from models.user_model import UserModel


class AuthController:

    def __init__(self, view):
        """
        :param view: LoginView instance
        """
        self.view = view
        # Wire the login button and Enter key
        self.view.login_btn.clicked.connect(self.handle_login)
        self.view.pw_input.returnPressed.connect(self.handle_login)

    # ── Slot ──────────────────────────────────────────────────────────────────
    def handle_login(self):
        email    = self.view.get_email()
        password = self.view.get_password()

        # Basic front-end validation
        if not email or not password:
            QMessageBox.warning(self.view, "Login", "Please enter both email and password.")
            return

        # Authenticate via model (hashlib SHA-256 happens inside UserModel)
        try:
            user = UserModel.verify_login(email, password)
        except Exception as exc:
            QMessageBox.critical(
                self.view,
                "Database Error",
                f"Cannot connect to the database.\n\n{exc}\n\n"
                "Make sure XAMPP / MySQL is running and you have executed setup_db.py.",
            )
            return

        if user is None:
            QMessageBox.warning(self.view, "Login Failed", "Invalid email or password.")
            self.view.clear_password()
            return

        # Route to the correct role window
        self._open_role_window(user)

    # ── Private helpers ───────────────────────────────────────────────────────
    def _open_role_window(self, user: dict):
        role = user["role"]

        if role == "admin":
            from views.admin_view import AdminView
            from controllers.admin_controller import AdminController
            view = AdminView(user)
            self._controller = AdminController(view, user)
            view.show()

        elif role == "owner":
            from views.owner_view import OwnerView
            from controllers.owner_controller import OwnerController
            view = OwnerView(user)
            self._controller = OwnerController(view, user)
            view.show()

        elif role == "department":
            from views.dept_view import DeptView
            from controllers.dept_controller import DeptController
            view = DeptView(user)
            self._controller = DeptController(view, user)
            view.show()

        else:
            QMessageBox.warning(self.view, "Login", f"Unknown role: '{role}'.")
            return

        self.view.close()