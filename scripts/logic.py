"""
logic.py — вспомогательная логика: обработка расписания, активных задач и правил блокировки окон.
"""

import system

def parse_time(value):
    if isinstance(value, int):
        return value, 0
    h, m = (int(value.split(":")[0]), int(value.split(":")[1])) if ":" in value else (int(value), 0)
    return h, m

def in_time_range(start, end, now):
    start_h, start_m = parse_time(start)
    end_h, end_m = parse_time(end)
    start_minutes = start_h*60 + start_m
    end_minutes = end_h*60 + end_m
    now_minutes = now.hour*60 + now.minute
    return start_minutes <= now_minutes <= end_minutes

def get_current_day_time(now):
    return now.strftime("%A").lower(), now

def get_current_active_tasks(week_plan, now):
    day, _ = get_current_day_time(now)
    day_tasks = week_plan.get(day, {})
    return [
        task_name.lower()
        for task_name, hours in day_tasks.items()
        if isinstance(hours, list) and len(hours) == 2 and in_time_range(hours[0], hours[1], now)
    ]

def get_all_tasks(week_plan):
    return [t.lower() for day_tasks in week_plan.values() for t in day_tasks.keys()]

def diff_plans(old_plan, new_plan):
    changes = []
    for day, tasks in new_plan.items():
        old_tasks = old_plan.get(day, {})
        for task_name, hours in tasks.items():
            if task_name not in old_tasks or old_tasks[task_name] != hours:
                changes.append(f"{day}: {task_name} -> {hours}")
    return changes

def update_plan():
    system.update_local_repo()
    week_plan, cfg = system.load_week_plan()
    print("[LOG] Plan updated.")
    return week_plan, cfg

def handle_active_window(week_plan, cfg, now):
    try:
        title, hwnd = system.get_active_window_title()
        if not title or not hwnd:
            return

        title_lower = title.lower()
        active_tasks = get_current_active_tasks(week_plan, now)
        if any(task.lower() in title_lower for task in active_tasks):
            return

        for pattern in cfg["black"]["patterns"]:
            if pattern in title_lower:
                system.minimize_with_delay(hwnd, cfg["black"]["delay"], "BLACKLIST", pattern, title)
                return
    except Exception as e:
        print(f"[ERROR] handle_active_window: {e}")
