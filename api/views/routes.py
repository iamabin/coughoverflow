from api.models import db
from api.models.apidbs import Analysis_dbs

from flask import Blueprint, jsonify, request
import re
import base64

from datetime import datetime
import iso8601
import uuid
from datetime import datetime, timezone
from uuid import uuid4
import os
from flask import current_app


## TODO: return error without leakage of sensitive information
api = Blueprint('api', __name__, url_prefix='/api/v1')
VALID_LAB_IDS = {
    "4CT24811", "4CT41211", "4CT41221", "4CT41231", "4CT41232", "4CT41651",
    "4CT42131", "4CT42132", "4CT42133", "4CT42134", "4CT42801", "4CT42851",
    "4CT42852", "4CT42853", "4CT43111", "4CT45151", "4CT45521", "4CT45811",
    "4CT46601", "ACL24851", "ACL40121", "ACL40131", "ACL40191", "ACL40201",
    "ACL40691", "ACL41141", "ACL41151", "ACL41221", "ACL42071", "ACL42151",
    "ACL42161", "ACL42162", "ACL42163", "ACL42171", "ACL42231", "ACL42801",
    "ACL45091", "ACL45092", "ACL45561", "ACL45581", "ACL45582", "HAC26021",
    "QHD40011", "QML40671", "QML41011", "QML41201", "QML41202", "QML41203",
    "QML45701", "QML45702", "QML45703", "QML45704", "QML46551", "QML46552",
    "QML46701", "QML46702", "QML46703", "QML47001", "QML47002", "QML47011",
    "QML47012", "QML47401", "QML47402", "QML47403", "QML47404", "QML47405",
    "QML48021", "QML48022", "QML48121", "QML48122", "QML48123", "QML48201",
    "QML48251", "QML48601", "QML48771", "QML48791", "SNP40011", "SNP40651",
    "SNP43051", "SNP45701"
}


@api.route('/health')
def health():
    server_status = True
    if server_status:
        return jsonify({'status': 'healthy'}), 200
    else:
        return jsonify({'status': 'unhealthy'}), 503


