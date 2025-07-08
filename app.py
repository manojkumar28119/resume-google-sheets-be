from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import sqlite3
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flask_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DB_PATH = 'resume_requests.db'

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email_address TEXT,
                phone_number TEXT,
                career_objective TEXT,
                education TEXT,
                skills TEXT,
                projects TEXT,
                work_experience TEXT,
                certifications TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                transaction_id TEXT,
                payment_checkbox TEXT,
                payment_screenshot TEXT,
                job_description TEXT,
                is_verified INTEGER DEFAULT 0,
                resume_sent INTEGER DEFAULT 0,
                submission_timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized with correct schema.")
    else:
        logger.info("Database already exists.")

init_db()

@app.route("/submit", methods=["POST"])
def submit():
    logger.info(f"Received POST request to /submit from {request.remote_addr}")

    data = request.get_json()
    if not data:
        logger.warning("No data received in POST request")
        return jsonify({"error": "No data received"}), 400

    try:
        data['submission_timestamp'] = datetime.now().isoformat()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
    INSERT INTO resume_requests (
        full_name, email_address, phone_number, career_objective, education,
        skills, projects, work_experience, certifications, linkedin_url,
        github_url, transaction_id, payment_checkbox, payment_screenshot, job_description,
        submission_timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    data.get("full_name"),
    data.get("email_address"),
    str(data.get("phone_number")),
    data.get("career_objective"),
    data.get("education"),
    data.get("skills"),
    data.get("projects"),
    data.get("work_experience"),
    data.get("certifications"),
    data.get("linkedin_url"),
    data.get("github_url"),
    data.get("transaction_id", ""),
    data.get("☑️_payment_confirmation_checkbox", ""),
    data.get("📤_upload_screenshot_of_payment", ""),
    data.get("paste_the_job_description_(jd)_or_job_post", ""),
    data["submission_timestamp"]
))

        conn.commit()
        conn.close()

        logger.info("✅ Submission saved to database.")
        return jsonify({"message": "Data saved successfully"}), 200

    except Exception as e:
        logger.error(f"❌ Error processing submission: {str(e)}")
        logger.exception("Full exception details:")
        return jsonify({"error": str(e)}), 500



@app.route("/all", methods=["GET"])
def get_all_submissions():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This allows dictionary-style access
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resume_requests")
        rows = cursor.fetchall()
        conn.close()

        result = [dict(row) for row in rows]  # Convert each row to dict

        logger.info(f"Returning {len(result)} submissions")
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ Error fetching submissions: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route("/verify_payment", methods=["POST"])
def verify_payment():
    try:
        data = request.get_json()
        if not data or "id" not in data:
            return jsonify({"error": "Missing ID"}), 400

        submission_id = data["id"]
        action = data.get("action", "verify")  # "verify" or "reject"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if action == "verify":
            cursor.execute("UPDATE resume_requests SET is_verified = 1 WHERE id = ?", (submission_id,))
        elif action == "reject":
            cursor.execute("UPDATE resume_requests SET is_verified = -1 WHERE id = ?", (submission_id,))
        else:
            return jsonify({"error": "Invalid action"}), 400

        conn.commit()
        conn.close()

        logger.info(f"Submission ID {submission_id} marked as {action.upper()}")
        return jsonify({"message": f"Submission {action}ed successfully"}), 200

    except Exception as e:
        logger.error(f"❌ Error verifying payment: {str(e)}")
        logger.exception("Full exception details:")
        return jsonify({"error": str(e)}), 500



@app.route("/generate_resume", methods=["POST"])
def generate_resume():
    try:
        data = request.get_json()
        if not data or "id" not in data:
            return jsonify({"error": "Missing ID"}), 400

        submission_id = data["id"]

        # Connect to DB and fetch submission
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resume_requests WHERE id = ? AND is_verified = 1", (submission_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Submission not found or not verified"}), 404

        # Map DB row to keys
        columns = [column[0] for column in cursor.description]
        form_data = dict(zip(columns, row))

        # Run your existing resume pipeline
        from resume_filler import fill_resume_template
        from gpt_engine import generate_resume_json
        from email_sender import send_email

        resume_json = generate_resume_json(form_data)
        resume_path = fill_resume_template(resume_json)
        send_email(
            recipient=form_data["email_address"],
            subject="Your AI-Generated Resume",
            attachment_path=resume_path,
            delete_after_send=True
        )

        # Update database to mark resume as sent
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE resume_requests SET resume_sent = 1 WHERE id = ?", (submission_id,))
        conn.commit()
        conn.close()

        logger.info(f"Resume generated and emailed successfully for submission ID {submission_id}")
        return jsonify({"message": "Resume generated and emailed successfully."}), 200

    except Exception as e:
        logger.error(f"Error generating resume: {str(e)}")
        logger.exception("Full exception details:")
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    logger.info("Starting Flask development server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
    logger.info("Flask server stopped")
