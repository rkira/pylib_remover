import tkinter as tk
from tkinter import messagebox, ttk
import pkg_resources
import subprocess
import threading
import os
import site

# ----- Cancel_Flag -----
cancel_flag = False

# ----- Packages to exclude(should NEVER uninstall) -----
EXCLUDED_PACKAGES = {
    "pip", "setuptools", "pywin32", "py", "wheel"
}

# Utility Functions

def get_installed_packages_with_sizes():
    package_list = []
    for dist in pkg_resources.working_set:
        pkg_name = dist.project_name
        # Exclude core/system packages
        if pkg_name.lower() in EXCLUDED_PACKAGES or pkg_name.lower().startswith("python"):
            continue
        pkg_path = os.path.join(dist.location, dist.project_name.replace("-", "_"))
        pkg_size = directory_size(pkg_path) if os.path.exists(pkg_path) else 0
        package_list.append((pkg_name, pkg_size))
    return sorted(package_list, key=lambda x: x[0].lower())

def directory_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except Exception:
                pass
    return total

def size_format(bytes_size):
    return f"{bytes_size / (1024 * 1024):.2f} MB"

# ---------------------
# Core Logic
# ---------------------

def uninstall_packages(selected, listbox):
    def run():
        global cancel_flag
        cancel_flag = False

        uninstalling_label.config(text="")
        progress_bar["maximum"] = len(selected)
        progress_bar["value"] = 0
        cancel_button.pack(pady=5)

        for i, (pkg, _) in enumerate(selected):
            if cancel_flag:
                uninstalling_label.config(text="Uninstallation Cancelled.")
                break

            uninstalling_label.config(text=f"Uninstalling: {pkg}")
            listbox.itemconfig(package_names.index(pkg), {'fg': 'gray'})

            try:
                subprocess.run(['pip', 'uninstall', '-y', pkg], check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                messagebox.showerror("Error", f"Failed to uninstall {pkg}")
                continue

            progress_bar["value"] = i + 1
            root.update_idletasks()

        if not cancel_flag:
            uninstalling_label.config(text="Done.")
            messagebox.showinfo("Finished", "Selected packages uninstalled.")

        cancel_button.pack_forget()
        refresh_list()

    threading.Thread(target=run).start()

def refresh_list():
    listbox.delete(0, tk.END)
    global package_list, package_names
    package_list = get_installed_packages_with_sizes()
    package_names = [pkg for pkg, _ in package_list]

    for pkg, size in package_list:
        listbox.insert(tk.END, f"{size_format(size):>10} | {pkg}")

    select_all_var.set(False)
    uninstalling_label.config(text="")
    progress_bar["value"] = 0

def on_uninstall():
    selected_indices = listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Warning", "No packages selected!")
        return

    selected = [package_list[i] for i in selected_indices]
    total_size = sum(size for _, size in selected)
    size_str = size_format(total_size)

    msg = f"Uninstall {len(selected)} package(s)?\nTotal size: {size_str}"
    if messagebox.askyesno("Confirm Uninstall", msg):
        uninstall_packages(selected, listbox)

def on_select_all():
    if select_all_var.get():
        listbox.select_set(0, tk.END)
    else:
        listbox.select_clear(0, tk.END)

def on_mouse_drag(event):
    index = listbox.nearest(event.y)
    listbox.selection_set(index)

def cancel_uninstall():
    global cancel_flag
    cancel_flag = True

# ---------------------
# GUI Setup
# ---------------------

root = tk.Tk()
root.title("Python Package Uninstaller")
root.geometry("600x600")

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

scrollbar = tk.Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = tk.Listbox(
    frame,
    selectmode=tk.EXTENDED,
    yscrollcommand=scrollbar.set,
    font=("Courier New", 10),
    activestyle='none'
)
listbox.pack(fill=tk.BOTH, expand=True)
scrollbar.config(command=listbox.yview)

listbox.bind("<B1-Motion>", on_mouse_drag)

select_all_var = tk.BooleanVar()
select_all_checkbox = tk.Checkbutton(root, text="Select All", variable=select_all_var, command=on_select_all)
select_all_checkbox.pack()

btn_uninstall = tk.Button(root, text="Uninstall Selected", command=on_uninstall, bg="#e74c3c", fg="white")
btn_uninstall.pack(pady=5)

# Progress Bar + Status Label
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=5)

uninstalling_label = tk.Label(root, text="", font=("Arial", 10))
uninstalling_label.pack()

cancel_button = tk.Button(root, text="Cancel", command=cancel_uninstall, bg="gray", fg="white")

# Initialize
package_list = []
package_names = []
refresh_list()

root.mainloop()
