from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QParallelAnimationGroup,
    QPropertyAnimation,
)
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QGraphicsDropShadowEffect


def graphics_effects_supported() -> bool:
    """offscreen（無頭測試）平台對巢狀 GraphicsEffect 支援不穩定，故略過立體陰影。"""
    return QGuiApplication.platformName() != "offscreen"


class HoverLift(QObject):
    """按鈕的立體陰影：平時即有柔和 3D 陰影，Hover 時加深。"""

    def __init__(self, button, base_blur: float = 8.0):
        super().__init__(button)
        self._base_blur = base_blur
        self._hover_blur = base_blur + 10
        self._effect = None
        self._anim = None
        if not graphics_effects_supported():
            return
        self._effect = QGraphicsDropShadowEffect(button)
        self._effect.setBlurRadius(base_blur)
        self._effect.setOffset(0, 2)
        self._effect.setColor(QColor(0, 0, 0, 50))
        button.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"blurRadius", self)
        self._anim.setDuration(140)
        button.installEventFilter(self)

    def eventFilter(self, obj, event):
        if self._effect is None:
            return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.HoverEnter:
            self._animate_to(self._hover_blur)
        elif event.type() == QEvent.Type.HoverLeave:
            self._animate_to(self._base_blur)
        return super().eventFilter(obj, event)

    def _animate_to(self, target):
        if self._anim is None or self._effect is None:
            return
        self._anim.stop()
        self._anim.setStartValue(self._effect.blurRadius())
        self._anim.setEndValue(target)
        self._anim.start()


class AnimationHelper:
    @staticmethod
    def panel_pop_in(panel, x: int, y: int):
        panel.setWindowOpacity(0.0)
        panel.move(x, y + 8)
        panel.show()
        panel.raise_()
        panel.activateWindow()
        group = QParallelAnimationGroup(panel)
        fade = QPropertyAnimation(panel, b"windowOpacity")
        fade.setDuration(200)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        rise = QPropertyAnimation(panel, b"pos")
        rise.setDuration(200)
        rise.setStartValue(QPoint(x, y + 8))
        rise.setEndValue(QPoint(x, y))
        rise.setEasingCurve(QEasingCurve.OutCubic)
        group.addAnimation(fade)
        group.addAnimation(rise)
        panel._pop_group = group
        group.start()

    @staticmethod
    def panel_pop_out(panel, on_hidden):
        fade = QPropertyAnimation(panel, b"windowOpacity", panel)
        fade.setDuration(200)
        fade.setStartValue(panel.windowOpacity())
        fade.setEndValue(0.0)
        fade.finished.connect(on_hidden)
        panel._hide_anim = fade
        fade.start()

    @staticmethod
    def fade_in_widget(widget, duration: int = 200):
        effect = widget.graphicsEffect()
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        widget._fade_in_anim = anim
        anim.start()

    @staticmethod
    def fade_out_widget(widget, on_done=None, duration: int = 200):
        effect = widget.graphicsEffect()
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(effect.opacity())
        anim.setEndValue(0.0)
        if on_done is not None:
            anim.finished.connect(on_done)
        widget._fade_out_anim = anim
        anim.start()

    @staticmethod
    def apply_hover_lift(button, base_blur: float = 8.0):
        HoverLift(button, base_blur)
