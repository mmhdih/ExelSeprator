"""تست‌های نام‌گذاری امن فایل و شیت."""

import pytest

from backend.naming import (
    MAX_FILENAME_LENGTH,
    MAX_SHEET_NAME_LENGTH,
    UniqueNamer,
    safe_filename,
    safe_sheet_name,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("تهران", "تهران"),
        ("a/b", "a-b"),
        ('x<>:"|?*y', "x-y"),
        ("a//b", "a-b"),
        ("  فاصله   اضافه  ", "فاصله اضافه"),
        ("نقطه در انتها...", "نقطه در انتها"),
        ("", "بدون-عنوان"),
        (None, "بدون-عنوان"),
        (12.5, "12.5"),
    ],
)
def test_safe_filename(value, expected):
    assert safe_filename(value) == expected


@pytest.mark.parametrize("reserved", ["CON", "con", "NUL", "COM1", "LPT9"])
def test_reserved_windows_names_get_suffix(reserved):
    assert safe_filename(reserved) != reserved
    assert safe_filename(reserved).startswith(reserved)


def test_filename_length_is_capped():
    assert len(safe_filename("ب" * 500)) == MAX_FILENAME_LENGTH


def test_control_characters_removed():
    assert "\n" not in safe_filename("خط\nجدید")
    assert "\x00" not in safe_filename("تهی\x00")


def test_safe_sheet_name_limits():
    assert len(safe_sheet_name("ش" * 80)) == MAX_SHEET_NAME_LENGTH
    assert safe_sheet_name("a[b]c") == "a-b-c"
    assert safe_sheet_name("") == "Sheet"


def test_unique_namer_avoids_collisions():
    namer = UniqueNamer()
    assert namer.make_unique("گزارش") == "گزارش"
    assert namer.make_unique("گزارش") == "گزارش-2"
    assert namer.make_unique("گزارش") == "گزارش-3"


def test_unique_namer_is_case_insensitive_like_windows():
    namer = UniqueNamer()
    assert namer.make_unique("Report") == "Report"
    assert namer.make_unique("report") == "report-2"


def test_unique_namer_respects_max_length():
    namer = UniqueNamer(max_length=10)
    first = namer.make_unique("a" * 10)
    second = namer.make_unique("a" * 10)
    assert first == "a" * 10
    assert len(second) <= 10
    assert second != first
