# Catkit 桌面貓咪任務管理工具

一隻住在桌面上的小貓，同時是個人任務管理工具。小貓以像素風精靈動畫常駐桌面，任務提醒用「貓說話」的方式呈現，並內建個人任務統計、站立提醒與多主題介面。

## 功能特性

### 桌面小貓
- 懸浮於桌面（透明、置頂、不佔工作列），支援拖曳移動、單擊撫摸、雙擊喚出任務面板、右鍵選單
- 行為狀態機：坐著／打盹／撓癢／撒嬌／翻滾／散步／警覺，每 15–40 秒隨機切換
- 擬人化聯動：未完成任務越多，貓越少偷懶；逾期任務存在時維持警覺臉並定期催促
- 小貓大小（特小 0.5／小 0.75／中 1.0／大 1.25 倍）與透明度（30–100%）可調，設定持久化

### 任務面板
- 任務欄位：標題／分類（工作、生活、學習、健康、其它）／DRI／開始時間／結束時間／優先序／狀態
- 狀態三態：待開始、進行中、已完成；逾期任務自動標示
- 頂部四色統計標籤，點擊即可快速篩選（與篩選下拉雙向同步）
- 關鍵字搜尋（標題／分類／DRI）
- 時間錄入採日曆彈出選擇器（QCalendarWidget＋小時／分鐘滑桿），結束時間可留空（不提醒、不計逾期）
- 面板可拖曳、邊緣拖曳縮放（預設 700×440，最小 430×320）、最大化／還原、點擊面板外部自動收合
- 統計 Chip 具 3D 陰影與 Hover／作用中樣式；表格採斑馬紋列底色、淡分隔線，選取列以淡主色底標示
- 標題欄自動取得最寬寬度，其餘欄位固定寬並以省略號顯示；每列右側提供「編輯／刪除」行內圖示鈕（26px，刪除採危險色樣式）
- 新增任務鈕（32px 圓形）位於搜尋列右側；標題列右側另有「站立提醒」與「關於」膠囊按鈕（皆含 3D 陰影），「關於」顯示版本與開發人員

### 任務提醒（貓說話）
- 三段式提醒：提前提醒（預設 10 分鐘前）→ 準點 → 逾期催促（每 10 分鐘，語氣漸強）
- 開始時間與結束時間皆可觸發提醒，提醒方式（提前時長）可設
- 賴床（Snooze）：延後 5／10／30 分鐘
- 完成任務時貓翻滾慶祝＋喵聲；全部完成時撒嬌慶祝
- 提醒／撫摸播放程式合成的喵聲（44100 Hz wav，可靜音）

### 站立提醒
- 依間隔（30／45／60／90 分鐘）提醒起身活動，貓演出伸懶腰動作
- 以 `GetLastInputInfo` 監控使用者活動：連續工作累計、閒置逾 5 分鐘自動歸零

### 隱藏模式
- 隱藏後桌面完全不顯示小貓，程式常駐系統托盤（托盤選單可喚回、離開、切換設定）
- 隱藏期間所有提醒改以托盤氣球通知呈現；動畫與行為計時器暫停以節省資源
- 隱藏狀態持久化，重啟後保持隱藏

### 設置
- 三套主題：溫馨暖色（WARM）／賽博科技（TECH）／極簡北歐（NORDIC），小貓與氣泡配色連動
- 字體族、字號（9–16 pt）、氣泡大小（小／中／大）、靜音、預設提醒方式、小貓大小與透明度、站立提醒
- 所有設定即時套用並持久化（QSettings）

## 環境需求

- Windows 10 / 11
- Python 3.12
- PySide6（開發環境為 6.11.2，見 `requirements.txt`）

## 快速開始

```powershell
pip install -r requirements.txt
python main.py
```

首次啟動小貓出現在主螢幕右下角；雙擊小貓即可開啟任務面板。

## 測試

```powershell
python scripts\smoke.py
```

煙霧測試以 offscreen 平台執行（建立暫存資料庫、驗證任務 CRUD／提醒／主題切換／隱藏模式／面板操作等），結尾輸出 `SMOKE OK`。`scripts\preview_sheet.png` 為小貓精靈幀預覽圖。

