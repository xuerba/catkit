import math
from datetime import datetime, timedelta

from PySide6.QtCore import (
    QDate,
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    QTime,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QActionGroup,
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.model.task import (
    PRIORITY_NAMES,
    STATUS_DONE,
    STATUS_DOING,
    STATUS_NAMES,
    STATUS_TODO,
)
from app import __author__, __version__
from app.settings import AppSettings
from app.ui import sprite
from app.ui.animations import AnimationHelper, graphics_effects_supported
from app.ui.theme import ThemeManager

FILTERS = [
    ("all", "全部"),
    (STATUS_TODO, "待開始"),
    (STATUS_DOING, "進行中"),
    (STATUS_DONE, "已完成"),
    ("overdue", "已延期"),
]

REMIND_OPTIONS = ["不提醒", "準時提醒", "提前 5 分鐘", "提前 10 分鐘", "提前 30 分鐘"]
REMIND_OFFSETS = {1: 0, 2: 5, 3: 10, 4: 30}

CATEGORIES = ["工作", "生活", "學習", "健康", "其它"]

# 狀態 Chip 配色：(背景, 文字)；作用中則改用主題狀態色實心底＋白字
CHIP_PALETTE = {
    STATUS_TODO: ("#FBF7EE", "#8A6A4B"),   # 待開始：米白
    STATUS_DOING: ("#E4F0FB", "#3B7DBF"),  # 進行中：淺藍
    STATUS_DONE: ("#E7F5E9", "#3D8B4A"),   # 已完成：淺綠
    "overdue": ("#FCEAEA", "#C9524E"),     # 已延期：淺紅
}


def _emoji_icon(emoji: str, size: int = 16) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setFont(ThemeManager.font(pixel_size=int(size * 0.8)))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
    painter.end()
    return QIcon(pixmap)


def _chip_style(
    bg: str,
    fg: str,
    active_color: str,
    active: bool = False,
    muted: bool = False,
    hover: bool = False,
) -> str:
    base = "border-radius: 7px; padding: 3px 10px; font-size: 12px;"
    if active:
        return (
            f"background: {active_color}; color: #FFFFFF;"
            f"border: 1px solid {active_color};{base} font-weight: 700;"
        )
    if muted:
        return (
            f"background: {ThemeManager.tint(bg, 0.5)};"
            f"color: {ThemeManager.current().text_light};"
            f"border: 1px solid transparent;{base} font-weight: 600;"
        )
    border = ThemeManager.tint(fg, 0.55 if hover else 0.22)
    return (
        f"background: {bg}; color: {fg}; border: 1px solid {border};"
        f"{base} font-weight: 600;"
    )


def _alpha_color(hex_color: str, alpha: float) -> QColor:
    color = QColor(hex_color)
    color.setAlphaF(alpha)
    return color


def _icon_pixmap(kind: str, size: int, color: str) -> QPixmap:
    icon = sprite.build_icon(kind, size, color)
    pixmap = icon.pixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2)
    return pixmap


class _ChipLabel(QLabel):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("點擊篩選；再點一次取消篩選")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setContentsMargins(0, 0, 0, 0)
        self._bg = "#FFFFFF"
        self._fg = "#333333"
        self._active_color = "#4A90E2"
        self._active = False
        self._muted = False
        self._hover = False
        if graphics_effects_supported():
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(9)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 55))
            self.setGraphicsEffect(shadow)
        self._refresh_style()

    def set_appearance(
        self, bg: str, fg: str, active_color: str, active: bool, muted: bool
    ):
        self._bg = bg
        self._fg = fg
        self._active_color = active_color
        self._active = active
        self._muted = muted
        self._refresh_style()

    def _refresh_style(self):
        self.setStyleSheet(
            _chip_style(
                self._bg,
                self._fg,
                self._active_color,
                active=self._active,
                muted=self._muted,
                hover=self._hover,
            )
        )

    def enterEvent(self, event):
        self._hover = True
        self._refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._refresh_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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
    label: str, minimum: int, maximum: int, tick_interval: int, suffix: str
) -> tuple[QSlider, QWidget]:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setTickPosition(QSlider.TickPosition.TicksBelow)
    slider.setTickInterval(tick_interval)
    slider.setMinimumHeight(30)
    value_label = QLabel()
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    value_label.setMinimumWidth(44)

    def _refresh(value: int):
        value_label.setText(f"{value:02d}{suffix}")

    slider.valueChanged.connect(_refresh)
    slider.valueChanged.emit(slider.value())
    column = QVBoxLayout()
    column.setContentsMargins(0, 0, 0, 0)
    column.setSpacing(2)
    column.addWidget(_make_label(label))
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)
    row_layout.addWidget(slider, 1)
    row_layout.addWidget(value_label)
    column.addWidget(row)
    container = QWidget()
    container.setLayout(column)
    return slider, container


