from ui.colors import GREEN, RED, WHITE, EKL, LINE
from core.settings_manager import load_settings

MAX_SAFE_WORKERS = 200


# Prompt user to set number of worker threads or use default from settings
def get_worker_count(config_state, render_callback):
    settings = load_settings()
    worker_cfg = settings.get("worker_settings", {})
    ask_workers = worker_cfg.get("ask_for_workers", True)
    def_workers = worker_cfg.get("default_workers", 30)
    max_workers = worker_cfg.get("max_safe_workers", MAX_SAFE_WORKERS)

    worker_count = def_workers

    if ask_workers:
        if render_callback:
            render_callback()
        while True:
            try:
                inp = input(f" {GREEN}[{RED}●{GREEN}] Threads (Max {max_workers}) {EKL} ").strip()
                if not inp:
                    worker_count = def_workers
                    break
                wc = int(inp)
                if 1 <= wc <= max_workers:
                    worker_count = wc
                    break
                print(f"{RED} Invalid! Enter between 1-{max_workers}")
            except ValueError:
                print(f"{RED} Invalid number!")
            except KeyboardInterrupt:
                raise

    config_state["workers"] = f"{worker_count} Threads"
    if render_callback:
        render_callback()
    return worker_count
