from . import db
from datetime import datetime, timezone
from uuid import uuid4

class Analysis_dbs(db.Model):
    __tablename__ = "analysis_db"

    request_id = db.Column(db.String, primary_key=True)
    lab_id = db.Column(db.String, nullable=False)
    patient_id = db.Column(db.String, nullable=False)
    result = db.Column(db.String, nullable=False)
    urgent = db.Column(db.Boolean, nullable=False, default=False)
    start_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    image_path = db.Column(db.String, nullable=False)

