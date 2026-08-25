"""پنجره اصلی برنامه «جداساز اکسل».

منطق پردازش در بسته :mod:`backend` است؛ اینجا فقط چیدمان، اعتبارسنجی
ورودی‌ها و اجرای غیرمسدودکننده عملیات انجام می‌شود.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import queue
from tkinter import filedialog, messagebox

import customtkinter as ctk

from backend.excel_processor import (
    ExcelProcessor,
    OperationCancelled,
    ProcessingError,
    SUPPORTED_EXTENSIONS,
)

from . import theme
from .components import (
    Card,
    Check,
    Choice,
    Divider,
    GhostButton,
    PrimaryButton,
    RTLLabel,
    ReadOnlyPath,
    Select,
    StatusLine,
    StepHeader,
)
from .rtl import dialog, fa_number
from .theme import COLORS, Radius, Size, Space, Type

APP_NAME = "جداساز اکسل"
APP_TAGLINE = "فایل اکسل را بر اساس یک ستون، در چند ثانیه به فایل‌های جدا تبدیل کنید."
APP_VERSION = "2.0.0"

_FILE_TYPES = [
    ("فایل‌های اکسل و CSV", "*.xlsx *.xlsm *.xls *.csv"),
    ("همه فایل‌ها", "*.*"),
]


class AppUI(ctk.CTk):
    """پنجره اصلی."""

    def __init__(self) -> None:
        super().__init__()

        theme.load_fonts()
        ctk.set_appearance_mode("system")
        theme.resolve_font_family(self)

        self.processor = ExcelProcessor()
        self._worker: threading.Thread | None = None
        self._cancel = threading.Event()
        self._events: queue.Queue[tuple] = queue.Queue()
        self._last_output_dir = ""
        self._loaded_summary = ""
        self._sheet_enabled = False
        self._busy = False

        self._configure_window()
        self._build()
        self._refresh_run_state()
        self._poll_events()

    # ------------------------------------------------------------------
    # ساخت پنجره
    # ------------------------------------------------------------------
    def _configure_window(self) -> None:
        self.title(f"{APP_NAME} — Excel Separator")
        self.geometry(f"{Size.window_width}x{Size.window_height}")
        self.minsize(Size.min_width, Size.min_height)
        self.configure(fg_color=COLORS.canvas)
        self._center_on_screen()
        self._apply_window_icon()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - Size.window_width) // 2
        y = max(0, (self.winfo_screenheight() - Size.window_height) // 2 - 20)
        self.geometry(f"{Size.window_width}x{Size.window_height}+{x}+{y}")

    def _apply_window_icon(self) -> None:
        icon = os.path.join(theme.assets_dir(), "icon.ico")
        if sys.platform.startswith("win") and os.path.isfile(icon):
            try:
                self.iconbitmap(icon)
            except Exception:  # pragma: no cover - آیکون اختیاری است
                pass

    def _build(self) -> None:
        page = ctk.CTkFrame(self, fg_color=COLORS.clear)
        page.pack(fill="both", expand=True, padx=Space.xl + Space.xs, pady=Space.xl)

        # پاورقی پیش از کارت‌ها چیده می‌شود تا در پنجره‌های کوتاه هم
        # فضای خودش را از دست ندهد.
        self._build_header(page)
        self._build_footer(page)
        self._build_files_card(page)
        self._build_split_card(page)

    # -- سربرگ ---------------------------------------------------------
    def _build_header(self, parent) -> None:
        header = ctk.CTkFrame(parent, fg_color=COLORS.clear)
        header.pack(fill="x", pady=(0, Space.xl))

        titles = ctk.CTkFrame(header, fg_color=COLORS.clear)
        titles.pack(side="right", fill="x", expand=True)

        RTLLabel(titles, APP_NAME, size=Type.display, weight="bold").pack(
            anchor="e", fill="x"
        )
        RTLLabel(titles, APP_TAGLINE, size=Type.small, color=COLORS.muted).pack(
            anchor="e", fill="x", pady=(Space.xs, 0)
        )

        self._theme_button = GhostButton(
            header, "حالت تیره", self._toggle_theme, width=96
        )
        self._theme_button.pack(side="left", anchor="n")
        self._sync_theme_button()

    # -- مرحله ۱: فایل ورودی و پوشه مقصد -------------------------------
    def _build_files_card(self, parent) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=(0, Space.md))

        body = ctk.CTkFrame(card, fg_color=COLORS.clear)
        body.pack(fill="x", padx=Space.xl, pady=Space.lg)

        StepHeader(
            body, "۱", "فایل‌ها", "فایل ورودی و پوشه‌ای که خروجی در آن ساخته می‌شود."
        ).pack(fill="x", pady=(0, Space.md))

        # سطر فایل ورودی
        source = ctk.CTkFrame(body, fg_color=COLORS.clear)
        source.pack(fill="x")

        RTLLabel(
            source, "فایل ورودی", size=Type.small, color=COLORS.muted, width=76
        ).pack(side="right")
        self._file_button = GhostButton(source, "انتخاب فایل", self._choose_file)
        self._file_button.pack(side="left", padx=(Space.sm, 0))
        self._file_path = ReadOnlyPath(source, "هنوز فایلی انتخاب نشده است")
        self._file_path.pack(side="right", fill="x", expand=True, padx=(Space.sm, 0))

        # سطر شیت و سطر عنوان‌ها
        options = ctk.CTkFrame(body, fg_color=COLORS.clear)
        options.pack(fill="x", pady=(Space.sm, 0))

        RTLLabel(
            options, "شیت", size=Type.small, color=COLORS.muted, width=76
        ).pack(side="right")
        self._sheet_select = Select(options, "—", command=self._on_sheet_change)
        self._sheet_select.configure(width=248)
        self._sheet_select.pack(side="right", padx=(Space.sm, 0))

        RTLLabel(
            options, "سطر عنوان‌ها", size=Type.small, color=COLORS.muted
        ).pack(side="right", padx=(0, Space.xl))
        self._header_row = ctk.CTkEntry(
            options,
            width=64,
            height=Size.field_height,
            corner_radius=Radius.sm,
            fg_color=COLORS.inset,
            border_color=COLORS.border,
            border_width=1,
            text_color=COLORS.text,
            font=theme.font(Type.small),
            justify="center",
        )
        self._header_row.insert(0, "1")
        self._header_row.pack(side="right", padx=(Space.sm, 0))
        self._header_row.bind("<Return>", lambda _e: self._reload_current_file())
        self._header_row.bind("<FocusOut>", lambda _e: self._reload_current_file())

        Divider(body).pack(fill="x", pady=Space.md)

        # سطر پوشه مقصد
        destination = ctk.CTkFrame(body, fg_color=COLORS.clear)
        destination.pack(fill="x")

        RTLLabel(
            destination, "پوشه خروجی", size=Type.small, color=COLORS.muted, width=76
        ).pack(side="right")
        self._output_button = GhostButton(
            destination, "انتخاب پوشه", self._choose_output
        )
        self._output_button.pack(side="left", padx=(Space.sm, 0))
        self._output_path = ReadOnlyPath(destination, "هنوز پوشه‌ای انتخاب نشده است")
        self._output_path.pack(side="right", fill="x", expand=True, padx=(Space.sm, 0))

    # -- مرحله ۲: ستون و حالت خروجی -------------------------------------
    def _build_split_card(self, parent) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=(0, Space.md))

        body = ctk.CTkFrame(card, fg_color=COLORS.clear)
        body.pack(fill="x", padx=Space.xl, pady=Space.lg)

        StepHeader(
            body,
            "۲",
            "نحوه جداسازی",
            "به ازای هر مقدار یکتای ستون انتخابی یک خروجی ساخته می‌شود.",
        ).pack(fill="x", pady=(0, Space.md))

        column_row = ctk.CTkFrame(body, fg_color=COLORS.clear)
        column_row.pack(fill="x")

        RTLLabel(
            column_row, "ستون", size=Type.small, color=COLORS.muted, width=76
        ).pack(side="right")
        self._column_select = Select(
            column_row, "ابتدا فایل را انتخاب کنید", command=self._on_column_change
        )
        self._column_select.pack(side="right", fill="x", expand=True, padx=(Space.sm, 0))

        modes = ctk.CTkFrame(body, fg_color=COLORS.clear)
        modes.pack(fill="x", pady=(Space.sm, 0))

        RTLLabel(
            modes, "خروجی", size=Type.small, color=COLORS.muted, width=76
        ).pack(side="right")
        self._mode_choice = Choice(
            modes,
            [("چند فایل جدا", "files"), ("یک فایل چندشیتی", "workbook")],
            default="files",
            command=self._on_mode_change,
        )
        self._mode_choice.pack(side="right", padx=(Space.sm, 0))

        RTLLabel(modes, "قالب", size=Type.small, color=COLORS.muted).pack(
            side="right", padx=(0, Space.xl)
        )
        self._format_choice = Choice(
            modes,
            [("اکسل", "xlsx"), ("CSV", "csv")],
            default="xlsx",
            command=lambda _value: self._update_preview(),
        )
        self._format_choice.pack(side="right", padx=(Space.sm, 0))

        self._include_blanks = Check(
            body,
            "سطرهایی که در این ستون مقدار ندارند هم در یک گروه جداگانه ذخیره شوند",
            checked=True,
            command=lambda _checked: self._update_preview(),
        )
        self._include_blanks.pack(anchor="e", fill="x", pady=(Space.md, 0))

    # -- پاورقی: وضعیت و دکمه اجرا ---------------------------------------
    def _build_footer(self, parent) -> None:
        footer = ctk.CTkFrame(parent, fg_color=COLORS.clear)
        footer.pack(fill="x", side="bottom")

        self._status = StatusLine(footer)
        self._status.pack(fill="x", pady=(0, Space.md))

        actions = ctk.CTkFrame(footer, fg_color=COLORS.clear)
        actions.pack(fill="x")

        self._run_button = PrimaryButton(actions, "شروع جداسازی", self._start, width=190)
        self._run_button.pack(side="right")

        self._open_button = GhostButton(
            actions, "باز کردن پوشه خروجی", self._open_output_dir, width=170
        )

        RTLLabel(
            actions,
            f"نسخه {APP_VERSION}",
            size=Type.caption,
            color=COLORS.faint,
            anchor="w",
        ).pack(side="left")

    # ------------------------------------------------------------------
    # تعامل کاربر
    # ------------------------------------------------------------------
    def _choose_file(self) -> None:
        if self._busy:
            return
        path = filedialog.askopenfilename(
            title=dialog("انتخاب فایل ورودی"), filetypes=_FILE_TYPES
        )
        if not path:
            return
        if not path.lower().endswith(SUPPORTED_EXTENSIONS):
            self._alert("قالب پشتیبانی نمی‌شود؛ فقط xlsx، xlsm، xls و csv قابل خواندن است.")
            return

        self._file_path.set_path(path)
        self._load_sheets(path)

    def _load_sheets(self, path: str) -> None:
        try:
            sheets = ExcelProcessor.list_sheets(path)
        except ProcessingError as error:
            self._reset_data_state()
            self._status.error(str(error))
            return

        self._sheet_enabled = len(sheets) > 1
        self._sheet_select.set_options([(name, name) for name in sheets], sheets[0])
        self._sheet_select.configure(
            state="normal" if self._sheet_enabled else "disabled"
        )
        self._load_columns(path, sheets[0])

    def _load_columns(self, path: str, sheet: str) -> None:
        try:
            columns = self.processor.load(path, sheet, self._header_row_value())
        except ProcessingError as error:
            self._reset_data_state()
            self._status.error(str(error))
            return

        options = [
            (
                f"{info.name} — {fa_number(info.unique_count)} گروه"
                + (f" ({fa_number(info.blank_count)} خالی)" if info.blank_count else ""),
                info.name,
            )
            for info in columns
        ]
        # ستونی که کمترین تعداد گروه معنادار را دارد معمولاً گزینه درست است
        best = min(
            (i for i in columns if i.unique_count > 1),
            key=lambda i: i.unique_count,
            default=columns[0],
        )
        self._column_select.set_options(options, best.name)

        self._loaded_summary = (
            f"{fa_number(self.processor.row_count)} سطر و "
            f"{fa_number(len(columns))} ستون خوانده شد"
        )
        self._update_preview()

        if not self._output_path.value:
            self._output_path.set_path(
                os.path.join(os.path.dirname(path), "خروجی-جداسازی")
            )

    def _on_sheet_change(self, sheet: str) -> None:
        path = self._file_path.value
        if path:
            self._load_columns(path, sheet)

    def _reload_current_file(self) -> None:
        path = self._file_path.value
        sheet = self._sheet_select.value
        if path and sheet and not self._busy:
            self._load_columns(path, sheet)

    def _on_column_change(self, _column: str) -> None:
        self._update_preview()

    def _on_mode_change(self, mode: str) -> None:
        if mode == "workbook":
            self._format_choice.select("xlsx")
            self._format_choice.configure(state="disabled")
        else:
            self._format_choice.configure(state="normal")
        self._update_preview()

    def _update_preview(self) -> None:
        """نوار وضعیت را با خلاصه فایل و نتیجه مورد انتظار به‌روز می‌کند."""
        if self._busy:
            return

        column = self._column_select.value
        if not column or not self.processor.is_loaded:
            self._status.clear()
            self._refresh_run_state()
            return

        try:
            info = self.processor.column_info(column)
        except ProcessingError:
            self._status.info(self._loaded_summary)
            return

        groups = info.unique_count + (
            1 if info.blank_count and self._include_blanks.value else 0
        )
        if self._mode_choice.value == "workbook":
            outcome = f"یک فایل اکسل با {fa_number(groups)} شیت ساخته می‌شود"
        else:
            extension = self._format_choice.value or "xlsx"
            outcome = f"{fa_number(groups)} فایل {extension} ساخته می‌شود"

        self._status.info(f"{self._loaded_summary} — {outcome}")
        self._refresh_run_state()

    def _choose_output(self) -> None:
        if self._busy:
            return
        folder = filedialog.askdirectory(title=dialog("انتخاب پوشه خروجی"))
        if folder:
            self._output_path.set_path(folder)
            self._refresh_run_state()

    def _toggle_theme(self) -> None:
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if current == "Dark" else "dark")
        self._sync_theme_button()

    def _sync_theme_button(self) -> None:
        is_dark = ctk.get_appearance_mode() == "Dark"
        self._theme_button.set_text("حالت روشن" if is_dark else "حالت تیره")

    def _open_output_dir(self) -> None:
        folder = self._last_output_dir
        if not folder or not os.path.isdir(folder):
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            self._status.error("باز کردن پوشه ممکن نشد.")

    # ------------------------------------------------------------------
    # اجرای عملیات
    # ------------------------------------------------------------------
    def _header_row_value(self) -> int:
        raw = self._header_row.get().strip()
        try:
            return max(1, int(raw))
        except ValueError:
            return 1

    def _validate(self) -> str | None:
        """ورودی‌ها را بررسی می‌کند و در صورت اشکال پیام خطا برمی‌گرداند."""
        if not self.processor.is_loaded:
            return "ابتدا یک فایل اکسل انتخاب کنید."

        if not self._column_select.value:
            return "ستونی را که می‌خواهید بر اساس آن جدا شود انتخاب کنید."

        output_dir = self._output_path.value.strip()
        if not output_dir:
            return "مسیر ذخیره فایل‌ها را مشخص کنید."

        parent = os.path.dirname(os.path.abspath(output_dir)) or "."
        if not os.path.isdir(output_dir) and not os.path.isdir(parent):
            return "پوشه خروجی وجود ندارد و ساخته هم نمی‌شود."

        return None

    def _start(self) -> None:
        if self._busy:
            self._cancel.set()
            self._status.info("در حال لغو…")
            return

        problem = self._validate()
        if problem:
            self._alert(problem)
            return

        column = self._column_select.value or ""
        output_dir = self._output_path.value.strip()
        single_workbook = self._mode_choice.value == "workbook"
        output_format = "xlsx" if single_workbook else (self._format_choice.value or "xlsx")

        self._set_busy(True)
        self._cancel = threading.Event()
        self._status.info("در حال آماده‌سازی…")
        self._status.show_progress(0)

        self._worker = threading.Thread(
            target=self._run_split,
            args=(column, output_dir, output_format, single_workbook),
            daemon=True,
        )
        self._worker.start()

    def _run_split(
        self,
        column: str,
        output_dir: str,
        output_format: str,
        single_workbook: bool,
    ) -> None:
        """در نخ پس‌زمینه اجرا می‌شود؛ نتیجه از طریق صف به رابط کاربری می‌رسد."""
        try:
            result = self.processor.split(
                column,
                output_dir,
                output_format=output_format,
                single_workbook=single_workbook,
                include_blanks=self._include_blanks.value,
                progress=lambda done, total, label: self._events.put(
                    ("progress", done, total, label)
                ),
                cancel_event=self._cancel,
            )
            self._events.put(("done", result))
        except OperationCancelled:
            self._events.put(("cancelled",))
        except ProcessingError as error:
            self._events.put(("error", str(error)))
        except Exception as error:  # pragma: no cover - تور ایمنی
            self._events.put(("error", f"خطای پیش‌بینی‌نشده: {error}"))

    def _poll_events(self) -> None:
        """صف رویدادهای نخ پس‌زمینه را روی نخ رابط کاربری تخلیه می‌کند."""
        try:
            while True:
                event = self._events.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        self.after(60, self._poll_events)

    def _handle_event(self, event: tuple) -> None:
        kind = event[0]

        if kind == "progress":
            _, done, total, label = event
            self._status.show_progress(done / total if total else 0)
            self._status.info(
                f"{fa_number(done)} از {fa_number(total)} — {label}"
            )

        elif kind == "done":
            result = event[1]
            self._set_busy(False)
            self._status.hide_progress()
            self._last_output_dir = result.output_dir
            self._open_button.pack(side="right", padx=(Space.sm, 0))

            summary = (
                f"{fa_number(result.file_count)} فایل از "
                f"{fa_number(result.row_count)} سطر ساخته شد."
            )
            if result.skipped_blank_rows:
                summary += (
                    f" {fa_number(result.skipped_blank_rows)} سطر بدون مقدار نادیده گرفته شد."
                )
            self._status.success(summary)

        elif kind == "cancelled":
            self._set_busy(False)
            self._status.hide_progress()
            self._status.info("عملیات لغو شد.")

        elif kind == "error":
            self._set_busy(False)
            self._status.hide_progress()
            self._status.error(event[1])

    def _refresh_run_state(self) -> None:
        """دکمه اجرا فقط وقتی فعال است که همه ورودی‌های لازم آماده باشند."""
        if self._busy:
            return
        ready = self._validate() is None
        self._run_button.configure(
            state="normal" if ready else "disabled",
            fg_color=COLORS.accent if ready else COLORS.inset,
        )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._run_button.set_text("لغو عملیات" if busy else "شروع جداسازی")
        self._run_button.configure(
            state="normal",
            fg_color=COLORS.danger if busy else COLORS.accent,
            hover_color=COLORS.danger if busy else COLORS.accent_hover,
        )
        for widget in (self._file_button, self._output_button):
            widget.configure(state="disabled" if busy else "normal")
        self._sheet_select.configure(
            state="normal" if self._sheet_enabled and not busy else "disabled"
        )
        if not busy:
            self._refresh_run_state()

    # ------------------------------------------------------------------
    # کمکی‌ها
    # ------------------------------------------------------------------
    def _reset_data_state(self) -> None:
        self.processor = ExcelProcessor()
        self._column_select.clear()
        self._loaded_summary = ""

    def _alert(self, message: str) -> None:
        """پیام خطا را در نوار وضعیت نشان می‌دهد (بدون پنجره مزاحم)."""
        self._status.error(message)

    def _on_close(self) -> None:
        if self._busy:
            if not messagebox.askyesno(
                dialog("عملیات در حال اجراست"),
                dialog("پردازش هنوز تمام نشده است. می‌خواهید خارج شوید؟"),
                parent=self,
            ):
                return
            self._cancel.set()
        self.destroy()


__all__ = ["APP_NAME", "APP_VERSION", "AppUI"]
