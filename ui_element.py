import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap, QTransform
from PyQt6.QtWidgets import QLabel, QWidget

_DEBUG = os.environ.get("PSD_CLIPPER_DEBUG", "0") == "1"


def set_debug_overlay(enabled: bool) -> None:
    global _DEBUG
    _DEBUG = enabled


def is_debug_overlay() -> bool:
    return _DEBUG


class ImageLabel(QLabel):
    """QLabel subclass that renders a pixmap with opacity and rotation around a pivot."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source_pixmap = QPixmap()
        self._rotation = 0.0
        self._opacity = 1.0
        # 正規化ピボット座標 (0.0〜1.0)。回転の基準点。
        self._pivot_x = 0.5
        self._pivot_y = 0.5

    def setSourcePixmap(self, pixmap: QPixmap) -> None:
        self._source_pixmap = pixmap
        self.update()

    def setRotationDegree(self, degree: float) -> None:
        self._rotation = degree
        self.update()

    def setOpacityValue(self, alpha: float) -> None:
        self._opacity = max(0.0, min(1.0, alpha))
        self.update()

    def setPivot(self, px: float, py: float) -> None:
        self._pivot_x = px
        self._pivot_y = py
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        if self._source_pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setOpacity(self._opacity)

        if abs(self._rotation) < 1e-6:
            painter.drawPixmap(0, 0, self.width(), self.height(), self._source_pixmap)
        else:
            px = self.width() * self._pivot_x
            py = self.height() * self._pivot_y
            t = QTransform()
            t.translate(px, py)
            t.rotate(self._rotation)
            t.translate(-px, -py)
            painter.setTransform(t)
            painter.drawPixmap(0, 0, self.width(), self.height(), self._source_pixmap)

        if _DEBUG:
            painter.resetTransform()
            painter.setOpacity(1.0)
            painter.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
            # ピボット点を青い十字で表示
            painter.setPen(QPen(QColor(0, 120, 255), 1))
            px = int(self.width() * self._pivot_x)
            py = int(self.height() * self._pivot_y)
            painter.drawLine(px - 6, py, px + 6, py)
            painter.drawLine(px, py - 6, px, py + 6)

        painter.end()


class UIElement:
    """Wraps an ImageLabel with layer metadata, visibility, and transform state."""

    def __init__(
        self,
        id: str,
        type: str,
        label: QLabel,
        group: str = "",
        base_x: int = 0,
        base_y: int = 0,
        base_w: int = 0,
        base_h: int = 0,
    ) -> None:
        self._id = id
        self._type = type
        self._group = group
        self._label = label
        self._own_visible = not label.isHidden() if label else True
        self._group_visible = True
        # JSON由来の元の座標・サイズ
        self._base_x = base_x
        self._base_y = base_y
        self._base_w = base_w
        self._base_h = base_h
        # 正規化ピボット (0.0〜1.0)。回転・拡縮の基準点。デフォルトは中心。
        self._pivot_x = 0.5
        self._pivot_y = 0.5

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> str:
        return self._type

    @property
    def group(self) -> str:
        return self._group

    @property
    def label(self) -> QLabel:
        return self._label

    @property
    def own_visible(self) -> bool:
        return self._own_visible

    @property
    def group_visible(self) -> bool:
        return self._group_visible

    def set_visible(self, visible: bool) -> None:
        self._own_visible = visible
        self._apply_visibility()

    def set_group_visible(self, visible: bool) -> None:
        self._group_visible = visible
        self._apply_visibility()

    def set_pivot(self, px: float, py: float) -> None:
        """回転・拡縮の基準点を正規化座標で設定する。(0,0)=左上 (0.5,0.5)=中心 (1,1)=右下"""
        self._pivot_x = px
        self._pivot_y = py
        if isinstance(self._label, ImageLabel):
            self._label.setPivot(px, py)

    def set_image(self, path: str) -> None:
        if not isinstance(self._label, ImageLabel):
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"Warning: Image Not Found: {path}")
        self._label.setSourcePixmap(pixmap)

    def set_position(self, x: int, y: int) -> None:
        if self._label:
            self._label.move(x, y)

    def set_size(self, w: int, h: int) -> None:
        if self._label:
            self._label.resize(w, h)

    def set_scale(self, sx: float, sy: float | None = None) -> None:
        """元サイズを基準にスケールする。ピボット点の位置は画面上で固定される。"""
        if sy is None:
            sy = sx
        if not self._label or self._base_w == 0 or self._base_h == 0:
            return
        new_w = int(self._base_w * sx)
        new_h = int(self._base_h * sy)
        # ピボット点（画面座標）= 元の位置 + 元サイズ × ピボット比率
        pivot_screen_x = self._base_x + self._base_w * self._pivot_x
        pivot_screen_y = self._base_y + self._base_h * self._pivot_y
        # ピボット点が変わらないように新しい左上座標を計算
        new_x = int(pivot_screen_x - new_w * self._pivot_x)
        new_y = int(pivot_screen_y - new_h * self._pivot_y)
        self._label.setGeometry(new_x, new_y, new_w, new_h)

    def set_opacity(self, alpha: float) -> None:
        if isinstance(self._label, ImageLabel):
            self._label.setOpacityValue(alpha)

    def set_rotation(self, degree: float) -> None:
        if isinstance(self._label, ImageLabel):
            self._label.setRotationDegree(degree)

    def _apply_visibility(self) -> None:
        if self._label:
            self._label.setVisible(self._own_visible and self._group_visible)
