from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return "Welcome to the Job Match App!"

@app.route('/analyze', methods=['POST'])
def analyze():
    # Get job description
    job_description = request.form.get('job_description')
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400

    # Get and save resume
    if 'resume' not in request.files:
        return jsonify({'error': 'Resume file is required'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Extract and analyze text
    resume_text = extract_text(file_path)
    if not resume_text:
        return jsonify({'error': 'Failed to extract text from resume'}), 500

    result = analyze_resume(resume_text, job_description)
    return jsonify(result)

def extract_text(file_path):
    try:
        with open(file_path, 'r', errors='ignore') as file:
            return file.read()
    except Exception as e:
        return str(e)

def analyze_resume(resume_text, job_description):
    # Placeholder for real analysis
    resume_analysis = {
        'skills': ['Python', 'Data Science', 'Machine Learning'],
        'job_fit_score': 80
    }
    return resume_analysis

if __name__ == '__main__':
    app.run(debug=True)

