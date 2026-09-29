已根據優化建議，將主題 Token 化系統、賽博科技風與極簡北歐風主題、原生控制項美化、按鈕圓角一致性以及列狀態顯示優化等內容整合進 `UI_SPEC.md`。

修改後的完整 `UI_SPEC.md` 如下：

---

# Catkit UI 重構實作規格書 (UI_SPEC.md)

> **給 AI Agent 的指令**：
> 請嚴格按照本文件的規格，使用 PySide6 重構 `app/ui/` 目錄下的 UI 元件。
> **禁止引入任何第三方 UI 庫（如 PyQt-Fluent-Widgets）**，必須使用原生 PySide6 + QSS + QPainter 實作。
> 請遵循「先建立主題系統，再重構元件」的順序。
> 
> 

---

## 1. 全域多主題系統 (Multi-Theme System)

### 1.1 建立 `app/ui/theme.py`

請建立此文件，透過 `ThemeTokens` 類別集中管理所有設計 Token。所有 UI 元件必須動態引用當前主題 Token，禁止硬編碼顏色。

```python
# app/ui/theme.py
from dataclasses import dataclass

@dataclass
class ThemeTokens:
    name: str
    bg: str             # 面板背景色
    primary: str        # 主色調 (主要按鈕、焦點框)
    primary_hover: str  # 主要按鈕 Hover 狀態
    text_dark: str      # 深色文字 (標題、主要內文)
    text_light: str     # 淺色/次要文字 (標籤、表頭)
    border: str         # 輸入框背景、交替行背景、分隔線
    shadow: str         # 柔和陰影 (RGBA)

    # --- 狀態色 (Status Colors) ---
    status_todo: str    # 待開始
    status_doing: str   # 進行中
    status_done: str    # 已完成
    status_overdue: str # 已延期

    # --- 圓角與間距 (Radii & Spacing) ---
    radius_panel: str = "18px"
    radius_input: str = "8px"
    radius_button: str = "18px"
    padding_s: str = "6px"
    padding_m: str = "12px"
    padding_l: str = "18px"


class Themes:
    # 1. 溫馨暖色調 (預設貓橘奶油風格)
    WARM = ThemeTokens(
        name="warm",
        bg="#FFF9EF",
        primary="#F6B944",
        primary_hover="#E0A333",
        text_dark="#4A3728",
        text_light="#8C6D53",
        border="#F3E7D3",
        shadow="rgba(74, 55, 40, 0.08)",
        status_todo="#4A90D9",
        status_doing="#F5A623",
        status_done="#4CAF50",
        status_overdue="#E5484D"
    )

    # 2. 賽博/未來科技調 (暗黑霓虹風格)
    TECH = ThemeTokens(
        name="tech",
        bg="#121826",
        primary="#00F2FE",
        primary_hover="#4FACFE",
        text_dark="#E0E6ED",
        text_light="#7C8BA1",
        border="#1F293D",
        shadow="rgba(0, 242, 254, 0.15)",
        status_todo="#38EF7D",
        status_doing="#FFB300",
        status_done="#00F2FE",
        status_overdue="#FF5252"
    )

    # 3. 極簡北歐調 (清爽冷色風格)
    NORDIC = ThemeTokens(
        name="nordic",
        bg="#F8F9FA",
        primary="#4C6EF5",
        primary_hover="#3B5BD5",
        text_dark="#212529",
        text_light="#6C757D",
        border="#E9ECEF",
        shadow="rgba(0, 0, 0, 0.05)",
        status_todo="#4DABF7",
        status_doing="#FFD43B",
        status_done="#51CF66",
        status_overdue="#FF6B6B"
    )


class ThemeManager:
    current_theme: ThemeTokens = Themes.WARM

    @classmethod
    def set_theme(cls, app, theme_tokens: ThemeTokens):
        cls.current_theme = theme_tokens
        app.setStyleSheet(cls.build_qss(theme_tokens))

    @staticmethod
    def build_qss(t: ThemeTokens) -> str:
        return f"""
        QWidget {{
            background-color: {t.bg};
            color: {t.text_dark};
            font-family: "Noto Sans TC", "Microsoft YaHei", sans-serif;
        }}

        /* 膠囊型按鈕規範 */
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

        /* 輸入框、下拉選單與時間選擇器美化 (去原生化) */
        QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QDateEdit, QTimeEdit {{
            background-color: {t.border};
            color: {t.text_dark};
            border-radius: {t.radius_input};
            padding: 6px 12px;
            border: 1px solid transparent;
        }}
        QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QDateEdit:focus, QTimeEdit:focus {{
            border: 1px solid {t.primary};
        }}

        /* 自訂下拉箭頭與微調按鈕 */
        QComboBox::drop-down, QDateEdit::drop-down, QDateTimeEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 0px;
            border-top-right-radius: {t.radius_input};
            border-bottom-right-radius: {t.radius_input};
        }}
        QSpinBox::up-button, QSpinBox::down-button, QTimeEdit::up-button, QTimeEdit::down-button {{
            background: transparent;
            border: none;
        }}

        /* CheckBox 樣式美化 */
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

        /* 表格美化 */
        QTableWidget {{
            background-color: transparent;
            gridline-color: transparent;
            alternate-background-color: {t.border};
            selection-background-color: {t.primary};
            selection-color: #FFFFFF;
            border: none;
        }}
        QHeaderView::section {{
            background-color: transparent;
            color: {t.text_light};
            font-weight: bold;
            border: none;
            padding: 8px 6px;
        }}

        /* 捲軸美化 */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {t.primary};
            border-radius: 3px;
        }}
        """

```

