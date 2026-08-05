import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox

df = None

def select_file():
    global df
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)
        
        try:
            df = pd.read_excel(file_path)
            show_columns(df)
        except Exception as e:
            messagebox.showerror("Error", f"خطا در خواندن فایل:\n{e}")

def select_output():
    folder_path = filedialog.askdirectory()
    
    if folder_path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, folder_path)

def show_columns(df):
    column_listbox.delete(0, tk.END)
    
    for i, col in enumerate(df.columns):
        column_listbox.insert(tk.END, f"{i+1} - {col}")

def process_file():
    global df
    
    if df is None:
        messagebox.showwarning("Warning", "ابتدا فایل را انتخاب کن")
        return
    
    try:
        selected_index = column_listbox.curselection()[0]
        column_name = df.columns[selected_index]
    except:
        messagebox.showwarning("Warning", "یک ستون انتخاب کن")
        return
    
    output_folder = output_entry.get()
    
    if not output_folder:
        messagebox.showwarning("Warning", "مسیر خروجی را انتخاب کن")
        return
    
    os.makedirs(output_folder, exist_ok=True)
    
    unique_values = df[column_name].dropna().unique()
    
    for value in unique_values:
        filtered_df = df[df[column_name] == value]
        safe_value = str(value).replace(" ", "_").replace("/", "_")
        
        output_path = os.path.join(output_folder, f"{safe_value}.xlsx")
        filtered_df.to_excel(output_path, index=False)
    
    messagebox.showinfo("Done", "✅ فایل‌ها ساخته شدند")

# UI
root = tk.Tk()
root.title("Excel Splitter")
root.geometry("500x500")

tk.Label(root, text="📂 فایل اکسل:").pack()
file_entry = tk.Entry(root, width=50)
file_entry.pack()
tk.Button(root, text="انتخاب فایل", command=select_file).pack(pady=5)

tk.Label(root, text="📁 مسیر خروجی:").pack()
output_entry = tk.Entry(root, width=50)
output_entry.pack()
tk.Button(root, text="انتخاب مسیر", command=select_output).pack(pady=5)

tk.Label(root, text="📊 ستون‌ها:").pack()

column_listbox = tk.Listbox(root, width=60, height=10)
column_listbox.pack(pady=10)

tk.Button(root, text="🚀 اجرا", command=process_file, bg="green", fg="white").pack(pady=20)

root.mainloop()