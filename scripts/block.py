"""
block.py — основной управляющий цикл приложения: запуск потоков блокировки окон и контроль за процессами.
"""

import system
import logic
import threading
import sys
import traceback

# ----------------------------
# GLOBAL EXCEPTION HANDLING
# ----------------------------
def global_exception_handler(exctype, value, tb):
    error_msg = f"Unhandled exception: {exctype.__name__}: {value}"
    print(f"[ERROR] {error_msg}")
    try:
        with open("timeblocker_error.log", "a", encoding="utf-8") as f:
            f.write(f"{system.datetime.now().isoformat()}\n")
            f.write(f"{error_msg}\n")
            traceback.print_exception(exctype, value, tb, file=f)
            f.write("\n" + "="*50 + "\n\n")
    except:
        pass
    if hasattr(sys, 'frozen'):
        return
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_handler

# ----------------------------
# THREAD EXCEPTION HANDLING
# ----------------------------
def thread_exception_handler(args):
    print(f"[ERROR] Thread exception: {args.exc_type.__name__}: {args.exc_value}")
    try:
        with open("timeblocker_error.log", "a", encoding="utf-8") as f:
            f.write(f"{system.datetime.now().isoformat()} - Thread Error\n")
            f.write(f"{args.exc_type.__name__}: {args.exc_value}\n")
            traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=f)
            f.write("\n" + "="*50 + "\n\n")
    except:
        pass

threading.excepthook = thread_exception_handler

# ----------------------------
# MAIN LOOP
# ----------------------------
def main_loop():
    week_plan, cfg = logic.update_plan()
    last_reload = system.time.time()
    window_check_counter = 0
    process_check_counter = 0

    # ----------------------------
    # THREAD FUNCTIONS
    # ----------------------------
    def deprecated_windows_loop():
        while True:
            now = system.datetime.now()
            system.check_and_minimize_deprecated_windows(cfg["deprecated"], week_plan, now)
            system.time.sleep(0.05)

    def sometimes_windows_loop():
        while True:
            now = system.datetime.now()
            system.check_and_minimize_timed_windows(
                cfg["sometimes"]["patterns"],
                cfg["sometimes"]["timing"],
                cfg["sometimes"]["delay"],
                now,
                "SOMETIMES",
            )
            system.time.sleep(0.08)

    def often_windows_loop():
        while True:
            now = system.datetime.now()
            system.check_and_minimize_timed_windows(
                cfg["often"]["patterns"],
                cfg["often"]["timing"],
                cfg["often"]["delay"],
                now,
                "OFTEN",
            )
            system.time.sleep(0.08)

    def hourly_windows_loop():
        while True:
            now = system.datetime.now()
            system.check_and_minimize_hourly_windows(cfg["hourly"], now, "HOURLY")
            system.time.sleep(0.1)

    # ----------------------------
    # START THREADS
    # ----------------------------
    threading.Thread(target=deprecated_windows_loop, daemon=True).start()
    threading.Thread(target=sometimes_windows_loop, daemon=True).start()
    threading.Thread(target=often_windows_loop, daemon=True).start()
    threading.Thread(target=hourly_windows_loop, daemon=True).start()

    # ----------------------------
    # MAIN LOOP
    # ----------------------------
    while True:
        try:
            now = system.datetime.now()

            if system.time.time() - last_reload >= system.config.PLAN_RELOAD_INTERVAL:
                week_plan, cfg = logic.update_plan()
                last_reload = system.time.time()

            if window_check_counter >= system.config.WINDOW_CHECK_INTERVAL:
                logic.handle_active_window(week_plan, cfg, now)
                window_check_counter = 0
            else:
                window_check_counter += 1

            if process_check_counter >= system.config.PROCESS_CHECK_INTERVAL:
                system.ensure_processes_running()
                process_check_counter = 0
            else:
                process_check_counter += 1

            system.time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Main loop: {e}")
            system.time.sleep(0.5)

# ----------------------------
# ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("[LOG] Application stopped by user")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        system.time.sleep(1)
