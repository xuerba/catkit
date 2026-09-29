import os
import sys
import tempfile
import wave
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.db as db

db.DB_DIR = Path(tempfile.mkdtemp(prefix="catkit-smoke-"))
db.DB_PATH = db.DB_DIR / "tasks.db"

from PySide6.QtCore import (
    QDate,
    QPoint,
    QRect,
    QSettings,
    Qt,
    QTimer,
    qInstallMessageHandler,
)
from PySide6.QtWidgets import QApplication


def _quiet_qt_messages(mode, context, message):
    if (
        "window masks" in message
        or "does not support raise" in message
        or "Cannot find font directory" in message
    ):
        return
    sys.stderr.write(message + "\n")


qInstallMessageHandler(_quiet_qt_messages)

from app.service.stand_service import StandService
from app.service.reminder_service import ReminderService
from app.service.task_service import TaskService
from app.settings import AppSettings
from app.sound import MeowPlayer
from app.ui import sprite
from app.ui.theme import ThemeManager, Themes
from app.ui.pet_widget import PetWidget
from app.ui.settings_dialog import SettingsDialog
from app.ui.task_panel import TaskPanel, TaskDialog
from app.ui.tray import TrayIcon, make_icon

STATES = [
    "sit", "doze", "scratch", "cuddle", "roll", "walk",
    "alert", "lifted", "sleep",
]

app = QApplication(sys.argv)
app.setOrganizationName("catkit-smoke")
app.setApplicationName("catkit-smoke")
app.setQuitOnLastWindowClosed(False)
app.setFont(ThemeManager.font(point_size=10))
ThemeManager.set_theme(app, Themes.WARM)

db.init_db()
service = TaskService()

task_a = service.create("測試A", description="說明A", category="工作", dri="小貓", due_at=datetime.now() + timedelta(hours=2), priority=2, remind_at=datetime.now() + timedelta(minutes=30))
task_b = service.create("測試B", due_at=datetime.now() - timedelta(hours=1))
task_c = service.create("測試C")
assert task_a.id and task_b.id and task_c.id
assert task_a.category == "工作" and task_a.dri == "小貓"

stats = service.stats()
assert stats["todo"] == 3 and stats["overdue"] == 1, stats

assert service.list_tasks(keyword="測試A")[0].id == task_a.id
assert service.list_tasks(keyword="小貓")[0].id == task_a.id
assert len(service.list_tasks(status_filter="overdue")) == 1

updated = service.cycle_status(task_c.id)
assert updated.status == "doing"
updated = service.cycle_status(task_c.id)
assert updated.status == "done"
assert service.stats()["done"] == 1

service.snooze(task_a.id, 5)
task = service.get(task_a.id)
assert task.remind_at > datetime.now() and not task.reminded

service.update(task_a.id, "測試A-改", "x", "工作", "小貓", None, task.due_at, 2, datetime.now() - timedelta(minutes=1))
task = service.get(task_a.id)
assert task.title == "測試A-改" and not task.reminded

