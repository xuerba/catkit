import re
from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont


@dataclass
class ThemeTokens:
    name: str
    bg: str
    primary: str
    primary_hover: str
    text_dark: str
    text_light: str
    border: str
    shadow: str

    status_todo: str
    status_doing: str
    status_done: str
    status_overdue: str

    card: str = "#FFFFFF"
    radius_panel: str = "18px"
    radius_input: str = "8px"
    radius_button: str = "10px"
    padding_s: str = "6px"
    padding_m: str = "12px"
    padding_l: str = "18px"


class Themes:
    WARM = ThemeTokens(
        name="warm",
        bg="#FFF9EF",
        primary="#F6B944",
        primary_hover="#E0A333",
        text_dark="#4A3728",
        text_light="#8C6D53",
        border="#F3E7D3",
        shadow="rgba(74, 55, 40, 0.08)",
        card="#FFFDF8",
        status_todo="#4A90D9",
        status_doing="#F5A623",
        status_done="#4CAF50",
        status_overdue="#E5484D",
    )

    TECH = ThemeTokens(
        name="tech",
        bg="#121826",
        primary="#00F2FE",
        primary_hover="#4FACFE",
        text_dark="#E0E6ED",
        text_light="#7C8BA1",
        border="#1F293D",
        shadow="rgba(0, 242, 254, 0.15)",
        card="#1A2233",
        status_todo="#38EF7D",
        status_doing="#FFB300",
        status_done="#00F2FE",
        status_overdue="#FF5252",
    )

    NORDIC = ThemeTokens(
        name="nordic",
        bg="#F8F9FA",
        primary="#4C6EF5",
        primary_hover="#3B5BD5",
        text_dark="#212529",
        text_light="#6C757D",
        border="#E9ECEF",
        shadow="rgba(0, 0, 0, 0.05)",
        card="#FFFFFF",
        status_todo="#4DABF7",
        status_doing="#FFD43B",
        status_done="#51CF66",
        status_overdue="#FF6B6B",
    )


