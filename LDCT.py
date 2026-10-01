import csv
from datetime import datetime
from flask import Flask, render_template, request, url_for, send_file, jsonify
import os

app = Flask(__name__)

# --- Configuration ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(APP_ROOT, "survey_data.csv")

FIELDNAMES = [
    "timestamp", "lang", "smoking", "years_smoking", "secondhand_smoke", "pm25",
    "chronic_cough", "shortness_of_breath", "wheezing",
    "lung_disease_history", "family_cancer_history",
    "total_score", "risk_level", "recommendation", "name", "email"
]

TRANSLATIONS = {
    'th': {
        'low': {
            'risk_level': "ความเสี่ยงต่ำ",
            'recommendation': "แนะนำให้ติดตามด้วยตรวจสุขภาพประจำปีทั่วไป"
        },
        'medium': {
            'risk_level': "ความเสี่ยงปานกลาง",
            'recommendation': "ควรตรวจ CT Chest Low Dose หรือพบแพทย์เพื่อวางแผนดูแลต่อเนื่อง"
        },
        'high': {
            'risk_level': "ความเสี่ยงสูง",
            'recommendation': "ควรพบแพทย์เฉพาะทางโรคปอดทันที และตรวจ CT Chest Low dose"
        }
    },
    'en': {
        'low': {
            'risk_level': "Low Risk",
            'recommendation': "Annual health check-ups are recommended."
        },
        'medium': {
            'risk_level': "Medium Risk",
            'recommendation': "A Low-Dose CT Chest scan or consulting a doctor for a follow-up plan is advisable."
        },
        'high': {
            'risk_level': "High Risk",
            'recommendation': "Immediate consultation with a lung specialist and a Low-Dose CT Chest scan are strongly recommended."
        }
    }
}

def initialize_csv():
    """Creates the CSV file with a header if it doesn't exist.""" 
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()

@app.route("/", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        lang = request.form.get('lang', 'th')
        answers = {key: request.form.get(key, "") for key in FIELDNAMES}
        
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        answers["timestamp"] = timestamp
        answers["lang"] = lang
        
        score_keys = [
            "smoking", "years_smoking", "secondhand_smoke", "pm25",
            "chronic_cough", "shortness_of_breath", "wheezing",
            "lung_disease_history", "family_cancer_history"
        ]
        total_score = sum(int(answers[key] or 0) for key in score_keys)
        answers["total_score"] = total_score

        if total_score <= 4:
            risk_key = 'low'
        elif total_score <= 9:
            risk_key = 'medium'
        else:
            risk_key = 'high'
            
        risk_level = TRANSLATIONS[lang][risk_key]['risk_level']
        recommendation = TRANSLATIONS[lang][risk_key]['recommendation']
        
        answers["risk_level"] = risk_level
        answers["recommendation"] = recommendation

        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writerow(answers)

        return render_template(
            "result.html",
            lang=lang,
            timestamp=timestamp,
            total_score=total_score,
            risk_key=risk_key, # Pass the key for CSS class
            risk_level=risk_level,
            recommendation=recommendation
        )

    return render_template("survey.html")

@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name")
    email = request.form.get("email")
    timestamp = request.form.get("timestamp")
    lang = request.form.get("lang", "th") # Get lang from form

    if not all([name, email, timestamp]):
        return jsonify({'success': False, 'error': 'Missing required data'}), 400

    print(f"Received timestamp: {timestamp}") # Debugging line

    try:
        rows = []
        record_found = False
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('timestamp') == timestamp:
                    row['name'] = name
                    row['email'] = email
                    row['lang'] = lang # Save lang as well
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
        return jsonify({'success': False, 'error': 'Data file not found on server.'}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'success': False, 'error': 'An internal server error occurred.'}), 500

@app.route("/download")
def download():
    try:
        return send_file(CSV_FILE, as_attachment=True)
    except FileNotFoundError:
        return "File not found.", 404

if __name__ == "__main__":
    initialize_csv()
    app.run(debug=True)
