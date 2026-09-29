import html

from PySide6.QtCore import QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QTextDocument
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from app.ui.animations import AnimationHelper
from app.ui.theme import ThemeManager

BASE_MAX_WIDTH = 210.0
BASE_FONT_PIXEL = 15.0
BASE_PADDING = 12.0
BASE_TAIL_BUMP = 9.0
BASE_CORNER = 18.0

BUBBLE_SCALES = {"small": 0.8, "medium": 1.0, "large": 1.25}


class SpeechBubble(QWidget):
    def __init__(self, parent: QWidget, scale: float = 1.0):
        super().__init__(parent)
        self._text = ""
        self._tail_x = 0.5
        self._doc = QTextDocument()
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(1.0)
        self.setGraphicsEffect(self._effect)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._begin_fade_out)
        self._apply_scale(scale)
        self.hide()

    @property
    def scale(self) -> float:
        return self._scale

    def set_scale(self, scale: float):
        self._apply_scale(scale)
        if self.isVisible():
            self._adjust()
        self.update()

    def _apply_scale(self, scale: float):
        self._scale = max(0.5, min(2.0, float(scale)))
        self._max_width = int(BASE_MAX_WIDTH * self._scale)
        self._padding = max(6, int(BASE_PADDING * self._scale))
        self._tail_bump = max(5, int(BASE_TAIL_BUMP * self._scale))
        self._corner = max(10, int(BASE_CORNER * self._scale))
        self.setFont(
            ThemeManager.font(pixel_size=max(11, int(BASE_FONT_PIXEL * self._scale)))
        )

    def popup(self, text: str, seconds: float = 5.0):
        self._timer.stop()
        self._text = text
        self._adjust()
        self._effect.setOpacity(0.0)
        self.setVisible(True)
        self.raise_()
        AnimationHelper.fade_in_widget(self)
        self._timer.start(int(seconds * 1000))

    def pin(self, text: str):
        self._timer.stop()
        self._text = text
        self._adjust()
        self._effect.setOpacity(1.0)
        self.setVisible(True)
        self.raise_()

    def dismiss(self):
        self._timer.stop()
        if self.isVisible():
            if self._effect.opacity() > 0.99:
                AnimationHelper.fade_out_widget(self, self._on_fade_out_done)
            else:
                self._effect.setOpacity(0.0)
                self.setVisible(False)
                self._effect.setOpacity(1.0)

    def _begin_fade_out(self):
        if self.isVisible():
            AnimationHelper.fade_out_widget(self, self._on_fade_out_done)

    def _on_fade_out_done(self):
        self.setVisible(False)
        self._effect.setOpacity(1.0)

    def _build_document(self, text_width: float) -> QTextDocument:
        doc = QTextDocument()
        doc.setDefaultFont(self.font())
        doc.setDocumentMargin(0)
        safe = html.escape(self._text).replace("\n", "<br>")
        doc.setHtml(f'<p style="line-height:150%">{safe}</p>')
        doc.setTextWidth(text_width)
        return doc

    def _adjust(self):
        parent_w = self.parentWidget().width() if self.parentWidget() else 0
        max_total = min(
            self._max_width + self._padding * 2,
            (parent_w - 8) if parent_w > 0 else self._max_width + self._padding * 2,
        )
        measure = self._build_document(max_total - self._padding * 2)
        content_width = min(max(measure.idealWidth(), 30), max_total - self._padding * 2)
        width = max(content_width + self._padding * 2, 60)
        doc = self._build_document(width - self._padding * 2)
        self._doc = doc
        height = doc.size().height() + self._padding * 2 + self._tail_bump
        x = int(max(4, min((parent_w - width) / 2, parent_w - width - 4)))
        cat_center = parent_w / 2
        margin = int(18 * self._scale)
        self._tail_x = min(max(cat_center - x, margin), width - margin)
        self.setGeometry(x, 4, int(width), int(height + 1))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        tokens = ThemeManager.current()
        s = self._scale
        width, height = self.width(), self.height()
        body_h = height - self._tail_bump
        body = QPainterPath()
        body.addRoundedRect(
            QRectF(1.0, 1.0, width - 2.0, body_h - 2.0), self._corner, self._corner
        )
        tail = QPainterPath()
        tail.addEllipse(
            QRectF(
                self._tail_x - 10 * s, body_h - 9 * s, 20 * s, 18 * s
            )
        )
        painter.setPen(QPen(QColor(tokens.primary), 2))
        painter.setBrush(QColor(tokens.bg))
        painter.drawPath(body.united(tail))
        painter.setPen(QColor(tokens.text_dark))
        painter.save()
        painter.translate(self._padding, self._padding - 2)
        self._doc.drawContents(painter)
        painter.restore()
        paw = QColor(tokens.primary)
        paw.setAlpha(110)
        painter.setPen(Qt.NoPen)
        painter.setBrush(paw)
        painter.drawEllipse(QRectF(width - 32 * s, body_h - 17 * s, 12 * s, 9 * s))
        for offset in (30, 26, 22):
            painter.drawEllipse(
                QRectF(
                    width - offset * s, body_h - 22 * s, 4.5 * s, 4.5 * s
                )
            )

    def mousePressEvent(self, event):
        self.dismiss()