---

## 2. 任務面板重構規格 (`app/ui/task_panel.py`)

### 2.1 佈局與容器

* **主容器**：`QFrame`，套用 `QGraphicsDropShadowEffect` (模糊半徑 15，偏移 0, 5，顏色取自 `ThemeTokens.shadow`)。


* **背景**：套用 QSS `background-color: bg; border-radius: 18px;`。


* **移除所有背景浮水印圖片**。


* （v3.2）標題列右側三顆視窗控制鈕：最小化「─」、最大化「□」（還原「❐」）、關閉「✕」，樣式沿用 `#minimize`；最大化時停用拖曳與邊緣縮放。視窗維持邊緣 8px 拖曳縮放。



### 2.2 頂部統計列

* 使用 `QHBoxLayout`。


* 統計標籤使用彩色圓角小卡片形式：`待開始 (1)`、`進行中 (0)` 等。背景為同色系低透明度（如 `rgba(..., 0.15)`）。

* （v3.0 更新）主題切換入口與「今日番茄」小計已移除；主題改由設置對話框統一管理。



### 2.3 搜尋與篩選列

* 搜尋框 (`QLineEdit`) 加上 🔍 圖標。


* 篩選下拉框 (`QComboBox`) 採用動態 `ThemeTokens.border` 背景與焦點高亮邊框。



### 2.4 任務列表 (QTableWidget)

* **隱藏格線與表頭背景**。


* **設置預設行高**：設置 `verticalHeader()->setDefaultSectionSize(40)`，保持列與列間的呼吸感。
* **文字與狀態警示邏輯優化**：
* **非逾期任務**：標題與內容文字統一保持 `text_dark`，避免全列變紅造成視覺繁雜。
* **逾期任務**：僅「結束時間」欄位與「狀態欄」醒目顯示為 `status_overdue` 紅色。




* **狀態欄**：顯示為「彩色圓點 + 文字」（🔵 待開始 / 🟠 進行中 / 🟢 已完成 / 🔴 已延期）。


* **已完成任務**：標題加上刪除線 (`QFont.setStrikeOut(True)`)，文字變為 `text_light` 灰調。



### 2.5 底部操作列

* 左側：40px 圓形 primary FAB 按鈕（`.setObjectName("addFab")`），白色「＋」QPainter 圖示（`sprite.build_icon("plus", …)`），tooltip「新增任務」。


