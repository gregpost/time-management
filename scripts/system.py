"""
system.py — низкоуровневые функции для работы с окнами, процессами и планом
(чтение из YAML, свертывание окон, git-обновления).
"""

import subprocess
import os
import yaml
import psutil
import ctypes
import time
from datetime import datetime
import config
import logic

user32 = ctypes.windll.user32

# ----------------------------
# WINDOW HANDLING
# ----------------------------
def get_active_window_title():
    try:
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length+1)
        user32.GetWindowTextW(hwnd, buff, length+1)
        return buff.value, hwnd
    except Exception as e:
        print(f"[ERROR] get_active_window_title: {e}")
        return None, None

def minimize_window(hwnd):
    try:
        if hwnd:
            SW_MINIMIZE = 6
            user32.ShowWindow(hwnd, SW_MINIMIZE)
    except Exception as e:
        print(f"[ERROR] minimize_window: {e}")

def is_window_minimized(hwnd):
    try:
        return bool(user32.IsIconic(hwnd))
    except Exception:
        return False

def minimize_with_delay(hwnd, delay, label, pattern, title):
    try:
        if delay > 0:
            print(f"[{label}] Waiting {delay}s before minimizing (contains '{pattern}'): {title}")
            time.sleep(delay)
        minimize_window(hwnd)
        print(f"[{label}] Minimized window (contains '{pattern}'): {title}")
    except Exception as e:
        print(f"[ERROR] minimize_with_delay[{label}]: {e}")

# ----------------------------
# GIT REPO HANDLING
# ----------------------------
def run_git_command(args, **kwargs):
    return subprocess.run(
        ["git"] + args,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs
    )

def update_local_repo(user=config.GITHUB_USER, repo=config.GITHUB_REPO, path=config.LOCAL_REPO_PATH):
    repo_url = f"https://github.com/{user}/{repo}.git"
    if not os.path.exists(path):
        print(f"[LOG] Cloning repository {repo_url} into {path}...")
        run_git_command(["clone", repo_url, path])
    else:
        print(f"[LOG] Pulling updates in repository {path}...")
        run_git_command(["-C", path, "pull"])

# ----------------------------
# PLAN LOADING
# ----------------------------
def load_week_plan(path=config.LOCAL_REPO_PATH):
    plan_file = os.path.join(path, config.PLAN_FILE_NAME)
    if not os.path.exists(plan_file):
        print(f"[WARN] Plan file not found: {plan_file}")
        return {}, {}

    with open(plan_file, "r", encoding="utf-8") as f:
        full_data = yaml.safe_load(f) or {}

    def parse_section(section, default_delay=0.0):
        if isinstance(section, dict):
            patterns = [str(i).lower().strip() for i in section.get("patterns", [])]
            delay = float(section.get("delay", default_delay))
            timing = section.get("timing")
            return patterns, delay, timing
        elif isinstance(section, list):
            return [str(i).lower().strip() for i in section], default_delay, None
        return [], default_delay, None

    deprecated_patterns, deprecated_delay, _ = parse_section(full_data.get("deprecated_windows", []))
    black_patterns, black_delay, _ = parse_section(full_data.get("black_list", []))

    sometimes_patterns, sometimes_delay, sometimes_timing = parse_section(full_data.get("sometimes", {}))
    if sometimes_timing is None:
        sometimes_timing = [0, 8, 9, 9]

    often_patterns, often_delay, often_timing = parse_section(full_data.get("often", {}))
    if often_timing is None:
        often_timing = [0, 4, 5, 9]

    hourly_patterns, hourly_delay, _ = parse_section(full_data.get("hourly", []))

    week_plan = {}
    for key, value in full_data.items():
        if key.lower() not in ("deprecated_windows", "black_list", "sometimes", "often", "hourly") and isinstance(value, dict):
            week_plan[key.lower()] = value

    cfg = {
        "deprecated": {"patterns": deprecated_patterns, "delay": deprecated_delay},
        "black": {"patterns": black_patterns, "delay": black_delay},
        "sometimes": {"patterns": sometimes_patterns, "timing": sometimes_timing, "delay": sometimes_delay},
        "often": {"patterns": often_patterns, "timing": often_timing, "delay": often_delay},
        "hourly": {"patterns": hourly_patterns, "delay": hourly_delay},
    }
    return week_plan, cfg

# ----------------------------
# DEPRECATED WINDOW CHECK
# ----------------------------
def check_and_minimize_deprecated_windows(cfg, week_plan, now):
    try:
        patterns, delay = cfg["patterns"], cfg["delay"]
        if not patterns:
            return False

        title, hwnd = get_active_window_title()
        if not title or not hwnd:
            return False

        title_lower = title.lower()
        active_tasks = logic.get_current_active_tasks(week_plan, now)
        if any(task.lower() in title_lower for task in active_tasks):
            return False

        for deprecated_name in patterns:
            if deprecated_name in title_lower:
                minimize_with_delay(hwnd, delay, "DEPRECATED", deprecated_name, title)
                return True
        return False
    except Exception as e:
        print(f"[ERROR] check_and_minimize_deprecated_windows: {e}")
        return False

# ----------------------------
# GENERIC TIMED CHECK
# ----------------------------
def check_and_minimize_timed_windows(patterns, timing, delay, now, label="TIMED"):
    try:
        if not patterns:
            return False

        minute = now.minute % 10
        block_start, block_end, allow_start, allow_end = timing
        is_block = block_start <= minute <= block_end
        is_allow = allow_start <= minute <= allow_end

        title, hwnd = get_active_window_title()
        if not title or not hwnd:
            return False
        title_lower = title.lower()

        for pattern in patterns:
            if pattern in title_lower:
                if is_block:
                    if is_window_minimized(hwnd):
                        return True
                    minimize_with_delay(hwnd, delay, label, pattern, title)
                    return True
                elif is_allow:
                    print(f"[{label}] Allowed (contains '{pattern}'): {title} (minute={now.minute})")
                    return False
        return False
    except Exception as e:
        print(f"[ERROR] check_and_minimize_timed_windows[{label}]: {e}")
        return False

# ----------------------------
# HOURLY CHECK
# ----------------------------
def check_and_minimize_hourly_windows(cfg, now, label="HOURLY"):
    try:
        patterns, delay = cfg["patterns"], cfg["delay"]
        if not patterns:
            return False

        title, hwnd = get_active_window_title()
        if not title or not hwnd:
            return False
        title_lower = title.lower()

        for pattern in patterns:
            if pattern in title_lower:
                if now.minute == 59:
                    print(f"[{label}] Allowed (59 minute) (contains '{pattern}'): {title}")
                    return False
                else:
                    if is_window_minimized(hwnd):
                        return True
                    minimize_with_delay(hwnd, delay, label, pattern, title)
                    return True
        return False
    except Exception as e:
        print(f"[ERROR] check_and_minimize_hourly_windows[{label}]: {e}")
        return False

# ----------------------------
# PROCESS MANAGEMENT
# ----------------------------
def ensure_processes_running(process_list=config.PROCESS_NAMES):
    for path in process_list:
        name = os.path.basename(path).lower()
        if not any(p.name().lower() == name for p in psutil.process_iter()):
            subprocess.Popen([path], creationflags=subprocess.CREATE_NO_WINDOW)
