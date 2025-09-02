# gui.py
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar,
                        QAction, QFileDialog, QMessageBox, QTextEdit,
                        QStackedWidget, QWidget, QPushButton, QVBoxLayout,
                        QLabel, QHBoxLayout, QSizePolicy, QGroupBox, QGridLayout,
                        QComboBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
from yaml_loader import load_yaml_test
from test_runner import TestRunner
from datetime import datetime
import json
import sys

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
        self.exit_action.triggered.connect(self.close) # exit the application
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
        # Create a toolbar for file actions
        file_toolbar = self.addToolBar("File")
        file_toolbar.addAction(self.new_action)
        file_toolbar.addAction(self.open_action)
        file_toolbar.addAction(self.save_action)

        # Create a toolbar for edit actions
        edit_toolbar = self.addToolBar("Edit")
        edit_toolbar.addAction(self.undo_action)
        edit_toolbar.addAction(self.redo_action)
        edit_toolbar.addAction(self.copy_action)
        edit_toolbar.addAction(self.paste_action)
        edit_toolbar.addAction(self.cut_action)

        # Create a toolbar for view actions
        view_toolbar = self.addToolBar("View")
        view_toolbar.addAction(self.toggle_log_action)
        view_toolbar.addAction(self.history_log_action)

        #Create tool bar for test actions
        file_toolbar.addAction(self.run_test_action)

    def _create_menu_bar(self):
        """Create the menu bar with various menus and actions."""
        # Create the menu bar
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
        # Create a submenu for Find & Replace
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

        button_width = 200  # Set a fixed width for the buttons
        button_height = 60  # Set a fixed height for the buttons

        # Spacing
        mode_layout.addStretch(1)  # Add stretchable space before the label
        mode_layout.addWidget(mode_label)
        mode_layout.addSpacing(20)  # Add space after the label

        # Styling the logic buttons
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
            QPushButton:hover {
                background-color: #45A049; }
                                   """)

        # Styling the opamp button
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
            QPushButton:hover {
                background-color: #1976D2; 
            }
            """)

        #Horizontal layout for buttons
        button_row = QHBoxLayout()
        button_row.addStretch(1)  # Add stretchable space before the buttons
        button_row.addWidget(logic_button)
        button_row.addSpacing(20)  # Add space between the buttons
        button_row.addWidget(opamp_button)
        button_row.addStretch(1)  # Add stretchable space after the buttons

        mode_layout.addLayout(button_row)
        mode_layout.addStretch(1)  # Add stretchable space after the buttons
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

            QGroupBox QLabel {
                font-size: 14px;
                color: #333333;
            }
        """)

        logic_layout = QGridLayout()
        logic_layout.setHorizontalSpacing(20)
        logic_layout.setVerticalSpacing(20)

        # === 1. Chip Detection Card ===
        detection_group = QGroupBox("Chip Detection")
        detection_layout = QVBoxLayout()
        self.detection_label = QLabel("No chip detected.")
        detection_layout.addWidget(self.detection_label)
        detection_group.setLayout(detection_layout)

        # === 2. Truth Table Card ===
        truth_table_group = QGroupBox("Expected Truth Table")
        truth_layout = QVBoxLayout()
        self.truth_table_label = QLabel("Truth table will appear here.")
        truth_layout.addWidget(self.truth_table_label)
        truth_table_group.setLayout(truth_layout)

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
            QPushButton:hover {
                background-color: #45A049;
            }
        """)

        self.stop_test_button = QPushButton("Stop Test")
        self.stop_test_button.setFixedHeight(40)
        self.stop_test_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #f44336;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
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
            QPushButton:hover {         
                background-color: #1976D2;
            }
        """)

        controls_layout.addWidget(self.start_test_button)
        controls_layout.addWidget(self.stop_test_button)
        controls_layout.addWidget(self.reset_test_button)
        controls_group.setLayout(controls_layout)

        # === 4. Results Card ===
        results_group = QGroupBox("Test Results & Advice")
        results_layout = QVBoxLayout()
        self.results_label = QLabel("Results will appear here.")
        results_layout.addWidget(self.results_label)
        results_group.setLayout(results_layout)

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
            QPushButton:hover {
                background-color: #333333;
            }
        """)

        # Layout grid
        # Row 0
        logic_layout.addWidget(detection_group, 0, 0)
        logic_layout.addWidget(truth_table_group, 0, 1)
        # Row 1
        logic_layout.addWidget(selector_group, 1, 0)
        logic_layout.addWidget(results_group, 1, 1)
        # Row 2
        logic_layout.addWidget(controls_group, 2, 0)
        # Row 3 - Back button spanning both columns
        logic_layout.addWidget(logic_back_button, 3, 0, 1, 2)
        logic_chip_page.setLayout(logic_layout)

        # Page 2 : Op Amp Test Page
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
            QGroupBox QLabel {
                font-size: 14px;
                color: #333333;
            }
        """)

        opamp_layout = QGridLayout()
        opamp_layout.setHorizontalSpacing(20)
        opamp_layout.setVerticalSpacing(20)

        # 1. Chip Detection Group
        opamp_detection_group = QGroupBox("Chip Detection")
        opamp_detection_layout = QVBoxLayout()
        self.opamp_detection_label = QLabel("No op-amp detected.")
        opamp_detection_layout.addWidget(self.opamp_detection_label)
        opamp_detection_group.setLayout(opamp_detection_layout)

        # 2. Test Controls Group
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
            QPushButton:hover {
                background-color: #45A049;
            }
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
            QPushButton:hover {
                background-color: #d32f2f;
            }
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
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        opamp_controls_layout.addWidget(self.opamp_start_button)
        opamp_controls_layout.addWidget(self.opamp_stop_button)
        opamp_controls_layout.addWidget(self.opamp_reset_button)
        opamp_controls_group.setLayout(opamp_controls_layout)

        # 3. Waveform Display Group
        waveform_group = QGroupBox("Waveform Display")
        waveform_layout = QVBoxLayout()
        self.waveform_placeholder = QLabel("Waveform graph will appear here.")
        self.waveform_placeholder.setAlignment(Qt.AlignCenter)
        waveform_layout.addWidget(self.waveform_placeholder)
        waveform_group.setLayout(waveform_layout)

        # 4. Health Metrics Group
        metrics_group = QGroupBox("Health Metrics")
        metrics_layout = QVBoxLayout()
        self.max_voltage_label = QLabel("Max Voltage: N/A")
        self.min_voltage_label = QLabel("Min Voltage: N/A")
        self.avg_voltage_label = QLabel("Average Voltage: N/A")
        metrics_layout.addWidget(self.max_voltage_label)
        metrics_layout.addWidget(self.min_voltage_label)
        metrics_layout.addWidget(self.avg_voltage_label)
        metrics_group.setLayout(metrics_layout)

        # 5. Results Group
        opamp_results_group = QGroupBox("Test Results & Advice")
        opamp_results_layout = QVBoxLayout()
        self.opamp_results_label = QLabel("Results will appear here.")
        opamp_results_layout.addWidget(self.opamp_results_label)
        opamp_results_group.setLayout(opamp_results_layout)

        # 6. Back Button
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
            QPushButton:hover {
                background-color: #333333;
            }
        """)

        # === Layout the grid ===
        # Row 0
        opamp_layout.addWidget(opamp_detection_group, 0, 0)
        opamp_layout.addWidget(waveform_group, 0, 1)

        # Row 1
        opamp_layout.addWidget(opamp_controls_group, 1, 0)
        opamp_layout.addWidget(metrics_group, 1, 1)

        # Row 2
        opamp_layout.addWidget(opamp_results_group, 2, 0, 1, 2)

        # Row 3
        opamp_layout.addWidget(opamp_back_button, 3, 0, 1, 2)

        opamp_chip_page.setLayout(opamp_layout)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(mode_selection_page)  # Page 0
        self.stacked_widget.addWidget(logic_chip_page)      # Page 1
        self.stacked_widget.addWidget(opamp_chip_page)      # Page 2

        # ==== Connect buttons to switch pages ===
        logic_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        opamp_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        # ==== Connect test control buttons ===
        # Logic test controls
        self.start_test_button.clicked.connect(self._on_logic_start)
        self.stop_test_button.clicked.connect(self._on_stop)
        self.reset_test_button.clicked.connect(self._on_reset)

        # Op Amp test controls
        self.opamp_start_button.clicked.connect(self._on_opamp_start)
        self.opamp_stop_button.clicked.connect(self._on_stop)
        self.opamp_reset_button.clicked.connect(self._on_reset)

        # Logic selector signal
        self.logic_selector.currentIndexChanged.connect(self._on_logic_selection_changed)

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
            # Optional quick truth-table hint
            if idx == 0:
                self.truth_table_label.setText("NAND: Y = !(A & B)\nA B | Y\n0 0 | 1\n0 1 | 1\n1 0 | 1\n1 1 | 0")
            else:
                self.truth_table_label.setText("INV: Y = !A\nA | Y\n0 | 1\n1 | 0")
        except Exception:
            pass

    def _on_logic_start(self):
        idx = self.logic_selector.currentIndex()
        _, _, start_cmd = self.logic_tests[idx]
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
        ts = datetime.now().strftime("[%H:%M:%S]")
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
                    # Only sync logic selector for NAND(0)/INV(1)
                    if m in (0, 1) and self.logic_selector.currentIndex() != m:
                        self.logic_selector.blockSignals(True)
                        self.logic_selector.setCurrentIndex(m)
                        self.logic_selector.blockSignals(False)
                # Could also reflect RUNNING/IDLE if you add a label
            elif evt == "detect":
                chip = data.get("chip", "UNKNOWN")
                self.detection_label.setText(chip)
                self.opamp_detection_label.setText(chip)  # fine if UNKNOWN for op-amp
                self._log(f"[DETECT] {chip}")
            elif evt == "summary":
                test = data.get("test", "?")
                passes = data.get("passes", 0)
                fails = data.get("fails", 0)
                rate = data.get("pass_rate", 0.0)
                self.results_label.setText(f"{test.upper()}: {passes} pass / {fails} fail ({rate:.1f}%)")
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
            # Not JSON → normal text log
            self._log(line)

    # ---------- Existing file/test helpers ----------
    def open_test_file(self):
        """Open a test YAML file and display its content."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Test Definition YAML File", "", "YAML Files (*.yaml *.yml);; All Files (*)")
        if file_path:
            try:
                data = load_yaml_test(file_path)
                # If your TestRunner still supports these, keep; otherwise harmless try/except:
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
        """Legacy local-run hook; serial-driven flow uses Start/Stop/Reset instead."""
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
