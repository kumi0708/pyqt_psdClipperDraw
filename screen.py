from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget

from screen_data import ScreenData
from ui_element import ImageLabel, UIElement


class Screen:
    def __init__(self, data: ScreenData, screen_dir: str) -> None:
        self._name = data.name
        self._widget: QWidget | None = None
        self._elements: list[UIElement] = []
        self._build(data, screen_dir)

    def widget(self) -> QWidget:
        return self._widget

    def name(self) -> str:
        return self._name

    def elements(self) -> list[UIElement]:
        return self._elements

    def find(self, id: str) -> UIElement | None:
        for el in self._elements:
            if el.id == id:
                return el
        return None

    def find_group(self, group: str) -> list[UIElement]:
        return [el for el in self._elements if el.group == group]

    def element_at(self, pos: QPoint) -> UIElement | None:
        # _elements[0] = Photoshop topmost layer → first hit wins
        for el in self._elements:
            if not el.label or not el.label.isVisible():
                continue
            if el.label.geometry().contains(pos):
                return el
        return None

    def _build(self, data: ScreenData, screen_dir: str) -> None:
        self._widget = QWidget()
        self._widget.setFixedSize(data.canvas.width, data.canvas.height)
        self._widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._widget.setStyleSheet("background-color: black;")

        # Photoshop order: index 0 = topmost.
        # Qt: last widget created renders on top.
        # Iterate in reverse so JSON[0] ends up on top.
        for i in range(len(data.layers) - 1, -1, -1):
            layer = data.layers[i]
            if layer.type == "image":
                print(f"Load Image: {layer.src}")
                img_label = ImageLabel(self._widget)
                img_label.setGeometry(layer.x, layer.y, layer.w, layer.h)

                pixmap = QPixmap(f"{screen_dir}/{layer.src}")
                if pixmap.isNull():
                    print(f"Warning: Image Not Found: {layer.src}")
                img_label.setSourcePixmap(pixmap)
                img_label.setVisible(layer.visible)

                self._elements.insert(
                    0, UIElement(
                        layer.id, layer.type, img_label, layer.group,
                        layer.x, layer.y, layer.w, layer.h,
                    )
                )
            else:
                print(f"Warning: Unknown type, skipping: {layer.type}")
