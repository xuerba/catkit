import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)

from app.ui.theme import ThemeManager

SIZE = 192
GRID = 64.0

EYE = QColor("#33251a")
PINK = QColor("#f28ca4")
HEART = QColor("#ff7fa1")
ZZZ = QColor(110, 110, 150, 190)

BODY = QColor("#F6B944")
DARK = QColor("#E09A2B")
CREAM = QColor("#fdeed2")
OUTLINE = QColor("#6b4423")
ALERT = QColor("#E5484D")


def _refresh_palette():
    global BODY, DARK, CREAM, OUTLINE, ALERT
    tokens = ThemeManager.current()
    BODY = QColor("#F6B944")
    DARK = QColor("#E09A2B")
    CREAM = QColor("#fdeed2")
    OUTLINE = QColor("#6b4423")
    ALERT = QColor(tokens.status_overdue)


def _u():
    return SIZE / GRID


def _defaults():
    return {
        "eye": "open",
        "tail": 20.0,
        "tilt": 0.0,
        "pose": "stand",
        "step": 0.0,
        "sway": 0.0,
        "drop": 0.0,
        "alert": False,
        "hearts": False,
        "zzz": 0,
    }


def _options(state: str) -> list[dict]:
    if state == "sit":
        return [
            {"eye": "open", "tail": 25},
            {"eye": "open", "tail": 5},
            {"eye": "closed", "tail": -15},
            {"eye": "open", "tail": -30},
        ]
    if state == "doze":
        return [
            {"eye": "closed", "tail": 12, "tilt": -2, "zzz": 1},
            {"eye": "closed", "tail": 4, "tilt": 0, "zzz": 2},
            {"eye": "closed", "tail": -6, "tilt": -2, "zzz": 3},
            {"eye": "closed", "tail": 2, "tilt": 0, "zzz": 2},
        ]
    if state == "scratch":
        return [
            {"pose": "scratch", "eye": "happy", "tail": -20, "tilt": 5},
            {"pose": "scratch", "eye": "happy", "tail": -10, "tilt": 0},
            {"pose": "scratch", "eye": "happy", "tail": -20, "tilt": -5},
            {"pose": "scratch", "eye": "happy", "tail": -10, "tilt": 0},
        ]
    if state == "cuddle":
        return [
            {"eye": "happy", "tail": 35, "tilt": 8, "hearts": True},
            {"eye": "happy", "tail": 20, "tilt": -8, "hearts": True},
            {"eye": "happy", "tail": 35, "tilt": 8},
            {"eye": "open", "tail": 20, "tilt": -4},
        ]
    if state == "roll":
        return [
            {"eye": "happy", "tail": 30, "tilt": 0},
            {"eye": "happy", "tail": 30, "tilt": 45},
            {"eye": "happy", "tail": 30, "tilt": 90},
            {"eye": "happy", "tail": 30, "tilt": 45},
            {"eye": "happy", "tail": 30, "tilt": 0},
            {"eye": "happy", "tail": 30, "tilt": -45},
        ]
    if state == "walk":
        return [
            {"pose": "walk", "eye": "open", "step": 2.5, "tail": 20},
            {"pose": "walk", "eye": "open", "step": 0.5, "tail": 10, "drop": 0.6},
            {"pose": "walk", "eye": "open", "step": -2.5, "tail": 0},
            {"pose": "walk", "eye": "open", "step": -0.5, "tail": 10, "drop": 0.6},
        ]
    if state == "alert":
        return [
            {"eye": "wide", "tail": -15, "alert": True},
            {"eye": "wide", "tail": 5, "alert": True, "drop": 0.5},
        ]
    if state == "lifted":
        return [
            {"pose": "lifted", "eye": "wide", "sway": -2.5, "tail": 35},
            {"pose": "lifted", "eye": "wide", "sway": 2.5, "tail": 45},
        ]
    if state == "sleep":
        return [
            {"pose": "lying", "eye": "closed", "tail": 8},
            {"pose": "lying", "eye": "closed", "tail": 2, "drop": 0.3},
        ]
    return [{"eye": "open"}]