class ThemeManager:
    current_theme: ThemeTokens = Themes.WARM

    @classmethod
    def current(cls) -> ThemeTokens:
        return cls.current_theme

    @classmethod
    def set_theme(cls, app, tokens: ThemeTokens):
        cls.current_theme = tokens
        app.setStyleSheet(cls.build_qss(tokens))

    @classmethod
    def font(
        cls,
        pixel_size=None,
        point_size=None,
        bold=False,
        family=None,
    ) -> QFont:
        font = QFont()
        defaults = ["Microsoft JhengHei", "Microsoft YaHei", "Noto Sans TC", "Segoe UI"]
        families = (
            ([family] + [f for f in defaults if f != family]) if family else defaults
        )
        font.setFamilies(families)
        if pixel_size is not None:
            font.setPixelSize(pixel_size)
        if point_size is not None:
            font.setPointSize(point_size)
        font.setBold(bold)
        return font

    @classmethod
    def status_colors(cls) -> dict:
        t = cls.current_theme
        return {
            "todo": t.status_todo,
            "doing": t.status_doing,
            "done": t.status_done,
            "overdue": t.status_overdue,
        }

    @staticmethod
    def tint(hex_color: str, alpha: float = 0.15) -> str:
        value = hex_color.lstrip("#")
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    @staticmethod
    def parse_shadow(rgba_text: str) -> QColor:
        match = re.search(
            r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", rgba_text
        )
        if not match:
            return QColor(0, 0, 0, 20)
        r, g, b, alpha = match.groups()
        return QColor(int(r), int(g), int(b), int(float(alpha) * 255))

    @staticmethod
    def build_qss(t: ThemeTokens) -> str:
        return f"""
QWidget {{
    color: {t.text_dark};
    font-size: 13px;
}}
QToolTip {{
    background-color: {t.card};
    color: {t.text_dark};
    border: 1px solid {t.border};
    padding: 4px 8px;
}}
#card {{
    background-color: {t.bg};
    border-radius: {t.radius_panel};
}}
QDialog {{
    background-color: {t.bg};
}}
QMessageBox {{
    background-color: {t.bg};
}}
QLabel#panelTitle {{
    color: {t.text_dark};
    font-size: 16px;
    font-weight: 700;
}}
QLabel#fieldLabel {{
    color: {t.text_light};
    font-size: 12px;
}}
QFrame#separator {{
    background-color: {t.border};
    border: none;
    max-height: 1px;
}}
QPushButton#primary {{
    background-color: {t.primary};
    color: #FFFFFF;
    border-radius: {t.radius_button};
    padding: 8px 18px;
    font-weight: bold;
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {t.primary_hover};
}}
QPushButton#primary:pressed {{
    padding-top: 9px;
    padding-bottom: 7px;
}}
QPushButton#ghost {{
    background-color: transparent;
    color: {t.text_light};
    border: 1px solid {t.border};
    border-radius: {t.radius_button};
    padding: 8px 18px;
    font-weight: bold;
}}
QPushButton#ghost:hover {{
    background-color: {t.border};
    color: {t.text_dark};
}}
QPushButton#minimize, QPushButton#windowClose {{
    background-color: transparent;
    border: none;
    color: {t.text_light};
    font-size: 16px;
    font-weight: 600;
    padding: 0 6px;
    border-radius: 8px;
}}
QPushButton#minimize:hover {{
    background-color: {ThemeManager.tint(t.text_light, 0.14)};
}}
QPushButton#windowClose:hover {{
    background-color: {ThemeManager.tint(t.status_overdue, 0.16)};
    color: {t.status_overdue};
}}
QLineEdit#searchInput {{
    min-height: 32px;
    max-height: 32px;
    padding: 0 12px;
    border: 1px solid {ThemeManager.tint(t.text_light, 0.3)};
    border-radius: 8px;
    background-color: {t.card};
}}
QLineEdit#searchInput:hover {{
    border: 1px solid {ThemeManager.tint(t.text_light, 0.5)};
    background-color: {t.card};
}}
QLineEdit#searchInput:focus {{
    border: 1px solid {t.primary};
    background-color: {t.card};
}}
QPushButton#standBtn {{
    background-color: transparent;
    color: {t.text_light};
    border: 1px solid {t.border};
    border-radius: 13px;
    padding: 0 10px;
    font-size: 12px;
}}
QPushButton#standBtn:hover {{
    background-color: {ThemeManager.tint(t.primary, 0.14)};
    color: {t.text_dark};
}}
QPushButton#standBtn:pressed {{
    background-color: {ThemeManager.tint(t.primary, 0.28)};
}}
QPushButton#iconBtn {{
    background-color: transparent;
    border: 1px solid {t.border};
    border-radius: 17px;
    padding: 0px;
}}
QPushButton#iconBtn:hover {{
    background-color: {ThemeManager.tint(t.primary, 0.14)};
}}
QPushButton#iconBtn:pressed {{
    background-color: {ThemeManager.tint(t.primary, 0.28)};
}}
QPushButton#iconBtn:disabled {{
    border: 1px solid {ThemeManager.tint(t.border, 0.45)};
}}
QPushButton#iconDanger {{
    background-color: transparent;
    border: 1px solid {t.border};
    border-radius: 17px;
    padding: 0px;
}}
QPushButton#iconDanger:hover {{
    border: 1px solid {t.status_overdue};
    background-color: {ThemeManager.tint(t.status_overdue, 0.14)};
}}
QPushButton#iconDanger:pressed {{
    background-color: {ThemeManager.tint(t.status_overdue, 0.28)};
}}
QPushButton#iconDanger:disabled {{
    border: 1px solid {ThemeManager.tint(t.border, 0.45)};
}}
QPushButton#rowIconBtn {{
    background-color: transparent;
    border: none;
    border-radius: 13px;
    padding: 0px;
}}
QPushButton#rowIconBtn:hover {{
    background-color: {ThemeManager.tint(t.primary, 0.14)};
}}
QPushButton#rowIconBtn:pressed {{
    background-color: {ThemeManager.tint(t.primary, 0.28)};
}}
QPushButton#rowIconDanger {{
    background-color: transparent;
    border: none;
    border-radius: 13px;
    padding: 0px;
}}
QPushButton#rowIconDanger:hover {{
    background-color: {ThemeManager.tint(t.status_overdue, 0.16)};
}}
QPushButton#rowIconDanger:pressed {{
    background-color: {ThemeManager.tint(t.status_overdue, 0.30)};
}}
QPushButton#addFab {{
    background-color: {t.primary};
    border: none;
    border-radius: 16px;
    padding: 0px;
}}
QPushButton#addFab:hover {{
    background-color: {t.primary_hover};
}}
QPushButton#addFab:pressed {{
    background-color: {t.primary};
}}
QPushButton#dateField {{
    background-color: {t.border};
    color: {t.text_dark};
    border-radius: {t.radius_input};
    padding: 6px 12px;
    border: 1px solid transparent;
    text-align: left;
    min-height: 22px;
}}
QPushButton#dateField:hover {{
    border: 1px solid {t.primary};
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateTimeEdit, QDateEdit, QTimeEdit {{
    background-color: {t.border};
    color: {t.text_dark};
    border-radius: {t.radius_input};
    padding: 6px 12px;
    border: 1px solid transparent;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QDateTimeEdit:focus, QDateEdit:focus, QTimeEdit:focus {{
    border: 1px solid {t.primary};
}}
QComboBox::drop-down, QDateEdit::drop-down, QDateTimeEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-top-right-radius: {t.radius_input};
    border-bottom-right-radius: {t.radius_input};
    background: transparent;
}}
QSpinBox::up-button, QSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button,
QDateEdit::up-button, QDateEdit::down-button {{
    background: transparent;
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {t.bg};
    color: {t.text_dark};
    border: 1px solid {t.border};
    border-radius: 6px;
    selection-background-color: {t.primary};
    selection-color: #FFFFFF;
}}
QComboBox#filterCombo {{
    min-height: 32px;
    max-height: 32px;
    padding: 0 10px;
    border: 1px solid {ThemeManager.tint(t.text_light, 0.3)};
    border-radius: 8px;
    background-color: {t.card};
}}
QComboBox#filterCombo:hover {{
    border: 1px solid {ThemeManager.tint(t.text_light, 0.5)};
}}
QComboBox#filterCombo:focus {{
    border: 1px solid {t.primary};
}}
QComboBox#filterCombo:disabled {{
    color: {t.text_light};
    border: 1px solid {ThemeManager.tint(t.border, 0.6)};
}}
QCheckBox {{
    color: {t.text_dark};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {t.text_light};
    background-color: {t.border};
}}
QCheckBox::indicator:checked {{
    background-color: {t.primary};
    border-color: {t.primary};
}}
QTableWidget {{
    background-color: transparent;
    gridline-color: transparent;
    alternate-background-color: transparent;
    selection-background-color: {ThemeManager.tint(t.primary, 0.14)};
    selection-color: {t.text_dark};
    border: none;
    outline: 0;
}}
QTableWidget::item {{
    padding: 4px 10px;
    border-bottom: 1px solid {ThemeManager.tint(t.border, 0.6)};
}}
QTableWidget::item:hover {{
    background-color: {ThemeManager.tint(t.primary, 0.06)};
}}
QTableWidget::item:selected {{
    background-color: {ThemeManager.tint(t.primary, 0.16)};
    color: {t.text_dark};
}}
QHeaderView::section {{
    background-color: {ThemeManager.tint(t.text_light, 0.07)};
    color: {t.text_light};
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid {ThemeManager.tint(t.border, 0.8)};
    padding: 8px 10px;
}}
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 1px 2px 0;
}}
QScrollBar::handle:vertical {{
    background: {ThemeManager.tint(t.text_light, 0.45)};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ThemeManager.tint(t.text_light, 0.65)};
}}
QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 6px;
    border-radius: 3px;
    margin: 0 2px 1px 2px;
}}
QScrollBar::handle:horizontal {{
    background: {ThemeManager.tint(t.text_light, 0.45)};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ThemeManager.tint(t.text_light, 0.65)};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
    height: 0;
    width: 0;
}}
QMenu {{
    background-color: {t.bg};
    color: {t.text_dark};
    border: 1px solid {t.border};
    border-radius: 10px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 26px 6px 14px;
    border-radius: 6px;
}}
QMenu::item:disabled {{
    color: {t.text_light};
}}
QMenu::item:selected {{
    background-color: {ThemeManager.tint(t.primary, 0.35)};
}}
QMenu::separator {{
    height: 1px;
    background-color: {t.border};
    margin: 4px 8px;
}}
"""

THEME_BY_NAME = {
    Themes.WARM.name: Themes.WARM,
    Themes.TECH.name: Themes.TECH,
    Themes.NORDIC.name: Themes.NORDIC,
}
