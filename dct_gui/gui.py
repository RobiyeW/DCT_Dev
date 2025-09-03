# gui.py
import sys
import json
import re
from datetime import datetime
from typing import Optional, Union  # <-- for Python < 3.10
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPen, QPolygonF
from test_runner import TestRunner
from PyQt5.QtCore import Qt, QTimer, QPointF
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
        # source-of-truth for current test kind: "nand" or "inv"
        self.current_test_kind = "nand"
        # flag set when a test definition has been pushed to the MCU
        self.loaded_test_available = False
        # track which page initiated the last 'detect' request: 'logic' or 'opamp'
        self._last_detect_target = None

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
        # logic_layout.setRowStretch(3, 1)

        # # === 1. Chip Detection Card ===
        # detection_group = QGroupBox("Chip Detection")
        # detection_layout = QVBoxLayout()
        # self.detection_label = QLabel("No chip detected.")
        # detection_layout.addWidget(self.detection_label)
        # detection_group.setLayout(detection_layout)

        # === 1+2. Chip & Test Card (combined) ===
        chip_group = QGroupBox("Chip & Test")
        chip_layout = QVBoxLayout()

        # detection text
        self.detection_label = QLabel("No chip detected.")
        self.detection_label.setWordWrap(True)
        chip_layout.addWidget(self.detection_label)

        # small spacer
        sp = QWidget(); sp.setFixedHeight(6)
        chip_layout.addWidget(sp)

        # readonly current-test indicator (auto-driven by detection)
        self.logic_test_label = QLabel("Current test: NAND")
        self.logic_test_label.setStyleSheet("font-weight: bold;")
        chip_layout.addWidget(self.logic_test_label)

        chip_group.setLayout(chip_layout)


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

        # # === 2b. Logic Test Selector ===
        # selector_group = QGroupBox("Logic Test")
        # selector_layout = QVBoxLayout()
        # self.logic_selector = QComboBox()
        # for label, _, _ in self.logic_tests:
        #     self.logic_selector.addItem(label)
        # selector_layout.addWidget(QLabel("Choose test:"))
        # selector_layout.addWidget(self.logic_selector)
        # selector_group.setLayout(selector_layout)

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

        # Layout grid  (4 cards total)
        logic_layout.addWidget(chip_group,        0, 0)   # combined Chip & Test (left)
        logic_layout.addWidget(truth_table_group, 0, 1)   # Expected Truth Table (right)

        logic_layout.addWidget(controls_group,    1, 0)   # Test Controls (left)
        logic_layout.addWidget(results_group,     1, 1)   # Results table (right)

        # Back button spans both columns
        logic_layout.addWidget(logic_back_button, 2, 0, 1, 2)

        logic_chip_page.setLayout(logic_layout)

        logic_layout.setColumnStretch(0, 1)
        logic_layout.setColumnStretch(1, 3)
        logic_layout.setRowStretch(0, 0)
        logic_layout.setRowStretch(1, 1)
        logic_layout.setRowStretch(2, 0)



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

        # Detect for opamp page (does not modify logic truth tables)
        self.opamp_detect_button = QPushButton("Detect Chip")
        self.opamp_detect_button.setFixedHeight(40)
        self.opamp_detect_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #FB8C00; }
        """)

        opamp_controls_layout.addWidget(self.opamp_start_button)
        opamp_controls_layout.addWidget(self.opamp_stop_button)
        opamp_controls_layout.addWidget(self.opamp_reset_button)
        opamp_controls_layout.addWidget(self.opamp_detect_button)
        opamp_controls_group.setLayout(opamp_controls_layout)

        waveform_group = QGroupBox("Waveform Display")
        waveform_layout = QVBoxLayout()
        # NEW: actual plot
        self.waveform = WaveformWidget(max_points=320)
        self.waveform.set_range(0.0, 5.0)  # adjust if your board is 3.3V
        waveform_layout.addWidget(self.waveform)

        # Keep your live numeric readout
        self.pwm_readout_label = QLabel("Duty: —    Voltage: — V")
        self.pwm_readout_label.setAlignment(Qt.AlignCenter)
        f = self.pwm_readout_label.font(); f.setPointSize(14); f.setBold(True)
        self.pwm_readout_label.setFont(f)
        waveform_layout.addWidget(self.pwm_readout_label)
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
        # op-amp page detect should call detect_opamp (doesn't alter logic tables)
        self.opamp_detect_button.clicked.connect(self.detect_opamp)

        # (selector removed — GUI is auto-driven by detection)

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
            # the connect-time detect should target the logic page
            self._last_detect_target = "logic"
            self.test_runner.send_command("detect")

            # Default to NAND on connect (GUI state + MCU)
            self._set_current_test_kind("nand")
            self._send("select_nand")
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
        self._clear_results_y()   # blank previous results
        if getattr(self, "loaded_test_available", False):
            # run the test definition previously uploaded to the MCU
            self._send("start_loaded")
        else:
            # fallback to built-in tests (back-compat)
            start_cmd = "start_nand" if self._current_kind() == "nand" else "start_inverter"
            self._send(start_cmd)

    def _on_opamp_start(self):
        self._reset_opamp_stats()
        # ensure the waveform is cleared right before the run
        if hasattr(self, "waveform"):
            self.waveform.clear()
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

    def _send_test_definition(self, data: dict):
        """Normalize a loaded YAML test into MCU JSON and send it."""
        msg = {
            "cmd": "define_test",
            "mode": data.get("mode", "truth_table"),
            "chip": data.get("chip"),
            "name": data.get("name"),
            "pins": data.get("pins", {}),
            "rows": data.get("rows", []),
            "settle_ms": int(data.get("settle_ms", 5)),
        }
        # send as a single JSON command string
        self.test_runner.send_command(json.dumps(msg))
        # mark that Start should use the loaded test
        self.loaded_test_available = True

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
                if isinstance(m, int) and m in (0, 1):
                    self._set_current_test_kind("nand" if m == 0 else "inv")
                    # self.logic_selector.blockSignals(True)
                    # self.logic_selector.setCurrentIndex(m)
                    # self.logic_selector.blockSignals(False)

            elif evt == "detect":
                chip = data.get("chip", "UNKNOWN")
                target = getattr(self, "_last_detect_target", None)

                # Update only the page that initiated the detect.
                if target == "opamp":
                    if hasattr(self, "opamp_detection_label"):
                        self.opamp_detection_label.setText(chip)
                else:  # default/logic target
                    if hasattr(self, "detection_label"):
                        self.detection_label.setText(chip)
                    # only apply selection/patch tables when logic requested the detect
                    try:
                        self._apply_detected_chip(chip)
                    except Exception:
                        pass

                # clear the last-detect target after handling
                self._last_detect_target = None
                self._log(f"[DETECT] {chip} (from {target})")


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
                vavg = data.get("avg_v", None)
                if vmin is not None:
                    self.min_voltage_label.setText(f"Min Voltage: {float(vmin):.2f} V")
                if vmax is not None:
                    self.max_voltage_label.setText(f"Max Voltage: {float(vmax):.2f} V")
                if vavg is not None:
                    self.avg_voltage_label.setText(f"Average Voltage: {float(vavg):.2f} V")
                self._log(f"[HEALTH] min={vmin}V max={vmax}V avg={vavg}")

            elif evt == "pwm":
                # Live PWM sample: update readout, plot and running stats
                duty = data.get("duty")
                v = data.get("voltage")
                if duty is not None and v is not None:
                    try:
                        duty_i = int(duty)
                        v_f = float(v)
                        # live readout
                        if hasattr(self, "pwm_readout_label"):
                            self.pwm_readout_label.setText(f"Duty: {duty_i:3d}    Voltage: {v_f:.2f} V")
                        # plot
                        if hasattr(self, "waveform"):
                            self.waveform.append(v_f)
                        # stats
                        self._opamp_count += 1
                        self._opamp_sum += v_f
                        self._opamp_min = v_f if self._opamp_min is None else min(self._opamp_min, v_f)
                        self._opamp_max = v_f if self._opamp_max is None else max(self._opamp_max, v_f)
                        self.min_voltage_label.setText(f"Min Voltage: {self._opamp_min:.2f} V")
                        self.max_voltage_label.setText(f"Max Voltage: {self._opamp_max:.2f} V")
                        avg = self._opamp_sum / max(self._opamp_count, 1)
                        self.avg_voltage_label.setText(f"Average Voltage: {avg:.2f} V")
                    except Exception:
                        pass
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
        return getattr(self, "current_test_kind", "nand")

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

    def _set_current_test_kind(self, kind: str) -> None:
        """Set internal test kind and update the readonly label."""
        self.current_test_kind = "nand" if str(kind).lower() in ("nand", "74f00", "0") else "inv"
        pretty = "NAND Test" if self.current_test_kind == "nand" else "Inverter Test"
        if hasattr(self, "logic_test_label"):
            self.logic_test_label.setText(f"Current test: {pretty}")

    def _apply_detected_chip(self, chip: str) -> None:
        """
        Align GUI + MCU to the detected chip:
        - set combo box (without firing signals)
        - send MCU select command
        - show the matching truth tables
        - clear the Results Y column
        """
        up = (chip or "").upper()

        if "74F00" in up:
            self._set_current_test_kind("nand")
            self._fill_truth_table_nand()
            self._setup_results_table_nand()
            self._send("select_nand")
        elif "74F04" in up:
            self._set_current_test_kind("inv")
            self._fill_truth_table_inv()
            self._setup_results_table_inv()
            self._send("select_inverter")
        else:
            self._clear_truth_tables()
            return

        # Fresh run → blank Y column in the Results table
        self._clear_results_y()

        # (Optional) auto-start the test:
        # self._send("start_nand" if self.current_test_kind == "nand" else "start_inverter")

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

    def _reset_opamp_stats(self):
        """Reset running stats and UI readouts for op-amp (PWM) live data."""
        self._opamp_count = 0
        self._opamp_sum = 0.0
        self._opamp_min = None
        self._opamp_max = None
        if hasattr(self, "pwm_readout_label"):
            self.pwm_readout_label.setText("Duty: —    Voltage: — V")
        self.min_voltage_label.setText("Min Voltage: N/A")
        self.max_voltage_label.setText("Max Voltage: N/A")
        self.avg_voltage_label.setText("Average Voltage: N/A")
        # clear the plot too (if present)
        if hasattr(self, "waveform"):
            self.waveform.clear()

    # ---------- Detect chip slot ----------
    def detect_chip(self):
        if not self.test_runner.is_connected():
            QMessageBox.warning(self, "Connection Error", "Not connected to the device.")
            return
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_output.append(f"{timestamp} → detect")
        # mark that this detect was requested by the logic page
        self._last_detect_target = "logic"
        self.test_runner.send_command("detect")
        if hasattr(self, "detection_label"):
            self.detection_label.setText("Detecting...")

    def detect_opamp(self):
        """Request detection for the op-amp page only (won't change logic tables)."""
        if not self.test_runner.is_connected():
            QMessageBox.warning(self, "Connection Error", "Not connected to the device.")
            return
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_output.append(f"{timestamp} → detect (opamp)")
        self._last_detect_target = "opamp"
        self.test_runner.send_command("detect")
        if hasattr(self, "opamp_detection_label"):
            self.opamp_detection_label.setText("Detecting...")

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

                # Push the loaded test definition to the MCU so Start can use it
                try:
                    self._send_test_definition(data)
                    self._log("[SYS] Test definition sent to MCU.")
                except Exception as e:
                    QMessageBox.warning(self, "MCU", f"Failed to send test definition:\n{e}")
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


# NEW: lightweight waveform plotting widget (pure PyQt)
class WaveformWidget(QWidget):
    def __init__(self, max_points=300, parent=None):
        super().__init__(parent)
        self.max_points = max_points
        self.data = []
        self.vmin = 0.0
        self.vmax = 5.0
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_range(self, vmin, vmax):
        self.vmin, self.vmax = float(vmin), float(vmax)
        self.update()

    def clear(self):
        self.data.clear()
        self.update()

    def append(self, v):
        try:
            v = float(v)
        except Exception:
            return
        self.data.append(v)
        if len(self.data) > self.max_points:
            self.data = self.data[-self.max_points:]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # leave extra room for Y labels (left) and X labels (bottom)
        left_margin = 40
        bottom_margin = 24
        top_margin = 8
        right_margin = 8
        rect = self.rect().adjusted(left_margin, top_margin, -right_margin, -bottom_margin)

        # background and frame
        painter.fillRect(rect, QColor(245, 245, 245))
        frame_pen = QPen(QColor(200, 200, 200)); frame_pen.setWidth(1)
        painter.setPen(frame_pen)
        painter.drawRect(rect)

        # axes (Y on left, X on bottom)
        axis_pen = QPen(QColor(50, 50, 50)); axis_pen.setWidth(1)
        painter.setPen(axis_pen)
        painter.drawLine(int(rect.left()), int(rect.top()), int(rect.left()), int(rect.bottom()))   # Y axis
        painter.drawLine(int(rect.left()), int(rect.bottom()), int(rect.right()), int(rect.bottom())) # X axis

        # horizontal grid lines + Y ticks/labels
        grid_pen = QPen(QColor(220, 220, 220)); grid_pen.setWidth(1)
        painter.setFont(QFont("Sans", 9))
        ticks = 5
        h = rect.height(); w = rect.width()
        for i in range(ticks + 1):
            yf = rect.top() + i * (h / ticks)
            yi = int(round(yf))
            # light grid
            painter.setPen(grid_pen)
            painter.drawLine(int(rect.left()), yi, int(rect.right()), yi)
            # tick on Y axis
            painter.setPen(axis_pen)
            painter.drawLine(int(rect.left()) - 5, yi, int(rect.left()), yi)
            # label (invert i->value so top = vmax)
            v = self.vmax - (i * (self.vmax - self.vmin) / ticks)
            label_rect_x = rect.left() - left_margin
            painter.drawText(int(label_rect_x), yi - 8, left_margin - 6, 16, Qt.AlignRight | Qt.AlignVCenter, f"{v:.2f}")

        # optional X ticks (no numeric time values, just markers)
        xticks = 4
        for i in range(xticks + 1):
            xf = rect.left() + i * (w / xticks)
            xi = int(round(xf))
            painter.drawLine(xi, int(rect.bottom()), xi, int(rect.bottom()) + 5)
        # X axis label
        painter.drawText(int(rect.left()), int(rect.bottom()) + 6, int(w), 16, Qt.AlignHCenter | Qt.AlignTop, "Samples")

        # draw waveform over axes
        if len(self.data) >= 2 and self.vmax > self.vmin:
            line_pen = QPen(QColor(30, 30, 30)); line_pen.setWidth(2)
            painter.setPen(line_pen)
            n = len(self.data)
            dx = w / max(1, n - 1)
            pts = []
            for i, val in enumerate(self.data):
                v = min(max(val, self.vmin), self.vmax)
                norm = (v - self.vmin) / (self.vmax - self.vmin)
                y = rect.bottom() - norm * h
                x = rect.left() + i * dx
                pts.append(QPointF(x, y))
            if pts:
                painter.drawPolyline(QPolygonF(pts))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DCTGui()
    gui.show()
    sys.exit(app.exec_())
