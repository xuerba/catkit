import signal
import sys

from PySide6.QtCore import QLoggingCategory, QSettings
from PySide6.QtWidgets import QApplication

from app.db import init_db
from app.service.reminder_service import ReminderService
from app.service.stand_service import StandService
from app.service.task_service import TaskService
from app.settings import AppSettings
from app.sound import MeowPlayer
from app.ui.pet_widget import PetWidget
from app.ui.settings_dialog import SettingsDialog
from app.ui.task_panel import TaskPanel
from app.ui.theme import THEME_BY_NAME, ThemeManager, Themes
from app.ui.tray import TrayIcon, make_icon


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    QLoggingCategory.setFilterRules("qt.multimedia.ffmpeg=false")
    app = QApplication(sys.argv)
    app.setApplicationName("catkit")
    app.setOrganizationName("catkit")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(make_icon())
    init_db()
    service = TaskService()
    sound = MeowPlayer()
    pet = PetWidget(service, sound, QSettings())
    stand = StandService()
    panel = TaskPanel(service, stand, pet)
    reminder = ReminderService(service)
    pet.set_panel(panel)
    pet.set_quit_callback(lambda: _quit(app, pet))
    reminder.reminder_due.connect(pet.on_reminder)
    reminder.start()
    stand.stand_due.connect(pet.on_stand_reminder)
    panel.task_changed.connect(pet.refresh_stats)
    panel.task_completed.connect(pet.celebrate)

    def apply_all_settings():
        tokens = THEME_BY_NAME.get(AppSettings.theme_name(), Themes.WARM)
        ThemeManager.set_theme(app, tokens)
        pet.on_theme_changed()
        panel.apply_theme()
        pet.set_muted(AppSettings.muted())
        pet.set_bubble_size(AppSettings.bubble_size())
        pet.set_pet_size(AppSettings.pet_size())
        pet.set_pet_opacity(AppSettings.pet_opacity())
        _apply_font(app)

    def open_settings():
        dialog = SettingsDialog(pet)
        dialog.settings_applied.connect(apply_all_settings)
        dialog.exec()

    pet.settings_requested.connect(open_settings)
    tray = TrayIcon(pet, panel, lambda: _quit(app, pet), open_settings)
    pet.notify_requested.connect(
        lambda text: tray.show_message("Catkit 小貓提醒", text)
    )
    apply_all_settings()
    pet.initial_position()
    if AppSettings.hidden():
        pet.set_hidden_mode(True)
    else:
        pet.show()
    sys.exit(app.exec())


def _apply_font(app):
    family = AppSettings.font_family()
    app.setFont(
        ThemeManager.font(
            point_size=AppSettings.font_size(), family=family or None
        )
    )


def _quit(app, pet):
    pet.save_position()
    app.quit()


if __name__ == "__main__":
    main()
