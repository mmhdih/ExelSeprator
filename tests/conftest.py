"""پیکربندی مشترک تست‌ها."""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "شهر": ["تهران", "شیراز", "تهران", None, "اصفهان", "  شیراز  "],
            "نام": ["الف", "ب", "ج", "د", "ه", "و"],
            "مبلغ": [10, 20, 30, 40, 50, 60],
        }
    )


@pytest.fixture
def sample_xlsx(tmp_path, sample_frame) -> str:
    path = tmp_path / "نمونه.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        sample_frame.to_excel(writer, sheet_name="داده‌ها", index=False)
        sample_frame.head(2).to_excel(writer, sheet_name="شیت دوم", index=False)
    return str(path)
