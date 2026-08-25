"""تست‌های موتور جداسازی اکسل."""

import os
import threading

import pandas as pd
import pytest

from backend.excel_processor import (
    ExcelProcessor,
    OperationCancelled,
    ProcessingError,
)
from backend.naming import BLANK_LABEL


def test_list_sheets(sample_xlsx):
    assert ExcelProcessor.list_sheets(sample_xlsx) == ["داده‌ها", "شیت دوم"]


def test_list_sheets_rejects_missing_file(tmp_path):
    with pytest.raises(ProcessingError):
        ExcelProcessor.list_sheets(str(tmp_path / "نیست.xlsx"))


def test_list_sheets_rejects_unsupported_format(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("hello", encoding="utf-8")
    with pytest.raises(ProcessingError):
        ExcelProcessor.list_sheets(str(path))


def test_load_returns_column_info(sample_xlsx):
    processor = ExcelProcessor()
    columns = processor.load(sample_xlsx)

    assert [c.name for c in columns] == ["شهر", "نام", "مبلغ"]
    city = columns[0]
    # «  شیراز  » بعد از trim با «شیراز» یکی می‌شود
    assert city.unique_count == 3
    assert city.blank_count == 1
    assert processor.row_count == 6


def test_load_specific_sheet(sample_xlsx):
    processor = ExcelProcessor()
    processor.load(sample_xlsx, sheet_name="شیت دوم")
    assert processor.row_count == 2


def test_load_unknown_sheet(sample_xlsx):
    processor = ExcelProcessor()
    with pytest.raises(ProcessingError):
        processor.load(sample_xlsx, sheet_name="ندارد")


def test_load_with_header_row(tmp_path):
    frame = pd.DataFrame([["گزارش ماهانه", None], ["شهر", "مبلغ"], ["تهران", 10]])
    path = tmp_path / "header.xlsx"
    frame.to_excel(path, index=False, header=False)

    processor = ExcelProcessor()
    columns = processor.load(str(path), header_row=2)
    assert [c.name for c in columns] == ["شهر", "مبلغ"]


def test_split_creates_one_file_per_value(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)
    out = tmp_path / "out"

    result = processor.split("شهر", str(out))

    names = sorted(os.path.basename(p) for p in result.output_paths)
    assert names == sorted(
        ["تهران.xlsx", "شیراز.xlsx", "اصفهان.xlsx", f"{BLANK_LABEL}.xlsx"]
    )
    assert result.group_count == 4
    assert result.row_count == 6

    tehran = pd.read_excel(out / "تهران.xlsx")
    assert len(tehran) == 2
    assert list(tehran.columns) == ["شهر", "نام", "مبلغ"]


def test_split_can_skip_blank_rows(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)

    result = processor.split("شهر", str(tmp_path / "out"), include_blanks=False)

    assert result.group_count == 3
    assert result.skipped_blank_rows == 1
    assert all(BLANK_LABEL not in p for p in result.output_paths)


def test_split_to_csv(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)

    result = processor.split("شهر", str(tmp_path / "csv"), output_format="csv")

    assert all(p.endswith(".csv") for p in result.output_paths)
    frame = pd.read_csv(os.path.join(str(tmp_path / "csv"), "تهران.csv"))
    assert len(frame) == 2


def test_split_into_single_workbook(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)

    result = processor.split("شهر", str(tmp_path / "wb"), single_workbook=True)

    assert result.file_count == 1
    sheets = pd.ExcelFile(result.output_paths[0]).sheet_names
    assert set(sheets) == {"تهران", "شیراز", "اصفهان", BLANK_LABEL}


def test_single_workbook_rejects_csv(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)
    with pytest.raises(ProcessingError):
        processor.split(
            "شهر", str(tmp_path / "x"), output_format="csv", single_workbook=True
        )


def test_split_requires_loaded_file(tmp_path):
    with pytest.raises(ProcessingError):
        ExcelProcessor().split("شهر", str(tmp_path))


def test_split_rejects_unknown_column(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)
    with pytest.raises(ProcessingError):
        processor.split("ستون-ناموجود", str(tmp_path / "out"))


def test_progress_is_reported(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)
    seen: list[tuple[int, int]] = []

    processor.split(
        "شهر",
        str(tmp_path / "out"),
        progress=lambda done, total, label: seen.append((done, total)),
    )

    assert seen == [(1, 4), (2, 4), (3, 4), (4, 4)]


def test_cancellation_stops_processing(sample_xlsx, tmp_path):
    processor = ExcelProcessor()
    processor.load(sample_xlsx)
    cancel = threading.Event()
    cancel.set()

    with pytest.raises(OperationCancelled):
        processor.split("شهر", str(tmp_path / "out"), cancel_event=cancel)


def test_illegal_values_become_safe_filenames(tmp_path):
    frame = pd.DataFrame({"کد": ["a/b", "a:b", "CON"], "v": [1, 2, 3]})
    source = tmp_path / "in.xlsx"
    frame.to_excel(source, index=False)

    processor = ExcelProcessor()
    processor.load(str(source))
    result = processor.split("کد", str(tmp_path / "out"))

    names = sorted(os.path.basename(p) for p in result.output_paths)
    assert names == ["CON-1.xlsx", "a-b-2.xlsx", "a-b.xlsx"]
    assert result.file_count == 3


def test_duplicate_and_unnamed_columns_are_renamed(tmp_path):
    path = tmp_path / "dup.xlsx"
    pd.DataFrame([["شهر", "شهر", None], ["تهران", "الف", 1]]).to_excel(
        path, index=False, header=False
    )

    processor = ExcelProcessor()
    columns = processor.load(str(path))
    # pandas خودش عنوان تکراری را به «شهر.1» تبدیل می‌کند و ستون بی‌نام را ما
    assert [c.name for c in columns] == ["شهر", "شهر.1", "ستون 3"]


def test_csv_input_is_supported(tmp_path):
    source = tmp_path / "in.csv"
    pd.DataFrame({"شهر": ["تهران", "شیراز"], "v": [1, 2]}).to_csv(
        source, index=False, encoding="utf-8-sig"
    )

    processor = ExcelProcessor()
    processor.load(str(source))
    result = processor.split("شهر", str(tmp_path / "out"))
    assert result.file_count == 2
