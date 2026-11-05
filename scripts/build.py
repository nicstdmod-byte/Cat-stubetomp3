"""Build the Firefox and Chrome versions of the extension into dist/.

Usage: python3 scripts/build.py

  dist/firefox/                             unpacked Firefox extension
  dist/chrome/                              unpacked Chrome extension ("Load unpacked" this folder)
  dist/catstube2mp3-firefox-<version>.zip   upload to addons.mozilla.org for signing
  dist/catstube2mp3-chrome-<version>.zip    zip of dist/chrome for sharing
"""
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "extension"
DIST = ROOT / "dist"
CHROME_KEY = (ROOT / "scripts" / "chrome-public-key.txt").read_text().strip()


def copy_extension(target):
    shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns(".*", "*~"))
    return json.loads((target / "manifest.json").read_text(encoding="utf-8"))


def write_manifest(target, manifest):
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def zip_folder(folder, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(folder).as_posix())


def main():
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()

    firefox = DIST / "firefox"
    manifest = copy_extension(firefox)
    version = manifest["version"]
    write_manifest(firefox, manifest)
    zip_folder(firefox, DIST / f"catstube2mp3-firefox-{version}.zip")

    chrome = DIST / "chrome"
    manifest = copy_extension(chrome)
    manifest.pop("browser_specific_settings", None)
    manifest["key"] = CHROME_KEY  # fixes the extension ID so the helper can trust it
    write_manifest(chrome, manifest)
    zip_folder(chrome, DIST / f"catstube2mp3-chrome-{version}.zip")

    for path in sorted(DIST.iterdir()):
        print(f"built {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
