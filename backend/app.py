from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import uuid
import json

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

@app.route("/")
def home():
    return "Welcome to the Job Match App!"

@app.route('/results/<result_id>', methods=['GET'])
def get_results(result_id):
    try:
        result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
        with open(result_path, 'r') as f:
            result = json.load(f)
        return render_template('results.html', result=result)
    except FileNotFoundError:
        return "<h1>Result not found</h1>", 404
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
    # Generate unique result ID and save results
    result_id = str(uuid.uuid4())
    result_url = f"http://localhost:5000/results/{result_id}"
    
    # Save result to a file
    result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
    with open(result_path, 'w') as f:
        json.dump(result, f)
    
    # Return the result ID for frontend to redirect
    return jsonify({
        'result_id': result_id,
        'redirect_url': f'/results/{result_id}'
    })

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
        'job_fit_score': 80,
        'job_description': job_description,
        'resume_text': resume_text
    }
    return resume_analysis

if __name__ == '__main__':
    app.run(debug=True)

