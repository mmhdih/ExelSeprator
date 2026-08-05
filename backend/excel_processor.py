import pandas as pd
import os

class ExcelProcessor:
    def __init__(self):
        self.df = None

    def load_excel(self, file_path):
        """خواندن فایل اکسل و برگرداندن لیست ستون‌ها"""
        try:
            self.df = pd.read_excel(file_path)
            return self.df.columns.tolist(), None
        except Exception as e:
            return None, str(e)

    def process_and_split(self, column_name, output_folder):
        """جداسازی فایل بر اساس ستون انتخابی"""
        if self.df is None:
            return False, "هیچ فایلی بارگذاری نشده است."
        
        try:
            os.makedirs(output_folder, exist_ok=True)
            unique_values = self.df[column_name].dropna().unique()
            
            for value in unique_values:
                filtered_df = self.df[self.df[column_name] == value]
                # تمیز کردن نام فایل برای جلوگیری از خطاهای ویندوز
                safe_value = str(value).replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "")
                output_path = os.path.join(output_folder, f"{safe_value}.xlsx")
                
                filtered_df.to_excel(output_path, index=False)
                
            return True, "فایل‌ها با موفقیت ساخته و ذخیره شدند ✅"
        except Exception as e:
            return False, f"خطا در پردازش: {str(e)}"