def build_frames(state: str, size: int = SIZE) -> list[QPixmap]:
    _refresh_palette()
    frames = []
    for opt in _options(state):
        merged = _defaults()
        merged.update(opt)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        if size != SIZE:
            factor = size / SIZE
            painter.scale(factor, factor)
        _paint_cat(painter, merged)
        painter.end()
        frames.append(pixmap)
    return frames


def _paint_cat(p: QPainter, opt: dict) -> None:
    u = _u()
    cx, cy = 32 * u, 40 * u
    p.save()
    p.translate(cx, cy)
    p.rotate(opt["tilt"])
    p.translate(-cx, -cy - opt["drop"] * u)
    _draw_tail(p, opt["tail"])
    if opt["pose"] == "lying":
        body = QRectF(14 * u, 32 * u, 36 * u, 16 * u)
    else:
        body = QRectF(17 * u, 29 * u, 30 * u, 22 * u)
    p.setPen(_pen(2.2))
    p.setBrush(QBrush(BODY))
    p.drawEllipse(body)
    if opt["pose"] == "lying":
        belly = QRectF(22 * u, 36 * u, 20 * u, 10 * u)
    else:
        belly = QRectF(24 * u, 37 * u, 16 * u, 12 * u)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(CREAM))
    p.drawEllipse(belly)
    _draw_paws(p, opt)
    hy = 24 if opt["pose"] == "lying" else 21
    _draw_head(p, 32, hy, opt)
    p.restore()


def _pen(width: float, color=OUTLINE) -> QPen:
    return QPen(color, width * _u(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)


def _draw_tail(p: QPainter, angle: float) -> None:
    u = _u()
    a = math.radians(angle)
    start = QPointF(46.5 * u, 42 * u)
    ctrl = QPointF((46.5 + 6 * math.sin(a)) * u, (42 - 12 * math.cos(a)) * u)
    tip = QPointF((46.5 + 15 * math.sin(a)) * u, (42 - 9 * math.cos(a)) * u)
    path = QPainterPath(start)
    path.quadTo(ctrl, tip)
    p.setPen(_pen(4.0, DARK))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)


def _draw_paws(p: QPainter, opt: dict) -> None:
    u = _u()
    p.setPen(_pen(2.0))
    p.setBrush(QBrush(BODY))
    pose = opt["pose"]
    if pose == "lifted":
        positions = [(26, 53 + opt["sway"]), (38, 53 - opt["sway"])]
    elif pose == "scratch":
        positions = [(24, 50.5), (43, 37)]
    elif pose == "walk":
        step = opt["step"]
        positions = [(26 + step, 50.5), (38 - step, 50.5)]
    elif pose == "lying":
        positions = [(26, 46.5), (38, 46.5)]
    else:
        positions = [(26, 50.5), (38, 50.5)]
    for x, y in positions:
        p.drawEllipse(QPointF(x * u, y * u), 3.2 * u, 3.2 * u)


