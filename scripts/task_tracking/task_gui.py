import tkinter as tk
from tkinter import ttk

def save_task():
    task = task_combobox.get()
    subtask = subtask_combobox.get()
    with open("tasks.txt", "a", encoding="utf-8") as f:
        f.write(f"{task} | {subtask}\n")
    
    # Добавляем новые варианты в списки
    if task not in tasks:
        task_combobox['values'] = (*task_combobox['values'], task)
    if subtask not in subtasks:
        subtask_combobox['values'] = (*subtask_combobox['values'], subtask)
    
    task_combobox.set('')
    subtask_combobox.set('')

# Загружаем предыдущие задачи
try:
    with open("tasks.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        tasks = sorted(set(line.split('|')[0].strip() for line in lines))
        subtasks = sorted(set(line.split('|')[1].strip() for line in lines))
except:
    tasks, subtasks = [], []

root = tk.Tk()
root.title("Задачи")
root.geometry("300x150")

tk.Label(root, text="Задача:").pack(pady=5)
task_combobox = ttk.Combobox(root, width=27, values=tasks)
task_combobox.pack()

tk.Label(root, text="Подзадача:").pack(pady=5)
subtask_combobox = ttk.Combobox(root, width=27, values=subtasks)
subtask_combobox.pack()

tk.Button(root, text="Сохранить", command=save_task).pack(pady=10)

root.mainloop()
