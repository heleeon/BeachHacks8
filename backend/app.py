from flask import Flask, request, jsonify
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
        
        # Return an HTML page with formatted results
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Results</title>
            <style>
                #root {{
                    max-width: 1280px;
                    margin: 0 auto;
                    padding: 2rem;
                    text-align: center;
                    background: linear-gradient(180deg, #e6f6ff 0%, #99d3ff 50%, #004d99 100%);
                    min-height: 100vh;
                    min-width: 100%;
                    box-sizing: border-box;
                    font-family: Arial, sans-serif;
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto;
                    padding: 2em;
                }}
                .score {{ 
                    font-size: 24px; 
                    margin: 20px 0;
                    color: #00264d;
                }}
                .skills {{ 
                    margin: 20px 0;
                    color: #00264d;
                }}
                pre {{ 
                    background: rgba(255, 255, 255, 0.9);
                    padding: 15px; 
                    border-radius: 5px; 
                    overflow-x: auto;
                    text-align: left;
                }}
                h1, h2 {{
                    color: #00264d;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                li {{
                    margin: 10px 0;
                    color: #00264d;
                }}
            </style>
        </head>
        <body>
            <div id="root">
                <div class="container">
                    <h1>Analysis Results</h1>
                    <div class="score">
                        <strong>Job Fit Score:</strong> {result['job_fit_score']}%
                    </div>
                    <div class="skills">
                        <h2>Detected Skills:</h2>
                        <ul>
                            {' '.join(f'<li>{skill}</li>' for skill in result['skills'])}
                        </ul>
                    </div>
                    <h2>Job Description:</h2>
                    <pre>{result['job_description']}</pre>
                    <h2>Resume Text:</h2>
                    <pre>{result['resume_text']}</pre>
                </div>
            </div>
        </body>
        </html>
        """
        return html
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