OLD_SCHEMA = """
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    due_at      TEXT,
    priority    INTEGER NOT NULL DEFAULT 1,
    status      TEXT NOT NULL DEFAULT 'todo',
    remind_at   TEXT,
    reminded    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""
reminder = ReminderService(service)
events = []
reminder.reminder_due.connect(lambda task, stage: events.append((task.id, stage)))
reminder.check()
assert events, "提醒事件未觸發"
assert all(t.reminded for t in [service.get(task_a.id)])

task_start = service.create(
    "測試開始提醒",
    start_at=datetime.now() - timedelta(minutes=1),
    start_remind_at=datetime.now() - timedelta(minutes=2),
    due_at=datetime.now() + timedelta(hours=1),
    remind_at=datetime.now() + timedelta(minutes=30),
)
start_events = []
reminder2 = ReminderService(service)
reminder2.reminder_due.connect(
    lambda t, s: start_events.append((t.id, s))
)
reminder2.check()
assert (task_start.id, "start") in start_events, start_events
assert service.get(task_start.id).start_reminded
assert service.get(task_start.id).reminded is False

import app.service.stand_service as stand_module

stand_module.idle_seconds = lambda: 0.0
stand = StandService()
stand_events = []
stand.stand_due.connect(stand_events.append)
assert stand.enabled is False
stand.set_interval(1)
stand.set_enabled(True)
stand._accumulated = 55.0
stand._on_tick()
assert stand_events == [1], stand_events
assert stand._accumulated == 0.0
stand_module.idle_seconds = lambda: 400.0
stand._accumulated = 30.0
stand._on_tick()
assert stand._accumulated == 0.0 and stand_events == [1]
stand_module.idle_seconds = lambda: 0.0
stand.set_enabled(False)
assert AppSettings.stand_reminder_enabled() is False
assert AppSettings.stand_interval() == 1

for state in STATES:
    frames = sprite.build_frames(state)
    assert len(frames) >= 2, state
    assert frames[0].size().width() == 192, state

icon = make_icon()
assert not icon.isNull()

sound = MeowPlayer()
with wave.open(str(db.DB_DIR / "meow.wav"), "rb") as f:
    assert f.getframerate() == 44100

pet = PetWidget(service, sound, QSettings())
pet.initial_position()
pet.on_reminder(service.get(task_b.id), "overdue")
pet.on_stand_reminder(45)
pet.celebrate(False)
pet.bubble.popup("煙霧測試氣泡", 2)
pet.grab()
pet.bubble.dismiss()
pet.set_bubble_size("small")
pet.bubble.popup("大小測試", 1)
small_width = pet.bubble.width()
pet.bubble.dismiss()
pet.set_bubble_size("large")
pet.bubble.popup("大小測試", 1)
large_width = pet.bubble.width()
pet.grab()
pet.bubble.dismiss()
assert large_width > small_width, (small_width, large_width)
pet.set_bubble_size("medium")
pet.set_muted(True)
assert AppSettings.muted() is True and pet.sound.muted
pet.set_muted(False)
assert AppSettings.muted() is False and not pet.sound.muted

pet.set_pet_size("tiny")
assert pet.width() == int(300 * 0.5) and pet.animator._size == 96
pet.set_pet_size("large")
assert pet.width() == int(300 * 1.25) and pet.animator._size == 240
assert sprite.build_frames("sit", 240)[0].size().width() == 240
pet.set_pet_size("small")
assert pet.width() == int(300 * 0.75) and pet.animator._size == 144
pet.set_pet_size("medium")
assert pet.width() == 300 and pet.animator._size == 192
pet.set_pet_opacity(60)
assert AppSettings.pet_opacity() == 60
assert abs(pet.windowOpacity() - 0.6) < 0.01
pet.set_pet_opacity(200)
assert AppSettings.pet_opacity() == 100 and pet.windowOpacity() == 1.0

notify_events = []
pet.notify_requested.connect(notify_events.append)
pet.set_hidden_mode(True)
assert pet.isHidden() and AppSettings.hidden() is True
assert not pet.animator._timer.isActive()
pet.on_reminder(service.get(task_b.id), "due")
assert notify_events and notify_events[0].endswith("喵！"), notify_events
pet.set_hidden_mode(False)
assert not pet.isHidden() and not AppSettings.hidden()
assert pet.animator._timer.isActive()

panel = TaskPanel(service, stand, pet)
panel.refresh()
panel.grab()
assert panel._add_button.width() == 32
assert not panel._add_button.icon().isNull()
assert panel._table.rowCount() >= 3
assert panel._table.cellWidget(0, 6) is not None
panel.resize(640, 480)
assert panel.width() == 640 and panel.height() == 480, (
    panel.width(),
    panel.height(),
)
panel._resize_edges = Qt.Edge.RightEdge | Qt.Edge.BottomEdge
panel._resize_start_geo = QRect(panel.geometry())
panel._resize_start_pos = QPoint(0, 0)
panel._apply_resize(QPoint(80, 60))
assert panel.width() == 720 and panel.height() == 540, (
    panel.width(),
    panel.height(),
)
panel._apply_resize(QPoint(-100000, -100000))
assert panel.width() == 430 and panel.height() == 320, (
    panel.width(),
    panel.height(),
)
panel._resize_edges = Qt.Edge(0)
panel.resize(640, 480)
panel._on_chip_clicked("todo")
assert panel._filter == "todo" and panel._filter_combo.currentIndex() == 1
panel._on_chip_clicked("todo")
assert panel._filter == "all" and panel._filter_combo.currentIndex() == 0
panel._on_chip_clicked("overdue")
assert panel._filter == "overdue" and panel._filter_combo.currentIndex() == 4
panel._set_filter("all")
panel._table.setRowCount(0)
panel._table.grab()
panel.refresh()
panel.grab()
panel.toggle_for(pet)
panel.toggle_for(pet)

panel._toggle_maximize()
assert panel._maximized and panel.width() >= 800, panel.width()
panel._toggle_maximize()
assert not panel._maximized and panel.width() == 640

tray = TrayIcon(pet, panel, lambda: None, lambda: None)
assert tray.isVisible()

dialog_settings = SettingsDialog()
dialog_settings.font_size_slider.setValue(12)
dialog_settings.opacity_slider.setValue(80)
dialog_settings.pet_combo.setCurrentIndex(3)
dialog_settings._on_save()
assert AppSettings.font_size() == 12
assert AppSettings.pet_size() == "large"
assert AppSettings.pet_opacity() == 80
AppSettings.set_font_size(10)
AppSettings.set_pet_size("medium")
AppSettings.set_pet_opacity(100)

ThemeManager.set_theme(app, Themes.TECH)
pet.on_theme_changed()
panel.apply_theme()
panel.refresh()
assert sprite.build_frames("sit"), "TECH 主題幀重建失敗"
assert panel._table.rowCount() >= 3
ThemeManager.set_theme(app, Themes.WARM)
pet.on_theme_changed()
panel.apply_theme()
panel.refresh()

OLD_SCHEMA = """
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    due_at      TEXT,
    priority    INTEGER NOT NULL DEFAULT 1,
    status      TEXT NOT NULL DEFAULT 'todo',
    remind_at   TEXT,
    reminded    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""
