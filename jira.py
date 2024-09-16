import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget, QToolBar, QAction, QLabel, QShortcut, QTabWidget, QHBoxLayout
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QUrl, QTimer, Qt, QPropertyAnimation, QRect
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from functools import partial

# Initial page with App and Admin console buttons
class InitialPage(QWidget):
    def __init__(self, app_start_function, admin_console_function):
        super().__init__()
        self.app_start_function = app_start_function
        self.admin_console_function = admin_console_function

        # Create the layout for the initial page
        layout = QVBoxLayout()

        # Create buttons for App and Admin console
        self.app_button = QPushButton("App")
        self.app_button.clicked.connect(self.start_app)

        self.admin_button = QPushButton("Admin Console")
        self.admin_button.clicked.connect(self.start_admin_console)

        # Add buttons to the layout
        layout.addWidget(self.app_button)
        layout.addWidget(self.admin_button)

        # Add the label to show instructions or countdown
        self.label = QLabel("Select an option. Defaulting to 'App' in 10 seconds.")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Set the layout
        self.setLayout(layout)

        # Start the 10-second countdown timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_app)
        self.timer.setSingleShot(True)
        self.timer.start(10000)  # 10 seconds

        # Add keyboard shortcuts for App and Admin console
        self.app_button.setShortcut("A")  # Shortcut: Press 'A' to start App
        self.admin_button.setShortcut("D")  # Shortcut: Press 'D' to start Admin Console

    def start_app(self):
        """ Start the app and stop the timer if it is running. """
        if self.timer.isActive():
            self.timer.stop()  # Stop the timer if the user manually selects App
        self.app_start_function()  # Call the function to start the app

    def start_admin_console(self):
        """ Start the admin console. """
        if self.timer.isActive():
            self.timer.stop()  # Stop the timer if the user manually selects Admin Console
        self.admin_console_function()  # Call the function for admin console


def start_app():
    """ Function to load the main application (App) screen. """
    load_main_application()


def start_admin_console():
    """ Function for starting the Admin Console. """
    print("Admin Console started.")
    # You can add your Admin Console code here


def load_main_application():
    # This function will initialize the main application (your original code with the browser and auto tab switcher)
    base_ip = '10.0.0.186:8080'
    urls = [
        f'http://{base_ip}/browse/XCH-1?filter=-5',
        f'http://{base_ip}/browse/XCH-5?filter=-5',
        'https://www.github.com'
    ]
    interval = 5000  # 5 seconds interval
    open_fullscreen_browser_with_features(urls, interval)


def open_fullscreen_browser_with_features(urls, interval=0):
    app = QApplication.instance() or QApplication(sys.argv)

    profile = QWebEngineProfile('PersistentProfile', app)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    storage_path = os.path.join(os.getcwd(), 'browser_data')
    profile.setCachePath(storage_path)
    profile.setPersistentStoragePath(storage_path)

    main_widget = QWidget()
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_widget.setLayout(main_layout)

    # Create a QTabWidget to display the tab bar
    tab_widget = QTabWidget()
    web_views = []
    for index, url in enumerate(urls):
        web = QWebEngineView()
        web.setFocusPolicy(Qt.StrongFocus)
        page = QWebEnginePage(profile, web)
        web.setPage(page)
        web.setUrl(QUrl(url))
        tab_widget.addTab(web, f"Tab {index + 1}")
        web_views.append(web)

    toolbar = QToolBar()
    refresh_action = QAction("Refresh", main_widget)
    refresh_action.setShortcut("F5")
    refresh_action.triggered.connect(lambda: refresh_tab(tab_widget))
    toolbar.addAction(refresh_action)

    refresh_all_action = QAction("Refresh All", main_widget)
    refresh_all_action.setShortcut("Ctrl+F5")
    refresh_all_action.triggered.connect(lambda: refresh_all_tabs(tab_widget))
    toolbar.addAction(refresh_all_action)

    main_layout.addWidget(toolbar)
    main_layout.addWidget(tab_widget)

    pause_label = QLabel("Paused")
    pause_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
    pause_label.setStyleSheet("font-size: 18px; color: white; background-color: rgba(0, 0, 0, 0.5);")
    pause_label.setMargin(10)
    pause_label.hide()

    overlay_layout = QHBoxLayout()
    overlay_layout.addWidget(pause_label)
    overlay_layout.addStretch()
    main_layout.addLayout(overlay_layout)

    main_widget.showFullScreen()

    auto_switcher = AutoTabSwitcher(tab_widget, interval, pause_label, urls)
    tab_widget.auto_switcher = auto_switcher

    setup_keyboard_shortcuts(tab_widget, auto_switcher, len(urls))

    app.exec_()  # Ensure the event loop runs properly


def setup_keyboard_shortcuts(tab_widget, auto_switcher, num_tabs):
    next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), tab_widget)
    next_tab_shortcut.activated.connect(lambda: switch_tab(tab_widget, 1))

    prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), tab_widget)
    prev_tab_shortcut.activated.connect(lambda: switch_tab(tab_widget, -1))

    pause_shortcut = QShortcut(QKeySequence("Space"), tab_widget)
    pause_shortcut.activated.connect(auto_switcher.toggle)

    for i in range(num_tabs):
        key_sequence = QKeySequence(f"Ctrl+{i+1}")
        shortcut = QShortcut(key_sequence, tab_widget)
        shortcut.activated.connect(partial(switch_to_tab, tab_widget, i))

    QShortcut(QKeySequence("Ctrl+L"), tab_widget).activated.connect(lambda: auto_switcher.open_custom_link(0, 'https://example.com'))
    QShortcut(QKeySequence("Ctrl+M"), tab_widget).activated.connect(lambda: auto_switcher.open_custom_link(1, 'https://anotherexample.com'))
    QShortcut(QKeySequence("Ctrl+N"), tab_widget).activated.connect(lambda: auto_switcher.open_custom_link(2, 'https://yetanotherexample.com'))


def switch_tab(tab_widget, direction):
    current_index = tab_widget.currentIndex()
    total_tabs = tab_widget.count()
    new_index = (current_index + direction) % total_tabs
    tab_widget.setCurrentIndex(new_index)


def switch_to_tab(tab_widget, index):
    if 0 <= index < tab_widget.count():
        tab_widget.setCurrentIndex(index)


def refresh_tab(tab_widget):
    current_widget = tab_widget.currentWidget()
    if isinstance(current_widget, QWebEngineView):
        auto_switcher = getattr(tab_widget, 'auto_switcher', None)
        if auto_switcher:
            auto_switcher.save_ui_state(current_widget)
            current_widget.reload()
            current_widget.loadFinished.connect(lambda: auto_switcher.restore_ui_state(current_widget))
        else:
            current_widget.reload()


def refresh_all_tabs(tab_widget):
    auto_switcher = getattr(tab_widget, 'auto_switcher', None)
    for i in range(tab_widget.count()):
        widget = tab_widget.widget(i)
        if isinstance(widget, QWebEngineView):
            if auto_switcher:
                auto_switcher.save_ui_state(widget)
                widget.reload()
                widget.loadFinished.connect(lambda w=widget: auto_switcher.restore_ui_state(w))
            else:
                widget.reload()


def main():
    app = QApplication(sys.argv)

    # Create a stacked widget to switch between screens
    stacked_widget = QStackedWidget()

    # Create the initial page with buttons
    initial_page = InitialPage(start_app, start_admin_console)

    # Add the initial page to the stacked widget
    stacked_widget.addWidget(initial_page)

    # Show the initial page
    stacked_widget.showFullScreen()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
