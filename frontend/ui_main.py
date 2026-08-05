import customtkinter as ctk
from tkinter import filedialog, messagebox
from backend.excel_processor import ExcelProcessor

# تنظیمات تم رابط کاربری
ctk.set_appearance_mode("System")  # پشتیبانی از دارک‌مود/لایت‌مود سیستم
ctk.set_default_color_theme("blue")

class AppUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.processor = ExcelProcessor()
        
        self.title("Excel Separator | مقسم هوشمند اکسل")
        self.geometry("550x550")
        self.resizable(False, False)
        
        # عنوان برنامه
        self.title_label = ctk.CTkLabel(self, text="📊 Excel Separator", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=25)
        
        # بخش انتخاب فایل
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=10, padx=20, fill="x")
        
        self.file_label = ctk.CTkLabel(self.file_frame, text="📂 مسیر فایل اکسل:")
        self.file_label.pack(pady=(10,0))
        
        self.file_entry = ctk.CTkEntry(self.file_frame, width=350, placeholder_text="فایلی انتخاب نشده...")
        self.file_entry.pack(side="left", padx=15, pady=15)
        
        self.file_btn = ctk.CTkButton(self.file_frame, text="انتخاب فایل", width=100, command=self.select_file)
        self.file_btn.pack(side="right", padx=15, pady=15)
        
        # بخش انتخاب مسیر خروجی
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.pack(pady=10, padx=20, fill="x")
        
        self.output_label = ctk.CTkLabel(self.output_frame, text="📁 مسیر ذخیره فایل‌ها:")
        self.output_label.pack(pady=(10,0))
        
        self.output_entry = ctk.CTkEntry(self.output_frame, width=350, placeholder_text="مسیری انتخاب نشده...")
        self.output_entry.pack(side="left", padx=15, pady=15)
        
        self.output_btn = ctk.CTkButton(self.output_frame, text="انتخاب مسیر", width=100, command=self.select_output)
        self.output_btn.pack(side="right", padx=15, pady=15)
        
        # بخش انتخاب ستون (منوی کشویی)
        self.columns_label = ctk.CTkLabel(self, text="📊 انتخاب ستون برای جداسازی:")
        self.columns_label.pack(pady=(15,5))
        
        self.column_var = ctk.StringVar(value="ابتدا فایل را انتخاب کنید")
        self.column_menu = ctk.CTkOptionMenu(self, variable=self.column_var, values=["ابتدا فایل را انتخاب کنید"], width=300)
        self.column_menu.pack(pady=5)
        
        # دکمه اجرای نهایی
        self.process_btn = ctk.CTkButton(self, text="🚀 شروع پردازش", fg_color="#28a745", hover_color="#218838", 
                                         font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self.process_file)
        self.process_btn.pack(pady=35)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_entry.delete(0, 'end')
            self.file_entry.insert(0, file_path)
            
            # اتصال به بک‌اند
            columns, error = self.processor.load_excel(file_path)
            
            if error:
                messagebox.showerror("خطا", f"خطا در خواندن فایل:\n{error}")
            else:
                self.column_menu.configure(values=columns)
                if columns:
                    self.column_var.set(columns[0])

    def select_output(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, folder_path)

    def process_file(self):
        column_name = self.column_var.get()
        output_folder = self.output_entry.get()
        
        # اعتبارسنجی‌ها
        if self.processor.df is None:
            messagebox.showwarning("هشدار", "لطفاً ابتدا فایل اکسل را انتخاب کنید.")
            return
        if column_name == "ابتدا فایل را انتخاب کنید" or not column_name:
            messagebox.showwarning("هشدار", "لطفاً یک ستون را انتخاب کنید.")
            return
        if not output_folder:
            messagebox.showwarning("هشدار", "لطفاً مسیر ذخیره را انتخاب کنید.")
            return
        
        # تغییر ظاهر دکمه هنگام پردازش
        self.process_btn.configure(text="در حال پردازش ⏳", state="disabled")
        self.update()
        
        # اجرای بک‌اند
        success, message = self.processor.process_and_split(column_name, output_folder)
        
        # بازگرداندن دکمه به حالت عادی
        self.process_btn.configure(text="🚀 شروع پردازش", state="normal")
        
        if success:
            messagebox.showinfo("عملیات موفق", message)
        else:
            messagebox.showerror("خطا", message)
