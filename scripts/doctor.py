# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24", "jinja2>=3.1", "playwright>=1.45", "opencv-python-headless>=4.9", "numpy>=1.26", "scikit-image>=0.22"]
# ///
"""Check that the plugin's tools can run here, and fix what can be fixed.

  uv run doctor.py            report: uv, Python packages, Chromium, the reports/ folder
  uv run doctor.py --fix      also download Chromium when it is missing

Exit code 1 when something is still missing. Meant to be run by the agent (the `setup` skill),
so a person never types an install command.
"""
import argparse, importlib, os, pathlib, shutil, subprocess, sys


def check(label, ok, detail=""):
    print(f"  {'ok     ' if ok else 'MISSING'}  {label}{('  ' + detail) if detail else ''}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="download Chromium when it is missing")
    ap.add_argument("--project", default=os.environ.get("CLAUDE_PROJECT_DIR", "."), help="the project folder (holds reports/)")
    a = ap.parse_args()
    good = True
    print("pdf-to-template doctor")
    good &= check("uv", shutil.which("uv") is not None, shutil.which("uv") or "install uv: https://docs.astral.sh/uv/")
    good &= check("python", sys.version_info >= (3, 10), sys.version.split()[0])
    for mod in ("pymupdf", "jinja2", "playwright", "cv2", "skimage"):
        try:
            importlib.import_module(mod)
            good &= check(f"package {mod}", True)
        except Exception as e:  # noqa: BLE001
            good &= check(f"package {mod}", False, str(e))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        exe = pathlib.Path(p.chromium.executable_path)
        have = exe.exists()
        if not have and a.fix:
            print("  downloading Chromium once (playwright install chromium) ...")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
            have = exe.exists()
        good &= check("chromium", have, str(exe) if have else "run with --fix")
    reports = pathlib.Path(a.project) / "reports"
    n = len([d for d in reports.iterdir() if d.is_dir()]) if reports.is_dir() else 0
    check("reports/ folder", reports.is_dir(), f"{reports}  ({n} report folder{'s' if n != 1 else ''})" if reports.is_dir() else f"none at {reports}; created on the first report")
    print("ready" if good else "not ready: see MISSING above")
    sys.exit(0 if good else 1)


if __name__ == "__main__":
    main()
