import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QMenu, QAction, QTabWidget,
    QInputDialog, QMessageBox
)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile


class AdminPortal(QMainWindow):
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.urls = []
        self.interval = 5000
        self.pause_duration = 10000
        self.tab_pause_duration = 13000
        self.refresh_command = {'refresh_tab': None, 'refresh_all': False}
        self.shortcuts = {}
        self.web_views = []

        self.load_config()
        self.init_ui()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"Configuration file '{self.config_path}' not found.")
            return
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Error decoding JSON from '{self.config_path}': {e}")
            return

        # Validate configuration
        self.urls = config.get('urls', [])
        if not isinstance(self.urls, list) or not all(isinstance(url, str) for url in self.urls):
            QMessageBox.critical(self, "Error", "Invalid 'urls' in configuration.")
            return

        self.interval = config.get('interval', 5000)
        self.pause_duration = config.get('pause_duration', 10000)
        self.tab_pause_duration = config.get('tab_pause_duration', 13000)
        self.refresh_command = config.get('refresh_command', {'refresh_tab': None, 'refresh_all': False})
        self.shortcuts = config.get('shortcuts', {})

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump({
                    'urls': self.urls,
                    'interval': self.interval,
                    'pause_duration': self.pause_duration,
                    'tab_pause_duration': self.tab_pause_duration,
                    'refresh_command': self.refresh_command,
                    'shortcuts': self.shortcuts
                }, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving configuration: {e}")

    def init_ui(self):
        self.setWindowTitle("Admin Portal")
        self.showFullScreen()

        # Create the menu bar
        menu_bar = self.menuBar()
        
        # Apply styles to make the buttons larger
        self.setStyleSheet("""
            QMenuBar {
                font-size: 18px; /* Menu bar font size */
            }
            QMenu {
                font-size: 16px; /* Menu item font size */
                padding: 8px; /* Add padding to menu items */
            }
            QAction {
                font-size: 16px; /* Button font size */
            }
        """)

        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")

        # Edit URL action
        edit_url_action = QAction("Edit URL", self)
        edit_url_action.setShortcut("Ctrl+E")
        edit_url_action.triggered.connect(self.edit_current_url)
        tools_menu.addAction(edit_url_action)

        # Add tab action
        add_tab_action = QAction("Add Tab", self)
        add_tab_action.setShortcut("Ctrl+A")
        add_tab_action.triggered.connect(self.add_tab)
        tools_menu.addAction(add_tab_action)

        # Delete tab action
        delete_tab_action = QAction("Delete Tab", self)
        delete_tab_action.setShortcut("Ctrl+D")
        delete_tab_action.triggered.connect(self.delete_current_tab)
        tools_menu.addAction(delete_tab_action)

        # Refresh menu
        refresh_menu = menu_bar.addMenu("Refresh")

        # Refresh Tab action
        refresh_tab_action = QAction("Refresh Tab", self)
        refresh_tab_action.setShortcut("Ctrl+R")
        refresh_tab_action.triggered.connect(self.refresh_current_tab)
        refresh_menu.addAction(refresh_tab_action)

        # Refresh All action
        refresh_all_action = QAction("Refresh All", self)
        refresh_all_action.setShortcut("Ctrl+Shift+R")
        refresh_all_action.triggered.connect(self.refresh_all_tabs)
        refresh_menu.addAction(refresh_all_action)

        # Time menu
        time_menu = menu_bar.addMenu("Time")

        # Edit manual pause duration
        edit_pause_duration_action = QAction("Edit Manual Pause Duration", self)
        edit_pause_duration_action.setShortcut("Ctrl+P")
        edit_pause_duration_action.triggered.connect(self.edit_pause_duration)
        time_menu.addAction(edit_pause_duration_action)

        # Edit tab pause duration
        edit_tab_pause_duration_action = QAction("Edit Tab Pause Duration", self)
        edit_tab_pause_duration_action.setShortcut("Ctrl+T")
        edit_tab_pause_duration_action.triggered.connect(self.edit_tab_pause_duration)
        time_menu.addAction(edit_tab_pause_duration_action)

        # Options menu
        options_menu = menu_bar.addMenu("Options")

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        options_menu.addAction(exit_action)

        # Exit and open Frontend action
        exit_and_open_frontend_action = QAction("Exit and Open Frontend", self)
        exit_and_open_frontend_action.setShortcut("Ctrl+Shift+Q")
        exit_and_open_frontend_action.triggered.connect(self.exit_and_open_frontend)
        options_menu.addAction(exit_and_open_frontend_action)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Set the central widget
        self.setCentralWidget(self.tab_widget)

        # Load tabs
        self.load_tabs()

    def create_shared_profile(self):
        storage_path = os.path.join(os.path.expanduser('~'), '.my_browser_profile')
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        profile = QWebEngineProfile.defaultProfile()
        profile.setCachePath(storage_path)
        profile.setPersistentStoragePath(storage_path)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        return profile

    def load_tabs(self):
        self.tab_widget.clear()
        self.web_views.clear()
        for index, url in enumerate(self.urls):
            web = QWebEngineView()
            web.setFocusPolicy(Qt.StrongFocus)
            page = QWebEnginePage(self.create_shared_profile(), web)
            web.setPage(page)
            web.setUrl(QUrl(url))
            self.tab_widget.addTab(web, f"Tab {index + 1}")
            self.web_views.append(web)

    def edit_current_url(self):
        index = self.tab_widget.currentIndex()
        if index < 0:
            return
        current_url = self.urls[index]
        new_url, ok = QInputDialog.getText(self, "Edit URL", "Enter new URL:", text=current_url)
        if ok and new_url:
            self.urls[index] = new_url
            self.web_views[index].setUrl(QUrl(new_url))
            self.tab_widget.setTabText(index, f"Tab {index + 1}")
            self.save_config()

    def add_tab(self):
        new_url, ok = QInputDialog.getText(self, "Add New Tab", "Enter the URL for the new tab:")
        if ok and new_url:
            self.urls.append(new_url)
            web = QWebEngineView()
            web.setFocusPolicy(Qt.StrongFocus)
            page = QWebEnginePage(self.create_shared_profile(), web)
            web.setPage(page)
            web.setUrl(QUrl(new_url))
            new_tab_index = len(self.urls) - 1
            self.tab_widget.addTab(web, f"Tab {new_tab_index + 1}")
            self.web_views.append(web)
            shortcut_key = f"Ctrl+{new_tab_index + 1}"
            self.shortcuts[str(new_tab_index)] = shortcut_key
            self.save_config()

    def delete_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index < 0:
            return
        confirm = QMessageBox.question(
            self, "Delete Tab",
            f"Are you sure you want to delete Tab {index + 1}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.urls[index]
            self.save_config()
            self.load_tabs()

    def refresh_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index < 0:
            return
        self.web_views[index].reload()
        self.refresh_command['refresh_tab'] = index
        self.refresh_command['refresh_all'] = False
        self.save_config()

    def refresh_all_tabs(self):
        for web_view in self.web_views:
            web_view.reload()
        self.refresh_command['refresh_tab'] = None
        self.refresh_command['refresh_all'] = True
        self.save_config()

    def edit_pause_duration(self):
        current_pause_duration = self.pause_duration
        new_pause_duration, ok = QInputDialog.getInt(
            self, "Edit Manual Pause Duration",
            "Enter pause duration in milliseconds:",
            value=current_pause_duration, min=1000
        )
        if ok:
            self.pause_duration = new_pause_duration
            self.save_config()

    def edit_tab_pause_duration(self):
        current_tab_pause_duration = self.tab_pause_duration
        new_tab_pause_duration, ok = QInputDialog.getInt(
            self, "Edit Tab Pause Duration",
            "Enter tab switch pause duration in milliseconds:",
            value=current_tab_pause_duration, min=1000
        )
        if ok:
            self.tab_pause_duration = new_tab_pause_duration
            self.save_config()

    def on_tab_changed(self, index):
        pass

    def closeEvent(self, event):
        # Properly delete web views
        for web_view in self.web_views:
            web_view.page().deleteLater()
            web_view.deleteLater()
        event.accept()

    def exit_and_open_frontend(self):
        """Closes the admin portal and opens the frontend.py script."""
        # Close the current admin portal
        self.close()
        # Open the frontend script
        frontend_path = os.path.join(os.path.dirname(__file__), 'frontend.py')
        if os.path.exists(frontend_path):
            subprocess.Popen([sys.executable, frontend_path])
        else:
            QMessageBox.critical(self, "Error", f"Frontend script not found at {frontend_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_path = os.path.join(os.path.dirname(__file__), 'urls.json')
    admin_portal = AdminPortal(config_path)
    admin_portal.show()
    sys.exit(app.exec_())