## 打包（Windows exe）

```powershell
pip install pyinstaller pillow
python packaging\make_icon.py          # 以小貓 sprite 生成 packaging\catkit.ico
python -m PyInstaller --noconfirm --clean packaging\catkit.spec
```

- 產物：`dist\Catkit\Catkit.exe`（onedir，含 `_internal` 全部執行環境，含 QtMultimedia FFmpeg DLL）
- 安裝包：安裝 [Inno Setup 6](https://jrsoftware.org/isinfo.php) 後執行
  `ISCC.exe packaging\catkit.iss`，產出 `dist\installer\Catkit-Setup-4.5.0.exe`
- 安裝包功能：預設安裝至 Program Files、開始選單捷徑、可選桌面捷徑（預設不勾）、可選開機自動啟動（預設勾選，寫入 HKCU Run）、解除安裝器（**保留** `%APPDATA%\catkit` 使用者資料）
- 未簽署的 exe 首次執行會出現 SmartScreen 提示，選「更多資訊 → 仍要執行」即可

## 資料與設定儲存

| 項目 | 位置 |
|---|---|
| 任務資料庫 | `%APPDATA%\catkit\tasks.db`（SQLite，舊版 schema 自動遷移） |
| 喵聲音效檔 | `%APPDATA%\catkit\meow.wav`（啟動時自動合成／重生成） |
| 應用設定 | QSettings（登錄檔 `HKEY_CURRENT_USER\Software\catkit\catkit`） |

## 使用提示

- 隱藏模式依賴系統托盤：Windows 可能預設將托盤圖示收進「^」隱藏圖示區，可於「設定 → 個人化 → 工作列 → 其他系統匣圖示」將 Catkit 設為常駐顯示
- 托盤氣球通知需允許 Windows 通知（通知與專注助理設定）
- 若音效裝置不支援取樣率，程式會自動以 44100 Hz 重新生成音效檔；播放器進入錯誤狀態時會自動停用音效

## 專案結構

```
catkit/
├── main.py                  # 程式進入點：裝配服務、UI、托盤與設定套用
├── requirements.txt
├── app/
│   ├── db.py                # SQLite 初始化與 schema 遷移
│   ├── settings.py          # AppSettings（QSettings 封裝）
│   ├── sound.py             # 喵聲合成與播放（QSoundEffect）
│   ├── model/
│   │   ├── task.py          # Task 資料模型與常數
│   │   └── repository.py    # 任務資料存取
│   ├── service/
│   │   ├── task_service.py  # 任務業務邏輯與統計
│   │   ├── reminder_service.py  # 提醒輪詢與三段式階段判定
│   │   └── stand_service.py # 站立提醒與閒置偵測
│   └── ui/
│       ├── pet_widget.py    # 桌面小貓視窗（互動、隱藏模式、氣泡路由）
│       ├── animator.py      # 幀動畫計時器
│       ├── sprite.py        # 程式繪製小貓幀與 UI 圖示
│       ├── speech_bubble.py # 對話氣泡
│       ├── task_panel.py    # 任務清單面板與任務對話框
│       ├── settings_dialog.py
│       ├── animations.py    # 彈出／收合／淡入淡出／Hover 浮起動效
│       ├── theme.py         # 主題 Token 與全域 QSS
│       └── tray.py          # 系統托盤
├── scripts/
│   ├── smoke.py             # 離屏煙霧測試
│   └── preview_sheet.png    # 精靈幀預覽圖
└── docs/
    ├── DESIGN.md            # 設計文檔（含完整變更記錄）
    ├── UI_SPEC.md           # UI 實作規格書
    └── 打包步驟.md          # PyInstaller + Inno Setup 打包步驟與指令
```

## 相關文檔

- `docs/DESIGN.md`：設計定稿與逐版變更記錄（現行 v4.5）
- `docs/UI_SPEC.md`：UI 重構實作規格書
- `docs/打包步驟.md`：PyInstaller + Inno Setup 打包步驟與指令
