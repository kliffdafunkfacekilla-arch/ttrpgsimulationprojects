import sys
import os

# Add parent directory of python_fmg to sys.path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Removed absolute script path; scripts not needed for portable app

from PyQt6.QtWidgets import QApplication
from python_fmg.ui.lore_forge_window import LoreForgeMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoreForgeMainWindow()
    window.show()
    sys.exit(app.exec())