"""بک‌اند برنامه: خواندن و جداسازی فایل‌های اکسل، مستقل از رابط کاربری."""

from .excel_processor import (
    ColumnInfo,
    ExcelProcessor,
    OperationCancelled,
    ProcessingError,
    SplitResult,
)

__all__ = [
    "ColumnInfo",
    "ExcelProcessor",
    "OperationCancelled",
    "ProcessingError",
    "SplitResult",
]