def _draw_head(p: QPainter, hx: float, hy: float, opt: dict) -> None:
    u = _u()
    hx, hy = hx * u, hy * u
    p.setBrush(QBrush(BODY))
    p.setPen(_pen(2.2))
    for sx in (-1, 1):
        b1 = QPointF(hx + sx * 3.0 * u, hy - 10.0 * u)
        b2 = QPointF(hx + sx * 9.0 * u, hy - 6.5 * u)
        tip_y = hy - 17.0 * u if opt["alert"] else hy - 15.0 * u
        tip_x = hx + sx * (7.8 if opt["alert"] else 7.0) * u
        tri = QPolygonF([b1, b2, QPointF(tip_x, tip_y)])
        p.drawPolygon(tri)
        centroid = QPointF(
            (b1.x() + b2.x() + tip_x) / 3.0, (b1.y() + b2.y() + tip_y) / 3.0
        )
        inner = QPolygonF(
            [
                QPointF(centroid.x() + (b1.x() - centroid.x()) * 0.5, centroid.y() + (b1.y() - centroid.y()) * 0.5),
                QPointF(centroid.x() + (b2.x() - centroid.x()) * 0.5, centroid.y() + (b2.y() - centroid.y()) * 0.5),
                QPointF(centroid.x() + (tip_x - centroid.x()) * 0.5, centroid.y() + (tip_y - centroid.y()) * 0.5),
            ]
        )
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(PINK))
        p.drawPolygon(inner)
        p.setBrush(QBrush(BODY))
        p.setPen(_pen(2.2))
    p.drawEllipse(QPointF(hx, hy), 11 * u, 10 * u)
    _draw_eyes(p, hx, hy, opt["eye"])
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(PINK))
    p.drawEllipse(QPointF(hx, hy + 2.5 * u), 1.15 * u, 0.95 * u)
    p.setPen(_pen(1.2))
    p.setBrush(Qt.NoBrush)
    mouth = QPainterPath(QPointF(hx, hy + 3.4 * u))
    mouth.quadTo(QPointF(hx - 2.0 * u, hy + 4.8 * u), QPointF(hx - 3.2 * u, hy + 3.8 * u))
    mouth.moveTo(QPointF(hx, hy + 3.4 * u))
    mouth.quadTo(QPointF(hx + 2.0 * u, hy + 4.8 * u), QPointF(hx + 3.2 * u, hy + 3.8 * u))
    p.drawPath(mouth)
    for sx in (-1, 1):
        p.drawLine(QPointF(hx + sx * 5.0 * u, hy + 2.0 * u), QPointF(hx + sx * 11.0 * u, hy + 1.0 * u))
        p.drawLine(QPointF(hx + sx * 5.0 * u, hy + 3.6 * u), QPointF(hx + sx * 11.0 * u, hy + 4.8 * u))
    if opt["alert"]:
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(ALERT))
        p.drawRoundedRect(QRectF(hx + 8.5 * u, hy - 19 * u, 2.8 * u, 7.5 * u), 1.4 * u, 1.4 * u)
        p.drawEllipse(QPointF(hx + 9.9 * u, hy - 9.4 * u), 1.1 * u, 1.1 * u)
    if opt["hearts"]:
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(HEART))
        _draw_heart(p, hx + 12 * u, hy - 11 * u, 2.6 * u)
        _draw_heart(p, hx + 17 * u, hy - 6 * u, 1.9 * u)
    if opt["zzz"] > 0:
        p.setPen(QPen(ZZZ, 1))
        for i in range(opt["zzz"]):
            size = 6 + i * 2
            font = QFont()
            font.setPixelSize(int(size * u * 0.55))
            p.setFont(font)
            p.drawText(QPointF((47 + i * 3.2) * u, (16 - i * 4.5) * u), "z")


def _draw_eyes(p: QPainter, hx: float, hy: float, mode: str) -> None:
    u = _u()
    p.setBrush(QBrush(EYE))
    if mode == "closed":
        p.setPen(_pen(1.6, EYE))
        p.setBrush(Qt.NoBrush)
        for sx in (-1, 1):
            ex = hx + sx * 4.5 * u
            ey = hy - 1.0 * u
            path = QPainterPath(QPointF(ex - 2.2 * u, ey - 0.5 * u))
            path.quadTo(QPointF(ex, ey + 2.2 * u), QPointF(ex + 2.2 * u, ey - 0.5 * u))
            p.drawPath(path)
        return
    if mode == "happy":
        p.setPen(_pen(1.6, EYE))
        p.setBrush(Qt.NoBrush)
        for sx in (-1, 1):
            ex = hx + sx * 4.5 * u
            ey = hy - 1.0 * u
            path = QPainterPath(QPointF(ex - 2.2 * u, ey + 1.0 * u))
            path.quadTo(QPointF(ex, ey - 2.4 * u), QPointF(ex + 2.2 * u, ey + 1.0 * u))
            p.drawPath(path)
        return
    p.setPen(Qt.NoPen)
    for sx in (-1, 1):
        ex = hx + sx * 4.5 * u
        ey = hy - 1.0 * u
        if mode == "wide":
            p.drawEllipse(QPointF(ex, ey), 2.5 * u, 3.0 * u)
            p.setBrush(QBrush(Qt.white))
            p.drawEllipse(QPointF(ex - 0.7 * u, ey - 0.9 * u), 0.9 * u, 0.9 * u)
            p.setBrush(QBrush(EYE))
        elif mode == "narrow":
            p.drawEllipse(QPointF(ex, ey), 2.3 * u, 0.9 * u)
        else:
            p.drawEllipse(QPointF(ex, ey), 1.9 * u, 2.4 * u)
            p.setBrush(QBrush(Qt.white))
            p.drawEllipse(QPointF(ex - 0.6 * u, ey - 0.8 * u), 0.7 * u, 0.7 * u)
            p.setBrush(QBrush(EYE))


