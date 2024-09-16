import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QStackedWidget, QLabel, QShortcut
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QUrl, QTimer, Qt, QFileSystemWatcher, QPropertyAnimation, QRect, QParallelAnimationGroup
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile


class AutoTabSwitcher:
    def __init__(self, stacked_widget, pause_label, config_path):
        self.stacked_widget = stacked_widget
        self.pause_label = pause_label
        self.current_index = 0
        self.is_paused = False  # Track whether the tab switcher is paused or not
        self.config_path = config_path
        self.load_config()
        self.total_tabs = len(self.urls)

        # Timer for switching tabs
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self.switch_tab)

        # Timer for refreshing tabs
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_next_tab)

        # Timer for auto-resume after tab switching
        self.tab_pause_timer = QTimer()
        self.tab_pause_timer.setSingleShot(True)
        self.tab_pause_timer.timeout.connect(self.resume_current_tab)  # Auto resume after tab pause duration

        # Timer for auto-resume after manual pause
        self.auto_resume_timer = QTimer()
        self.auto_resume_timer.setSingleShot(True)
        self.auto_resume_timer.timeout.connect(self.resume_current_tab)  # Auto resume after manual pause duration

        # File watcher to detect changes in `urls.json`
        self.file_watcher = QFileSystemWatcher([self.config_path])
        self.file_watcher.fileChanged.connect(self.load_config)  # Reload the config when the file changes

        if self.interval > 0:
            self.start_timer()
        else:
            self.is_paused = True
            self.pause_label.show()

        # Bind shortcuts for existing tabs
        self.bind_shortcuts()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.urls = config['urls']
            self.interval = config.get('interval', 5000)
            self.pause_duration = config.get('pause_duration', 10000)
            self.tab_pause_duration = config.get('tab_pause_duration', 30000)  # Default 30 seconds
            self.refresh_command = config.get('refresh_command', {'refresh_tab': None, 'refresh_all': False})
            self.shortcuts = config.get('shortcuts', {})  # Load shortcuts from config

            # Update tabs based on the new URLs
            self.update_tabs()

            # Handle refresh commands
            self.handle_refresh_command()

        except FileNotFoundError:
            print(f"Configuration file '{self.config_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from '{self.config_path}': {e}")
            sys.exit(1)

    def update_tabs(self):
        current_tab_count = self.stacked_widget.count()

        # Add new tabs if more URLs are in the config
        for i in range(current_tab_count, len(self.urls)):
            web_view = QWebEngineView()
            web_view.setFocusPolicy(Qt.StrongFocus)
            profile = self.stacked_widget.widget(0).page().profile()
            page = QWebEnginePage(profile, web_view)
            web_view.setPage(page)
            web_view.setUrl(QUrl(self.urls[i]))
            self.stacked_widget.addWidget(web_view)

        # Remove extra tabs if necessary
        while self.stacked_widget.count() > len(self.urls):
            widget = self.stacked_widget.widget(self.stacked_widget.count() - 1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()

        self.total_tabs = len(self.urls)

    def handle_refresh_command(self):
        # Check if a specific tab needs to be refreshed
        if self.refresh_command['refresh_tab'] is not None:
            tab_index = self.refresh_command['refresh_tab']
            if 0 <= tab_index < self.stacked_widget.count():
                widget = self.stacked_widget.widget(tab_index)
                if isinstance(widget, QWebEngineView):
                    widget.reload()

        # Check if all tabs need to be refreshed
        if self.refresh_command['refresh_all']:
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if isinstance(widget, QWebEngineView):
                    widget.reload()

        # Reset the refresh command after execution
        self.refresh_command['refresh_tab'] = None
        self.refresh_command['refresh_all'] = False
        self.save_config()

    def save_config(self):
        # Update the refresh commands in the config file
        with open(self.config_path, 'r+') as f:
            config = json.load(f)
            config['refresh_command'] = self.refresh_command
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()

    def start_timer(self):
        self.is_paused = False
        self.pause_label.hide()
        self.switch_timer.start(self.interval)
        self.schedule_refresh()

    def stop_timer(self):
        self.is_paused = True
        self.switch_timer.stop()
        self.refresh_timer.stop()

    def toggle_pause(self):
        if self.is_paused:
            self.auto_resume_timer.stop()  # Stop auto-resume if manually resumed
            self.resume_current_tab()  # Resume manually if paused
        else:
            self.pause_current_tab()  # Pause if running

    def schedule_refresh(self):
        refresh_interval = max(0, self.interval - 3000)
        self.refresh_timer.start(refresh_interval)

    def refresh_next_tab(self):
        next_index = (self.current_index + 1) % self.total_tabs
        widget = self.stacked_widget.widget(next_index)
        if isinstance(widget, QWebEngineView):
            widget.reload()
        self.refresh_timer.stop()

    def switch_tab(self):
        next_index = (self.current_index + 1) % self.total_tabs
        self.perform_transition(self.current_index, next_index)
        self.current_index = next_index
        self.schedule_refresh()

    def perform_transition(self, current_index, next_index):
        current_widget = self.stacked_widget.widget(current_index)
        next_widget = self.stacked_widget.widget(next_index)

        width = self.stacked_widget.frameGeometry().width()
        height = self.stacked_widget.frameGeometry().height()

        start_pos = QRect(width, 0, width, height)
        end_pos = QRect(0, 0, width, height)

        next_widget.setGeometry(start_pos)
        next_widget.show()

        current_animation = QPropertyAnimation(current_widget, b'geometry')
        current_animation.setDuration(1000)
        current_animation.setStartValue(QRect(0, 0, width, height))
        current_animation.setEndValue(QRect(-width, 0, width, height))

        next_animation = QPropertyAnimation(next_widget, b'geometry')
        next_animation.setDuration(1000)
        next_animation.setStartValue(start_pos)
        next_animation.setEndValue(end_pos)

        animation_group = QParallelAnimationGroup()
        animation_group.addAnimation(current_animation)
        animation_group.addAnimation(next_animation)

        if not hasattr(self, '_animations'):
            self._animations = []
        self._animations.append(animation_group)

        animation_group.start()

        def on_animation_finished():
            current_widget.setGeometry(0, 0, width, height)
            next_widget.setGeometry(0, 0, width, height)
            self.stacked_widget.setCurrentIndex(next_index)
            self._animations.remove(animation_group)

        animation_group.finished.connect(on_animation_finished)

    def pause_current_tab(self):
        self.stop_timer()
        self.pause_label.setText(f"Screen is paused. Press Ctrl+P to resume, or auto-resume in {self.tab_pause_duration / 1000:.1f} seconds.")
        self.pause_label.show()
        self.auto_resume_timer.start(self.tab_pause_duration)  # Use tab_pause_duration for each tab switch

    def resume_current_tab(self):
        self.start_timer()
        self.pause_label.hide()

    def bind_shortcut_for_tab(self, tab_index, shortcut_sequence):
        # Bind a custom shortcut for the given tab index from the config
        shortcut = QShortcut(QKeySequence(shortcut_sequence), self.stacked_widget)
        shortcut.activated.connect(lambda idx=tab_index: self.switch_to_tab(idx))

    def switch_to_tab(self, index):
        self.perform_transition(self.current_index, index)
        self.current_index = index
        self.pause_current_tab()  # Pause for the tab switch duration

    def bind_shortcuts(self):
        # Bind shortcuts for existing tabs based on the `shortcuts` field in `urls.json`
        for index, shortcut in self.shortcuts.items():
            if 0 <= int(index) < self.total_tabs:
                self.bind_shortcut_for_tab(int(index), shortcut)


def open_fullscreen_browser_with_features(config_path):
    app = QApplication(sys.argv)

    profile = QWebEngineProfile('SharedProfile', app)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    storage_path = os.path.join(os.path.expanduser('~'), '.my_browser_profile')
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    profile.setCachePath(storage_path)
    profile.setPersistentStoragePath(storage_path)

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        urls = config['urls']
    except FileNotFoundError:
        print(f"Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{config_path}': {e}")
        sys.exit(1)

    main_widget = QWidget()
    main_widget.setWindowFlags(Qt.FramelessWindowHint)
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_widget.setLayout(main_layout)

    stacked_widget = QStackedWidget()
    for url in urls:
        web = QWebEngineView()
        web.setFocusPolicy(Qt.StrongFocus)
        page = QWebEnginePage(profile, web)
        web.setPage(page)
        web.setUrl(QUrl(url))
        stacked_widget.addWidget(web)

    main_layout.addWidget(stacked_widget)

    pause_label = QLabel("Paused")
    pause_label.setAlignment(Qt.AlignCenter)
    pause_label.setStyleSheet("font-size: 24px; color: white; background-color: rgba(0, 0, 0, 0.5); padding: 10px;")
    pause_label.hide()
    main_layout.addWidget(pause_label)

    auto_switcher = AutoTabSwitcher(stacked_widget, pause_label, config_path)
    stacked_widget.auto_switcher = auto_switcher

    # Bind Ctrl+P for pause and resume
    pause_shortcut = QShortcut(QKeySequence("Ctrl+P"), main_widget)
    pause_shortcut.activated.connect(auto_switcher.toggle_pause)

    main_widget.showFullScreen()

    sys.exit(app.exec_())


if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'urls.json')
    open_fullscreen_browser_with_features(config_path)
