import base64
import ctypes
import json
import os
import re
import sys
from pathlib import Path
import webview


def find_html() -> str:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "dollmaker.html")
    candidates.append(Path(sys.executable).parent / "dollmaker.html")
    candidates.append(Path(__file__).resolve().parent / "dollmaker.html")

    for path in candidates:
        if path.is_file():
            return str(path)

    searched = "\n".join(str(p) for p in candidates)
    ctypes.windll.user32.MessageBoxW(
        0,
        f"Could not find dollmaker.html.\n\nSearched:\n{searched}",
        "Dollmaker - File Not Found",
        0x10,
    )
    sys.exit(1)


DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "MakeYourOwnDollmaker"
DATA_DIR.mkdir(parents=True, exist_ok=True)
WARDROBE_FILE = DATA_DIR / "wardrobe.json"

WARDROBES_DIR = DATA_DIR / "wardrobes"
WARDROBES_DIR.mkdir(parents=True, exist_ok=True)


def _safe_wardrobe_path(name: str) -> Path:
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name.strip())
    clean = clean.strip(". ") or "wardrobe"
    return WARDROBES_DIR / f"{clean}.json"


class Api:
    def __init__(self):
        self._window = None

    def load_wardrobe(self):
        if not WARDROBE_FILE.exists():
            return []
        try:
            return json.loads(WARDROBE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save_wardrobe(self, items):
        tmp = WARDROBE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(items), encoding="utf-8")
        os.replace(tmp, WARDROBE_FILE)
        return True

    def list_saved_wardrobes(self):
        out = []
        for path in sorted(WARDROBES_DIR.glob("*.json"), key=lambda p: p.name.lower()):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    name = data.get("name") or path.stem
                    items = data.get("items") or []
                elif isinstance(data, list):
                    name = path.stem
                    items = data
                else:
                    continue
                out.append({"name": name, "count": len(items)})
            except Exception:
                continue
        return out

    def save_named_wardrobe(self, name, items):
        target = _safe_wardrobe_path(name)
        tmp = target.with_suffix(".tmp")
        payload = {"version": 1, "name": name.strip() or target.stem, "items": items}
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, target)
        return self.list_saved_wardrobes()

    def load_named_wardrobe(self, name):
        target = _safe_wardrobe_path(name)
        if not target.exists():
            for path in WARDROBES_DIR.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and data.get("name") == name:
                        target = path
                        break
                except Exception:
                    continue
        if not target.exists():
            return []
        data = json.loads(target.read_text(encoding="utf-8"))
        return data.get("items", []) if isinstance(data, dict) else data

    def delete_named_wardrobe(self, name):
        target = _safe_wardrobe_path(name)
        if target.exists():
            target.unlink()
        else:
            for path in WARDROBES_DIR.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and data.get("name") == name:
                        path.unlink()
                        break
                except Exception:
                    continue
        return self.list_saved_wardrobes()

    def save_png(self, data_url, default_name="my-doll.png"):
        dialog_enum = getattr(webview, "FileDialog", None)
        mode = dialog_enum.SAVE if dialog_enum else webview.SAVE_DIALOG

        result = self._window.create_file_dialog(
            mode,
            save_filename=default_name,
            file_types=("PNG Image (*.png)",),
        )
        if not result:
            return False

        out_path = result[0] if isinstance(result, (list, tuple)) else result
        header, b64 = data_url.split(",", 1)
        Path(out_path).write_bytes(base64.b64decode(b64))
        return True

    def save_json(self, json_text, default_name="my-wardrobe.json"):
        dialog_enum = getattr(webview, "FileDialog", None)
        mode = dialog_enum.SAVE if dialog_enum else webview.SAVE_DIALOG

        result = self._window.create_file_dialog(
            mode,
            save_filename=default_name,
            file_types=("JSON Backup (*.json)",),
        )
        if not result:
            return False

        out_path = result[0] if isinstance(result, (list, tuple)) else result
        Path(out_path).write_text(json_text, encoding="utf-8")
        return True


if __name__ == "__main__":
    api = Api()
    html_path = find_html()
    window = webview.create_window(
        "Make-Your-Own Dollmaker",
        url=html_path,
        js_api=api,
        width=1220,
        height=820,
        min_size=(820, 600),
    )
    api._window = window
    webview.start(http_server=True)