"""
Scheduler module for automatic reminders and penalties
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import date, timedelta
from pmb_system.database import SessionLocal, engine
from .models import Billing
import logging
from krs_system.models import KRS


def calculate_penalty(total_amount: int, weeks_late: int) -> int:
    """
    Calculate penalty based on weeks late
    - 1% of total_amount per week of delay
    """
    penalty_rate = 0.01  # 1% per week
    penalty = int(total_amount * penalty_rate * weeks_late)
    return penalty


def process_billing_reminders_and_penalties():
    db = SessionLocal()
    try:
        today = date.today()

        billing_records = db.query(Billing).filter(
            Billing.due_date < today,
            Billing.status != 'paid'
        ).all()

        print(f"[SCHEDULER] Found {len(billing_records)} overdue billing(s)")

        for billing in billing_records:
            days_late = (today - billing.due_date).days
            weeks_late = max(1, days_late // 7)

            penalty = calculate_penalty(billing.total_amount, weeks_late)

            billing.total_amount += penalty
            billing.status = 'overdue'

            print(
                f"[REMINDER] NIM {billing.nim} | Semester {billing.semester} | "
                f"Late {days_late} days | Penalty {penalty}"
            )

            # BLOCK KRS
            krs_list = db.query(KRS).filter(
                KRS.nim == billing.nim,
                KRS.semester == billing.semester
            ).all()

            for krs in krs_list:
                if krs.status != "BLOCKED":
                    krs.status = "BLOCKED"
                    print(
                        f"[KRS BLOCKED] NIM {krs.nim} | Semester {krs.semester}"
                    )

        db.commit()
        print("[SCHEDULER] Billing reminder & penalty process completed")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Scheduler failed: {e}")
        raise e

    finally:
        db.close()




def start_scheduler():
    """
    Start the APScheduler with the billing reminder/penalty job
    """
    scheduler = BackgroundScheduler()
    
    # Add the job to run once per day at midnight
    scheduler.add_job(
        func=process_billing_reminders_and_penalties,
        #trigger=CronTrigger.from_crontab("*/1 * * * *"),  # Every 1 minute
        trigger=CronTrigger.from_crontab("0 0 * * *"),  # Every day at midnight
        id='billing_reminder_penalty_job',
        name='Process billing reminders and penalties',
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started for billing reminders and penalties")
    
    return scheduler


def stop_scheduler(scheduler):
    """
    Stop the scheduler gracefully
    """
    try:
        scheduler.shutdown()
        print("Scheduler stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")