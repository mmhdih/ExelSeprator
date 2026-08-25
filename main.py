"""نقطه شروع برنامه «جداساز اکسل».

اجرا:
    python main.py
"""

from __future__ import annotations

import os
import sys
import traceback

# وقتی برنامه به صورت exe اجرا می‌شود، ریشه پروژه باید روی sys.path باشد
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _show_startup_error(error: BaseException) -> None:
    """اگر برنامه اصلاً بالا نیامد، خطا را جایی نشان بده که کاربر ببیند."""
    details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    print(details, file=sys.stderr)
    try:
        from tkinter import messagebox

        messagebox.showerror(
            "خطا در اجرای برنامه",
            "برنامه اجرا نشد.\n\n" + str(error),
        )
    except Exception:
        pass


def main() -> int:
    try:
        from frontend.ui_main import AppUI

        AppUI().mainloop()
        return 0
    except Exception as error:  # pragma: no cover - مسیر خطای راه‌اندازی
        _show_startup_error(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
