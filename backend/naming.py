"""ابزارهای نام‌گذاری امن برای فایل‌ها و شیت‌های خروجی.

ویندوز محدودیت‌های سختگیرانه‌ای برای نام فایل دارد و اکسل هم برای نام شیت.
این ماژول تمام آن محدودیت‌ها را در یک جا جمع می‌کند تا موتور پردازش
هیچ‌وقت به خاطر یک نام نامعتبر شکست نخورد.
"""

from __future__ import annotations

import re
import unicodedata

#: کاراکترهایی که ویندوز در نام فایل نمی‌پذیرد
_INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

#: کاراکترهایی که اکسل در نام شیت نمی‌پذیرد
_INVALID_SHEET_CHARS = re.compile(r"[\[\]:*?/\\\x00-\x1f]")

#: نام‌های رزرو شده در ویندوز (بدون توجه به پسوند)
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

#: بیشترین طول مجاز برای بخش نام فایل (بدون پسوند)
MAX_FILENAME_LENGTH = 120

#: بیشترین طول مجاز برای نام شیت در اکسل
MAX_SHEET_NAME_LENGTH = 31

#: نامی که برای مقادیر خالی استفاده می‌شود
BLANK_LABEL = "بدون مقدار"


def _collapse_whitespace(text: str) -> str:
    """تبدیل هر نوع فاصله (از جمله نیم‌فاصله و فاصله‌های یونیکد) به یک فاصله ساده."""
    text = text.replace("‌", " ").replace("‏", "").replace("‎", "")
    return re.sub(r"\s+", " ", text).strip()


def safe_filename(value: object, fallback: str = "بدون-عنوان") -> str:
    """تبدیل هر مقداری به یک نام فایل معتبر در ویندوز، مک و لینوکس.

    Args:
        value: مقداری که باید به نام فایل تبدیل شود.
        fallback: نامی که وقتی چیزی از مقدار باقی نماند استفاده می‌شود.

    Returns:
        نام فایل بدون پسوند، معتبر و قابل استفاده در همه سیستم‌عامل‌ها.
    """
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFC", text)
    text = _INVALID_FILE_CHARS.sub("-", text)
    text = re.sub(r"-{2,}", "-", text)  # چند کاراکتر نامعتبر پشت‌سرهم = یک خط تیره
    text = _collapse_whitespace(text)

    # ویندوز نقطه و فاصله انتهایی را دور می‌اندازد و باعث تداخل نام می‌شود
    text = text.rstrip(". ")

    if not text:
        return fallback

    if text.upper().split(".")[0] in _RESERVED_NAMES:
        text = f"{text}-1"

    if len(text) > MAX_FILENAME_LENGTH:
        text = text[:MAX_FILENAME_LENGTH].rstrip(". ")

    return text or fallback


def safe_sheet_name(value: object, fallback: str = "Sheet") -> str:
    """تبدیل هر مقداری به یک نام شیت معتبر برای اکسل (حداکثر ۳۱ کاراکتر)."""
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFC", text)
    text = _INVALID_SHEET_CHARS.sub("-", text)
    text = _collapse_whitespace(text)
    text = text.strip("'")

    if not text:
        return fallback

    if len(text) > MAX_SHEET_NAME_LENGTH:
        text = text[:MAX_SHEET_NAME_LENGTH].strip()

    return text or fallback


class UniqueNamer:
    """نام‌های تکراری را با پسوند عددی یکتا می‌کند.

    دو مقدار متفاوت (مثل ``a/b`` و ``a-b``) ممکن است بعد از پاک‌سازی به یک نام
    برسند؛ این کلاس جلوی بازنویسی شدن فایل‌ها را می‌گیرد. مقایسه بدون حساسیت به
    بزرگی و کوچکی حروف انجام می‌شود چون فایل‌سیستم ویندوز هم همین‌طور است.
    """

    def __init__(self, max_length: int = MAX_FILENAME_LENGTH) -> None:
        self._seen: set[str] = set()
        self._max_length = max_length

    def make_unique(self, name: str) -> str:
        key = name.casefold()
        if key not in self._seen:
            self._seen.add(key)
            return name

        counter = 2
        while True:
            suffix = f"-{counter}"
            base = name
            if len(base) + len(suffix) > self._max_length:
                base = base[: self._max_length - len(suffix)].rstrip(". ")
            candidate = f"{base}{suffix}"
            if candidate.casefold() not in self._seen:
                self._seen.add(candidate.casefold())
                return candidate
            counter += 1
