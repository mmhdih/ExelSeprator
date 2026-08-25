# -*- mode: python ; coding: utf-8 -*-
"""پیکربندی PyInstaller برای ساخت نسخه پرتابل ویندوز.

اجرا:
    python packaging/make_version_info.py
    pyinstaller --noconfirm --clean ExcelSeparator.spec

خروجی یک فایل exe تک‌تکه در پوشه ``dist`` است که به نصب پایتون نیاز ندارد.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(SPECPATH)  # noqa: F821 - PyInstaller این را تعریف می‌کند
sys.path.insert(0, ROOT)

from app_meta import APP_NAME_EN  # noqa: E402

# قلم فارسی و آیکون باید داخل exe بسته‌بندی شوند
datas = [(os.path.join(ROOT, "assets"), "assets")]
binaries = []
hiddenimports = []

# این بسته‌ها فایل داده همراه دارند و بدون جمع‌آوری کامل کار نمی‌کنند
for package in ("customtkinter", "arabic_reshaper", "bidi"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

# چیزهایی که برنامه استفاده نمی‌کند و فقط حجم exe را زیاد می‌کنند
excludes = [
    "matplotlib",
    "scipy",
    "IPython",
    "notebook",
    "jupyter",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "pytest",
    "sphinx",
    "setuptools",
    "pip",
]

version_file = os.path.join(ROOT, "packaging", "version_info.txt")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + ["app_meta"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME_EN.replace(" ", ""),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, "assets", "icon.ico"),
    version=version_file if os.path.isfile(version_file) else None,
)
