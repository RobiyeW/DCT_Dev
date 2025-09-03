# gui.py
import sys
import json
import re
from datetime import datetime
from typing import Optional, Union  # <-- for Python < 3.10
from PyQt5.QtGui import QIcon, QFont
from test_runner import TestRunner
from PyQt5.QtCore import Qt, QTimer
from yaml_loader import load_yaml_test
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QAction, QFileDialog, QMessageBox, QTextEdit,
    QStackedWidget, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy,
    QGroupBox, QGridLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem
)


class DCTGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCT v2 GUI")
        self.resize(900, 650)

        # Serial runner (do NOT auto-connect; use serial bar)
        self.test_runner = TestRunner(timeout=0.05)

        # Create a QTextEdit for log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(100)

        # Logic selector mapping (index -> (label, select_cmd, start_cmd))
        self.logic_tests = [
            ("NAND Test",     "select_nand",     "start_nand"),
            ("Inverter Test", "select_inverter", "start_inverter"),
        ]

        # Create the main layout and widgets
        self._create_actions_()
        self._create_menu_bar()
        self._create_tools_bars()
        self._create_stacked_pages()
        self._build_serial_bar()

        # ---- Central container ----
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_widget.setLayout(central_layout)
        # Serial controls on top
        serial_row = QHBoxLayout()
        serial_row.addLayout(self.serial_bar)
        central_layout.addLayout(serial_row)
        # Pages
        central_layout.addWidget(self.stacked_widget)
        # Log at bottom
        central_layout.addWidget(self.log_output)
        self.setCentralWidget(central_widget)

        # Serial poller (non-blocking)
        self.serial_timer = QTimer(self)
        self.serial_timer.setInterval(50)  # ms
        self.serial_timer.timeout.connect(self._drain_serial)
        self.serial_timer.start()

        # Populate available ports
        self._refresh_ports()

    def _create_actions_(self):
        """Create actions for the menu bar."""
        # Create actions for the file bar
        self.new_action = QAction("New", self)
        self.open_action = QAction("Open", self)
        self.save_action = QAction("Save", self)
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)  # exit the application
        self.open_action.triggered.connect(self.open_test_file)
        self.new_action.setIcon(QIcon("icon/new_file_svg.svg"))
        self.open_action.setIcon(QIcon("icon/open_file_svg.svg"))
        self.save_action.setIcon(QIcon("icon/save_svg.svg"))

        #create actions for the edit menu
        self.undo_action = QAction("Undo", self)
        self.redo_action = QAction("Redo", self)
        self.copy_action = QAction("Copy", self)
        self.paste_action = QAction("Paste", self)
        self.cut_action = QAction("Cut", self)
        self.find_action = QAction("Find", self)
        self.replace_action = QAction("Replace", self)
        self.undo_action.setIcon(QIcon("icon/undo_svg.svg"))
        self.redo_action.setIcon(QIcon("icon/redo_svg.svg"))
        self.copy_action.setIcon(QIcon("icon/copy_svg.svg"))
        self.paste_action.setIcon(QIcon("icon/paste_svg.svg"))
        self.cut_action.setIcon(QIcon("icon/cut_svg.svg"))

        #create actions for the view menu
        self.new_window_action = QAction("New window", self)
        self.new_tab_action = QAction("New tab", self)
        self.minimize_action = QAction("Minimize", self)
        self.maximize_action = QAction("Maximize", self)
        self.toggle_log_action = QAction("Toggle log", self)
        self.history_log_action = QAction("History log", self)
        self.toggle_log_action.setIcon(QIcon("icon/log_svg.svg"))
        self.history_log_action.setIcon(QIcon("icon/history_svg.svg"))

        #create actions for the help menu
        self.about_action = QAction("About", self)
        self.hotkeys_action = QAction("Hot Keys", self)
        self.tips_action = QAction("Tips", self)
        self.documentation_action = QAction("Documentation", self)

        #create actions for test menu (legacy menu action)
        self.run_test_action = QAction("Run Test", self)
        self.run_test_action.triggered.connect(self.run_test)

    def _create_tools_bars(self):
        """Create toolbars for the main window."""
        file_toolbar = self.addToolBar("File")
        file_toolbar.addAction(self.new_action)
        file_toolbar.addAction(self.open_action)
        file_toolbar.addAction(self.save_action)

        edit_toolbar = self.addToolBar("Edit")
        edit_toolbar.addAction(self.undo_action)
        edit_toolbar.addAction(self.redo_action)
        edit_toolbar.addAction(self.copy_action)
        edit_toolbar.addAction(self.paste_action)
        edit_toolbar.addAction(self.cut_action)

        view_toolbar = self.addToolBar("View")
        view_toolbar.addAction(self.toggle_log_action)
        view_toolbar.addAction(self.history_log_action)

        file_toolbar.addAction(self.run_test_action)

    def _create_menu_bar(self):
        """Create the menu bar with various menus and actions."""
        menu_bar = self.menuBar()

        # === File Menu ===
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # === Edit Menu ===
        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.cut_action)
        edit_menu.addSeparator()
        find_menu = edit_menu.addMenu("Find & Replace")
        find_menu.addAction(self.find_action)
        find_menu.addAction(self.replace_action)

        # === View Menu ===
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self.new_tab_action)
        view_menu.addAction(self.new_window_action)
        view_menu.addAction(self.minimize_action)
        view_menu.addAction(self.maximize_action)
        view_menu.addSeparator()
        view_menu.addAction(self.toggle_log_action)
        view_menu.addAction(self.history_log_action)

        # === Help Menu ===
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction(self.about_action)
        help_menu.addAction(self.hotkeys_action)
        help_menu.addAction(self.tips_action)
        help_menu.addSeparator()
        help_menu.addAction(self.documentation_action)

    def _create_stacked_pages(self):
        """Create stacked pages for different functionalities."""
        self.stacked_widget = QStackedWidget(self)

        # Page 0: Selection Page
        mode_selection_page = QWidget()
        mode_selection_page.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0,
                x2:0, y2:1,
                stop:0 #6a11cb,
                stop:1 #2575fc
            );
        """)
        mode_layout = QVBoxLayout()

        mode_label = QLabel("Select test mode:")
        mode_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        mode_label.setAlignment(Qt.AlignCenter)

        button_width = 200
        button_height = 60

        mode_layout.addStretch(1)
        mode_layout.addWidget(mode_label)
        mode_layout.addSpacing(20)

        logic_button = QPushButton("Logic Test")
        logic_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logic_button.setMinimumSize(button_width, button_height)
        logic_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #4CAF50; 
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #45A049; }
        """)

        opamp_button = QPushButton("Opamp Test")
        opamp_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        opamp_button.setMinimumSize(button_width, button_height)
        opamp_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #2196F3; 
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(logic_button)
        button_row.addSpacing(20)
        button_row.addWidget(opamp_button)
        button_row.addStretch(1)

        mode_layout.addLayout(button_row)
        mode_layout.addStretch(1)
        mode_selection_page.setLayout(mode_layout)

        # Page 1 : Logic Chip Test Page UI
        logic_chip_page = QWidget()
        logic_chip_page.setObjectName("LogicPage")
        logic_chip_page.setStyleSheet("""
            QWidget#LogicPage {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:0, y2:1,
                    stop:0 #43cea2,
                    stop:1 #000046
                );
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding: 16px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 4px 8px;
                margin-top: 4px;
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: black;
                border-radius: 4px;
            }
            QGroupBox QLabel { font-size: 14px; color: #333333; }
        """)

        logic_layout = QGridLayout()
        logic_layout.setHorizontalSpacing(20)
        logic_layout.setVerticalSpacing(20)

        # proportions
        logic_layout.setColumnStretch(0, 1)
        logic_layout.setColumnStretch(1, 3)
        logic_layout.setRowStretch(0, 0)
        logic_layout.setRowStretch(1, 0)
        logic_layout.setRowStretch(2, 0)
        logic_layout.setRowStretch(3, 1)

        # === 1. Chip Detection Card ===
        detection_group = QGroupBox("Chip Detection")
        detection_layout = QVBoxLayout()
        self.detection_label = QLabel("No chip detected.")
        detection_layout.addWidget(self.detection_label)
        detection_group.setLayout(detection_layout)

        # === 2. Truth Table Card ===
        truth_table_group = QGroupBox("Expected Truth Table")
        truth_layout = QVBoxLayout()

        self.truth_table = QTableWidget(4, 3)
        self.truth_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.truth_table.setFixedHeight(170)
        self.truth_table.verticalHeader().setVisible(False)
        self.truth_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.truth_table.setSelectionMode(QTableWidget.NoSelection)
        self.truth_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.truth_table.verticalHeader().setDefaultSectionSize(24)
        self.truth_table.setHorizontalHeaderLabels(["A", "B", "Y"])

        # center header text + bold table font
        self.truth_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        tf = self.truth_table.font()
        tf.setBold(True)
        self.truth_table.setFont(tf)

        truth_layout.addWidget(self.truth_table)
        truth_table_group.setLayout(truth_layout)
        truth_table_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        truth_table_group.setMaximumHeight(230)

        # === 2b. Logic Test Selector ===
        selector_group = QGroupBox("Logic Test")
        selector_layout = QVBoxLayout()
        self.logic_selector = QComboBox()
        for label, _, _ in self.logic_tests:
            self.logic_selector.addItem(label)
        selector_layout.addWidget(QLabel("Choose test:"))
        selector_layout.addWidget(self.logic_selector)
        selector_group.setLayout(selector_layout)

        # === 3. Test Controls Card ===
        controls_group = QGroupBox("Test Controls")
        controls_layout = QVBoxLayout()

        self.start_test_button = QPushButton("Start Test")
        self.start_test_button.setFixedHeight(40)
        self.start_test_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45A049; }
        """)

        self.detect_button = QPushButton("Detect Chip")
        self.detect_button.setFixedHeight(40)
        self.detect_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #FB8C00; }
        """)

        self.reset_test_button = QPushButton("Reset Test")
        self.reset_test_button.setFixedHeight(40)
        self.reset_test_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)

        controls_layout.addWidget(self.start_test_button)
        controls_layout.addWidget(self.detect_button)
        controls_layout.addWidget(self.reset_test_button)
        controls_group.setLayout(controls_layout)

        # === 4. Results Card ===
        results_group = QGroupBox("Test Results & Advice")
        self.results_group = results_group
        results_layout = QVBoxLayout()

        self.results_table = QTableWidget(0, 0)
        self.results_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.results_table.setFixedHeight(170)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionMode(QTableWidget.NoSelection)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.horizontalHeader().setDefaultSectionSize(60)
        self.results_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        rf = self.results_table.font()
        rf.setBold(True)
        self.results_table.setFont(rf)

        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        results_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        results_group.setMaximumHeight(230)

        # === Back Button ===
        logic_back_button = QPushButton("Back to Mode Selection")
        logic_back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        logic_back_button.setFixedHeight(40)
        logic_back_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #555555;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #333333; }
        """)

        # Layout grid
        logic_layout.addWidget(detection_group, 0, 0)
        logic_layout.addWidget(truth_table_group, 0, 1)
        logic_layout.addWidget(selector_group, 1, 0)
        logic_layout.addWidget(results_group, 1, 1)
        logic_layout.addWidget(controls_group, 2, 0)
        logic_layout.addWidget(logic_back_button, 3, 0, 1, 2)
        logic_chip_page.setLayout(logic_layout)

        # Page 2 : Op Amp Test Page  (unchanged except formatting)
        opamp_chip_page = QWidget()
        opamp_chip_page.setObjectName("OpAmpPage")
        opamp_chip_page.setStyleSheet("""
            QWidget#OpAmpPage {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:0, y2:1,
                    stop:0 #1CB5E0,
                    stop:1 #000046
                );
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding: 16px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 4px 8px;
                margin-top: 4px;
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: black;
                border-radius: 4px;
            }
            QGroupBox QLabel { font-size: 14px; color: #333333; }
        """)

        opamp_layout = QGridLayout()
        opamp_layout.setHorizontalSpacing(20)
        opamp_layout.setVerticalSpacing(20)

        opamp_detection_group = QGroupBox("Chip Detection")
        opamp_detection_layout = QVBoxLayout()
        self.opamp_detection_label = QLabel("No op-amp detected.")
        opamp_detection_layout.addWidget(self.opamp_detection_label)
        opamp_detection_group.setLayout(opamp_detection_layout)

        opamp_controls_group = QGroupBox("Test Controls")
        opamp_controls_layout = QVBoxLayout()

        self.opamp_start_button = QPushButton("Start Test")
        self.opamp_start_button.setFixedHeight(40)
        self.opamp_start_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45A049; }
        """)

        self.opamp_stop_button = QPushButton("Stop Test")
        self.opamp_stop_button.setFixedHeight(40)
        self.opamp_stop_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #f44336;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)

        self.opamp_reset_button = QPushButton("Reset Test")
        self.opamp_reset_button.setFixedHeight(40)
        self.opamp_reset_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)

        opamp_controls_layout.addWidget(self.opamp_start_button)
        opamp_controls_layout.addWidget(self.opamp_stop_button)
        opamp_controls_layout.addWidget(self.opamp_reset_button)
        opamp_controls_group.setLayout(opamp_controls_layout)

        waveform_group = QGroupBox("Waveform Display")
        waveform_layout = QVBoxLayout()
        self.waveform_placeholder = QLabel("Waveform graph will appear here.")
        self.waveform_placeholder.setAlignment(Qt.AlignCenter)
        waveform_layout.addWidget(self.waveform_placeholder)
        waveform_group.setLayout(waveform_layout)

        metrics_group = QGroupBox("Health Metrics")
        metrics_layout = QVBoxLayout()
        self.max_voltage_label = QLabel("Max Voltage: N/A")
        self.min_voltage_label = QLabel("Min Voltage: N/A")
        self.avg_voltage_label = QLabel("Average Voltage: N/A")
        metrics_layout.addWidget(self.max_voltage_label)
        metrics_layout.addWidget(self.min_voltage_label)
        metrics_layout.addWidget(self.avg_voltage_label)
        metrics_group.setLayout(metrics_layout)

        opamp_results_group = QGroupBox("Test Results & Advice")
        opamp_results_layout = QVBoxLayout()
        self.opamp_results_label = QLabel("Results will appear here.")
        opamp_results_layout.addWidget(self.opamp_results_label)
        opamp_results_group.setLayout(opamp_results_layout)

        opamp_back_button = QPushButton("Back to Mode Selection")
        opamp_back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        opamp_back_button.setFixedHeight(40)
        opamp_back_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #555555;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #333333; }
        """)

        opamp_layout.addWidget(opamp_detection_group, 0, 0)
        opamp_layout.addWidget(waveform_group, 0, 1)
        opamp_layout.addWidget(opamp_controls_group, 1, 0)
        opamp_layout.addWidget(metrics_group, 1, 1)
        opamp_layout.addWidget(opamp_results_group, 2, 0, 1, 2)
        opamp_layout.addWidget(opamp_back_button, 3, 0, 1, 2)
        opamp_chip_page.setLayout(opamp_layout)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(mode_selection_page)  # Page 0
        self.stacked_widget.addWidget(logic_chip_page)      # Page 1
        self.stacked_widget.addWidget(opamp_chip_page)      # Page 2

        # Switch-page buttons
        logic_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        opamp_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        # Test control buttons
        self.start_test_button.clicked.connect(self._on_logic_start)
        self.detect_button.clicked.connect(self.detect_chip)
        self.reset_test_button.clicked.connect(self._on_reset)
        self.opamp_start_button.clicked.connect(self._on_opamp_start)
        self.opamp_stop_button.clicked.connect(self._on_stop)
        self.opamp_reset_button.clicked.connect(self._on_reset)

        # Logic selector signal
        self.logic_selector.currentIndexChanged.connect(self._on_logic_selection_changed)

        # Initialize both tables to NAND by default
        self._fill_truth_table_nand()
        self._setup_results_table_nand()
        self._clear_results_y()

    # ---------- Serial bar ----------
    def _build_serial_bar(self):
        self.serial_bar = QHBoxLayout()
        self.serial_bar.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.serial_bar.addWidget(self.port_combo)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_ports)
        self.serial_bar.addWidget(self.refresh_btn)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._connect_or_disconnect)
        self.serial_bar.addWidget(self.connect_btn)

        self.status_label = QLabel("Disconnected")
        self.serial_bar.addWidget(self.status_label)
        self.serial_bar.addStretch(1)

    def _refresh_ports(self):
        try:
            current = self.port_combo.currentText()
            self.port_combo.blockSignals(True)
            self.port_combo.clear()
            for dev, desc in TestRunner.available_ports():
                self.port_combo.addItem(f"{dev}  {desc}", dev)
            idx = self.port_combo.findText(current)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)
            self.port_combo.blockSignals(False)
            self._log("[SYS] Ports refreshed.")
        except Exception as e:
            QMessageBox.warning(self, "Serial", f"Port refresh failed:\n{e}")

    def _selected_port(self):
        idx = self.port_combo.currentIndex()
        return self.port_combo.itemData(idx) if idx >= 0 else None

    def _connect_or_disconnect(self):
        try:
            if self.test_runner.is_connected():
                self.test_runner.close_connection()
                self.connect_btn.setText("Connect")
                self.status_label.setText("Disconnected")
                self._log("[SYS] Disconnected.")
                return

            port = self._selected_port()
            if not port:
                QMessageBox.warning(self, "Serial", "No port selected.")
                return

            self.test_runner.connect(port=port, baudrate=9600, timeout=0.05)
            self.connect_btn.setText("Disconnect")
            self.status_label.setText(f"Connected: {port}")
            self._log(f"[SYS] Connected to {port}")

            # Prime panels
            self.test_runner.send_command("status")
            self.test_runner.send_command("detect")

            # Default logic selection → NAND
            self.logic_selector.blockSignals(True)
            self.logic_selector.setCurrentIndex(0)
            self.logic_selector.blockSignals(False)
            self.test_runner.send_command("select_nand")
        except Exception as e:
            QMessageBox.warning(self, "Serial", f"Connection failed:\n{e}")

    # ---------- Button handlers ----------
    def _on_logic_selection_changed(self, idx: int):
        try:
            _, select_cmd, _ = self.logic_tests[idx]
            self._send(select_cmd)
            if idx == 0:
                self._fill_truth_table_nand()
                self._setup_results_table_nand()
            else:
                self._fill_truth_table_inv()
                self._setup_results_table_inv()
            self._clear_results_y()
        except Exception:
            pass

    def _on_logic_start(self):
        idx = self.logic_selector.currentIndex()
        _, _, start_cmd = self.logic_tests[idx]
        self._clear_results_y()   # blank previous results
        self._send(start_cmd)

    def _on_opamp_start(self):
        self._send("start_opamp")

    def _on_stop(self):
        self._send("stop")

    def _on_reset(self):
        self._send("reset")

    def _send(self, cmd: str):
        if not self.test_runner.is_connected():
            QMessageBox.warning(self, "Connection Error", "Not connected to the device.")
            return
        ok = self.test_runner.send_command(cmd)
        ts = datetime.now().strftime("[%H:%M:%S]")  # <-- fixed closing bracket
        self.log_output.append(f"{ts} → {cmd}" if ok else f"{ts} [ERR] failed to send: {cmd}")

    # ---------- Serial polling & routing ----------
    def _drain_serial(self):
        if not self.test_runner or not self.test_runner.is_connected():
            return
        for _ in range(50):
            line = self.test_runner.receive_response()
            if not line:
                break
            self._handle_serial_line(line)

    def _handle_serial_line(self, line: str):
        # Try JSON events first
        try:
            data = json.loads(line)
            evt = data.get("event")
            if evt == "status":
                m = data.get("menuIndex")
                if isinstance(m, int):
                    if m in (0, 1) and self.logic_selector.currentIndex() != m:
                        self.logic_selector.blockSignals(True)
                        self.logic_selector.setCurrentIndex(m)
                        self.logic_selector.blockSignals(False)

            elif evt == "detect":
                chip = data.get("chip", "UNKNOWN")
                self.detection_label.setText(chip)
                self.opamp_detection_label.setText(chip)

                up = (chip or "UNKNOWN").upper()
                if "74F00" in up:
                    self._fill_truth_table_nand()
                    self._setup_results_table_nand()
                elif "74F04" in up:
                    self._fill_truth_table_inv()
                    self._setup_results_table_inv()
                else:
                    self._clear_truth_tables()

                self._log(f"[DETECT] {chip}")

            elif evt == "vector":
                # Live update a single row in the Results table (quick path)
                try:
                    if "B" in data:  # NAND: A,B,Y
                        a = int(data.get("A", 0))
                        b = int(data.get("B", 0))
                        y = int(data.get("Y", 0))
                        self._set_results_y(a, b, y)
                    else:            # Inverter: A,Y
                        a = int(data.get("A", 0))
                        y = int(data.get("Y", 0))
                        self._set_results_y(a, None, y)
                except Exception:
                    pass
                return

            elif evt in ("row", "sample", "probe"):
                # per-vector JSON results for alternate event names
                a = data.get("A", None)
                b = data.get("B", None)
                y = data.get("Y", data.get("output", None))
                inputs = data.get("inputs")
                if a is None and isinstance(inputs, list):
                    if len(inputs) >= 1:
                        a = inputs[0]
                    if len(inputs) >= 2:
                        b = inputs[1]
                if a is not None and y is not None:
                    try:
                        a = int(a)
                        y = int(y)
                        if self._current_kind() == 'inv':
                            self._set_results_y(a, None, y)
                        else:
                            b = 0 if b is None else int(b)
                            self._set_results_y(a, b, y)
                    except Exception:
                        pass
                self._log(f"[VECTOR] A={a} B={b} -> Y={y}")

            elif evt == "summary":
                test = data.get("test", "?")
                passes = data.get("passes", 0)
                fails = data.get("fails", 0)
                rate = data.get("pass_rate", 0.0)

                if hasattr(self, "results_group"):
                    self.results_group.setTitle(f"Test Results & Advice — {test.upper()} • {passes} pass / {fails} fail ({rate:.1f}%)")

                rows = data.get("truth_table") or data.get("observed") or data.get("rows")
                if isinstance(rows, list) and rows:
                    if all(isinstance(t, (list, tuple)) for t in rows):
                        if len(rows[0]) == 3:  # NAND
                            for r, (a, b, y) in enumerate(rows):
                                self.results_table.setItem(r, 2, self._make_center_item(str(y)))
                        elif len(rows[0]) == 2:  # INV
                            for r, (a, y) in enumerate(rows):
                                self.results_table.setItem(r, 1, self._make_center_item(str(y)))
                    elif all(isinstance(t, dict) for t in rows):
                        sample = rows[0]
                        if "Y" in sample:
                            if "B" in sample:  # NAND
                                for r, row in enumerate(rows):
                                    self.results_table.setItem(r, 2, self._make_center_item(str(row.get("Y"))))
                            else:              # INV
                                for r, row in enumerate(rows):
                                    self.results_table.setItem(r, 1, self._make_center_item(str(row.get("Y"))))
                        elif "output" in sample:
                            if isinstance(sample.get("inputs"), (list, tuple)) and len(sample["inputs"]) == 2:
                                for r, row in enumerate(rows):
                                    self.results_table.setItem(r, 2, self._make_center_item(str(row.get("output"))))
                            else:
                                for r, row in enumerate(rows):
                                    self.results_table.setItem(r, 1, self._make_center_item(str(row.get("output"))))

                self._log(f"[SUMMARY] {test}: {passes} pass / {fails} fail ({rate:.1f}%)")

            elif evt == "health":
                vmin = data.get("min_v", None)
                vmax = data.get("max_v", None)
                if vmin is not None:
                    self.min_voltage_label.setText(f"Min Voltage: {vmin:.2f} V")
                if vmax is not None:
                    self.max_voltage_label.setText(f"Max Voltage: {vmax:.2f} V")
                self._log(f"[HEALTH] min={vmin:.2f}V max={vmax:.2f}V")
            else:
                self._log(line)
            return

        except Exception:
            # Not JSON → try to parse text vector lines; else just log
            if self._try_parse_vector_text_line(line):
                return
            self._log(line)

    # ---------- Truth table helpers ----------
    def _truth_table_nand_text(self) -> str:
        lines = [
            "A B | Y = !(A&B)",
            "0 0 | 1",
            "0 1 | 1",
            "1 0 | 1",
            "1 1 | 0",
        ]
        return "\n".join(lines)

    def _truth_table_inverter_text(self) -> str:
        lines = [
            "A | Y = !A",
            "0 | 1",
            "1 | 0",
        ]
        return "\n".join(lines)

    def _make_center_item(self, text: str) -> QTableWidgetItem:
        it = QTableWidgetItem(text)
        it.setTextAlignment(Qt.AlignCenter)
        return it

    # --- Expected table fillers (center cells) ---
    def _fill_truth_table_nand(self):
        data = [("0", "0", "1"), ("0", "1", "1"), ("1", "0", "1"), ("1", "1", "0")]
        self.truth_table.setRowCount(len(data))
        self.truth_table.setColumnCount(3)
        self.truth_table.setHorizontalHeaderLabels(["A", "B", "Y"])
        for r, (a, b, y) in enumerate(data):
            self.truth_table.setItem(r, 0, self._make_center_item(a))
            self.truth_table.setItem(r, 1, self._make_center_item(b))
            self.truth_table.setItem(r, 2, self._make_center_item(y))

    def _fill_truth_table_inv(self):
        data = [("0", "1"), ("1", "0")]
        self.truth_table.setRowCount(len(data))
        self.truth_table.setColumnCount(2)
        self.truth_table.setHorizontalHeaderLabels(["A", "Y"])
        for r, (a, y) in enumerate(data):
            self.truth_table.setItem(r, 0, self._make_center_item(a))
            self.truth_table.setItem(r, 1, self._make_center_item(y))

    # --- Results table setup (same centered format, Y blank initially) ---
    def _setup_results_table_nand(self):
        rows = [("0", "0", ""), ("0", "1", ""), ("1", "0", ""), ("1", "1", "")]
        self.results_table.setRowCount(len(rows))
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["A", "B", "Y"])
        for r, (a, b, y) in enumerate(rows):
            self.results_table.setItem(r, 0, self._make_center_item(a))
            self.results_table.setItem(r, 1, self._make_center_item(b))
            self.results_table.setItem(r, 2, self._make_center_item(y))

    def _setup_results_table_inv(self):
        rows = [("0", ""), ("1", "")]
        self.results_table.setRowCount(len(rows))
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["A", "Y"])
        for r, (a, y) in enumerate(rows):
            self.results_table.setItem(r, 0, self._make_center_item(a))
            self.results_table.setItem(r, 1, self._make_center_item(y))

    def _clear_truth_tables(self):
        self.truth_table.setRowCount(0)
        self.truth_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)

    def _current_kind(self) -> str:
        return 'nand' if self.logic_selector.currentIndex() == 0 else 'inv'

    def _row_index_for_inputs(self, a: int, b: Optional[int] = None) -> Optional[int]:
        if self._current_kind() == 'nand':
            order = [(0, 0), (0, 1), (1, 0), (1, 1)]
            try:
                return order.index((a, b))
            except ValueError:
                return None
        else:
            order = [0, 1]  # inverter uses only A
            try:
                return order.index(a)
            except ValueError:
                return None

    def _clear_results_y(self) -> None:
        if self._current_kind() == 'nand':
            for r in range(4):
                self.results_table.setItem(r, 2, self._make_center_item(""))
        else:
            for r in range(2):
                self.results_table.setItem(r, 1, self._make_center_item(""))

    def _set_results_y(self, a: int, b: Optional[int], y: Union[int, str]) -> None:
        idx = self._row_index_for_inputs(a, b)
        if idx is None:
            return
        if self._current_kind() == 'nand':
            self.results_table.setItem(idx, 2, self._make_center_item(str(y)))
        else:
            self.results_table.setItem(idx, 1, self._make_center_item(str(y)))

    def _try_parse_vector_text_line(self, line: str) -> bool:
        """
        Parse plain-text vector results like:
          'A=0 B=1 Y=1'
          'IN: 0,1 -> OUT: 1'
          'A:1, Y:0' (for inverter)
        """
        s = line.strip()

        m = re.search(r'\bA\s*[:=]\s*([01])\b.*?\bB\s*[:=]\s*([01])\b.*?\bY\s*[:=]\s*([01])\b', s, re.I)
        if m:
            a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            self._set_results_y(a, b, y)
            return True

        m = re.search(r'IN(?:PUTS?)?\s*[:=]\s*\[?\s*([01])\s*[, ]\s*([01])\s*\]?\D+OUT(?:PUT)?\s*[:=]\s*([01])', s, re.I)
        if m:
            a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            self._set_results_y(a, b, y)
            return True

        if self._current_kind() == 'inv':
            m = re.search(r'\bA\s*[:=]\s*([01])\b.*?\bY\s*[:=]\s*([01])\b', s, re.I)
            if m:
                a, y = int(m.group(1)), int(m.group(2))
                self._set_results_y(a, None, y)
                return True

        return False

    # ---------- Detect chip slot ----------
    def detect_chip(self):
        if not self.test_runner.is_connected():
            QMessageBox.warning(self, "Connection Error", "Not connected to the device.")
            return
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_output.append(f"{timestamp} → detect")
        self.test_runner.send_command("detect")
        self.detection_label.setText("Detecting...")

    # ---------- Existing file/test helpers ----------
    def open_test_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Test Definition YAML File", "",
            "YAML Files (*.yaml *.yml);; All Files (*)"
        )
        if file_path:
            try:
                data = load_yaml_test(file_path)
                try:
                    self.test_runner.load_test(data)
                except Exception:
                    pass

                if data is None:
                    QMessageBox.warning(self, "Warning", "The file is empty or could not be loaded.")
                else:
                    formatted = (
                        f"Chip: {data.get('chip')}\n"
                        f"Type: {data.get('type')}\n\n"
                        f"Test Input Vector: {data.get('inputs')}\n"
                        f"Expected Outputs: {data.get('outputs')}\n\n"
                        f"Truth Table:\n"
                    )
                    for row in data.get('truth_table', []):
                        formatted += f"  IN: {row.get('inputs')} → OUT: {row.get('output')}\n"
                    QMessageBox.information(self, "Test File Info", formatted)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

    def run_test(self):
        try:
            results = self.test_runner.run_test()
            formatted = self.test_runner.format_results(results)
            self.log_output.append(formatted)
            QMessageBox.information(self, "Test Results", formatted)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Run test failed:\n{e}")

    # ---------- Logging helper ----------
    def _log(self, msg: str):
        ts = datetime.now().strftime("[%H:%M:%S]")
        self.log_output.append(f"{ts} {msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DCTGui()
    gui.show()
    sys.exit(app.exec_())
