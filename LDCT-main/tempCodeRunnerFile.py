import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import os

app = Flask(__name__)

# --- Configuration ---
CSV_FILE = "survey_data.csv"
FIELDNAMES = [
    "timestamp", "smoking", "years_smoking", "secondhand_smoke", "pm25",
    "chronic_cough", "shortness_of_breath", "wheezing",
    "lung_disease_history", "family_cancer_history",
    "total_score", "risk_level", "recommendation", "name", "email"
]

# Ensure the CSV file has a header
def initialize_csv():
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()

@app.route("/", methods=["GET", "POST"])
def survey():
    """Handles the survey form submission and displays the survey page."""
    if request.method == "POST":
        answers = {key: request.form.get(key, "") for key in FIELDNAMES}
        # Generate a unique timestamp for this submission
        timestamp = datetime.utcnow().isoformat(timespec='seconds')
        answers["timestamp"] = timestamp
        
        score_keys = [
            "smoking", "years_smoking", "secondhand_smoke", "pm25",
            "chronic_cough", "shortness_of_breath", "wheezing",
            "lung_disease_history", "family_cancer_history"
        ]
        total_score = sum(int(answers[key] or 0) for key in score_keys)
        answers["total_score"] = total_score

        if total_score <= 4:
            risk_level = "ความเสี่ยงต่ำ"
            recommendation = "แนะนำให้ติดตามด้วยตรวจสุขภาพประจำปีทั่วไป"
        elif total_score <= 9:
            risk_level = "ความเสี่ยงปานกลาง"
            recommendation = "ควรตรวจ CT Chest Low Dose หรือพบแพทย์เพื่อวางแผนดูแลต่อเนื่อง"
        else:
            risk_level = "ความเสี่ยงสูง"
            recommendation = "ควรพบแพทย์เฉพาะทางโรคปอดทันที และตรวจ CT Chest Low dose"
            
        answers["risk_level"] = risk_level
        answers["recommendation"] = recommendation

        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writerow(answers)

        # Pass the unique timestamp to the result template
        return render_template(
            "result.html",
            timestamp=timestamp,
            total_score=total_score,
            risk_level=risk_level,
            recommendation=recommendation
        )

    return render_template("survey.html")

@app.route("/contact", methods=["POST"])
def contact():
    """Updates a specific entry in the CSV with contact information and returns a JSON response."""
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    timestamp = request.form.get("timestamp", "")

    if not all([name, email, timestamp]):
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    rows = []
    record_found = False
    try:
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Find the matching record by its unique timestamp
                if row['timestamp'] == timestamp:
                    row['name'] = name
                    row['email'] = email
                    record_found = True
                rows.append(row)

        if record_found:
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows)
            return jsonify({'success': True, 'name': name})
        else:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'CSV file not found'}), 500


@app.route("/download")
def download():
    """Allows downloading the survey data CSV file."""
    return send_file(CSV_FILE, as_attachment=True)

if __name__ == "__main__":
    initialize_csv()
    app.run(debug=True)
