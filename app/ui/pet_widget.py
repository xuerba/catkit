import random
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QPainter, QRegion
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from app.settings import AppSettings
from app.ui.animator import Animator
from app.ui.speech_bubble import BUBBLE_SCALES, SpeechBubble

W, H = 300, 330
CAT_X, CAT_Y, CAT_SIZE = 54, 132, 192

PET_SIZES = {"tiny": 0.5, "small": 0.75, "medium": 1.0, "large": 1.25}

IDLE_STATES = ["sit", "doze", "scratch", "roll", "walk", "cuddle"]

OVERDUE_TEXTS = [
    "還沒做完『{t}』…貓替你著急喵！",
    "『{t}』已經延期了，喵嗚…拜託動手吧！",
    "『{t}』再不做，貓要生氣囉！(炸毛)",
]


class PetWidget(QWidget):
    muted_changed = Signal(bool)
    settings_requested = Signal()
    hidden_changed = Signal(bool)
    notify_requested = Signal(str)

    def __init__(self, service, sound, settings, parent=None):
        super().__init__(
            None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.service = service
        self.sound = sound
        self.settings = settings
        self._panel = None
        self._quit_callback = None
        self._pet_size = AppSettings.pet_size()
        if self._pet_size not in PET_SIZES:
            self._pet_size = "medium"
        scale = PET_SIZES[self._pet_size]
        self._cat_x = int(CAT_X * scale)
        self._cat_y = int(CAT_Y * scale)
        self.setFixedSize(int(W * scale), int(H * scale))
        self.setWindowTitle("Catkit 桌面貓")
        self._pixmap = None
        self._state = "sit"
        self._special = False
        self._hidden_mode = False
        self._stats = service.stats()
        self._nag_counts = {}
        self.animator = Animator(self)
        self.animator.set_size(int(CAT_SIZE * scale))
        self._bubble_size = AppSettings.bubble_size()
        if self._bubble_size not in BUBBLE_SCALES:
            self._bubble_size = "medium"
        self.bubble = SpeechBubble(
            self, scale=BUBBLE_SCALES[self._bubble_size] * scale
        )
        self.animator.frame_ready.connect(self._on_frame)
        self.animator.set_state("sit")
        self._press_pos = None
        self._drag_offset = None
        self._drag_moved = False
        self._press_time = 0.0
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(280)
        self._click_timer.timeout.connect(self._pet_action)
        self._walk_dir = 1
        self._walk_left = 0
        self._walk_timer = QTimer(self)
        self._walk_timer.setInterval(70)
        self._walk_timer.timeout.connect(self._walk_step)
        self._behavior = QTimer(self)
        self._behavior.setInterval(1000)
        self._behavior.timeout.connect(self._idle_tick)
        self._behavior.start()

    def set_panel(self, panel):
        self._panel = panel

    def set_quit_callback(self, callback):
        self._quit_callback = callback

    def refresh_stats(self):
        self._stats = self.service.stats()

    def on_theme_changed(self):
        loop = self._state in ("sit", "doze", "walk", "lifted", "sleep")
        self.animator.set_state(
            self._state, loop=loop, on_done=None if loop else self._back_to_sit
        )
        self.bubble.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._pixmap is not None:
            painter.drawPixmap(self._cat_x, self._cat_y, self._pixmap)

    def _on_frame(self, pixmap):
        self._pixmap = pixmap
        self.update()
        region = QRegion(pixmap.createHeuristicMask())
        region.translate(self._cat_x, self._cat_y)
        if self.bubble is not None and self.bubble.isVisible():
            region += QRegion(self.bubble.geometry())
        self.setMask(region)

    def _idle_tick(self):
        if self._special or self._hidden_mode:
            return
        if self._state not in ("sit", "doze"):
            return
        if random.random() > 0.12:
            return
        state = random.choices(IDLE_STATES, weights=self._weights(), k=1)[0]
        if state == self._state:
            state = "sit"
        if state == "walk":
            self._start_walk()
        else:
            self._play(state)

    def _weights(self):
        pending = self._stats.get("todo", 0) + self._stats.get("doing", 0)
        overdue = self._stats.get("overdue", 0)
        doze = max(0.2, 1.6 - pending * 0.12 - overdue * 0.3)
        return [2.0, doze, 1.2, 0.8, 1.0, 0.6]

    def _play(self, state: str, on_done=None):
        self._state = state
        self._special = state in ("scratch", "roll", "cuddle")
        one_shot = self._special
        callback = on_done or (self._back_to_sit if one_shot else None)
        self.animator.set_state(state, loop=not one_shot, on_done=callback)

    def _back_to_sit(self):
        self._special = False
        self._state = "sit"
        self.animator.set_state("sit")

    def _start_walk(self):
        self._state = "walk"
        self._walk_left = random.randint(60, 150)
        screen = self.screen().availableGeometry() if self.screen() else None
        geo = self.geometry()
        if screen is not None:
            if geo.left() <= screen.left() + 10:
                self._walk_dir = 1
            elif geo.right() >= screen.right() - 10:
                self._walk_dir = -1
            else:
                self._walk_dir = random.choice((-1, 1))
        self.animator.set_state("walk")
        self._walk_timer.start()

    def _walk_step(self):
        new_x = self.x() + self._walk_dir * 2
        self.move(new_x, self.y())
        self._walk_left -= 2
        screen = self.screen().availableGeometry() if self.screen() else None
        out_of_bounds = screen is not None and (
            new_x <= screen.left() + 4 or new_x + self.width() >= screen.right() - 4
        )
        if self._walk_left <= 0 or out_of_bounds:
            self._walk_timer.stop()
            self._state = "sit"
            self.animator.set_state("sit")

    def _pet_action(self):
        self.sound.play()
        self.bubble.popup(self._stats_report(), 5)
        self._play("cuddle")

    def _stats_report(self):
        s = self._stats
        if s.get("todo", 0) + s.get("doing", 0) + s.get("overdue", 0) == 0:
            if s.get("done", 0) > 0:
                return "今天全數完成，喵嗚～可以一起打盹了！"
            return "今天沒有待辦，一起打盹吧，喵～"
        return (
            f"待開始 {s.get('todo', 0)}、進行中 {s.get('doing', 0)}、"
            f"已延期 {s.get('overdue', 0)}，喵～"
        )

    def on_reminder(self, task, stage: str):
        title = task.title
        if stage == "start":
            text = f"『{title}』開始時間到啦，動工喵！"
        elif stage == "early":
            text = f"喵～『{title}』就快到時間囉！"
        elif stage == "due":
            text = f"時間到啦！『{title}』該動手了喵！"
        else:
            count = self._nag_counts.get(task.id, 0)
            self._nag_counts[task.id] = count + 1
            text = OVERDUE_TEXTS[min(count, len(OVERDUE_TEXTS) - 1)].format(t=title)
        if self._hidden_mode:
            self.notify_requested.emit(text)
            return
        self.sound.play()
        self._show_alert(text)

    def _show_alert(self, text: str):
        if self._hidden_mode:
            return
        self.bubble.popup(text, 6)
        self._state = "alert"
        self._special = True
        self.animator.set_state("alert", loop=False, on_done=self._back_to_sit)

    def celebrate(self, all_done: bool):
        self.refresh_stats()
        text = "全部完成！喵嗚～撒嬌時間！" if all_done else "搞定啦！喵嗚～"
        if self._hidden_mode:
            self.notify_requested.emit(text)
            return
        self.bubble.popup(text, 4)
        self._play("cuddle" if all_done else "roll")
        self.sound.play()

    def say(self, text: str, seconds: float = 5.0):
        if self._hidden_mode:
            self.notify_requested.emit(text)
            return
        self.bubble.popup(text, seconds)
        self.sound.play()

    def on_stand_reminder(self, minutes: int):
        if self._hidden_mode:
            self.notify_requested.emit(
                f"已連續工作 {minutes} 分鐘囉！站起來伸展一下吧，喵～"
            )
            return
        self.bubble.popup(
            f"已連續工作 {minutes} 分鐘囉！站起來伸個懶腰吧，喵～", 8
        )
        self.sound.play()
        self._state = "scratch"
        self._special = True
        self.animator.set_state("scratch", loop=False, on_done=self._back_to_sit)

    def set_hidden_mode(self, on: bool):
        on = bool(on)
        if self._hidden_mode == on:
            return
        self._hidden_mode = on
        AppSettings.set_hidden(on)
        if on:
            self.animator.stop()
            self._behavior.stop()
            self._walk_timer.stop()
            self.bubble.dismiss()
            self.hide()
        else:
            self.show()
            self._behavior.start()
            self._back_to_sit()
        self.hidden_changed.emit(on)

    def show_normal(self):
        if self._hidden_mode:
            self.set_hidden_mode(False)
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def initial_position(self):
        x = self.settings.value("pet/x", None)
        y = self.settings.value("pet/y", None)
        if x is not None and y is not None:
            self.move(int(x), int(y))
            return
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.right() - self.width() - 24, screen.bottom() - self.height() - 8
        )

    def save_position(self):
        self.settings.setValue("pet/x", self.x())
        self.settings.setValue("pet/y", self.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
            self._drag_moved = False
            self._press_time = time.monotonic()
        elif event.button() == Qt.RightButton:
            self._show_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self._press_pos is None:
            return
        delta = event.globalPosition().toPoint() - self._press_pos
        if not self._drag_moved and delta.manhattanLength() > 10:
            self._drag_moved = True
            self._click_timer.stop()
            self._state = "lifted"
            self._special = True
            self.animator.set_state("lifted", loop=True)
        if self._drag_moved:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._press_pos is None:
            return
        if self._drag_moved:
            self.save_position()
            self._special = False
            self._state = "sit"
            self.animator.set_state("sit")
        elif time.monotonic() - self._press_time < 1.0:
            self._click_timer.start()
        self._press_pos = None
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        self._click_timer.stop()
        if self._panel is not None:
            self._panel.toggle_for(self)

    def set_bubble_size(self, size_key: str):
        if size_key not in BUBBLE_SCALES:
            return
        self._bubble_size = size_key
        AppSettings.set_bubble_size(size_key)
        self.bubble.set_scale(
            BUBBLE_SCALES[size_key] * PET_SIZES[self._pet_size]
        )

    def set_pet_size(self, size_key: str):
        if size_key not in PET_SIZES:
            return
        self._pet_size = size_key
        AppSettings.set_pet_size(size_key)
        self._apply_pet_layout()

    def set_pet_opacity(self, percent: int):
        percent = max(20, min(100, int(percent)))
        AppSettings.set_pet_opacity(percent)
        self.setWindowOpacity(percent / 100.0)

    def _apply_pet_layout(self):
        scale = PET_SIZES[self._pet_size]
        self._cat_x = int(CAT_X * scale)
        self._cat_y = int(CAT_Y * scale)
        self.setFixedSize(int(W * scale), int(H * scale))
        self.animator.set_size(int(CAT_SIZE * scale))
        self.bubble.set_scale(
            BUBBLE_SCALES[self._bubble_size] * scale
        )
        loop = self._state in ("sit", "doze", "walk", "lifted", "sleep")
        self.animator.set_state(
            self._state, loop=loop, on_done=None if loop else self._back_to_sit
        )
        self.update()

    def set_muted(self, muted: bool):
        self.sound.set_muted(bool(muted))
        AppSettings.set_muted(bool(muted))
        self.muted_changed.emit(bool(muted))

    def _show_menu(self, gpos):
        menu = QMenu(self)
        if self._panel is not None:
            menu.addAction("新增任務", lambda: self._panel.open_new(self))
            menu.addAction("任務清單", lambda: self._panel.toggle_for(self))
        size_menu = menu.addMenu("氣泡大小")
        size_group = QActionGroup(size_menu)
        size_group.setExclusive(True)
        for key, label in (("small", "小"), ("medium", "中"), ("large", "大")):
            action = size_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(key == self._bubble_size)
            action.triggered.connect(
                lambda checked=False, k=key: self.set_bubble_size(k)
            )
            size_group.addAction(action)
        hidden_action = menu.addAction("隱藏模式")
        hidden_action.setCheckable(True)
        hidden_action.setChecked(self._hidden_mode)
        hidden_action.toggled.connect(self.set_hidden_mode)
        mute_action = menu.addAction("靜音")
        mute_action.setCheckable(True)
        mute_action.setChecked(self.sound.muted)
        mute_action.toggled.connect(self.set_muted)
        menu.addAction("設置…", lambda: self.settings_requested.emit())
        menu.addSeparator()
        menu.addAction("離開", self._quit)
        menu.exec(gpos)

    def _quit(self):
        if self._quit_callback:
            self._quit_callback()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
