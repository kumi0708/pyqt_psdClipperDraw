from dataclasses import dataclass, field
from typing import List


@dataclass
class LayerData:
    id: str = ""
    type: str = ""
    src: str = ""
    group: str = ""
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    visible: bool = True


@dataclass
class CanvasData:
    width: int = 0
    height: int = 0


@dataclass
class ScreenData:
    name: str = ""
    canvas: CanvasData = field(default_factory=CanvasData)
    layers: List[LayerData] = field(default_factory=list)
    valid: bool = False
