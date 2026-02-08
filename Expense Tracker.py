import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# ---------------- DATABASE ----------------
conn = sqlite3.connect("expenses.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    description TEXT,
    amount REAL
)
""")
conn.commit()

# ---------------- MAIN WINDOW ----------------
root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("900x600")

MONTHLY_BUDGET = 10000

# ---------------- VARIABLES ----------------
date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
category_var = tk.StringVar()
desc_var = tk.StringVar()
amount_var = tk.StringVar()
total_var = tk.StringVar()
selected_id = None  # hidden database ID

# ---------------- FUNCTIONS ----------------
def update_total():
    cur.execute("SELECT SUM(amount) FROM expenses")
    total = cur.fetchone()[0]
    total_var.set(f"Total Expenses: ₹{total if total else 0}")

def load_data():
    for row in tree.get_children():
        tree.delete(row)

    cur.execute("SELECT * FROM expenses")
    rows = cur.fetchall()

    for i, row in enumerate(rows, start=1):
        # row = (id, date, category, description, amount)
        tree.insert(
            "",
            tk.END,
            values=(i, row[1], row[2], row[3], row[4]),
            tags=(row[0],)  # store ID secretly
        )

    update_total()

def add_expense():
    if not category_var.get() or not amount_var.get():
        messagebox.showerror("Error", "Please fill all fields")
        return

    try:
        amount = float(amount_var.get())
    except ValueError:
        messagebox.showerror("Error", "Amount must be numeric")
        return

    cur.execute(
        "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
        (date_var.get(), category_var.get(), desc_var.get(), amount)
    )
    conn.commit()
    clear_fields()
    load_data()
    check_budget()

def select_expense(event):
    global selected_id
    selected = tree.selection()
    if not selected:
        return

    selected_id = tree.item(selected[0], "tags")[0]  # hidden ID
    values = tree.item(selected[0])["values"]

    date_var.set(values[1])
    category_var.set(values[2])
    desc_var.set(values[3])
    amount_var.set(values[4])

def update_expense():
    if not selected_id:
        messagebox.showwarning("Warning", "Select an expense to update")
        return

    cur.execute("""
        UPDATE expenses
        SET date=?, category=?, description=?, amount=?
        WHERE id=?
    """, (
        date_var.get(),
        category_var.get(),
        desc_var.get(),
        float(amount_var.get()),
        selected_id
    ))
    conn.commit()
    clear_fields()
    load_data()

def delete_expense():
    if not selected_id:
        messagebox.showwarning("Warning", "Select an expense to delete")
        return

    cur.execute("DELETE FROM expenses WHERE id=?", (selected_id,))
    conn.commit()
    clear_fields()
    load_data()

def clear_fields():
    global selected_id
    selected_id = None
    date_var.set(datetime.now().strftime("%Y-%m-%d"))
    category_var.set("")
    desc_var.set("")
    amount_var.set("")

def show_chart():
    cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cur.fetchall()

    if not data:
        messagebox.showinfo("Info", "No data to display")
        return

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct="%1.1f%%")
    plt.title("Category-wise Spending")
    plt.show()

def export_csv():
    cur.execute("SELECT date, category, description, amount FROM expenses")
    rows = cur.fetchall()

    with open("expenses.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Category", "Description", "Amount"])
        writer.writerows(rows)

    messagebox.showinfo("Success", "Data exported to expenses.csv")

def check_budget():
    cur.execute("SELECT SUM(amount) FROM expenses")
    total = cur.fetchone()[0]

    if total and total > MONTHLY_BUDGET:
        messagebox.showwarning(
            "Budget Alert",
            f"Monthly Budget Exceeded!\nTotal: ₹{total}"
        )

# ---------------- UI ----------------
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="Date").grid(row=0, column=0)
tk.Entry(input_frame, textvariable=date_var).grid(row=0, column=1)

tk.Label(input_frame, text="Category").grid(row=0, column=2)
ttk.Combobox(
    input_frame,
    textvariable=category_var,
    values=["Food", "Travel", "Rent", "Shopping", "Bills", "Others"],
    width=15
).grid(row=0, column=3)

tk.Label(input_frame, text="Description").grid(row=1, column=0)
tk.Entry(input_frame, textvariable=desc_var, width=30).grid(row=1, column=1, columnspan=2)

tk.Label(input_frame, text="Amount").grid(row=1, column=3)
tk.Entry(input_frame, textvariable=amount_var).grid(row=1, column=4)

# ---------------- BUTTONS ----------------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Add", width=15, command=add_expense).grid(row=0, column=0)
tk.Button(btn_frame, text="Update", width=15, command=update_expense).grid(row=0, column=1)
tk.Button(btn_frame, text="Delete", width=15, command=delete_expense).grid(row=0, column=2)
tk.Button(btn_frame, text="Chart", width=15, command=show_chart).grid(row=0, column=3)
tk.Button(btn_frame, text="Export CSV", width=15, command=export_csv).grid(row=0, column=4)

# ---------------- TOTAL ----------------
tk.Label(
    root,
    textvariable=total_var,
    font=("Arial", 13, "bold"),
    fg="green"
).pack(pady=5)

# ---------------- TABLE (Serial Number instead of ID) ----------------
columns = ("S.No", "Date", "Category", "Description", "Amount")
tree = ttk.Treeview(root, columns=columns, show="headings")

tree.heading("S.No", text="S.No")
tree.column("S.No", width=60, anchor="center")

for col in ("Date", "Category", "Description", "Amount"):
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<<TreeviewSelect>>", select_expense)

# ---------------- START ----------------
load_data()
root.mainloop()
