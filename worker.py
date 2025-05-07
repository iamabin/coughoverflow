import os
import json
import base64
import tempfile
import subprocess
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import boto3
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

class Analysis_dbs(Base):
    __tablename__ = "analysis_db"

    request_id = Column(String, primary_key=True)
    lab_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    result = Column(String, nullable=False)
    urgent = Column(Boolean, nullable=False, default=False)
    start_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    image_path = Column(String, nullable=False)



QUEUE_URL = os.environ["SQS_QUEUE_URL"]
REGION = os.getenv("AWS_REGION", "us-east-1")
DATABASE_URL = os.environ["DATABASE_URL"]
ENGINE_PATH = os.environ.get("ENGINE_PATH", os.path.abspath("./overflowengine"))

sqs = boto3.client("sqs", region_name=REGION)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)



def process_message(message):
    body = json.loads(message["Body"])
    request_id = body["request_id"]
    image_base64 = body["image_base64"]

    session = Session()

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
            image_path = tmp_img.name
            tmp_img.write(base64.b64decode(image_base64))

        output_path = os.path.join("/tmp", f"{request_id}_output.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        subprocess.run([
            ENGINE_PATH,
            "--input", image_path,
            "--output", output_path
        ], capture_output=True, text=True)

        try:
            with open(output_path, "r") as f:
                result = f.read().strip().lower()
                if result.startswith("covid"):
                    result = "covid"
                elif result in {"h5n1", "healthy"}:
                    pass
                else:
                    result = "failed"
        except Exception:
            result = "failed"

        analysis = session.query(Analysis_dbs).filter_by(request_id=request_id).first()
        if analysis:
            analysis.result = result
            analysis.updated_at = datetime.now(timezone.utc)
            analysis.image_path = image_path
            session.commit()

    except Exception as e:
        print(f"Error for process_message function: {e}")

    finally:
        session.close()
        if os.path.exists(image_path):
            os.remove(image_path)
        if os.path.exists(output_path):
            os.remove(output_path)



def poll_queue():
    executor = ThreadPoolExecutor(max_workers=8)
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        messages = response.get("Messages", [])
        for msg in messages:
            executor.submit(process_message, msg)
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=msg["ReceiptHandle"]
            )


if __name__ == "__main__":
    poll_queue()
