import time
from apscheduler.schedulers.background import BackgroundScheduler


def task():
    print("Task is running!")


scheduler = BackgroundScheduler()
scheduler.add_job(task, 'interval', hours=2)
scheduler.start()

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