raw_conn = db.connect()
raw_conn.execute("DROP TABLE tasks")
raw_conn.execute(OLD_SCHEMA)
raw_conn.commit()
raw_conn.close()
db.init_db()
migrated = TaskService()
task_m = migrated.create("遷移任務", category="生活", dri="小魚")
assert migrated.get(task_m.id).dri == "小魚"

dialog = TaskDialog()
data = dialog.result_data()
assert data["start_at"] is not None and data["due_at"] is None
assert data["start_remind_at"] is not None and data["remind_at"] is None
assert dialog.category_combo.count() == 5 and dialog.category_combo.currentText() == "工作"
dialog.category_combo.setCurrentIndex(3)
assert dialog.result_data()["category"] == "健康"
legacy = service.create("舊分類任務", category="自訂分類")
legacy_dialog = TaskDialog(None, service.get(legacy.id))
assert legacy_dialog.category_combo.currentText() == "自訂分類"
assert legacy_dialog.result_data()["category"] == "自訂分類"
AppSettings.set_reminder_option(0)
dialog = TaskDialog()
data = dialog.result_data()
assert data["remind_at"] is None and data["start_remind_at"] is None
assert data["start_at"] is not None and data["due_at"] is None
AppSettings.set_reminder_option(3)

dialog = TaskDialog()
dialog.end_field.set_value(
    datetime.now().replace(second=0, microsecond=0) + timedelta(hours=25)
)
data = dialog.result_data()
assert data["due_at"] is not None and data["remind_at"] is not None
assert data["start_remind_at"] < data["start_at"] < data["remind_at"] < data["due_at"]

dialog_keep = TaskDialog()
field = dialog_keep.end_field
assert field.value() is None
popup = field._popup
popup._calendar.setSelectedDate(QDate(2026, 10, 5))
popup._hour_slider.setValue(9)
popup._minute_slider.setValue(30)
popup._confirm()
assert popup.result_datetime == datetime(2026, 10, 5, 9, 30)
popup._clear()
assert popup.result_datetime is None

trip = service.create(
    "往返測試",
    start_at=datetime.now() + timedelta(hours=1),
    due_at=datetime.now() + timedelta(hours=2),
    remind_at=datetime.now() + timedelta(hours=2) - timedelta(minutes=5),
    start_remind_at=datetime.now() + timedelta(hours=1) - timedelta(minutes=10),
)
dlg = TaskDialog(None, service.get(trip.id))
out = dlg.result_data()
assert out["start_at"] is not None and out["due_at"] is not None
assert out["remind_at"] is not None and out["start_remind_at"] is not None
assert out["start_remind_at"] < out["start_at"] < out["remind_at"] < out["due_at"]

pet.save_position()
pet.set_hidden_mode(True)
pet.set_hidden_mode(False)

QTimer.singleShot(200, app.quit)
app.exec()
print("SMOKE OK")
