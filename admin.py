import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QToolBar, QAction, QTabWidget, QInputDialog
)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

class AdminPortal(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.load_config()
        self.init_ui()

    def load_config(self):
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        self.urls = config['urls']
        self.interval = config.get('interval', 5000)
        self.pause_duration = config.get('pause_duration', 10000)
        self.tab_pause_duration = config.get('tab_pause_duration', 13000)
        self.refresh_command = config.get('refresh_command', {'refresh_tab': None, 'refresh_all': False})
        self.shortcuts = config.get('shortcuts', {})  # Load the shortcuts if they exist

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump({
                'urls': self.urls,
                'interval': self.interval,
                'pause_duration': self.pause_duration,
                'tab_pause_duration': self.tab_pause_duration,
                'refresh_command': self.refresh_command,  # Save refresh commands in the config
                'shortcuts': self.shortcuts  # Ensure shortcuts are saved
            }, f, indent=4)

    def init_ui(self):
        self.setWindowTitle("Admin Portal")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tab_widget = QTabWidget()
        self.web_views = []
        for index, url in enumerate(self.urls):
            web = QWebEngineView()
            web.setFocusPolicy(Qt.StrongFocus)
            page = QWebEnginePage(self.create_shared_profile(), web)
            web.setPage(page)
            web.setUrl(QUrl(url))
            self.tab_widget.addTab(web, f"Tab {index + 1}")
            self.web_views.append(web)

        toolbar = QToolBar()

        # Edit URL action
        edit_url_action = QAction("Edit URL", self)
        edit_url_action.setShortcut("Ctrl+E")
        edit_url_action.triggered.connect(self.edit_current_url)
        toolbar.addAction(edit_url_action)

        # Add tab action with keyboard shortcut Ctrl+A
        add_tab_action = QAction("Add Tab", self)
        add_tab_action.setShortcut("Ctrl+A")
        add_tab_action.triggered.connect(self.add_tab)
        toolbar.addAction(add_tab_action)

        # Add "Refresh Tab" action
        refresh_tab_action = QAction("Refresh Tab", self)
        refresh_tab_action.setShortcut("Ctrl+R")
        refresh_tab_action.triggered.connect(self.refresh_current_tab)
        toolbar.addAction(refresh_tab_action)

        # Add "Refresh All" action
        refresh_all_action = QAction("Refresh All", self)
        refresh_all_action.setShortcut("Ctrl+Shift+R")
        refresh_all_action.triggered.connect(self.refresh_all_tabs)
        toolbar.addAction(refresh_all_action)

        # Add action to edit manual pause duration
        edit_pause_duration_action = QAction("Edit Manual Pause Duration", self)
        edit_pause_duration_action.setShortcut("Ctrl+P")
        edit_pause_duration_action.triggered.connect(self.edit_pause_duration)
        toolbar.addAction(edit_pause_duration_action)

        # Add action to edit tab pause duration
        edit_tab_pause_duration_action = QAction("Edit Tab Pause Duration", self)
        edit_tab_pause_duration_action.setShortcut("Ctrl+T")
        edit_tab_pause_duration_action.triggered.connect(self.edit_tab_pause_duration)
        toolbar.addAction(edit_tab_pause_duration_action)

        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.tab_widget)

    def create_shared_profile(self):
        storage_path = os.path.join(os.path.expanduser('~'), '.my_browser_profile')
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        profile = QWebEngineProfile('SharedProfile', self)
        profile.setCachePath(storage_path)
        profile.setPersistentStoragePath(storage_path)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        return profile

    def edit_current_url(self):
        index = self.tab_widget.currentIndex()
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
            new_tab_index = len(self.urls)
            self.tab_widget.addTab(web, f"Tab {new_tab_index}")
            self.web_views.append(web)
            shortcut_key = f"Ctrl+{new_tab_index}"
            self.shortcuts[str(new_tab_index - 1)] = shortcut_key
            self.save_config()

    def refresh_current_tab(self):
        index = self.tab_widget.currentIndex()
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
        new_pause_duration, ok = QInputDialog.getInt(self, "Edit Manual Pause Duration",
                                                     "Enter pause duration in milliseconds:",
                                                     value=current_pause_duration, min=1000)
        if ok:
            self.pause_duration = new_pause_duration
            self.save_config()

    def edit_tab_pause_duration(self):
        current_tab_pause_duration = self.tab_pause_duration
        new_tab_pause_duration, ok = QInputDialog.getInt(self, "Edit Tab Pause Duration",
                                                         "Enter tab switch pause duration in milliseconds:",
                                                         value=current_tab_pause_duration, min=1000)
        if ok:
            self.tab_pause_duration = new_tab_pause_duration
            self.save_config()

    def closeEvent(self, event):
        for web_view in self.web_views:
            web_view.page().deleteLater()
            web_view.deleteLater()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_path = os.path.join(os.path.dirname(__file__), 'urls.json')
    admin_portal = AdminPortal(config_path)
    sys.exit(app.exec_())