class DateTimePopup(QDialog):
    def __init__(self, parent=None, allow_clear=False):
        super().__init__(
            parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.result_datetime = None
        self._calendar = QCalendarWidget()
        self._calendar.setGridVisible(True)
        self._calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self._hour_slider, hour_widget = _make_slider_row(
            "小時", 0, 23, 3, " 時"
        )
        self._minute_slider, minute_widget = _make_slider_row(
            "分鐘", 0, 59, 5, " 分"
        )
        actions_row = QHBoxLayout()
        actions_row.addStretch(1)
        if allow_clear:
            clear_button = QPushButton("未設定")
            clear_button.setObjectName("ghost")
            clear_button.clicked.connect(self._clear)
            actions_row.addWidget(clear_button)
        confirm_button = QPushButton("確定")
        confirm_button.setObjectName("primary")
        confirm_button.clicked.connect(self._confirm)
        actions_row.addWidget(confirm_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self._calendar)
        layout.addWidget(hour_widget)
        layout.addWidget(minute_widget)
        layout.addLayout(actions_row)
        self.setMinimumWidth(330)

    def open_for(self, current: datetime | None) -> bool:
        if current is not None:
            self._calendar.setSelectedDate(
                QDate(current.year, current.month, current.day)
            )
            self._hour_slider.setValue(current.hour)
            self._minute_slider.setValue(current.minute)
        else:
            self._calendar.setSelectedDate(QDate.currentDate())
        accepted = self.exec() == QDialog.DialogCode.Accepted
        return accepted

    def _confirm(self):
        qdate = self._calendar.selectedDate()
        self.result_datetime = datetime(
            qdate.year(),
            qdate.month(),
            qdate.day(),
            self._hour_slider.value(),
            self._minute_slider.value(),
        )
        self.accept()

    def _clear(self):
        self.result_datetime = None
        self.accept()


class DateTimeField(QPushButton):
    def __init__(self, initial: datetime | None = None, allow_clear=False, parent=None):
        super().__init__(parent)
        self.setObjectName("dateField")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._allow_clear = allow_clear
        self._value = initial
        self._popup = DateTimePopup(self, allow_clear=allow_clear)
        self.clicked.connect(self._open)
        self._refresh()

    def value(self) -> datetime | None:
        return self._value

    def set_value(self, value: datetime | None):
        self._value = value
        self._refresh()

    def _refresh(self):
        if self._value is None:
            self.setText("未設定")
        else:
            self.setText(self._value.strftime("%Y-%m-%d %H:%M"))

    def _open(self):
        if self._popup.open_for(self._value):
            self._value = self._popup.result_datetime
            self._refresh()


class _SearchInput(QLineEdit):
    """搜尋框：文字一律靠左，Focus 狀態由 QSS 主色外框呈現。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchInput")
        self.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )


class _RowStyledDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        tokens = ThemeManager.current()
        if selected:
            background = _alpha_color(tokens.primary, 0.16)
        elif hovered:
            background = _alpha_color(tokens.primary, 0.08)
        elif index.row() % 2 == 1:
            background = _alpha_color(tokens.text_light, 0.06)
        else:
            background = QColor(tokens.bg)
        painter.save()
        painter.fillRect(option.rect, background)
        painter.setPen(QPen(_alpha_color(tokens.border, 0.6), 1))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        self._paint_content(painter, option, index)
        painter.restore()

    def _paint_content(self, painter, option, index):
        pass


class _CellDelegate(_RowStyledDelegate):
    """分類／DRI／結束時間等一般文字欄位，共用列的底色與選取樣式。"""

    def _paint_content(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        brush = index.data(Qt.ItemDataRole.ForegroundRole)
        if isinstance(brush, QBrush):
            color = brush.color()
        elif isinstance(brush, QColor):
            color = brush
        else:
            color = QColor(ThemeManager.current().text_dark)
        elided = QFontMetrics(option.font).elidedText(
            text, Qt.TextElideMode.ElideRight, option.rect.width() - 20
        )
        painter.setFont(option.font)
        painter.setPen(color)
        painter.drawText(
            option.rect.adjusted(10, 0, -8, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided,
        )


class _TitleDelegate(_RowStyledDelegate):
    def _paint_content(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        metrics = QFontMetrics(option.font)
        elided = metrics.elidedText(
            text, Qt.TextElideMode.ElideRight, option.rect.width() - 22
        )
        painter.setFont(option.font)
        painter.setPen(QColor(ThemeManager.current().text_dark))
        painter.drawText(
            option.rect.adjusted(10, 0, -6, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided,
        )


class _PriorityDelegate(_RowStyledDelegate):
    _COLORS = {}

    def _paint_content(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        tokens = ThemeManager.current()
        colors = {
            "高": tokens.status_overdue,
            "中": tokens.status_doing,
            "低": tokens.text_light,
        }
        color = colors.get(text, tokens.text_light)
        painter.setFont(option.font)
        metrics = QFontMetrics(option.font)
        width = metrics.horizontalAdvance(text) + 16
        badge = QRect(option.rect.left() + 10, 0, width, 20)
        badge.moveTop(option.rect.center().y() - 10)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_alpha_color(color, 0.14))
        painter.drawRoundedRect(badge, 6, 6)
        painter.setPen(QColor(color))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, text)


class _StatusDelegate(_RowStyledDelegate):
    def __init__(self, table):
        super().__init__(table)
        self._table = table

    def _paint_content(self, painter, option, index):
        status = index.data(Qt.ItemDataRole.UserRole) or STATUS_TODO
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        overdue = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        tokens = ThemeManager.current()
        colors = {
            "todo": tokens.status_todo,
            "doing": tokens.status_doing,
            "done": tokens.status_done,
            "overdue": tokens.status_overdue,
        }
        color = QColor(colors.get(status, tokens.text_light))
        if overdue and status != STATUS_DONE:
            color = QColor(tokens.status_overdue)
        dot = QColor(color)
        if status == STATUS_DOING and not overdue:
            phase = getattr(self._table, "_pulse_phase", 0.0)
            dot.setAlphaF(0.45 + 0.55 * (0.5 + 0.5 * math.sin(phase * 2 * math.pi)))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot)
        painter.drawEllipse(
            QPoint(option.rect.left() + 14, option.rect.center().y()), 4, 4
        )
        painter.setFont(option.font)
        painter.setPen(color)
        painter.drawText(
            option.rect.adjusted(26, 0, -8, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )
        painter.restore()


class TaskTable(QTableWidget):
    empty_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(0, 7, parent)
        self._empty_pixmap = None
        self._pulse_phase = 0.0
        self._has_active = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(60)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.refresh_theme_pixmap()

    def set_active_dot(self, active: bool):
        self._has_active = bool(active)
        self._sync_pulse()

    def _sync_pulse(self):
        if self._has_active and self.isVisible():
            if not self._pulse_timer.isActive():
                self._pulse_timer.start()
        else:
            self._pulse_timer.stop()

    def _tick_pulse(self):
        self._pulse_phase = (self._pulse_phase + 1 / 60.0) % 1.0
        if self.columnCount() > 5:
            x = self.columnViewportPosition(5)
            self.viewport().update(x, 0, self.columnWidth(5), self.viewport().height())
        else:
            self.viewport().update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_pulse()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._pulse_timer.stop()

    def refresh_theme_pixmap(self):
        self._empty_pixmap = sprite.build_frames("sleep")[0].scaled(
            84,
            84,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount() > 0:
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        viewport = self.viewport().rect()
        pixmap = self._empty_pixmap
        tokens = ThemeManager.current()
        font = ThemeManager.font(pixel_size=14)
        hint_font = ThemeManager.font(pixel_size=12)
        title_height = QFontMetrics(font).height()
        hint_height = QFontMetrics(hint_font).height()
        gap = 8
        total = pixmap.height() + gap + title_height + 2 + hint_height
        top = max(4, viewport.center().y() - total // 2)
        painter.drawPixmap(
            viewport.center().x() - pixmap.width() // 2, top, pixmap
        )
        painter.setFont(font)
        painter.setPen(QColor(tokens.text_dark))
        painter.drawText(
            QRect(
                0,
                top + pixmap.height() + gap,
                viewport.width(),
                title_height + 4,
            ),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "暫無任務",
        )
        painter.setFont(hint_font)
        painter.setPen(QColor(tokens.text_light))
        painter.drawText(
            QRect(
                0,
                top + pixmap.height() + gap + title_height + 2,
                viewport.width(),
                hint_height + 4,
            ),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "點擊上方 ＋ 新增任務，喵～",
        )
        painter.end()

    def mousePressEvent(self, event):
        if self.rowCount() == 0 and event.button() == Qt.MouseButton.LeftButton:
            self.empty_clicked.emit()
        super().mousePressEvent(event)


class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("新增任務" if task is None else "編輯任務")
        self.setMinimumWidth(420)
        self.title_edit = QLineEdit()
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setFixedHeight(72)
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.dri_edit = QLineEdit()
        self.dri_edit.setPlaceholderText("直接負責人")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["低", "中", "高"])
        self.priority_combo.setCurrentIndex(1)
        self.start_field = DateTimeField(
            initial=datetime.now().replace(second=0, microsecond=0)
        )
        self.end_field = DateTimeField(allow_clear=True)
        self.remind_combo = QComboBox()
        self.remind_combo.addItems(REMIND_OPTIONS)
        if task is None:
            self.remind_combo.setCurrentIndex(AppSettings.reminder_option())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(4)
        layout.addWidget(_make_label("標題"))
        layout.addWidget(self.title_edit)
        layout.addSpacing(6)
        layout.addWidget(_make_label("說明"))
        layout.addWidget(self.desc_edit)
        layout.addSpacing(10)
        layout.addWidget(_make_separator())
        layout.addSpacing(8)
        grid_row = QHBoxLayout()
        grid_row.setSpacing(12)
        for text, widget in (
            ("分類", self.category_combo),
            ("DRI", self.dri_edit),
            ("優先序", self.priority_combo),
        ):
            column = QVBoxLayout()
            column.setSpacing(4)
            column.addWidget(_make_label(text))
            column.addWidget(widget)
            grid_row.addLayout(column, 1)
        layout.addLayout(grid_row)
        layout.addSpacing(8)
        layout.addWidget(_make_separator())
        layout.addSpacing(8)
        layout.addWidget(_make_label("開始時間"))
        start_row = QHBoxLayout()
        start_row.addWidget(self.start_field, 1)
        layout.addLayout(start_row)
        layout.addSpacing(6)
        layout.addWidget(_make_label("結束時間"))
        due_row = QHBoxLayout()
        due_row.addWidget(self.end_field, 1)
        layout.addLayout(due_row)
        layout.addSpacing(6)
        layout.addWidget(_make_label("提醒方式"))
        layout.addWidget(self.remind_combo)
        layout.addSpacing(12)
        buttons_row = QHBoxLayout()
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("ghost")
        cancel_button.clicked.connect(self.reject)
        ok_button = QPushButton("確定")
        ok_button.setObjectName("primary")
        ok_button.clicked.connect(self.accept)
        buttons_row.addStretch(1)
        buttons_row.addWidget(cancel_button)
        buttons_row.addWidget(ok_button)
        layout.addLayout(buttons_row)
        AnimationHelper.apply_hover_lift(ok_button)
        if task is not None:
            self._prefill(task)

    def _prefill(self, task: object):
        self.title_edit.setText(task.title)
        self.desc_edit.setPlainText(task.description)
        stored_category = (task.category or "").strip()
        stored_index = self.category_combo.findText(stored_category)
        if stored_category and stored_index < 0:
            self.category_combo.addItem(stored_category)
            self.category_combo.setCurrentIndex(self.category_combo.count() - 1)
        else:
            self.category_combo.setCurrentIndex(max(stored_index, 0))
        self.dri_edit.setText(task.dri)
        self.priority_combo.setCurrentIndex(int(task.priority))
        if task.start_at is not None:
            self.start_field.set_value(task.start_at)
        self.end_field.set_value(task.due_at)
        if task.remind_at is None and task.start_remind_at is None:
            self.remind_combo.setCurrentIndex(0)
        elif task.remind_at is not None and task.due_at is not None:
            self.remind_combo.setCurrentIndex(
                self._best_offset_index(task.due_at, task.remind_at)
            )
        elif task.remind_at is not None:
            self.end_field.set_value(task.remind_at)
            self.remind_combo.setCurrentIndex(1)
        elif task.start_at is not None:
            self.remind_combo.setCurrentIndex(
                self._best_offset_index(task.start_at, task.start_remind_at)
            )
        else:
            self.remind_combo.setCurrentIndex(1)

    def _best_offset_index(self, base: datetime, remind: datetime) -> int:
        diff = (base - remind).total_seconds() / 60.0
        best_index = 1
        best_gap = None
        for index, offset in REMIND_OFFSETS.items():
            gap = abs(diff - offset)
            if best_gap is None or gap < best_gap:
                best_gap = gap
                best_index = index
        return best_index

    def accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "提醒", "任務標題不可為空")
            return
        super().accept()

    def result_data(self) -> dict:
        start = self.start_field.value()
        due = self.end_field.value()
        index = self.remind_combo.currentIndex()

        def offset_time(base: datetime | None):
            if index == 0 or base is None:
                return None
            return base - timedelta(minutes=REMIND_OFFSETS[index])

        return {
            "title": self.title_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "category": self.category_combo.currentText(),
            "dri": self.dri_edit.text().strip(),
            "start_at": start,
            "due_at": due,
            "priority": self.priority_combo.currentIndex(),
            "remind_at": offset_time(due),
            "start_remind_at": offset_time(start),
        }


class TaskPanel(QWidget):
    task_changed = Signal()
    task_completed = Signal(bool)

    def __init__(self, service, stand, pet, parent=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.service = service
        self.stand = stand
        self.pet = pet
        self._keyword = ""
        self._filter = "all"
        self._drag_offset = None
        self._hiding = False
        self._maximized = False
        self._normal_geometry = None
        self._resize_edges = Qt.Edge(0)
        self._resize_start_geo = None
        self._resize_start_pos = None
        self.setMouseTracking(True)
        self.resize(700, 440)
        self.setMinimumSize(430, 320)
        card = QFrame(self)
        card.setObjectName("card")
        self._card = card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 5)
        shadow.setColor(ThemeManager.parse_shadow(ThemeManager.current().shadow))
        card.setGraphicsEffect(shadow)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 14)
        outer.addWidget(card)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 6, 14, 10)
        header_row = QHBoxLayout()
        header_row.setSpacing(4)
        title_icon = QLabel()
        title_icon.setPixmap(
            _icon_pixmap("check", 16, ThemeManager.current().primary)
        )
        title_icon.setFixedSize(16, 16)
        panel_title = QLabel("任務清單")
        panel_title.setObjectName("panelTitle")
        minimize_button = QPushButton("─")
        minimize_button.setObjectName("minimize")
        minimize_button.setFixedSize(28, 24)
        minimize_button.setToolTip("最小化")
        minimize_button.clicked.connect(self.animate_hide)
        self._max_button = QPushButton("□")
        self._max_button.setObjectName("minimize")
        self._max_button.setFixedSize(28, 24)
        self._max_button.setToolTip("最大化")
        self._max_button.clicked.connect(self._toggle_maximize)
        close_button = QPushButton("✕")
        close_button.setObjectName("windowClose")
        close_button.setFixedSize(28, 24)
        close_button.setToolTip("關閉")
        close_button.clicked.connect(self.animate_hide)
        self._stand_button = QPushButton("站立提醒")
        self._stand_button.setObjectName("standBtn")
        self._stand_button.setFixedHeight(26)
        self._stand_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stand_button.setToolTip("站立提醒：定期提醒你站起來活動，避免久坐")
        self._stand_button.clicked.connect(self._show_stand_menu)
        self._about_button = QPushButton("關於")
        self._about_button.setObjectName("standBtn")
        self._about_button.setFixedHeight(26)
        self._about_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._about_button.setToolTip("關於 Catkit")
        self._about_button.clicked.connect(self._show_about)
        header_row.addWidget(title_icon)
        header_row.addWidget(panel_title)
        header_row.addStretch(1)
        header_row.addWidget(self._stand_button)
        header_row.addWidget(self._about_button)
        header_row.addWidget(minimize_button)
        header_row.addWidget(self._max_button)
        header_row.addWidget(close_button)
        inner.addLayout(header_row)
        header_line = QFrame()
        header_line.setObjectName("separator")
        header_line.setFixedHeight(1)
        inner.addSpacing(4)
        inner.addWidget(header_line)
        inner.addSpacing(4)
        chips_row = QHBoxLayout()
        self._chips = {}
        for key, label in (
            (STATUS_TODO, "待開始"),
            (STATUS_DOING, "進行中"),
            (STATUS_DONE, "已完成"),
            ("overdue", "已延期"),
        ):
            chip = _ChipLabel()
            chip.clicked.connect(lambda k=key: self._on_chip_clicked(k))
            chips_row.addWidget(chip)
            self._chips[key] = chip
        chips_row.addStretch(1)
        inner.addLayout(chips_row)
        self._update_chip_styles()
        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        self._search = _SearchInput()
        self._search.setPlaceholderText("搜尋任務名稱、分類或 DRI...")
        self._search.addAction(
            _emoji_icon("🔍"), QLineEdit.ActionPosition.LeadingPosition
        )
        palette = self._search.palette()
        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor(ThemeManager.current().text_light),
        )
        self._search.setPalette(palette)
        self._search.textChanged.connect(self._on_search)
        self._filter_combo = QComboBox()
        self._filter_combo.setObjectName("filterCombo")
        self._filter_combo.setFixedWidth(112)
        self._filter_combo.setToolTip("依狀態篩選任務")
        for _, label in FILTERS:
            self._filter_combo.addItem(label)
        self._filter_combo.currentIndexChanged.connect(self._on_filter)
        self._add_button = QPushButton()
        self._add_button.setObjectName("addFab")
        self._add_button.setFixedSize(32, 32)
        self._add_button.setToolTip("新增任務")
        self._add_button.clicked.connect(self.open_new)
        search_row.addWidget(self._search, 1)
        search_row.addWidget(self._filter_combo)
        search_row.addWidget(self._add_button)
        inner.addLayout(search_row)
        self._table = TaskTable()
        self._table.setHorizontalHeaderLabels(
            ["標題", "分類", "DRI", "結束時間", "優先序", "狀態", "操作"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self._table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_menu)
        self._table.doubleClicked.connect(lambda _: self._edit())
        self._table.empty_clicked.connect(self.open_new)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(40)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in {1: 56, 2: 60, 3: 92, 4: 52, 5: 84, 6: 66}.items():
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(column, width)
        self._table.setItemDelegateForColumn(0, _TitleDelegate(self._table))
        for column in range(1, 4):
            self._table.setItemDelegateForColumn(column, _CellDelegate(self._table))
        self._table.setItemDelegateForColumn(4, _PriorityDelegate(self._table))
        self._table.setItemDelegateForColumn(5, _StatusDelegate(self._table))
        self._table.setItemDelegateForColumn(6, _RowStyledDelegate(self._table))
        self._table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._table.setWordWrap(False)
        header.setFixedHeight(38)
        header.setHighlightSections(False)
        inner.addWidget(self._table, 1)
        self._apply_button_icons()
        AnimationHelper.apply_hover_lift(self._add_button)
        AnimationHelper.apply_hover_lift(self._stand_button)
        AnimationHelper.apply_hover_lift(self._about_button)
        QApplication.instance().installEventFilter(self)
        self.refresh()

    def _edges_at(self, pos) -> Qt.Edges:
        margin = 10
        edges = Qt.Edge(0)
        if pos.x() <= margin:
            edges |= Qt.Edge.LeftEdge
        if pos.x() >= self.width() - margin:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= margin:
            edges |= Qt.Edge.TopEdge
        if pos.y() >= self.height() - margin:
            edges |= Qt.Edge.BottomEdge
        return edges

    def _cursor_for(self, edges: Qt.Edges) -> Qt.CursorShape:
        horizontal = bool(edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge))
        vertical = bool(edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge))
        if horizontal and vertical:
            left_top = bool(edges & Qt.Edge.LeftEdge) and bool(edges & Qt.Edge.TopEdge)
            right_bottom = bool(edges & Qt.Edge.RightEdge) and bool(
                edges & Qt.Edge.BottomEdge
            )
            if left_top or right_bottom:
                return Qt.CursorShape.SizeFDiagCursor
            return Qt.CursorShape.SizeBDiagCursor
        if horizontal:
            return Qt.CursorShape.SizeHorCursor
        return Qt.CursorShape.SizeVerCursor

    def _update_resize_cursor(self, pos):
        edges = self._edges_at(pos)
        if edges:
            self.setCursor(self._cursor_for(edges))
        else:
            self.unsetCursor()

    def eventFilter(self, obj, event):
        try:
            if (
                obj is QApplication.instance()
                and self.isVisible()
                and not self._hiding
                and event.type() == QEvent.Type.MouseButtonPress
            ):
                pos = event.globalPosition().toPoint()
                if not self.frameGeometry().contains(pos) and (
                    self.pet is None or not self.pet.frameGeometry().contains(pos)
                ):
                    self.animate_hide()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def toggle_for(self, pet: QWidget):
        if self.isVisible():
            self.animate_hide()
            return
        self.refresh()
        geo = pet.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry()
        x = min(max(geo.left(), screen.left() + 4), screen.right() - self.width() - 4)
        y = max(screen.top() + 4, geo.top() - self.height() - 8)
        self._animate_show(x, y)

    def _animate_show(self, x: int, y: int):
        AnimationHelper.panel_pop_in(self, x, y)

    def animate_hide(self):
        if self._hiding:
            return
        self._hiding = True
        AnimationHelper.panel_pop_out(self, self._on_hidden)

    def _on_hidden(self):
        self.hide()
        self.setWindowOpacity(1.0)
        if self._maximized:
            self._toggle_maximize()
        self._hiding = False

    def _toggle_maximize(self):
        screen = self.screen() or QApplication.primaryScreen()
        available = screen.availableGeometry()
        if self._maximized:
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            self._maximized = False
            self._max_button.setText("□")
            self._max_button.setToolTip("最大化")
        else:
            self._normal_geometry = self.geometry()
            self.setGeometry(available)
            self._maximized = True
            self._max_button.setText("❐")
            self._max_button.setToolTip("還原")

    def apply_theme(self):
        self._apply_button_icons()
        self._update_chip_styles()
        self._table.refresh_theme_pixmap()
        shadow = self._card.graphicsEffect()
        if shadow is not None:
            shadow.setColor(
                ThemeManager.parse_shadow(ThemeManager.current().shadow)
            )
        self.refresh()

    def refresh(self):
        tokens = ThemeManager.current()
        stats = self.service.stats()
        for key, label in (
            (STATUS_TODO, "待開始"),
            (STATUS_DOING, "進行中"),
            (STATUS_DONE, "已完成"),
            ("overdue", "已延期"),
        ):
            count = stats.get(key, 0)
            self._chips[key].setText(f"{label}&nbsp;<b>{count}</b>")
        tasks = self.service.list_tasks(self._keyword, self._filter)
        now = datetime.now()
        table = self._table
        table.setRowCount(len(tasks))
        strike_font = QFont()
        strike_font.setStrikeOut(True)
        has_active = False
        for row, task in enumerate(tasks):
            overdue = task.is_overdue(now)
            done = task.status == STATUS_DONE
            if task.status == STATUS_DOING:
                has_active = True
            base_color = QColor(tokens.text_light if done else tokens.text_dark)
            items = [
                QTableWidgetItem(task.title),
                QTableWidgetItem(task.category),
                QTableWidgetItem(task.dri),
                QTableWidgetItem(
                    task.due_at.strftime("%m-%d %H:%M") if task.due_at else "-"
                ),
                QTableWidgetItem(PRIORITY_NAMES.get(task.priority, "中")),
                QTableWidgetItem(STATUS_NAMES.get(task.status, task.status)),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                item.setForeground(base_color)
                table.setItem(row, col, item)
            status_item = items[5]
            status_item.setData(Qt.ItemDataRole.UserRole, task.status)
            status_item.setData(Qt.ItemDataRole.UserRole + 1, overdue)
            if overdue and not done:
                items[3].setForeground(QColor(tokens.status_overdue))
            if done:
                items[0].setFont(strike_font)
            items[0].setToolTip(task.title)
            items[0].setData(Qt.ItemDataRole.UserRole, task.id)
            table.setCellWidget(row, 6, self._make_row_actions(task.id))
        table.set_active_dot(has_active)

    def _on_search(self, text: str):
        self._keyword = text.strip()
        self.refresh()

    def _show_about(self):
        QMessageBox.information(
            self,
            "關於 Catkit",
            f"Catkit 桌面貓咪任務管理工具\n\n"
            f"版本：v{__version__}\n"
            f"開發人員：{__author__}",
        )

    def _show_stand_menu(self):
        menu = QMenu(self)
        if self.stand is None:
            return
        enable_action = menu.addAction("啟用站立提醒")
        enable_action.setCheckable(True)
        enable_action.setChecked(self.stand.enabled)
        enable_action.toggled.connect(self._on_stand_toggled)
        menu.addSeparator()
        interval_group = QActionGroup(menu)
        interval_group.setExclusive(True)
        for minutes in (30, 45, 60, 90):
            action = menu.addAction(f"每 {minutes} 分鐘")
            action.setCheckable(True)
            action.setChecked(self.stand.interval == minutes)
            interval_group.addAction(action)
            action.triggered.connect(
                lambda checked=False, m=minutes: self._on_stand_interval(m)
            )
        menu.exec(self._stand_button.mapToGlobal(self._stand_button.rect().bottomLeft()))

    def _on_stand_toggled(self, checked: bool):
        self.stand.set_enabled(checked)
        if checked:
            self.pet.say(f"好喵！每 {self.stand.interval} 分鐘提醒你站起來活動！")
        else:
            self.pet.say("知道囉，先關閉站立提醒喵。")

    def _on_stand_interval(self, minutes: int):
        self.stand.set_interval(minutes)
        if self.stand.enabled:
            self.pet.say(f"好喵！改成每 {minutes} 分鐘提醒你站起來！")

    def _on_filter(self, index: int):
        self._filter = FILTERS[index][0]
        self._update_chip_styles()
        self.refresh()

    def _on_chip_clicked(self, key: str):
        self._set_filter("all" if self._filter == key else key)

    def _set_filter(self, key: str):
        self._filter = key
        index = next(
            (i for i, (k, _) in enumerate(FILTERS) if k == key), 0
        )
        self._filter_combo.blockSignals(True)
        self._filter_combo.setCurrentIndex(index)
        self._filter_combo.blockSignals(False)
        self._update_chip_styles()
        self.refresh()

    def _update_chip_styles(self):
        colors = ThemeManager.status_colors()
        tokens = ThemeManager.current()
        stats = self.service.stats()
        for key, chip in self._chips.items():
            default = (tokens.text_light, tokens.text_dark)
            bg, fg = CHIP_PALETTE.get(key, default)
            muted = stats.get(key, 0) == 0 and self._filter != key
            chip.set_appearance(
                bg,
                fg,
                colors.get(key, tokens.primary),
                active=key == self._filter,
                muted=muted,
            )

    def _apply_button_icons(self):
        tokens = ThemeManager.current()
        self._stand_button.setIcon(
            QIcon(
                sprite.build_frames("sit")[0].scaled(
                    14,
                    14,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        )
        self._stand_button.setIconSize(QSize(14, 14))
        self._add_button.setIcon(sprite.build_icon("plus", 16, "#FFFFFF"))
        self._add_button.setIconSize(QSize(16, 16))
        self._row_edit_icon = sprite.build_icon("edit", 14, tokens.primary)
        self._row_delete_icon = sprite.build_icon(
            "trash", 14, tokens.status_overdue
        )

    def _make_row_actions(self, task_id: int) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 4, 0)
        row.setSpacing(6)
        edit_button = QPushButton()
        edit_button.setObjectName("rowIconBtn")
        edit_button.setFixedSize(26, 26)
        edit_button.setToolTip("編輯")
        edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_button.setIcon(self._row_edit_icon)
        edit_button.setIconSize(QSize(14, 14))
        edit_button.clicked.connect(lambda _=False, tid=task_id: self._edit_task(tid))
        delete_button = QPushButton()
        delete_button.setObjectName("rowIconDanger")
        delete_button.setFixedSize(26, 26)
        delete_button.setToolTip("刪除")
        delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_button.setIcon(self._row_delete_icon)
        delete_button.setIconSize(QSize(14, 14))
        delete_button.clicked.connect(
            lambda _=False, tid=task_id: self._delete_task(tid)
        )
        row.addStretch(1)
        row.addWidget(edit_button)
        row.addWidget(delete_button)
        return container

    def _edit_task(self, task_id: int):
        task = self.service.get(task_id)
        if task is None:
            return
        dialog = TaskDialog(self, task)
        if dialog.exec():
            self.service.update(task.id, **dialog.result_data())
            self._after_change()

    def _delete_task(self, task_id: int):
        task = self.service.get(task_id)
        if task is None:
            return
        answer = QMessageBox.question(
            self, "刪除任務", f"確定刪除「{task.title}」？"
        )
        if answer == QMessageBox.Yes:
            self.service.delete(task.id)
            self._after_change()

    def _selected_task(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if item is None:
            return None
        task_id = item.data(Qt.ItemDataRole.UserRole)
        return self.service.get(task_id) if task_id is not None else None

    def _after_change(self):
        self.refresh()
        self.task_changed.emit()

    def open_new(self, parent=None):
        dialog = TaskDialog(self)
        if dialog.exec():
            self.service.create(**dialog.result_data())
            self._after_change()

    def _edit(self):
        task = self._selected_task()
        if task is None:
            return
        dialog = TaskDialog(self, task)
        if dialog.exec():
            self.service.update(task.id, **dialog.result_data())
            self._after_change()

    def _delete(self):
        task = self._selected_task()
        if task is None:
            return
        answer = QMessageBox.question(
            self, "刪除任務", f"確定刪除「{task.title}」？"
        )
        if answer == QMessageBox.Yes:
            self.service.delete(task.id)
            self._after_change()

    def _cycle(self):
        task = self._selected_task()
        if task is None:
            return
        updated = self.service.cycle_status(task.id)
        if updated.status == STATUS_DONE:
            stats = self.service.stats()
            all_done = (
                stats.get(STATUS_TODO, 0) == 0
                and stats.get(STATUS_DOING, 0) == 0
                and stats.get("overdue", 0) == 0
                and stats.get(STATUS_DONE, 0) > 0
            )
            self.task_completed.emit(all_done)
        self._after_change()

    def _snooze(self, minutes: int):
        task = self._selected_task()
        if task is None:
            return
        self.service.snooze(task.id, minutes)
        self._after_change()

    def _show_menu(self, pos):
        task = self._selected_task()
        if task is None:
            return
        menu = QMenu(self)
        menu.addAction("編輯", self._edit)
        menu.addAction("切換狀態", self._cycle)
        snooze_menu = menu.addMenu("賴床")
        for minutes, label in (
            (5, "再打個盹 5 分鐘"),
            (10, "再打個盹 10 分鐘"),
            (30, "再打個盹 30 分鐘"),
        ):
            snooze_menu.addAction(label, lambda m=minutes: self._snooze(m))
        menu.addSeparator()
        menu.addAction("刪除", self._delete)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._maximized:
                self._drag_offset = None
                return
            pos = event.position().toPoint()
            edges = self._edges_at(pos)
            if edges:
                self._resize_edges = edges
                self._resize_start_geo = QRect(self.geometry())
                self._resize_start_pos = event.globalPosition().toPoint()
                self._drag_offset = None
                self.setCursor(self._cursor_for(edges))
                return
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        gpos = event.globalPosition().toPoint()
        if self._resize_edges:
            self._apply_resize(gpos)
            return
        if self._maximized:
            self.unsetCursor()
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            self._update_resize_cursor(event.position().toPoint())
            return
        if self._drag_offset is not None:
            self.move(gpos - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._resize_edges = Qt.Edge(0)
            self._resize_start_geo = None
            self._resize_start_pos = None
            if not self._edges_at(event.position().toPoint()):
                self.unsetCursor()
        self._drag_offset = None

    def _apply_resize(self, gpos):
        geo = QRect(self._resize_start_geo)
        dx = gpos.x() - self._resize_start_pos.x()
        dy = gpos.y() - self._resize_start_pos.y()
        min_w = self.minimumSize().width()
        min_h = self.minimumSize().height()
        edges = self._resize_edges
        if edges & Qt.Edge.LeftEdge:
            geo.setLeft(min(geo.left() + dx, geo.right() - min_w + 1))
        elif edges & Qt.Edge.RightEdge:
            geo.setRight(max(geo.right() + dx, geo.left() + min_w - 1))
        if edges & Qt.Edge.TopEdge:
            geo.setTop(min(geo.top() + dy, geo.bottom() - min_h + 1))
        elif edges & Qt.Edge.BottomEdge:
            geo.setBottom(max(geo.bottom() + dy, geo.top() + min_h - 1))
        self.setGeometry(geo)
