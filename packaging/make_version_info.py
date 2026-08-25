"""ساخت فایل اطلاعات نسخه برای exe ویندوز.

خروجی این اسکریپت به PyInstaller داده می‌شود تا نام محصول، شرکت و شماره
نسخه در «Properties» فایل exe دیده شود.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_meta import (  # noqa: E402
    APP_NAME,
    APP_NAME_EN,
    APP_PUBLISHER,
    APP_VERSION,
    VERSION_TUPLE,
)

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', {publisher!r}),
         StringStruct('FileDescription', {description!r}),
         StringStruct('FileVersion', {version!r}),
         StringStruct('InternalName', {internal!r}),
         StringStruct('OriginalFilename', {filename!r}),
         StringStruct('ProductName', {product!r}),
         StringStruct('ProductVersion', {version!r})])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> int:
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version_info.txt")
    content = TEMPLATE.format(
        version_tuple=VERSION_TUPLE,
        publisher=APP_PUBLISHER,
        description=f"{APP_NAME_EN} — {APP_NAME}",
        version=APP_VERSION,
        internal=APP_NAME_EN.replace(" ", ""),
        filename=f"{APP_NAME_EN.replace(' ', '')}.exe",
        product=APP_NAME_EN,
    )
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(f"version info -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
