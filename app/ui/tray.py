from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.settings import AppSettings
from app.ui.sprite import BODY, EYE, OUTLINE, PINK


def make_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    outline = QPen(OUTLINE, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(outline)
    painter.setBrush(QBrush(BODY))
    for sx in (-1, 1):
        triangle = QPolygonF(
            [
                QPointF(32 + sx * 6, 16),
                QPointF(32 + sx * 16, 22),
                QPointF(32 + sx * 12, 8),
            ]
        )
        painter.drawPolygon(triangle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(PINK))
        inner = QPolygonF(
            [
                QPointF(32 + sx * 8.5, 14.5),
                QPointF(32 + sx * 13.5, 18.5),
                QPointF(32 + sx * 12, 11),
            ]
        )
        painter.drawPolygon(inner)
        painter.setBrush(QBrush(BODY))
        painter.setPen(outline)
    painter.drawEllipse(QPointF(32, 36), 23, 20)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(EYE))
    painter.drawEllipse(QPointF(25, 33), 2.6, 3.2)
    painter.drawEllipse(QPointF(39, 33), 2.6, 3.2)
    painter.setBrush(QBrush(PINK))
    painter.drawEllipse(QPointF(32, 40), 2.2, 1.8)
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, pet, panel, quit_callback, open_settings_callback, parent=None):
        super().__init__(make_icon(), parent)
        self._pet = pet
        self._menu = QMenu()
        self._menu.addAction("顯示小貓", pet.show_normal)
        if panel is not None:
            self._menu.addAction("任務清單", lambda: panel.toggle_for(pet))
        hidden_action = self._menu.addAction("隱藏模式")
        hidden_action.setCheckable(True)
        hidden_action.setChecked(AppSettings.hidden())
        hidden_action.toggled.connect(pet.set_hidden_mode)
        pet.hidden_changed.connect(self._on_hidden_changed)
        self._hidden_action = hidden_action
        self._mute_action = self._menu.addAction("靜音")
        self._mute_action.setCheckable(True)
        self._mute_action.setChecked(pet.sound.muted)
        self._mute_action.toggled.connect(pet.set_muted)
        pet.muted_changed.connect(self._on_muted_changed)
        self._menu.addAction("設置…", open_settings_callback)
        self._menu.addSeparator()
        self._menu.addAction("離開", quit_callback)
        self.setContextMenu(self._menu)
        self.setToolTip("Catkit 桌面貓任務管理")
        self.activated.connect(self._on_activated)
        self.show()

    def _on_muted_changed(self, muted: bool):
        self._mute_action.blockSignals(True)
        self._mute_action.setChecked(bool(muted))
        self._mute_action.blockSignals(False)

    def _on_hidden_changed(self, hidden: bool):
        self._hidden_action.blockSignals(True)
        self._hidden_action.setChecked(bool(hidden))
        self._hidden_action.blockSignals(False)

    def show_message(self, title: str, text: str):
        self.showMessage(
            title, text, QSystemTrayIcon.MessageIcon.Information, 8000
        )

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._pet.show_normal()
