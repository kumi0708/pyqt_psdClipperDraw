from typing import Callable, Optional

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QWidget

from json_loader import JsonLoader
from screen import Screen
from ui_element import UIElement


class _ClickOverlay(QWidget):
    """Transparent overlay that intercepts mouse clicks and forwards them."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.on_clicked: Optional[Callable[[QPoint], None]] = None

    def set_inspect_mode(self, inspect: bool) -> None:
        self.setCursor(
            Qt.CursorShape.CrossCursor if inspect else Qt.CursorShape.ArrowCursor
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self.on_clicked:
            self.on_clicked(event.pos())


class ScreenManager:
    ClickHandler = Callable[[], None]

    def __init__(
        self,
        screens_dir: str = "screens",
        parent: QWidget | None = None,
    ) -> None:
        self._screens_dir = screens_dir
        self._parent = parent
        self._cache: dict[str, Screen] = {}
        self._current_screen: str = ""

        self._id_handlers: dict[str, ScreenManager.ClickHandler] = {}
        self._group_handlers: dict[str, ScreenManager.ClickHandler] = {}

        self._click_overlay: Optional[_ClickOverlay] = None
        self._click_inspect = False
        self._click_callback: Optional[Callable[[str, str], None]] = None

    # ── Screen lifecycle ──────────────────────────────────────────────

    def load_screen(self, name: str) -> bool:
        if name in self._cache:
            return True

        print(f"Loading Screen: {name}")
        screen_dir = f"{self._screens_dir}/{name}"
        data = JsonLoader.load(f"{screen_dir}/screen.json")
        if not data.valid:
            print(f"Warning: Failed to load screen: {name}")
            return False

        screen = Screen(data, screen_dir)
        screen.widget().hide()
        self._cache[name] = screen
        return True

    def preload(self, names: list[str]) -> None:
        """スクリーンを事前にまとめてロードする。show_screen 時はキャッシュから即座に表示される。"""
        for name in names:
            self.load_screen(name)

    def show_screen(self, name: str) -> bool:
        if not self.load_screen(name):
            return False

        if self._current_screen and self._current_screen in self._cache:
            self._cache[self._current_screen].widget().hide()

        print(f"Show Screen: {name}")
        self._current_screen = name
        w = self._cache[name].widget()

        if self._parent and w.parent() is not self._parent:
            w.setParent(self._parent)
            w.move(0, 0)
        w.show()
        w.raise_()

        self._update_overlay()
        return True

    def unload_screen(self, name: str) -> bool:
        if name not in self._cache:
            return False

        if self._current_screen == name:
            self._cache[name].widget().hide()
            self._current_screen = ""

        screen = self._cache.pop(name)
        screen.widget().deleteLater()
        return True

    def current_screen(self) -> str:
        return self._current_screen

    # ── Per-element API ───────────────────────────────────────────────

    def find(self, id: str) -> UIElement | None:
        screen = self._current_screen_obj()
        return screen.find(id) if screen else None

    def set_visible(self, id: str, visible: bool) -> None:
        el = self.find(id)
        if el:
            el.set_visible(visible)

    def set_image(self, id: str, path: str) -> None:
        el = self.find(id)
        if el:
            el.set_image(path)

    def set_position(self, id: str, x: int, y: int) -> None:
        el = self.find(id)
        if el:
            el.set_position(x, y)

    def set_size(self, id: str, w: int, h: int) -> None:
        el = self.find(id)
        if el:
            el.set_size(w, h)

    def set_opacity(self, id: str, alpha: float) -> None:
        el = self.find(id)
        if el:
            el.set_opacity(alpha)

    def set_rotation(self, id: str, degree: float) -> None:
        el = self.find(id)
        if el:
            el.set_rotation(degree)

    def set_scale(self, id: str, sx: float, sy: float | None = None) -> None:
        el = self.find(id)
        if el:
            el.set_scale(sx, sy)

    def set_pivot(self, id: str, px: float, py: float) -> None:
        el = self.find(id)
        if el:
            el.set_pivot(px, py)

    # ── Per-group API ─────────────────────────────────────────────────

    def find_group(self, group: str) -> list[UIElement]:
        screen = self._current_screen_obj()
        return screen.find_group(group) if screen else []

    def set_group_visible(self, group: str, visible: bool) -> None:
        for el in self.find_group(group):
            el.set_group_visible(visible)

    def set_group_opacity(self, group: str, alpha: float) -> None:
        for el in self.find_group(group):
            el.set_opacity(alpha)

    def set_group_scale(self, group: str, sx: float, sy: float | None = None) -> None:
        for el in self.find_group(group):
            el.set_scale(sx, sy)

    def set_group_pivot(self, group: str, px: float, py: float) -> None:
        for el in self.find_group(group):
            el.set_pivot(px, py)

    # ── Introspection ─────────────────────────────────────────────────

    def elements(self) -> list[UIElement]:
        screen = self._current_screen_obj()
        return screen.elements() if screen else []

    # ── App click handlers ────────────────────────────────────────────

    def on_click(self, id: str, handler: ClickHandler) -> None:
        self._id_handlers[id] = handler
        self._update_overlay()

    def on_group_click(self, group: str, handler: ClickHandler) -> None:
        self._group_handlers[group] = handler
        self._update_overlay()

    def clear_click_handlers(self) -> None:
        self._id_handlers.clear()
        self._group_handlers.clear()
        self._update_overlay()

    # ── Click inspect (F5 debug) ──────────────────────────────────────

    def set_click_inspect_mode(
        self,
        active: bool,
        callback: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        self._click_inspect = active
        if callback:
            self._click_callback = callback

        if self._click_overlay:
            self._click_overlay.set_inspect_mode(active)

        self._update_overlay()
        print(
            "[Debug] Click Inspect: ON  (F5 to toggle)"
            if active
            else "[Debug] Click Inspect: OFF"
        )

    def is_click_inspect_mode(self) -> bool:
        return self._click_inspect

    # ── Private ───────────────────────────────────────────────────────

    def _current_screen_obj(self) -> Screen | None:
        if not self._current_screen:
            return None
        return self._cache.get(self._current_screen)

    def _handle_click(self, pos: QPoint) -> None:
        screen = self._current_screen_obj()
        if not screen:
            return

        el = screen.element_at(pos)

        if self._click_inspect:
            if el:
                print(f"Click: {el.group} / {el.id}")
                if self._click_callback:
                    self._click_callback(el.group, el.id)
            else:
                print(f"Click: (no element) at {pos.x()},{pos.y()}")
                if self._click_callback:
                    self._click_callback("", "")

        if not el:
            return

        if el.id in self._id_handlers:
            self._id_handlers[el.id]()
            return
        if el.group in self._group_handlers:
            self._group_handlers[el.group]()

    def _update_overlay(self) -> None:
        need_overlay = (
            self._click_inspect
            or bool(self._id_handlers)
            or bool(self._group_handlers)
        )

        screen = self._current_screen_obj()
        if not need_overlay or not screen:
            if self._click_overlay:
                self._click_overlay.hide()
            return

        if not self._click_overlay and self._parent:
            ov = _ClickOverlay(self._parent)
            ov.on_clicked = self._handle_click
            self._click_overlay = ov

        if not self._click_overlay:
            return

        self._click_overlay.set_inspect_mode(self._click_inspect)

        sw = screen.widget()
        self._click_overlay.setGeometry(sw.x(), sw.y(), sw.width(), sw.height())
        self._click_overlay.show()
        self._click_overlay.raise_()
