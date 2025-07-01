from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, 
                        QAction, QFileDialog, QMessageBox, QTextEdit, 
                        QStackedWidget, QWidget, QPushButton, QVBoxLayout, 
                        QLabel, QHBoxLayout, QSizePolicy, QGroupBox, QGridLayout)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from yaml_loader import load_yaml_test
from test_runner import TestRunner
import sys

class DCTGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCT v2 GUI")
        self.resize(600, 400)
        self._create_actions_()
        self._create_menu_bar()
        self._create_tools_bars()
        self._create_stacked_pages()

        #More specialized widgets
        # self.setCentralWidget(self.log_output)
        self.test_runner = TestRunner()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

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

        #create actions for test menu
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
        
        # Add the label and buttons to the layout
        # mode_layout.addWidget(logic_button)
        # mode_layout.addWidget(opamp_button)
        # mode_layout.addStretch(1)  # Add stretchable space after the buttons

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

        # Page 1 : Logic Chip Test Page UI PlaceHolder
        logic_chip_page = QWidget()
        logic_chip_page.setObjectName("LogicPage")
        logic_chip_page.setStyleSheet("""
            QWidget#LogicPage {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:0, y2:1,
                    stop:0 #6a11cb,
                    stop:1 #2575fc
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
        logic_layout.setSpacing(15)

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

        # Add all sections to the main vertical layout
        # logic_layout.addWidget(detection_group)
        # logic_layout.addWidget(truth_table_group)
        # logic_layout.addWidget(controls_group)
        # logic_layout.addWidget(results_group)
        # logic_layout.addWidget(logic_back_button)

        # logic_chip_page.setLayout(logic_layout)
        logic_layout = QGridLayout()
        logic_layout.setHorizontalSpacing(20)
        logic_layout.setVerticalSpacing(20)

        # Row 0
        logic_layout.addWidget(detection_group, 0, 0)
        logic_layout.addWidget(truth_table_group, 0, 1)

        # Row 1
        logic_layout.addWidget(controls_group, 1, 0)
        logic_layout.addWidget(results_group, 1, 1)

        # Row 2 - Back button spanning both columns
        logic_layout.addWidget(logic_back_button, 2, 0, 1, 2)

        logic_chip_page.setLayout(logic_layout)



        # Page 2 : Opamp Test Page UI PlaceHolder
        opamp_chip_page = QWidget()
        opamp_layout = QVBoxLayout()
        opamp_label = QLabel("Opamp Testing Interface")
        opamp_layout.addWidget(opamp_label)
        opamp_chip_page.setLayout(opamp_layout)
        opamp_back_button = QPushButton("Back to Mode Selection")
        opamp_back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        opamp_layout.addWidget(opamp_back_button)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(mode_selection_page)  # Page 0
        self.stacked_widget.addWidget(logic_chip_page)      # Page 1
        self.stacked_widget.addWidget(opamp_chip_page)      # Page 2

        # Set the stacked widget as the central widget
        self.setCentralWidget(self.stacked_widget)

        # ==== Connect buttons to switch pages ===
        logic_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        opamp_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))


    def open_test_file(self):
        """Open a test YAML file and display its content."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Test Definition YAML File", "", "YAML Files (*.yaml *.yml);; All Files (*)")
        if file_path:
            try:
                data = load_yaml_test(file_path)
                self.test_runner.load_test(data)
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
        """Run the loaded test and display the results."""
        results = self.test_runner.run_test()
        formatted = self.test_runner.format_results(results)
        self.log_output.append(formatted)
        QMessageBox.information(self, "Test Results", formatted)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DCTGui()
    gui.show()
    sys.exit(app.exec_())
