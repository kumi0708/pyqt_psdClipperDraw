import json
from pathlib import Path

from screen_data import CanvasData, LayerData, ScreenData


class JsonLoader:
    @staticmethod
    def load(json_path: str) -> ScreenData:
        data = ScreenData()
        path = Path(json_path)

        if not path.exists():
            print(f"Warning: screen.json not found: {json_path}")
            return data

        try:
            with open(path, encoding="utf-8") as f:
                root = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: JSON parse error: {e}")
            return data

        data.name = root.get("name", "")

        canvas = root.get("canvas", {})
        data.canvas = CanvasData(
            width=canvas.get("width", 0),
            height=canvas.get("height", 0),
        )

        for obj in root.get("layers", []):
            layer = LayerData(
                id=obj.get("id", ""),
                type=obj.get("type", ""),
                src=obj.get("src", ""),
                group=obj.get("group", ""),
                x=obj.get("x", 0),
                y=obj.get("y", 0),
                w=obj.get("w", 0),
                h=obj.get("h", 0),
                visible=obj.get("visible", True),
            )
            data.layers.append(layer)

        data.valid = True
        return data
