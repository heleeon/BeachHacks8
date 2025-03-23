from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import uuid
import json
import spacy
from pyresparser import ResumeParser

# Load NLP model
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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
        resume_data = ResumeParser(file_path).get_extracted_data()
    except Exception as e:
        return jsonify({'error': f'Failed to parse resume: {str(e)}'}), 500

    resume_text = ' '.join(resume_data.get('experience', []) + resume_data.get('skills', []))
    if not resume_text:
        return jsonify({'error': 'Failed to extract text from resume'}), 500

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

def extract_keywords(text):
    doc = nlp(text.lower())
    return list(set([token.text for token in doc if not token.is_stop and token.is_alpha]))

def compare_resume_with_job(resume_text, job_text):
    resume_keywords = set(extract_keywords(resume_text))
    job_keywords = set(extract_keywords(job_text))
    missing_skills = job_keywords - resume_keywords
    return list(missing_skills)

def analyze_resume(resume_text, job_description):
    missing_skills = compare_resume_with_job(resume_text, job_description)
    job_fit_score = max(0, 100 - len(missing_skills) * 5)
    return {
        'skills': extract_keywords(resume_text),
        'job_fit_score': job_fit_score,
        'missing_skills': missing_skills,
        'job_description': job_description,
        'resume_text': resume_text
    }

if __name__ == '__main__':
    app.run(debug=True)
