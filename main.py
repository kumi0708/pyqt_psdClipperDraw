import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QWidget

import ui_element
from debug_panel import DebugPanel
from screen_manager import ScreenManager

_DEFAULT_SCREENS = str(Path(__file__).parent / "screens")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("screens_dir", nargs="?", default=_DEFAULT_SCREENS)
    args, qt_args = parser.parse_known_args()

    app = QApplication([sys.argv[0]] + qt_args)

    window = QWidget()
    window.setWindowTitle("PSD Clipper Draw")

    manager = ScreenManager(args.screens_dir, window)

    # 事前ロード（省略可）: ここに列挙したスクリーンは起動時に全画像をロードしておく
    # manager.preload(["PARTS_METER_00_BASE", "home", "settings"])

    manager.show_screen("PARTS_METER_00_BASE")

    window.adjustSize()

    debug_panel = DebugPanel(manager)

    f4 = QShortcut(QKeySequence(Qt.Key.Key_F4), window)

    def toggle_debug() -> None:
        if debug_panel.isVisible():
            debug_panel.hide()
        else:
            debug_panel.refresh()
            debug_panel.show()
            debug_panel.raise_()

    f4.activated.connect(toggle_debug)

    f5 = QShortcut(QKeySequence(Qt.Key.Key_F5), window)

    def toggle_inspect() -> None:
        active = not manager.is_click_inspect_mode()

        def on_click(group: str, id: str) -> None:
            debug_panel.append_click_log(group, id)
            if not debug_panel.isVisible():
                debug_panel.refresh()
                debug_panel.show()
                debug_panel.raise_()

        manager.set_click_inspect_mode(active, on_click)
        debug_panel.set_click_inspect_active(active)
        if not debug_panel.isVisible():
            debug_panel.refresh()
            debug_panel.show()
            debug_panel.raise_()

    f5.activated.connect(toggle_inspect)

    f6 = QShortcut(QKeySequence(Qt.Key.Key_F6), window)

    def toggle_bounds() -> None:
        ui_element.set_debug_overlay(not ui_element.is_debug_overlay())
        for el in manager.elements():
            el.label.update()
        debug_panel._bounds_cb.setChecked(ui_element.is_debug_overlay())

    f6.activated.connect(toggle_bounds)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
