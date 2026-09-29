import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

from app.ui import sprite

here = os.path.dirname(os.path.abspath(__file__))
pixmap = sprite.build_frames("sit", 512)[0]
pixmap.save(os.path.join(here, "catkit.png"))

from PIL import Image

image = Image.open(os.path.join(here, "catkit.png"))
image.save(
    os.path.join(here, "catkit.ico"),
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print("icon written:", os.path.join(here, "catkit.ico"))
