from datetime import datetime, timedelta
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.maintenance import VehicleMaintenance
from app.models.notification import Notification

@celery_app.task
def check_upcoming_maintenance():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        warning_date = now + timedelta(days=7)
        
        # Find maintenance records where next_service_date is <= 7 days away or overdue
        # and where an alert has not been sent yet
        records = db.query(VehicleMaintenance).filter(
            VehicleMaintenance.next_service_date != None,
            VehicleMaintenance.next_service_date <= warning_date,
            VehicleMaintenance.status != "Completed",
            VehicleMaintenance.alert_sent == False
        ).all()
        
        for record in records:
            # Determine if overdue or just upcoming
            if record.next_service_date < now:
                message = f"ALERT: Maintenance '{record.maintenance_type}' for vehicle {record.vehicle_id} is OVERDUE."
            else:
                message = f"Reminder: Maintenance '{record.maintenance_type}' for vehicle {record.vehicle_id} is upcoming on {record.next_service_date.strftime('%Y-%m-%d')}."
            
            print(f"========================================\n{message}\n========================================")
            
            # Record notification (Assuming Admin or Fleet Manager receives this, we can set user_id=None or to a specific system user)
            # Based on requirements, we just need to log it and optionally save a notification
            notification = Notification(
                user_id=None, # System wide alert
                message=message
            )
            db.add(notification)
            
            # Mark alert as sent
            record.alert_sent = True
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error checking maintenance: {e}")
    finally:
        db.close()
