"""شناسنامه برنامه؛ تنها جایی که نام و نسخه تعریف می‌شود.

هم رابط کاربری و هم اسکریپت‌های بیلد از همین مقادیر استفاده می‌کنند تا
نسخه در چند جا از هم جدا نیفتد.
"""

APP_NAME = "جداساز اکسل"
APP_NAME_EN = "Excel Separator"
APP_VERSION = "2.0.0"
APP_TAGLINE = "فایل اکسل را بر اساس یک ستون، در چند ثانیه به فایل‌های جدا تبدیل کنید."
APP_URL = "https://github.com/mmhdih/ExelSeprator"
APP_PUBLISHER = "mmhdih"

#: امضایی که در پایین پنجره برنامه دیده می‌شود
APP_CREDIT = "Powered By Haj Mehdi"

#: نسخه به صورت چهارتایی، برای اطلاعات نسخه فایل exe در ویندوز
VERSION_TUPLE = tuple(int(part) for part in APP_VERSION.split(".")) + (0,)

__all__ = [
    "APP_CREDIT",
    "APP_NAME",
    "APP_NAME_EN",
    "APP_PUBLISHER",
    "APP_TAGLINE",
    "APP_URL",
    "APP_VERSION",
    "VERSION_TUPLE",
]
