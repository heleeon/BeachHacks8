from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import uuid
import json
import pdfplumber

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# Home route
@app.route("/")
def home():
    return "Welcome to the Job Match App!"

# Displays results page
@app.route('/results/<result_id>', methods=['GET'])
def get_results(result_id):
    try:
        result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
        with open(result_path, 'r') as f:
            result = json.load(f)
        return render_template('results.html', result=result)
    except FileNotFoundError:
        return "<h1>Result not found</h1>", 404

# Analyze route
@app.route('/analyze', methods=['POST'])
def analyze():
    job_description = request.form.get('job_description')
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400

    if 'resume' not in request.files:
        return jsonify({'error': 'Resume file is required'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        resume_text = extract_text_from_pdf(file_path)
        if not resume_text:
            return jsonify({'error': 'Failed to extract text from PDF'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to read resume: {str(e)}'}), 500

    # Perform skill analysis
    result = analyze_resume(resume_text, job_description)

    result_id = str(uuid.uuid4())
    result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
    with open(result_path, 'w') as f:
        json.dump(result, f)

    return jsonify({
        'result_id': result_id,
        'redirect_url': f'/results/{result_id}'
    })


def extract_text_from_pdf(file_path):
    try:
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ''
        return text.strip()
    except Exception as e:
        print(f"Error extracting text with pdfplumber: {e}")
        return None


def extract_keywords(text):
    words = text.lower().split()
    return set(word.strip('.,!?()[]') for word in words if word.isalpha())

def compare_resume_with_job(resume_text, job_text):
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_text)
    missing_skills = job_keywords - resume_keywords
    return list(missing_skills)

def analyze_resume(resume_text, job_description):
    missing_skills = compare_resume_with_job(resume_text, job_description)
    job_fit_score = max(0, 100 - len(missing_skills) * 5)
    return {
        'skills': list(extract_keywords(resume_text)),
        'job_fit_score': job_fit_score,
        'missing_skills': missing_skills,
        'job_description': job_description,
        'resume_text': resume_text
    }

if __name__ == '__main__':
    app.run(debug=True)
