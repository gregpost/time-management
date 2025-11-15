import tkinter as tk

def save_task():
    task = task_entry.get()
    subtask = subtask_entry.get()
    with open("tasks.txt", "a", encoding="utf-8") as f:
        f.write(f"{task} | {subtask}\n")
    task_entry.delete(0, tk.END)
    subtask_entry.delete(0, tk.END)

root = tk.Tk()
root.title("Задачи")
root.geometry("300x150")

tk.Label(root, text="Задача:").pack(pady=5)
task_entry = tk.Entry(root, width=30)
task_entry.pack()

tk.Label(root, text="Подзадача:").pack(pady=5)
subtask_entry = tk.Entry(root, width=30)
subtask_entry.pack()

tk.Button(root, text="Сохранить", command=save_task).pack(pady=10)

root.mainloop()
