"""اجزای پایه رابط کاربری؛ همه راست‌چین و هماهنگ با زبان طراحی برنامه.

هر ویجت اینجا دو کار را تضمین می‌کند: متن فارسی درست شکل می‌گیرد و
چیدمان از راست به چپ است.
"""

from __future__ import annotations

from typing import Callable, Sequence

import customtkinter as ctk

from . import theme
from .rtl import path_for_display, shape
from .theme import COLORS, Radius, Size, Space, Type


class RTLLabel(ctk.CTkLabel):
    """برچسبی که متنش را خودکار شکل می‌دهد و به راست می‌چسبد."""

    def __init__(
        self,
        master,
        text: str = "",
        *,
        size: int = Type.body,
        weight: str = "normal",
        color=COLORS.text,
        anchor: str = "e",
        justify: str = "right",
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            text=shape(text),
            font=theme.font(size, weight),
            text_color=color,
            anchor=anchor,
            justify=justify,
            fg_color=COLORS.clear,
            **kwargs,
        )

    def set_text(self, text: str) -> None:
        """متن را با شکل‌دهی مجدد جایگزین می‌کند."""
        self.configure(text=shape(text))


class Card(ctk.CTkFrame):
    """کارت سفید با گوشه گرد و خط مویی؛ واحد اصلی چیدمان صفحه."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS.surface,
            border_color=COLORS.border,
            border_width=1,
            corner_radius=Radius.lg,
            **kwargs,
        )


class StepHeader(ctk.CTkFrame):
    """سرتیتر یک بخش: شماره مرحله، عنوان و توضیح کوتاه."""

    def __init__(self, master, step: str, title: str, subtitle: str = "") -> None:
        super().__init__(master, fg_color=COLORS.clear)

        badge = ctk.CTkLabel(
            self,
            text=step,
            width=26,
            height=26,
            corner_radius=Radius.pill,
            fg_color=COLORS.accent_soft,
            text_color=COLORS.accent,
            font=theme.font(Type.caption, "bold"),
        )
        badge.pack(side="right", padx=(0, 0))

        texts = ctk.CTkFrame(self, fg_color=COLORS.clear)
        texts.pack(side="right", padx=(0, Space.md), fill="x", expand=True)

        RTLLabel(texts, title, size=Type.heading, weight="bold").pack(
            anchor="e", fill="x"
        )
        if subtitle:
            RTLLabel(
                texts, subtitle, size=Type.caption, color=COLORS.muted
            ).pack(anchor="e", fill="x", pady=(2, 0))


class PrimaryButton(ctk.CTkButton):
    """دکمه اصلی و پررنگ صفحه."""

    def __init__(self, master, text: str, command: Callable[[], None], **kwargs) -> None:
        super().__init__(
            master,
            text=shape(text),
            command=command,
            height=Size.primary_height,
            corner_radius=Radius.md,
            fg_color=COLORS.accent,
            hover_color=COLORS.accent_hover,
            text_color="#FFFFFF",
            text_color_disabled=COLORS.faint,
            font=theme.font(Type.heading, "bold"),
            **kwargs,
        )

    def set_text(self, text: str) -> None:
        self.configure(text=shape(text))


class GhostButton(ctk.CTkButton):
    """دکمه ثانویه با زمینه خنثی؛ برای کارهای فرعی مثل انتخاب مسیر."""

    def __init__(
        self,
        master,
        text: str,
        command: Callable[[], None],
        *,
        width: int = 116,
        danger: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            text=shape(text),
            command=command,
            width=width,
            height=Size.control_height,
            corner_radius=Radius.sm,
            fg_color=COLORS.inset,
            hover_color=COLORS.hover,
            text_color=COLORS.danger if danger else COLORS.text,
            border_width=1,
            border_color=COLORS.border,
            font=theme.font(Type.small, "normal"),
            **kwargs,
        )

    def set_text(self, text: str) -> None:
        self.configure(text=shape(text))


class ReadOnlyPath(ctk.CTkEntry):
    """نمایش مسیر انتخاب‌شده؛ غیرقابل ویرایش.

    متن روی صفحه کوتاه و شکل‌دهی می‌شود تا مسیرهای فارسی درست دیده شوند؛
    مسیر واقعی همیشه از خاصیت :attr:`value` خوانده می‌شود، نه از ``get()``.
    """

    def __init__(self, master, placeholder: str) -> None:
        self._value = ""
        super().__init__(
            master,
            height=Size.field_height,
            corner_radius=Radius.sm,
            fg_color=COLORS.inset,
            border_color=COLORS.border,
            border_width=1,
            text_color=COLORS.text,
            placeholder_text=shape(placeholder),
            placeholder_text_color=COLORS.faint,
            font=theme.font(Type.small),
            justify="right",
        )
        self._readonly()

    def _readonly(self) -> None:
        # به جای state="disabled" که متن را محو می‌کند، ویرایش را با
        # بی‌اثر کردن کلیدها می‌گیریم تا کاربر بتواند مسیر را کپی کند.
        self.bind("<Key>", self._block_key)

    @staticmethod
    def _block_key(event):
        allowed = {"c", "a", "x", "Left", "Right", "Home", "End", "Tab"}
        if event.state & 0x4 or event.keysym in allowed:  # Ctrl+…
            return None
        return "break"

    def set_path(self, path: str) -> None:
        """مسیر کامل را نگه می‌دارد و نسخه کوتاه‌شده را نشان می‌دهد."""
        self._value = path or ""
        self.delete(0, "end")
        if self._value:
            self.insert(0, shape(path_for_display(self._value)))

    @property
    def value(self) -> str:
        """مسیر کامل و واقعی (نه متن کوتاه‌شده روی صفحه)."""
        return self._value


class Select(ctk.CTkOptionMenu):
    """منوی کشویی راست‌چین با نگاشت «متن نمایشی → مقدار واقعی»."""

    def __init__(
        self,
        master,
        placeholder: str = "",
        command: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        self._display_to_value: dict[str, str] = {}
        self._callback = command
        self._placeholder = shape(placeholder)
        self._variable = ctk.StringVar(value=self._placeholder)

        super().__init__(
            master,
            variable=self._variable,
            values=[self._placeholder],
            command=self._on_change,
            height=Size.field_height,
            corner_radius=Radius.sm,
            fg_color=COLORS.inset,
            button_color=COLORS.inset,
            button_hover_color=COLORS.hover,
            text_color=COLORS.text,
            dropdown_fg_color=COLORS.surface,
            dropdown_hover_color=COLORS.hover,
            dropdown_text_color=COLORS.text,
            font=theme.font(Type.small),
            dropdown_font=theme.font(Type.small),
            anchor="e",
            dynamic_resizing=False,
            **kwargs,
        )
        self.configure(state="disabled")

    def _on_change(self, display: str) -> None:
        if self._callback and display in self._display_to_value:
            self._callback(self._display_to_value[display])

    def set_options(
        self, options: Sequence[tuple[str, str]], selected: str | None = None
    ) -> None:
        """گزینه‌ها را جایگزین می‌کند.

        Args:
            options: دنباله‌ای از ``(متن نمایشی، مقدار واقعی)``.
            selected: مقدار واقعی که باید انتخاب شود.
        """
        if not options:
            self.clear()
            return

        self._display_to_value = {shape(label): value for label, value in options}
        displays = list(self._display_to_value)
        self.configure(values=displays, state="normal")

        target = displays[0]
        if selected is not None:
            for display, value in self._display_to_value.items():
                if value == selected:
                    target = display
                    break
        self._variable.set(target)

    @property
    def has_options(self) -> bool:
        """آیا گزینه واقعی برای انتخاب وجود دارد؟"""
        return bool(self._display_to_value)

    def clear(self) -> None:
        self._display_to_value = {}
        self.configure(values=[self._placeholder], state="disabled")
        self._variable.set(self._placeholder)

    @property
    def value(self) -> str | None:
        """مقدار واقعی گزینه انتخاب‌شده (نه متن نمایشی)."""
        return self._display_to_value.get(self._variable.get())


class Choice(ctk.CTkSegmentedButton):
    """انتخابگر تک‌گزینه‌ای افقی، با ترتیب راست‌به‌چپ."""

    def __init__(
        self,
        master,
        options: Sequence[tuple[str, str]],
        default: str,
        command: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        # ترتیب معکوس تا اولین گزینه در سمت راست بنشیند
        self._display_to_value = {shape(label): value for label, value in options}
        self._callback = command
        displays = list(reversed(list(self._display_to_value)))

        super().__init__(
            master,
            values=displays,
            command=self._on_change,
            height=Size.control_height,
            corner_radius=Radius.sm,
            fg_color=COLORS.inset,
            selected_color=COLORS.surface,
            selected_hover_color=COLORS.surface,
            unselected_color=COLORS.inset,
            unselected_hover_color=COLORS.hover,
            text_color=COLORS.text,
            border_width=2,
            font=theme.font(Type.small),
            **kwargs,
        )
        self.select(default)

    def _on_change(self, display: str) -> None:
        if self._callback and display in self._display_to_value:
            self._callback(self._display_to_value[display])

    def select(self, value: str) -> None:
        for display, mapped in self._display_to_value.items():
            if mapped == value:
                self.set(display)
                return

    @property
    def value(self) -> str | None:
        return self._display_to_value.get(self.get())


class Check(ctk.CTkFrame):
    """چک‌باکس راست‌چین: مربع در سمت راست و متن در سمت چپ آن.

    ``CTkCheckBox`` جای مربع را قابل تنظیم نمی‌کند، برای همین اینجا از یک
    ترکیب ساده استفاده شده تا چیدمان واقعاً راست‌چین باشد.
    """

    def __init__(
        self,
        master,
        text: str,
        *,
        checked: bool = True,
        command: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color=COLORS.clear)
        self._checked = checked
        self._callback = command

        self._box = ctk.CTkButton(
            self,
            text="✓" if checked else "",
            width=20,
            height=20,
            corner_radius=6,
            border_width=1,
            border_color=COLORS.accent if checked else COLORS.border,
            fg_color=COLORS.accent if checked else COLORS.surface,
            hover_color=COLORS.accent_hover if checked else COLORS.hover,
            text_color="#FFFFFF",
            font=theme.font(Type.caption, "bold"),
            command=self.toggle,
        )
        self._box.pack(side="right")

        self._label = RTLLabel(self, text, size=Type.small, color=COLORS.muted)
        self._label.pack(side="right", padx=(0, Space.sm))
        self._label.bind("<Button-1>", lambda _event: self.toggle())

    def toggle(self) -> None:
        self.set(not self._checked)
        if self._callback:
            self._callback(self._checked)

    def set(self, checked: bool) -> None:
        self._checked = checked
        self._box.configure(
            text="✓" if checked else "",
            fg_color=COLORS.accent if checked else COLORS.surface,
            border_color=COLORS.accent if checked else COLORS.border,
            hover_color=COLORS.accent_hover if checked else COLORS.hover,
        )

    @property
    def value(self) -> bool:
        return self._checked


class StatusLine(ctk.CTkFrame):
    """نوار وضعیت پایین صفحه: نوار پیشرفت به همراه یک پیام کوتاه."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color=COLORS.clear)

        self._bar = ctk.CTkProgressBar(
            self,
            height=4,
            corner_radius=Radius.pill,
            fg_color=COLORS.inset,
            progress_color=COLORS.accent,
        )
        self._bar.set(0)

        self._message = RTLLabel(self, "", size=Type.caption, color=COLORS.muted)
        self._message.pack(anchor="e", fill="x")

    def show_progress(self, fraction: float) -> None:
        if not self._bar.winfo_ismapped():
            self._bar.pack(fill="x", pady=(Space.sm, 0))
        self._bar.set(max(0.0, min(1.0, fraction)))

    def hide_progress(self) -> None:
        if self._bar.winfo_ismapped():
            self._bar.pack_forget()
        self._bar.set(0)

    def info(self, text: str) -> None:
        self._message.configure(text_color=COLORS.muted)
        self._message.set_text(text)

    def success(self, text: str) -> None:
        self._message.configure(text_color=COLORS.success)
        self._message.set_text(text)

    def error(self, text: str) -> None:
        self._message.configure(text_color=COLORS.danger)
        self._message.set_text(text)

    def clear(self) -> None:
        self._message.set_text("")
        self.hide_progress()


class Divider(ctk.CTkFrame):
    """خط جداکننده مویی."""

    def __init__(self, master) -> None:
        # ارتفاع ۱ پیکسل روی بوم CustomTkinter اصلاً رسم نمی‌شود؛
        # کمترین مقداری که یک خط مویی می‌دهد ۲ است.
        super().__init__(master, height=2, fg_color=COLORS.border, corner_radius=0)


__all__ = [
    "Card",
    "Check",
    "Choice",
    "Divider",
    "GhostButton",
    "PrimaryButton",
    "RTLLabel",
    "ReadOnlyPath",
    "Select",
    "StatusLine",
    "StepHeader",
]
