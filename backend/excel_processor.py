"""موتور پردازش و جداسازی فایل‌های اکسل.

این ماژول هیچ وابستگی‌ای به رابط کاربری ندارد و می‌توان آن را مستقل
(در اسکریپت، تست یا خط فرمان) استفاده کرد.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

import pandas as pd

from .naming import BLANK_LABEL, UniqueNamer, safe_filename, safe_sheet_name

#: پسوندهایی که برنامه می‌تواند بخواند
SUPPORTED_EXTENSIONS = (".xlsx", ".xlsm", ".xls", ".csv")

#: قالب‌های خروجی پشتیبانی‌شده
OUTPUT_FORMATS = ("xlsx", "csv")

#: بیشترین تعداد شیت مجاز در حالت «یک فایل چندشیتی»
MAX_SHEETS_PER_WORKBOOK = 200

ProgressCallback = Callable[[int, int, str], None]


class ProcessingError(Exception):
    """خطای قابل نمایش به کاربر در جریان بارگذاری یا پردازش."""


class OperationCancelled(Exception):
    """کاربر عملیات را نیمه‌کاره لغو کرده است."""


@dataclass(frozen=True)
class ColumnInfo:
    """خلاصه‌ای از وضعیت یک ستون برای نمایش در رابط کاربری."""

    name: str
    unique_count: int
    blank_count: int
    sample: str = ""


@dataclass
class SplitResult:
    """نتیجه یک عملیات جداسازی."""

    output_paths: list[str] = field(default_factory=list)
    group_count: int = 0
    row_count: int = 0
    skipped_blank_rows: int = 0
    output_dir: str = ""

    @property
    def file_count(self) -> int:
        return len(self.output_paths)


class ExcelProcessor:
    """بارگذاری فایل اکسل و جداسازی سطرها بر اساس مقادیر یک ستون."""

    def __init__(self) -> None:
        self.df: pd.DataFrame | None = None
        self.file_path: str = ""
        self.sheet_name: str = ""
        self._sheets: list[str] = []

    # ------------------------------------------------------------------
    # بارگذاری
    # ------------------------------------------------------------------
    @staticmethod
    def list_sheets(file_path: str) -> list[str]:
        """فهرست شیت‌های یک فایل اکسل را برمی‌گرداند.

        برای فایل CSV یک شیت مجازی به نام ``CSV`` برگردانده می‌شود.
        """
        if not file_path:
            raise ProcessingError("مسیر فایل خالی است.")
        if not os.path.isfile(file_path):
            raise ProcessingError("فایل انتخاب‌شده پیدا نشد.")

        extension = os.path.splitext(file_path)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ProcessingError(
                "قالب فایل پشتیبانی نمی‌شود. فقط xlsx، xlsm، xls و csv مجاز است."
            )

        if extension == ".csv":
            return ["CSV"]

        try:
            with pd.ExcelFile(file_path) as workbook:
                sheets = [str(name) for name in workbook.sheet_names]
        except ImportError as exc:  # نبودن موتور خواندن xls
            raise ProcessingError(
                "برای خواندن فایل‌های قدیمی xls باید بسته xlrd نصب باشد."
            ) from exc
        except Exception as exc:
            raise ProcessingError(f"فایل باز نشد: {exc}") from exc

        if not sheets:
            raise ProcessingError("این فایل هیچ شیتی ندارد.")
        return sheets

    def load(
        self,
        file_path: str,
        sheet_name: str | None = None,
        header_row: int = 1,
    ) -> list[ColumnInfo]:
        """فایل را می‌خواند و اطلاعات ستون‌ها را برمی‌گرداند.

        Args:
            file_path: مسیر فایل ورودی.
            sheet_name: نام شیت؛ اگر داده نشود اولین شیت خوانده می‌شود.
            header_row: شماره سطر عنوان‌ها (از ۱ شروع می‌شود).

        Raises:
            ProcessingError: اگر فایل خوانده نشود یا داده‌ای نداشته باشد.
        """
        if header_row < 1:
            raise ProcessingError("شماره سطر عنوان باید حداقل ۱ باشد.")

        sheets = self.list_sheets(file_path)
        self._sheets = sheets
        target_sheet = sheet_name or sheets[0]
        if target_sheet not in sheets:
            raise ProcessingError(f"شیت «{target_sheet}» در این فایل وجود ندارد.")

        extension = os.path.splitext(file_path)[1].lower()
        try:
            if extension == ".csv":
                frame = pd.read_csv(file_path, header=header_row - 1, dtype=object)
            else:
                frame = pd.read_excel(
                    file_path,
                    sheet_name=target_sheet,
                    header=header_row - 1,
                    dtype=object,
                )
        except ProcessingError:
            raise
        except Exception as exc:
            raise ProcessingError(f"خطا در خواندن فایل: {exc}") from exc

        frame = _deduplicate_columns(frame)

        if frame.empty:
            raise ProcessingError("این شیت هیچ سطر داده‌ای ندارد.")
        if not len(frame.columns):
            raise ProcessingError("هیچ ستونی در این شیت پیدا نشد.")

        self.df = frame
        self.file_path = file_path
        self.sheet_name = target_sheet
        return self.describe_columns()

    # ------------------------------------------------------------------
    # اطلاعات
    # ------------------------------------------------------------------
    @property
    def sheets(self) -> list[str]:
        return list(self._sheets)

    @property
    def is_loaded(self) -> bool:
        return self.df is not None

    @property
    def row_count(self) -> int:
        return 0 if self.df is None else int(len(self.df))

    def column_names(self) -> list[str]:
        if self.df is None:
            return []
        return [str(column) for column in self.df.columns]

    def describe_columns(self) -> list[ColumnInfo]:
        """برای هر ستون تعداد گروه‌های یکتا و مقادیر خالی را محاسبه می‌کند."""
        if self.df is None:
            return []

        infos: list[ColumnInfo] = []
        for column in self.df.columns:
            series = _normalize(self.df[column])
            blanks = int(series.isna().sum())
            filled = series.dropna()
            uniques = filled.unique()
            sample = str(uniques[0]) if len(uniques) else ""
            infos.append(
                ColumnInfo(
                    name=str(column),
                    unique_count=int(len(uniques)),
                    blank_count=blanks,
                    sample=sample,
                )
            )
        return infos

    def column_info(self, column_name: str) -> ColumnInfo:
        for info in self.describe_columns():
            if info.name == column_name:
                return info
        raise ProcessingError(f"ستون «{column_name}» پیدا نشد.")

    # ------------------------------------------------------------------
    # جداسازی
    # ------------------------------------------------------------------
    def split(
        self,
        column_name: str,
        output_dir: str,
        *,
        output_format: str = "xlsx",
        single_workbook: bool = False,
        include_blanks: bool = True,
        progress: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
    ) -> SplitResult:
        """سطرها را بر اساس مقادیر یکتای یک ستون جدا می‌کند.

        Args:
            column_name: ستونی که مبنای جداسازی است.
            output_dir: پوشه‌ای که خروجی در آن ساخته می‌شود.
            output_format: ``xlsx`` یا ``csv``.
            single_workbook: اگر درست باشد، همه گروه‌ها در یک فایل اکسل و هر
                کدام در یک شیت جداگانه ذخیره می‌شوند.
            include_blanks: سطرهایی که در این ستون مقدار ندارند هم یک گروه
                جداگانه بسازند یا نادیده گرفته شوند.
            progress: تابعی که با ``(انجام‌شده، کل، عنوان گروه)`` صدا زده می‌شود.
            cancel_event: رویدادی که با ``set()`` عملیات را لغو می‌کند.

        Raises:
            ProcessingError: خطای قابل نمایش به کاربر.
            OperationCancelled: وقتی کاربر عملیات را لغو کند.
        """
        if self.df is None:
            raise ProcessingError("هنوز هیچ فایلی بارگذاری نشده است.")
        if column_name not in self.df.columns:
            raise ProcessingError(f"ستون «{column_name}» در این فایل وجود ندارد.")
        if output_format not in OUTPUT_FORMATS:
            raise ProcessingError("قالب خروجی نامعتبر است.")
        if not output_dir:
            raise ProcessingError("پوشه خروجی مشخص نشده است.")

        if single_workbook and output_format == "csv":
            raise ProcessingError("حالت «یک فایل چندشیتی» فقط با قالب اکسل کار می‌کند.")

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as exc:
            raise ProcessingError(f"پوشه خروجی ساخته نشد: {exc}") from exc

        if not os.access(output_dir, os.W_OK):
            raise ProcessingError("اجازه نوشتن در پوشه خروجی وجود ندارد.")

        groups = self._build_groups(column_name, include_blanks)
        if not groups:
            raise ProcessingError(
                "هیچ گروهی برای جداسازی پیدا نشد؛ این ستون مقدار معتبری ندارد."
            )

        if single_workbook and len(groups) > MAX_SHEETS_PER_WORKBOOK:
            raise ProcessingError(
                f"تعداد گروه‌ها ({len(groups)}) برای یک فایل چندشیتی زیاد است؛ "
                f"حداکثر {MAX_SHEETS_PER_WORKBOOK} شیت پشتیبانی می‌شود."
            )

        blank_rows = int(_normalize(self.df[column_name]).isna().sum())
        result = SplitResult(
            group_count=len(groups),
            output_dir=output_dir,
            skipped_blank_rows=0 if include_blanks else blank_rows,
        )

        if single_workbook:
            self._write_single_workbook(groups, output_dir, result, progress, cancel_event)
        else:
            self._write_many_files(
                groups, output_dir, output_format, result, progress, cancel_event
            )

        return result

    # ------------------------------------------------------------------
    # کمکی‌های داخلی
    # ------------------------------------------------------------------
    def _build_groups(
        self, column_name: str, include_blanks: bool
    ) -> list[tuple[str, pd.DataFrame]]:
        """سطرها را بر اساس مقدار ستون گروه‌بندی می‌کند.

        از ``groupby`` استفاده می‌شود تا حتی روی فایل‌های بزرگ هم یک بار
        پیمایش کافی باشد؛ ``sort=False`` ترتیب اولین ظهور مقادیر را حفظ
        می‌کند تا خروجی قابل پیش‌بینی بماند.
        """
        assert self.df is not None
        series = _normalize(self.df[column_name])

        groups: list[tuple[str, pd.DataFrame]] = [
            (str(value), frame)
            for value, frame in self.df.groupby(series, sort=False, dropna=True)
        ]

        if include_blanks:
            blank_mask = series.isna()
            if bool(blank_mask.any()):
                groups.append((BLANK_LABEL, self.df[blank_mask]))

        return groups

    def _write_many_files(
        self,
        groups: Sequence[tuple[str, pd.DataFrame]],
        output_dir: str,
        output_format: str,
        result: SplitResult,
        progress: ProgressCallback | None,
        cancel_event: threading.Event | None,
    ) -> None:
        namer = UniqueNamer()
        total = len(groups)

        for index, (label, frame) in enumerate(groups, start=1):
            _check_cancelled(cancel_event)
            file_name = namer.make_unique(safe_filename(label))
            path = os.path.join(output_dir, f"{file_name}.{output_format}")

            try:
                if output_format == "csv":
                    frame.to_csv(path, index=False, encoding="utf-8-sig")
                else:
                    frame.to_excel(path, index=False, sheet_name=safe_sheet_name(label))
            except PermissionError as exc:
                raise ProcessingError(
                    f"فایل «{os.path.basename(path)}» قابل نوشتن نیست؛ "
                    "شاید در اکسل باز باشد."
                ) from exc
            except OSError as exc:
                raise ProcessingError(f"ذخیره فایل ناموفق بود: {exc}") from exc

            result.output_paths.append(path)
            result.row_count += int(len(frame))
            _report(progress, index, total, label)

    def _write_single_workbook(
        self,
        groups: Sequence[tuple[str, pd.DataFrame]],
        output_dir: str,
        result: SplitResult,
        progress: ProgressCallback | None,
        cancel_event: threading.Event | None,
    ) -> None:
        source_name = os.path.splitext(os.path.basename(self.file_path))[0] or "خروجی"
        path = os.path.join(output_dir, f"{safe_filename(source_name)}-تفکیک‌شده.xlsx")
        namer = UniqueNamer(max_length=31)
        total = len(groups)

        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                for index, (label, frame) in enumerate(groups, start=1):
                    _check_cancelled(cancel_event)
                    sheet = namer.make_unique(safe_sheet_name(label))
                    frame.to_excel(writer, sheet_name=sheet, index=False)
                    result.row_count += int(len(frame))
                    _report(progress, index, total, label)
        except OperationCancelled:
            _remove_quietly(path)
            raise
        except PermissionError as exc:
            raise ProcessingError(
                "فایل خروجی قابل نوشتن نیست؛ شاید همین حالا در اکسل باز باشد."
            ) from exc
        except OSError as exc:
            raise ProcessingError(f"ذخیره فایل ناموفق بود: {exc}") from exc

        result.output_paths.append(path)


# ----------------------------------------------------------------------
# توابع کمکی ماژول
# ----------------------------------------------------------------------
def _normalize(series: pd.Series) -> pd.Series:
    """رشته‌ها را trim می‌کند و رشته خالی را معادل «بدون مقدار» می‌گیرد."""
    normalized = series.copy()
    is_text = normalized.map(lambda value: isinstance(value, str))
    if bool(is_text.any()):
        normalized[is_text] = normalized[is_text].map(str.strip)
        normalized = normalized.mask(is_text & (normalized == ""), other=None)
    return normalized


def _deduplicate_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """نام ستون‌های تکراری یا بی‌نام را یکتا و خوانا می‌کند."""
    namer = UniqueNamer(max_length=200)
    columns: list[str] = []
    for position, column in enumerate(frame.columns, start=1):
        name = "" if column is None else str(column).strip()
        if not name or name.lower().startswith("unnamed:"):
            name = f"ستون {position}"
        columns.append(namer.make_unique(name))
    frame = frame.copy()
    frame.columns = columns
    return frame


def _check_cancelled(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise OperationCancelled("عملیات توسط کاربر لغو شد.")


def _report(progress: ProgressCallback | None, done: int, total: int, label: str) -> None:
    if progress is not None:
        progress(done, total, label)


def _remove_quietly(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


__all__: Iterable[str] = (
    "ColumnInfo",
    "ExcelProcessor",
    "OperationCancelled",
    "OUTPUT_FORMATS",
    "ProcessingError",
    "SplitResult",
    "SUPPORTED_EXTENSIONS",
)
