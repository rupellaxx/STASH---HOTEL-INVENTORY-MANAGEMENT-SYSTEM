#!/usr/bin/env python3
"""
main.py
───────
STASH – Hotel Inventory Management System
MVC Architecture

This is the ONLY file you run:
    python main.py

Startup flow:
    main.py
      └── creates QApplication
      └── creates LoginView          (views/login_view.py)
      └── creates AuthController     (controllers/auth_controller.py)
            └── on success → AdminController    +  AdminView
                           │  OwnerController   +  OwnerView
                           └  DeptController    +  DeptView

Folder structure:
    stash_mvc/
    ├── main.py               ← YOU ARE HERE (entry point)
    ├── setup_db.py           ← run once to create DB + seed data
    ├── models/
    │   ├── database.py            DB connection + hashlib password hashing
    │   ├── user_model.py          users table
    │   ├── item_model.py          items table
    │   ├── purchase_model.py      purchases + purchase_items tables
    │   ├── supplier_model.py      suppliers table
    │   ├── request_model.py       requests table
    │   ├── message_model.py       messages table
    │   ├── damage_model.py        damages table
    │   └── inventory_history_model.py
    ├── views/
    │   ├── styles.py              shared Qt stylesheet
    │   ├── login_view.py          login screen UI
    │   ├── admin_view.py          admin panel UI
    │   ├── owner_view.py          owner panel UI
    │   └── dept_view.py           department manager panel UI
    └── controllers/
        ├── auth_controller.py     login logic + routing
        ├── admin_controller.py    admin business logic
        ├── owner_controller.py    owner business logic
        └── dept_controller.py     dept manager business logic

Professor requirements addressed:
  ✔  User Management      — AdminController + AdminUserManagementPage
  ✔  Dept Manager Reports — DeptController._load_reports + DeptReportsPage
  ✔  hashlib passwords    — models/database.py → hash_password() (SHA-256)
"""

import sys
import os

# ── Make sure the project root is on sys.path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui     import QFont

from views.login_view            import LoginView
from controllers.auth_controller import AuthController


def main() -> None:
    app = QApplication(sys.argv)

    # Global default fontad
    app.setFont(QFont("Segoe UI", 10))
    app.setApplicationName("STASH – Hotel Inventory Management System")
    app.setApplicationVersion("2.0")

    # Instantiate view + controller (MVC entry point)
    login_view       = LoginView()
    _auth_controller = AuthController(login_view)   # wires signals internally

    login_view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()