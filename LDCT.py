import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file


app = Flask(__name__)

CSV_FILE = "survey_data.csv"
FIELDNAMES = [
    "timestamp", "smoking", "years_smoking", "secondhand_smoke", "pm25",
    "chronic_cough", "shortness_of_breath", "wheezing",
    "lung_disease_history", "family_cancer_history",
    "total_score", "risk_level", "recommendation", "name", "email"
]

@app.route("/", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        answers = {
            "timestamp": datetime.utcnow().isoformat(),
            "smoking": request.form.get("smoking", ""),
            "years_smoking": request.form.get("years_smoking", ""),
            "secondhand_smoke": request.form.get("secondhand_smoke", ""),
            "pm25": request.form.get("pm25", ""),
            "chronic_cough": request.form.get("chronic_cough", ""),
            "shortness_of_breath": request.form.get("shortness_of_breath", ""),
            "wheezing": request.form.get("wheezing", ""),
            "lung_disease_history": request.form.get("lung_disease_history", ""),
            "family_cancer_history": request.form.get("family_cancer_history", ""),
            "total_score": 0,
            "risk_level": "",
            "recommendation": "",
            "name": "",
            "email": ""
        }

        total_score = sum(int(answers[key]) for key in [
            "smoking", "years_smoking", "secondhand_smoke", "pm25",
            "chronic_cough", "shortness_of_breath", "wheezing",
            "lung_disease_history", "family_cancer_history"
        ] if answers[key].isdigit())
        answers["total_score"] = total_score

        if total_score <= 6:
            risk_level = "ความเสี่ยงต่ำ"
            recommendation = "แนะนำให้ติดตามด้วยตรวจสุขภาพประจำปีทั่วไป"
        elif 7 <= total_score <= 12:
            risk_level = "ความเสี่ยงปานกลาง"
            recommendation = "ควรตรวจ CT Chest Low Dose หรือพบแพทย์เพื่อวางแผนดูแลต่อเนื่อง"
        else:
            risk_level = "ความเสี่ยงสูง"
            recommendation = "ควรพบแพทย์เฉพาะทางโรคปอดทันที และตรวจ CT Chest Low dose"

        answers["risk_level"] = risk_level
        answers["recommendation"] = recommendation

        # บันทึกลง CSV (name/email ว่าง)
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(answers)

        # ส่งข้อมูลไปหน้า result
        return render_template(
            "result.html",
            total_score=total_score,
            risk_level=risk_level,
            recommendation=recommendation
        )

    return render_template("survey.html")

@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "")
    email = request.form.get("email", "")

    # อ่านข้อมูลทั้งหมด
    rows = []
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = list(csv.DictReader(csvfile))
        rows = reader

    # อัปเดตแถวล่าสุด
    if rows:
        rows[-1]["name"] = name
        rows[-1]["email"] = email

    # เขียนกลับลงไฟล์
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return render_template("thankyou.html", name=name)

@app.route("/download")
def download():
    return send_file(CSV_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
