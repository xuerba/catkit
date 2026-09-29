from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.settings import AppSettings
from app.ui.animations import AnimationHelper
from app.ui.task_panel import REMIND_OPTIONS
from app.ui.theme import Themes

THEME_LABELS = [
    ("溫馨暖色", "warm"),
    ("賽博科技", "tech"),
    ("極簡北歐", "nordic"),
]

BUBBLE_LABELS = [("小", "small"), ("中", "medium"), ("大", "large")]

PET_SIZE_LABELS = [("特小", "tiny"), ("小", "small"), ("中", "medium"), ("大", "large")]

FONT_CANDIDATES = [
    "Noto Sans TC",
    "Microsoft YaHei",
    "Microsoft JhengHei",
    "PingFang TC",
    "SimHei",
]


def _make_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("fieldLabel")
    return label


def _make_separator() -> QFrame:
    line = QFrame()
    line.setObjectName("separator")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line


def _make_slider_row(
    minimum: int, maximum: int, tick_interval: int, suffix: str
) -> tuple[QSlider, QWidget]:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    slider.setTickInterval(tick_interval)
    slider.setMinimumHeight(30)
    value_label = QLabel()
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    value_label.setMinimumWidth(48)

    def _refresh(value: int):
        value_label.setText(f"{value}{suffix}")

    slider.valueChanged.connect(_refresh)
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)
    row_layout.addWidget(slider, 1)
    row_layout.addWidget(value_label)
    return slider, row


class SettingsDialog(QDialog):
    settings_applied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設置")
        self.setMinimumWidth(380)

        self.theme_combo = QComboBox()
        for label, _ in THEME_LABELS:
            self.theme_combo.addItem(label)

        self.font_combo = QComboBox()
        self.font_combo.addItem("系統預設", "")
        installed = set(QFontDatabase.families())
        for family in FONT_CANDIDATES:
            if family in installed:
                self.font_combo.addItem(family, family)

        self.font_size_slider, self._font_size_row = _make_slider_row(
            9, 16, 1, " pt"
        )

        self.opacity_slider, self._opacity_row = _make_slider_row(
            30, 100, 10, " %"
        )

        self.pet_combo = QComboBox()
        for label, _ in PET_SIZE_LABELS:
            self.pet_combo.addItem(label)

        self.bubble_combo = QComboBox()
        for label, _ in BUBBLE_LABELS:
            self.bubble_combo.addItem(label)

        self.mute_check = QCheckBox("靜音（關閉喵聲）")

        self.remind_combo = QComboBox()
        self.remind_combo.addItems(REMIND_OPTIONS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(4)

        layout.addWidget(_make_label("主題"))
        layout.addWidget(self.theme_combo)
        layout.addSpacing(4)
        layout.addWidget(_make_label("字體"))
        layout.addWidget(self.font_combo)
        layout.addSpacing(4)
        layout.addWidget(_make_label("字體大小"))
        layout.addWidget(self._font_size_row)
        layout.addSpacing(4)
        layout.addWidget(_make_label("小貓透明度"))
        layout.addWidget(self._opacity_row)
        layout.addSpacing(4)
        size_row = QHBoxLayout()
        size_row.setSpacing(12)
        for text, widget in (
            ("小貓大小", self.pet_combo),
            ("氣泡大小", self.bubble_combo),
        ):
            column = QVBoxLayout()
            column.setSpacing(2)
            column.addWidget(_make_label(text))
            column.addWidget(widget)
            size_row.addLayout(column, 1)
        layout.addLayout(size_row)
        layout.addSpacing(8)
        layout.addWidget(_make_separator())
        layout.addSpacing(8)

        layout.addWidget(_make_label("提醒與音效"))
        layout.addWidget(self.mute_check)
        layout.addSpacing(4)
        layout.addWidget(_make_label("預設提醒方式（套用於新增任務）"))
        layout.addWidget(self.remind_combo)
        layout.addSpacing(12)

        buttons_row = QHBoxLayout()
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("ghost")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("儲存")
        save_button.setObjectName("primary")
        save_button.clicked.connect(self._on_save)
        buttons_row.addStretch(1)
        buttons_row.addWidget(cancel_button)
        buttons_row.addWidget(save_button)
        layout.addLayout(buttons_row)
        AnimationHelper.apply_hover_lift(save_button)
        self._prefill()

    def _prefill(self):
        theme_name = AppSettings.theme_name()
        for index, (_, name) in enumerate(THEME_LABELS):
            if name == theme_name:
                self.theme_combo.setCurrentIndex(index)
                break
        current_family = AppSettings.font_family()
        family_index = self.font_combo.findData(current_family)
        self.font_combo.setCurrentIndex(max(family_index, 0))
        self.font_size_slider.setValue(AppSettings.font_size())
        bubble_index = 1
        for index, (_, key) in enumerate(BUBBLE_LABELS):
            if key == AppSettings.bubble_size():
                bubble_index = index
                break
        self.bubble_combo.setCurrentIndex(bubble_index)
        pet_index = 1
        for index, (_, key) in enumerate(PET_SIZE_LABELS):
            if key == AppSettings.pet_size():
                pet_index = index
                break
        self.pet_combo.setCurrentIndex(pet_index)
        self.opacity_slider.setValue(AppSettings.pet_opacity())
        self.mute_check.setChecked(AppSettings.muted())
        self.remind_combo.setCurrentIndex(
            max(0, min(AppSettings.reminder_option(), self.remind_combo.count() - 1))
        )

    def _on_save(self):
        AppSettings.set_theme_name(THEME_LABELS[self.theme_combo.currentIndex()][1])
        AppSettings.set_font_family(self.font_combo.currentData() or "")
        AppSettings.set_font_size(self.font_size_slider.value())
        AppSettings.set_bubble_size(BUBBLE_LABELS[self.bubble_combo.currentIndex()][1])
        AppSettings.set_pet_size(PET_SIZE_LABELS[self.pet_combo.currentIndex()][1])
        AppSettings.set_pet_opacity(self.opacity_slider.value())
        AppSettings.set_muted(self.mute_check.isChecked())
        AppSettings.set_reminder_option(self.remind_combo.currentIndex())
        self.settings_applied.emit()
        self.accept()
