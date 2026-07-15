from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPlainTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

import ui_element

_ROLE_ID = Qt.ItemDataRole.UserRole
_ROLE_GROUP = Qt.ItemDataRole.UserRole + 1
_DIM_COLOR = QColor(130, 130, 130)


def _apply_dimming(group_item: QTreeWidgetItem, dimmed: bool) -> None:
    for i in range(group_item.childCount()):
        child = group_item.child(i)
        if dimmed:
            child.setForeground(0, _DIM_COLOR)
        else:
            child.setData(0, Qt.ItemDataRole.ForegroundRole, None)


class DebugPanel(QWidget):
    def __init__(self, manager, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._manager = manager
        self._updating = False

        self.setWindowTitle("Debug Panel  [F4 to close]")
        self.resize(320, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        hint = QLabel("Check group or layer to toggle visibility", self)
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

        self._bounds_cb = QCheckBox("Show bounds  [red overlay]", self)
        self._bounds_cb.setChecked(ui_element.is_debug_overlay())
        self._bounds_cb.toggled.connect(self._on_bounds_toggled)
        layout.addWidget(self._bounds_cb)

        self._tree = QTreeWidget(self)
        self._tree.setHeaderLabel("Layer / Group")
        self._tree.setColumnCount(1)
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree, 3)

        self._log_label = QLabel("● Click Log  [F5 to inspect clicks]", self)
        self._log_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 4px;")
        layout.addWidget(self._log_label)

        self._log = QPlainTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(200)
        self._log.setStyleSheet("font-size: 11px; background: #1a1a1a; color: #ccc;")
        self._log.setFixedHeight(130)
        layout.addWidget(self._log, 1)

        self._tree.itemChanged.connect(self._on_item_changed)

    def _on_bounds_toggled(self, checked: bool) -> None:
        ui_element.set_debug_overlay(checked)
        for el in self._manager.elements():
            el.label.update()

    def set_click_inspect_active(self, active: bool) -> None:
        if active:
            self._log_label.setStyleSheet(
                "color: #ff4444; font-size: 11px; font-weight: bold; margin-top: 4px;"
            )
        else:
            self._log_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 4px;")

    def append_click_log(self, group: str, id: str) -> None:
        if not id:
            self._log.appendPlainText("(no element)")
        elif not group:
            self._log.appendPlainText(f"Layer: {id}")
        else:
            self._log.appendPlainText(f"Group: {group}  /  Layer: {id}")
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def refresh(self) -> None:
        self._updating = True
        self._tree.clear()

        group_items: dict[str, QTreeWidgetItem] = {}

        for el in self._manager.elements():
            group = el.group
            own_vis = el.own_visible
            group_vis = el.group_visible

            def make_layer_item(parent_item: QTreeWidgetItem | None) -> None:
                if parent_item:
                    item = QTreeWidgetItem(parent_item)
                else:
                    item = QTreeWidgetItem(self._tree)
                item.setText(0, el.id)
                item.setData(0, _ROLE_ID, el.id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    0,
                    Qt.CheckState.Checked if own_vis else Qt.CheckState.Unchecked,
                )
                item.setToolTip(0, el.id)
                if not group_vis:
                    item.setForeground(0, _DIM_COLOR)

            if not group:
                make_layer_item(None)
            else:
                if group not in group_items:
                    gi = QTreeWidgetItem(self._tree)
                    gi.setText(0, group)
                    gi.setData(0, _ROLE_GROUP, group)
                    gi.setFlags(gi.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    gi.setCheckState(
                        0,
                        Qt.CheckState.Checked if group_vis else Qt.CheckState.Unchecked,
                    )
                    gi.setExpanded(True)
                    group_items[group] = gi
                make_layer_item(group_items[group])

        self._updating = False

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating or column != 0:
            return
        self._updating = True

        checked = item.checkState(0) != Qt.CheckState.Unchecked
        group_val = item.data(0, _ROLE_GROUP)

        if group_val:
            self._manager.set_group_visible(group_val, checked)
            _apply_dimming(item, not checked)
        else:
            id_val = item.data(0, _ROLE_ID)
            self._manager.set_visible(id_val, checked)

        self._updating = False
