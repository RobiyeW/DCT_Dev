from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, 
                             QAction, QFileDialog, QMessageBox)
from PyQt5.QtGui import QIcon
from yaml_loader import load_yaml_test
import sys

class DCTGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCT v2 GUI")
        self.resize(600, 400)
        self._create_actions_()
        self._create_menu_bar()
        self._create_tools_bars()

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

    def open_test_file(self):
        """Open a test YAML file and display its content."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Test Definition YAML File", "", "YAML Files (*.yaml *.yml);; All Files (*)")
        if file_path:
            try:
                data = load_yaml_test(file_path)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DCTGui()
    gui.show()
    sys.exit(app.exec_())
