"""زبان طراحی برنامه: رنگ، فاصله، گردی گوشه‌ها و قلم.

همه مقادیر ظاهری در همین یک فایل جمع شده‌اند تا تغییر ظاهر برنامه بدون
دست زدن به منطق رابط کاربری ممکن باشد.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

#: خانواده قلم‌هایی که به ترتیب اولویت امتحان می‌شوند
FONT_CANDIDATES = ("Vazirmatn", "Segoe UI", "Tahoma", "DejaVu Sans", "Arial")

#: نام قلم پیش‌فرض تا وقتی قلم واقعی شناسایی شود
_font_family = "Vazirmatn"


# ----------------------------------------------------------------------
# رنگ‌ها
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Palette:
    """یک جفت رنگ برای حالت روشن و تیره.

    CustomTkinter برای هر رنگ یک تاپل ``(روشن، تیره)`` می‌پذیرد؛ همین
    ساختار اینجا هم رعایت شده تا مقادیر مستقیم قابل استفاده باشند.
    """

    #: پس‌زمینه پنجره
    canvas: tuple[str, str] = ("#F5F5F7", "#0B0B0D")
    #: پس‌زمینه کارت‌ها
    surface: tuple[str, str] = ("#FFFFFF", "#161618")
    #: پس‌زمینه فرورفته (ورودی‌ها)
    inset: tuple[str, str] = ("#F2F2F4", "#1F1F22")
    #: خط مرزی مویی
    border: tuple[str, str] = ("#E3E3E6", "#2A2A2E")
    #: متن اصلی
    text: tuple[str, str] = ("#1D1D1F", "#F5F5F7")
    #: متن کم‌رنگ‌تر
    muted: tuple[str, str] = ("#6E6E73", "#98989D")
    #: متن بسیار کم‌رنگ
    faint: tuple[str, str] = ("#A1A1A6", "#6B6B70")
    #: رنگ تأکید (آبی سیستم)
    accent: tuple[str, str] = ("#0071E3", "#0A84FF")
    accent_hover: tuple[str, str] = ("#0077ED", "#3D9BFF")
    accent_soft: tuple[str, str] = ("#EAF3FE", "#12283F")
    #: موفقیت
    success: tuple[str, str] = ("#1D8B4A", "#32D74B")
    success_soft: tuple[str, str] = ("#E8F6EE", "#12291B")
    #: خطا
    danger: tuple[str, str] = ("#C7362F", "#FF6961")
    danger_soft: tuple[str, str] = ("#FCECEB", "#2E1614")
    #: حالت شناور دکمه‌های بی‌رنگ
    hover: tuple[str, str] = ("#ECECEE", "#242428")
    #: شفاف (بدون پس‌زمینه)
    clear: str = "transparent"


COLORS = Palette()


# ----------------------------------------------------------------------
# فاصله‌ها و اندازه‌ها
# ----------------------------------------------------------------------
class Space:
    """مقیاس فاصله‌گذاری بر پایه ۴ پیکسل."""

    xs = 4
    sm = 8
    md = 12
    lg = 16
    xl = 24
    xxl = 32


class Radius:
    """گردی گوشه‌ها."""

    sm = 8
    md = 12
    lg = 16
    pill = 999


class Size:
    """اندازه‌های ثابت اجزای رابط کاربری."""

    window_width = 880
    window_height = 734
    min_width = 800
    min_height = 620
    control_height = 38
    primary_height = 46
    field_height = 38


# ----------------------------------------------------------------------
# قلم
# ----------------------------------------------------------------------
def assets_dir() -> str:
    """مسیر پوشه ``assets`` را در حالت توسعه و در حالت باندل‌شده برمی‌گرداند."""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return os.path.join(bundled, "assets")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "assets")


def _register_windows_fonts(font_dir: str) -> bool:
    """قلم‌های همراه برنامه را فقط برای همین پروسه به ویندوز معرفی می‌کند."""
    try:
        import ctypes

        gdi32 = ctypes.WinDLL("gdi32")  # type: ignore[attr-defined]
        fr_private = 0x10
        loaded = 0
        for name in sorted(os.listdir(font_dir)):
            if name.lower().endswith((".ttf", ".otf")):
                path = os.path.join(font_dir, name)
                loaded += gdi32.AddFontResourceExW(ctypes.c_wchar_p(path), fr_private, 0)
        return loaded > 0
    except Exception:
        return False


def load_fonts() -> None:
    """قلم فارسی همراه برنامه را (در ویندوز) نصب موقت می‌کند.

    اگر نصب ممکن نباشد اتفاق بدی نمی‌افتد؛ :func:`resolve_font_family`
    سراغ اولین قلم موجود سیستم می‌رود.
    """
    font_dir = os.path.join(assets_dir(), "fonts")
    if not os.path.isdir(font_dir):
        return
    if sys.platform.startswith("win"):
        _register_windows_fonts(font_dir)


def resolve_font_family(root) -> str:
    """اولین قلم موجود از فهرست اولویت را انتخاب و ذخیره می‌کند."""
    global _font_family
    try:
        from tkinter import font as tkfont

        available = {name.lower() for name in tkfont.families(root)}
    except Exception:  # pragma: no cover
        available = set()

    for candidate in FONT_CANDIDATES:
        if candidate.lower() in available:
            _font_family = candidate
            break
    else:
        _font_family = FONT_CANDIDATES[-1]
    return _font_family


def family() -> str:
    """خانواده قلم انتخاب‌شده."""
    return _font_family


def font(size: int = 13, weight: str = "normal"):
    """یک شیء قلم CustomTkinter با خانواده انتخاب‌شده می‌سازد."""
    import customtkinter as ctk

    return ctk.CTkFont(family=_font_family, size=size, weight=weight)


class Type:
    """اندازه‌های تایپوگرافی."""

    display = 27
    title = 17
    heading = 14
    body = 13
    small = 12
    caption = 11


__all__ = [
    "COLORS",
    "FONT_CANDIDATES",
    "Palette",
    "Radius",
    "Size",
    "Space",
    "Type",
    "assets_dir",
    "family",
    "font",
    "load_fonts",
    "resolve_font_family",
]
