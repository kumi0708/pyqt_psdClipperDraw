# PSD Clipper Draw

PSD から書き出したレイヤー画像と JSON 定義をもとに、PyQt6 でスクリーン（画面）を構築・表示するツール。
本ドキュメントでは、画像の描画処理（回転・不透明度・ピボットなどのレンダリング詳細）を除いた、
アプリとしての機能をまとめる。

## 起動方法

```
python main.py [screens_dir]
```

- `screens_dir` を省略した場合は `screens/` ディレクトリを使用する。
- 起動時に `PARTS_METER_00_BASE` スクリーンを表示する（`main.py` 内で指定）。

## スクリーン管理 (ScreenManager)

`screen_manager.py` がスクリーンのライフサイクルを管理する。

- **load_screen(name)**: `screens_dir/<name>/screen.json` を読み込み、`Screen` を生成してキャッシュする。読み込み済みの場合は何もしない。
- **preload(names)**: 複数スクリーンをまとめて事前ロードする（起動時のもたつき防止用、`main.py` 内でコメントアウトされている）。
- **show_screen(name)**: 現在表示中のスクリーンを隠し、指定スクリーンを表示に切り替える。未ロードなら自動的にロードする。
- **unload_screen(name)**: キャッシュからスクリーンを破棄する。
- **current_screen()**: 現在表示中のスクリーン名を返す。

## JSON によるスクリーン定義

各スクリーンは `screens/<name>/screen.json` で定義する（`json_loader.py`, `screen_data.py`）。

```json
{
    "name": "home",
    "canvas": { "width": 800, "height": 600 },
    "layers": [
        {
            "id": "bg",
            "type": "image",
            "src": "bg.png",
            "group": "",
            "x": 0, "y": 0, "w": 800, "h": 600,
            "visible": true
        }
    ]
}
```

- `canvas`: スクリーン全体のサイズ。
- `layers`: レイヤー配列。**配列の先頭が Photoshop 上の最前面**に対応し、内部で順序を反転して Qt の描画順に変換する。
- JSON の解析に失敗、またはファイルが存在しない場合は `ScreenData.valid = False` となり、`ScreenManager` はロード失敗としてスキップする。

## 要素・グループ操作 API

`ScreenManager` 経由で、現在表示中スクリーン内の要素を ID / グループ単位で操作できる。

| 対象 | メソッド |
|---|---|
| ID単位 | `find`, `set_visible`, `set_image`, `set_position`, `set_size`, `set_opacity`, `set_rotation`, `set_scale`, `set_pivot` |
| グループ単位 | `find_group`, `set_group_visible`, `set_group_opacity`, `set_group_scale`, `set_group_pivot` |
| 一覧 | `elements()` — 現在スクリーンの全 `UIElement` を取得 |

表示状態は「自身の visible」と「所属グループの visible」の両方が真の場合のみ表示される（`UIElement._apply_visibility`）。

## クリックハンドリング

- `on_click(id, handler)` / `on_group_click(group, handler)`: 特定の ID・グループがクリックされたときのコールバックを登録する。
- `clear_click_handlers()`: 登録済みハンドラを全解除する。
- 内部では透明なオーバーレイウィジェット（`_ClickOverlay`）を現在のスクリーン上に重ね、クリック座標からヒットテスト（`Screen.element_at`）を行い、最前面レイヤーから順にヒット判定する。
- ハンドラが一つも登録されておらず、クリックインスペクトモードも OFF の場合はオーバーレイを非表示にし、通常のクリックを透過させる。

## デバッグ機能

`main.py` でグローバルなキーボードショートカットとして登録されている。

| キー | 機能 |
|---|---|
| **F4** | デバッグパネルの表示/非表示を切り替える |
| **F5** | クリックインスペクトモードの ON/OFF を切り替える |
| **F6** | バウンディングボックス（赤枠）とピボット点（青十字）のオーバーレイ表示を切り替える |

### デバッグパネル (`debug_panel.py`)

- レイヤー / グループをツリー表示し、チェックボックスで表示・非表示を切り替えられる（グループ配下のレイヤーはグループの表示状態に応じてグレーアウト表示）。
- "Show bounds" チェックボックスで F6 と同じバウンディングボックス表示を切り替え可能。
- クリックインスペクトモード中にクリックされた要素の `グループ / ID` をログとして表示する（`append_click_log`）。

### クリックインスペクトモード

`set_click_inspect_mode(active, callback)` で有効化すると、クリック時に要素を実行せず、クリックされた要素の情報をコールバック・コンソール双方に出力する（要素の当たり判定確認・ID 調査用）。

## ディレクトリ構成

```
main.py             起動処理、ショートカット登録
screen_manager.py    スクリーンのロード・切替・要素操作・クリック処理
screen.py            1スクリーン分のウィジェット構築・要素検索・ヒットテスト
json_loader.py       screen.json の読み込み・パース
screen_data.py       JSON に対応するデータクラス（ScreenData / CanvasData / LayerData）
ui_element.py        レイヤー要素のラッパーと画像描画（本ドキュメントの対象外）
debug_panel.py       デバッグ用パネル UI
screens/             スクリーンごとの screen.json と画像アセット
requirements.txt     依存パッケージ（PyQt6）
```

## 依存関係

`requirements.txt` を参照（PyQt6 / PyQt6-Qt6 / PyQt6_sip）。