@api.route('/labs/results/<lab_id>', methods=['GET'])
def labs_results(lab_id):
    try:
        if lab_id not in VALID_LAB_IDS:
            return jsonify({"error": f" '{lab_id}' not in the list."}), 404

        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        start = request.args.get('start', default=None, type=str)
        end = request.args.get('end', default=None, type=str)
        patient_id = request.args.get('patient_id', default=None, type=str)
        status = request.args.get('status', default=None, type=str)
        urgent = request.args.get('urgent', default=None, type=str)

        if limit <= 0 or limit > 1000:
            return jsonify({"error": "Invalid limit value. Must be between 1 and 1000."}), 400
        if offset < 0:
            return jsonify({"error": "Invalid offset value. Must be >= 0."}), 400
        query = Analysis_dbs.query.filter_by(lab_id=lab_id)
        if start:
            try:
                start_date = iso8601.parse_date(start)
                query = query.filter(Analysis_dbs.start_at >= start_date)
            except Exception:
                return jsonify({"error": "Invalid start date format. Must be RFC3339."}), 400
        if end:
            try:
                end_date = iso8601.parse_date(end)
                query = query.filter(Analysis_dbs.start_at <= end_date)
            except Exception:
                return jsonify({"error": "Invalid end date format. Must be RFC3339."}), 400
        if patient_id:
            if not re.fullmatch(r"\d{11}", patient_id):
                return jsonify({"error": "Invalid patient_id format. Must be an 11-digit Medicare number."}), 400
            query = query.filter_by(patient_id=patient_id)

        if status:
            valid_statuses = {"pending", "covid", "h5n1", "healthy", "failed"}
            if status not in valid_statuses:
                return jsonify({"error": f"Invalid status."}), 400
            query = query.filter_by(result=status)
        if urgent:
            if urgent.lower() not in {"true", "false"}:
                return jsonify({"error": "Invalid urgent format."}), 400
            query = query.filter_by(urgent=(urgent.lower() == "true"))

        results = query.offset(offset).limit(limit).all()
        response = [{
            "request_id": r.request_id,
            "lab_id": r.lab_id,
            "patient_id": str(r.patient_id),
            "result": r.result,
            "urgent": r.urgent,
            "created_at": r.start_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        } for r in results]
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/labs/results/<lab_id>/summary', methods=['GET'])
def labs_results_summary(lab_id):
    try:
        if lab_id not in VALID_LAB_IDS:
            return jsonify({"error": f" '{lab_id}' not in the list."}), 404
        query = Analysis_dbs.query.filter_by(lab_id=lab_id)

        temp_start = request.args.get('start', default=None, type=str)
        temp_end = request.args.get('end', default=None, type=str)

        if temp_start:
            try:
                start_date = iso8601.parse_date(temp_start)
                query = query.filter(Analysis_dbs.start_at >= start_date)
            except Exception:
                return jsonify({"error": "Invalid start date format. Must be RFC3339."}), 400
        if temp_end:
            try:
                end_date = iso8601.parse_date(temp_end)
                query = query.filter(Analysis_dbs.start_at <= end_date)
            except Exception:
                return jsonify({"error": "Invalid end date format. Must be RFC3339."}), 400

        status_counts = {
            "pending": query.filter_by(result="pending").count(),
            "covid": query.filter_by(result="covid").count(),
            "h5n1": query.filter_by(result="h5n1").count(),
            "healthy": query.filter_by(result="healthy").count(),
            "failed": query.filter_by(result="failed").count(),
            "urgent": query.filter_by(urgent=True).count(),
        }
        response = {
            "lab_id": lab_id,
            **status_counts,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        return jsonify(response), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/labs", methods=["GET"])
def labs():
    try:
        return jsonify(list(VALID_LAB_IDS)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/patients/results", methods=["GET"])
def patient_results():
    try:

        patient_id = request.args.get('patient_id', default=None, type=str)
        start = request.args.get('start', default=None, type=str)
        end = request.args.get('end', default=None, type=str)
        status = request.args.get('status', default=None, type=str)
        urgent = request.args.get('urgent', default=None, type=str)

        if not patient_id:
            return jsonify({"error": "Missing patient_id."}), 400

        if not re.fullmatch(r"\d{11}", patient_id):
            return jsonify({"error": "Invalid patient_id format. Must be an 11-digit Medicare number."}), 400

        query = Analysis_dbs.query.filter_by(patient_id=patient_id)

        if not query.all():
            return jsonify({"error": "Patient identifier does not correspond to a known patient."}), 404

        if start:
            try:
                start_date = iso8601.parse_date(start)
                query = query.filter(Analysis_dbs.start_at >= start_date)
            except Exception:
                return jsonify({"error": "Invalid start date format. Must be RFC3339."}), 400
        if end:
            try:
                end_date = iso8601.parse_date(end)
                query = query.filter(Analysis_dbs.start_at <= end_date)
            except Exception:
                return jsonify({"error": "Invalid end date format. Must be RFC3339."}), 400
        if status:
            valid_statuses = {"pending", "covid", "h5n1", "healthy", "failed"}
            if status not in valid_statuses:
                return jsonify({"error": f"Invalid status."}), 400
            query = query.filter_by(result=status)
        if urgent:
            if urgent.lower() not in {"true", "false"}:
                return jsonify({"error": "Invalid urgent format."}), 400
            query = query.filter_by(urgent=(urgent.lower() == "true"))
        results = query.all()

        response = [{
            "request_id": r.request_id,
            "lab_id": r.lab_id,
            "patient_id": str(r.patient_id),
            "result": r.result,
            "urgent": r.urgent,
            "created_at": r.start_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        } for r in results]
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/analysis", methods=["GET"])
def get_analysis():
    try:
        request_id = request.args.get("request_id", None)

        if not request_id:
            return jsonify({"error": "Please enter a request ID."}), 404
        try:
            uuid.UUID(str(request_id))
        except ValueError:
            return jsonify({"error": "The analysis request ID is not a valid UUID."}), 404

        result = Analysis_dbs.query.filter_by(request_id=request_id).first()
        if not result:
            return jsonify({"error": "The analysis request ID does not correspond to a known request."}), 404

        response = {
            "request_id": result.request_id,
            "lab_id": result.lab_id,
            "patient_id": result.patient_id,
            "result": result.result,
            "urgent": result.urgent,
            "created_at": result.start_at.isoformat(),
            "updated_at": result.updated_at.isoformat()
        }

        return jsonify(response), 200


    except Exception as e:

        return jsonify({"error": str(e)}), 500


@api.route("/analysis", methods=["POST"])
def create_analysis():
    patient_id = request.args.get('patient_id', default=None, type=str)
    lab_id = request.args.get('lab_id', default=None, type=str)
    urgent = request.args.get('urgent', default=None, type=str)
    if not patient_id:
        return jsonify({"error": "missing_patient_id"}), 400
    if not re.fullmatch(r"\d{11}", patient_id):
        return jsonify({"error": "invalid_patient_id"}), 400
    if not lab_id:
        return jsonify({"error": "missing_lab_id"}), 400

    if lab_id not in VALID_LAB_IDS:
        return jsonify({"error": "invalid_lab_id"}), 404

    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "no_image"}), 400

    try:
        image_data = base64.b64decode(data['image'], validate=True)
    except Exception:
        return jsonify({"error": "invalid_image"}), 400

    image_size_kb = len(image_data) / 1024
    if image_size_kb < 4 or image_size_kb > 150:
        return jsonify({
            "error": "image_size",
            "detail": f"Image must be between 4KB and 150KB. Got {int(image_size_kb)}KB"

        }), 400

    new_id = str(uuid4())
    now = datetime.now(timezone.utc)

    upload_dir = os.path.join(current_app.instance_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{new_id}.jpg"
    image_path = os.path.join(upload_dir, filename)
    try:
        with open(image_path, 'wb') as f:
            f.write(image_data)
    except Exception as e:
        return jsonify({"error": "image_save_failed", "detail": str(e)}), 500

    analysis = Analysis_dbs(
        request_id=new_id,
        lab_id=lab_id,
        patient_id=patient_id,
        result="pending",
        urgent=urgent.lower() == 'true',
        start_at=now,
        updated_at=now,
        image_path=image_path
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        "id": new_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "status": "pending"
    }), 201

@api.route("/analysis", methods=["PUT"])
def update_lab_id():
    request_id = request.args.get("request_id", type=str)
    new_lab_id = request.args.get("lab_id", type=str)

    if not request_id or not new_lab_id:
        return jsonify({"error": "Missing request_id or lab_id"}), 400
    if new_lab_id not in VALID_LAB_IDS:
        return jsonify({"error": "Invalid lab identifier."}), 400
    result = Analysis_dbs.query.filter_by(request_id=request_id).first()
    if not result:
        return jsonify({"error": "Analysis job not found."}), 404
    result.lab_id = new_lab_id
    result.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "request_id": result.request_id,
        "lab_id": result.lab_id,
        "patient_id": result.patient_id,
        "result": result.result,
        "urgent": result.urgent,
        "created_at": result.start_at.isoformat(),
        "updated_at": result.updated_at.isoformat()
    }), 200