* 右側：「編輯」、「切換狀態」為 34px 正圓幽靈圖示鈕（`.setObjectName("iconBtn")`，鉛筆／循環箭頭圖示）；間隔 12px 後為「刪除」34px 危險樣式圓形圖示鈕（`.setObjectName("iconDanger")`，垃圾桶圖示，hover 轉紅）。未選取任務列時三顆按鈕自動 disabled（`itemSelectionChanged` → `_sync_action_buttons`）。



---

## 3. 新增/編輯對話框重構規格 (`app/ui/task_panel.py` 中的 Dialog)

### 3.1 佈局重構

* 採用垂直佈局 (`QVBoxLayout`)，標籤一律置於輸入框**上方**，文字使用 `text_light` (12px)。


* **對話框結構**：


* **Group 1 (主要資訊)**：標題 -> 輸入框；說明 -> 文字框。


* **分隔線**：淺色 `border` 的 QFrame。


* **Group 2 (屬性資訊)**：`QGridLayout`，包含分類、DRI、優先序。（v3.1 更新：改為並排一行，見下）


* **分隔線**。


* **Group 2 (屬性列)**：分類、DRI、優先序三者並排佔用一行（各自 label 在上、控制項在下）。
* **Group 3 (時間與提醒)**：開始時間（QDateEdit + QTimeEdit，直接錄入，預設現在）、結束時間（QDateEdit + QTimeEdit，直接錄入，預設明天＋1 小時）、提醒方式（同時套用於開始與結束提醒）。（v3.7：已移除啟用開關）





### 3.2 控制項細節美化

* 徹底摒棄 Windows 原生控制項樣式（如灰邊與原生箭頭）。


* 底部按鈕靠右對齊：


* 「取消」：幽靈膠囊按鈕 (`#ghost`)。


* 「確定」：主要膠囊按鈕 (`#primary`)。





---

## 4. 語音氣泡與小貓規格 (`app/ui/speech_bubble.py`)

### 4.1 氣泡 (SpeechBubble)

* 使用 `QPainter` 自繪。


* **形狀**：圓角矩形 (圓角 18px) + 胖短圓尾。


* **顏色**：背景 `bg`，邊框 `primary` 2px。


* **文字**：`text_dark`，行距放寬 (1.5倍)。


* **裝飾**：底部繪製爪印印章。



---

## 5. 動效實作規格 (`app/ui/animations.py`)

提供 `AnimationHelper` 靜態方法：

* **面板彈出動效**：`windowOpacity` (0->1) 與 `pos` ((x, y+8)->(x, y)) 並行 200ms 淡入上浮。


* **氣泡淡入淡出**：200ms `windowOpacity` 漸變。


* **按鈕 Hover 微縮與浮起**：透過 QGraphicsDropShadowEffect 動態改變陰影模糊度。



---

## 6. Step-by-Step 執行計劃

1. **Step 1: 建立多主題系統**

* 寫入 `ThemeTokens` 與 `Themes` 類別。


* 實作 `ThemeManager` 與 `build_qss()`。


* 在 `main.py` 初始化時呼叫 `ThemeManager.set_theme(app, Themes.WARM)`。




2. **Step 2: 重構任務面板佈局與膠囊按鈕**

* 修改 `task_panel.py`，移除背景圖與硬編碼樣式。


* 為所有按鈕設置對應的 `setObjectName("primary")` 或 `setObjectName("ghost")`。


* （v3.0 更新）主題切換改由設置對話框管理，面板僅被動套用主題。


3. **Step 3: 重構表格與欄位提醒邏輯**

* 設定列高與隱藏格線。


* 實作「彩色圓點 + 文字」狀態欄。


* 修復逾期邏輯：僅高亮結束時間與狀態。




4. **Step 4: 對話框美化與去原生化**

* 改為垂直佈局分組。


* 套用全域 QSS 消除 QDateEdit/QCheckBox 的原生 Windows 灰框。




5. **Step 5: 實作氣泡繪製與動效**

* 完成 `speech_bubble.py` 的 QPainter 繪製與動畫整合。