def _draw_heart(p: QPainter, cx: float, cy: float, r: float) -> None:
    path = QPainterPath()
    path.moveTo(cx, cy + r * 1.6)
    path.cubicTo(cx - r * 2.0, cy, cx - r * 0.8, cy - r * 1.8, cx, cy - r * 0.4)
    path.cubicTo(cx + r * 0.8, cy - r * 1.8, cx + r * 2.0, cy, cx, cy + r * 1.6)
    p.drawPath(path)


def build_icon(kind: str, size: int, color: str) -> QIcon:
    ratio = 2
    s = size * ratio
    pixmap = QPixmap(s, s)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    m = s * 0.20
    pen = QPen(QColor(color))
    pen.setWidthF(max(2.0, s * 0.085))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if kind == "edit":
        painter.save()
        painter.translate(s / 2, s / 2)
        painter.rotate(-45)
        body_w = s * 0.20
        body_l = s * 0.54
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(
            QRectF(-body_l / 2, -body_w / 2, body_l, body_w),
            body_w / 2,
            body_w / 2,
        )
        tip = QPainterPath()
        tip.moveTo(-body_l / 2 - s * 0.13, 0)
        tip.lineTo(-body_l / 2 + s * 0.01, -body_w * 0.52)
        tip.lineTo(-body_l / 2 + s * 0.01, body_w * 0.52)
        tip.closeSubpath()
        painter.drawPath(tip)
        painter.restore()
    elif kind == "trash":
        lid_y = m + s * 0.06
        painter.drawLine(QPointF(m * 0.8, lid_y), QPointF(s - m * 0.8, lid_y))
        painter.drawLine(QPointF(s / 2, m * 0.9), QPointF(s / 2, lid_y))
        bx = m + s * 0.10
        body_top = lid_y + s * 0.06
        body = QRectF(bx, body_top, s - 2 * bx, s - m - body_top)
        painter.drawRoundedRect(body, s * 0.07, s * 0.07)
        inner_top = body_top + s * 0.10
        inner_bottom = s - m - s * 0.08
        for offset in (-s * 0.075, s * 0.075):
            painter.drawLine(
                QPointF(s / 2 + offset, inner_top),
                QPointF(s / 2 + offset, inner_bottom),
            )
    elif kind == "check":
        painter.drawRoundedRect(
            QRectF(m, m, s - 2 * m, s - 2 * m), s * 0.18, s * 0.18
        )
        painter.drawLine(QPointF(s * 0.33, s * 0.52), QPointF(s * 0.45, s * 0.64))
        painter.drawLine(QPointF(s * 0.45, s * 0.64), QPointF(s * 0.69, s * 0.36))
    elif kind == "cycle":
        r = (s - 2 * m) / 2 * 0.94
        rect = QRectF(s / 2 - r, s / 2 - r, 2 * r, 2 * r)
        painter.drawArc(rect, 90 * 16, -180 * 16)
        painter.drawArc(rect, 270 * 16, -180 * 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(s / 2 - 0.30 * r, s / 2 + r),
                    QPointF(s / 2 + 0.10 * r, s / 2 + r - 0.17 * r),
                    QPointF(s / 2 + 0.10 * r, s / 2 + r + 0.17 * r),
                ]
            )
        )
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(s / 2 + 0.30 * r, s / 2 - r),
                    QPointF(s / 2 - 0.10 * r, s / 2 - r - 0.17 * r),
                    QPointF(s / 2 - 0.10 * r, s / 2 - r + 0.17 * r),
                ]
            )
        )
    elif kind == "plus":
        thick = QPen(QColor(color))
        thick.setWidthF(max(2.5, s * 0.13))
        thick.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(thick)
        pad = m + s * 0.06
        painter.drawLine(QPointF(s / 2, pad), QPointF(s / 2, s - pad))
        painter.drawLine(QPointF(pad, s / 2), QPointF(s - pad, s / 2))
    painter.end()
    pixmap.setDevicePixelRatio(ratio)
    return QIcon(pixmap)
