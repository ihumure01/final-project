from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

app = Flask(__name__)
CORS(app)

DATA_FILE = Path(__file__).parent / "courses.json"


def load_courses():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_courses(courses):
    DATA_FILE.write_text(json.dumps(courses, indent=4), encoding="utf-8")


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/courses", methods=["GET"])
def get_courses():
    return jsonify(load_courses()), 200


@app.route("/api/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    course = next((c for c in load_courses() if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course), 200


@app.route("/api/courses", methods=["POST"])
def create_course():
    data = request.get_json(silent=True) or {}
    fields = ["name", "description", "target_date", "status"]

    if any(not isinstance(data.get(f), str) or not data[f].strip() for f in fields):
        return jsonify({"error": "All course fields are required"}), 400

    if data["status"] not in ["Not Started", "In Progress", "Completed"]:
        return jsonify({"error": "Invalid status"}), 400

    courses = load_courses()
    course = {
        "id": str(uuid.uuid4()),
        "name": data["name"].strip(),
        "description": data["description"].strip(),
        "target_date": data["target_date"],
        "status": data["status"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    courses.append(course)
    save_courses(courses)
    return jsonify(course), 201


@app.route("/api/courses/<course_id>", methods=["PUT"])
def update_course(course_id):
    data = request.get_json(silent=True) or {}
    courses = load_courses()

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    for field in ["name", "description", "target_date", "status"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return jsonify({"error": f"Invalid {field}"}), 400
            course[field] = data[field].strip()

    if course["status"] not in ["Not Started", "In Progress", "Completed"]:
        return jsonify({"error": "Invalid status"}), 400

    save_courses(courses)
    return jsonify(course), 200


@app.route("/api/courses/<course_id>", methods=["DELETE"])
def delete_course(course_id):
    courses = load_courses()
    remaining = [c for c in courses if c["id"] != course_id]

    if len(remaining) == len(courses):
        return jsonify({"error": "Course not found"}), 404

    save_courses(remaining)
    return jsonify({"message": "Course deleted successfully"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
