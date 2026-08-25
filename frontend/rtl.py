"""پشتیبانی راست‌چین (RTL) برای Tk.

موتور متن Tk 8.6 حروف فارسی را به هم نمی‌چسباند و ترتیب کلمات را برعکس
نشان می‌دهد. برای همین هر متنی که قرار است *نمایش داده* شود از فیلتر
:func:`shape` عبور می‌کند تا ابتدا شکل حروف اصلاح و سپس الگوریتم دوطرفه
یونیکد روی آن اجرا شود.

نکته مهم: این تبدیل فقط برای نمایش است. هرگز نباید روی متنی که کاربر
ویرایش می‌کند یا روی مسیر فایل‌ها اعمال شود، چون رشته خروجی ترتیب
منطقی حروف را ندارد.
"""

from __future__ import annotations

import os
import re
import sys

try:  # pragma: no cover - وابسته به محیط اجرا
    import arabic_reshaper
    from bidi.algorithm import get_display

    _RESHAPER = arabic_reshaper.ArabicReshaper(
        configuration={"delete_harakat": False, "support_ligatures": True}
    )
    _AVAILABLE = True
except Exception:  # pragma: no cover - در نبود کتابخانه‌ها برنامه باید بالا بیاید
    _RESHAPER = None
    _AVAILABLE = False

#: با تنظیم این متغیر محیطی می‌توان تبدیل را خاموش کرد (برای Tk 9 که خودش
#: شکل‌دهی می‌کند یا برای عیب‌یابی).
_DISABLED = os.environ.get("EXCELSEP_DISABLE_RESHAPE", "").strip() in {"1", "true", "yes"}

_RTL_CHARS = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def is_available() -> bool:
    """آیا کتابخانه‌های شکل‌دهی متن در دسترس هستند؟"""
    return _AVAILABLE and not _DISABLED


def has_rtl(text: str) -> bool:
    """آیا متن حرف فارسی/عربی دارد؟"""
    return bool(_RTL_CHARS.search(text))


def shape(text: object) -> str:
    """متن را برای نمایش درست در Tk آماده می‌کند.

    اگر متن فارسی نداشته باشد بدون تغییر برمی‌گردد تا اعداد و مسیرهای
    انگلیسی دست‌نخورده بمانند.
    """
    value = "" if text is None else str(text)
    if not value or not is_available() or not has_rtl(value):
        return value

    try:
        reshaped = _RESHAPER.reshape(value)  # type: ignore[union-attr]
        return get_display(reshaped, base_dir="R")
    except Exception:  # pragma: no cover - هیچ‌وقت نباید UI را بشکند
        return value


_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_digits(value: object) -> str:
    """ارقام لاتین را به ارقام فارسی تبدیل می‌کند (فقط برای نمایش)."""
    return str(value).translate(_PERSIAN_DIGITS)


def fa_number(value: int) -> str:
    """عدد را با جداکننده هزارگان و ارقام فارسی نمایش می‌دهد."""
    return fa_digits(f"{int(value):,}").replace(",", "٬")


#: ویندوز و مک برای پنجره‌های سیستمی (پیام و انتخاب فایل) از دیالوگ بومی
#: استفاده می‌کنند و خودشان متن راست‌چین را درست می‌چینند؛ اعمال دوباره
#: شکل‌دهی روی آن‌ها نتیجه را خراب می‌کند.
_NATIVE_DIALOGS = sys.platform.startswith("win") or sys.platform == "darwin"


def dialog(text: object) -> str:
    """متن مناسب برای پنجره‌های سیستمی (messagebox و filedialog)."""
    value = "" if text is None else str(text)
    return value if _NATIVE_DIALOGS else shape(value)


def path_for_display(path: str, max_length: int = 58) -> str:
    """مسیر فایل را برای نمایش کوتاه می‌کند بدون آنکه ترتیبش به هم بخورد."""
    if not path:
        return ""
    if len(path) <= max_length:
        return path
    head = os.path.basename(path)
    if len(head) >= max_length - 4:
        return "…" + head[-(max_length - 1) :]
    remaining = max_length - len(head) - 4
    return f"{path[:remaining]}…{os.sep}{head}"


__all__ = [
    "dialog",
    "fa_digits",
    "fa_number",
    "has_rtl",
    "is_available",
    "path_for_display",
    "shape",
]
