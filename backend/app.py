from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import uuid
import json
import pdfplumber
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import LogisticRegression
import spacy
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Expanded buzzwords common across industries (as a Python set)
BUZZWORDS = {
    "candidate", "experience", "proficient", "opportunity", "requirement",
    "results-driven", "self-starter", "team player", "innovative", "dynamic",
    "motivated", "strategic", "competitive", "leadership", "collaborative"
}

# Expanded skill map (canonical skills to list of synonyms)
SKILL_MAP = {
    "python": ["python", "python programming", "py"],
    "java": ["java", "jdk", "j2ee"],
    "c++": ["cpp", "c plus plus"],
    "javascript": ["javascript", "js", "typescript", "nodejs"]
}
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

    # Predict recommended job
    recommended_job = find_job_category(resume_text)
    result['recommended_job'] = recommended_job

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
    doc = nlp(text.lower())

    # Extract noun keywords and noun phrases
    noun_keywords = {token.lemma_ for token in doc if token.pos_ in ["NOUN", "PROPN"]}
    noun_phrases = {" ".join(token.lemma_ for token in chunk if token.pos_ in ["NOUN", "PROPN", "ADJ"])
                    for chunk in doc.noun_chunks if not all(tok.is_stop for tok in chunk)}

    # Combine extracted keywords
    combined_keywords = noun_keywords.union(noun_phrases)

    # Normalize and filter keywords using skill map and buzzwords
    normalized = set()
    for skill in combined_keywords:
        lower_skill = skill.lower()
        if lower_skill in BUZZWORDS or any(buzz in lower_skill for buzz in BUZZWORDS):
            continue
        found = False
        for canonical_form, variants in SKILL_MAP.items():
            if any(variant in lower_skill for variant in variants):
                normalized.add(canonical_form)
                found = True
                break
        if not found:
            normalized.add(skill)

    return normalized

def compare_resume_with_job(resume_text, job_text):
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_text)
    matched_skills = resume_keywords.intersection(job_keywords)
    missing_skills = job_keywords - resume_keywords
    return list(matched_skills), list(missing_skills)


def analyze_resume(resume_text, job_description):
    matched_skills, missing_skills = compare_resume_with_job(resume_text, job_description)
    job_fit_score = max(0, 100 - len(missing_skills) * 5)
    return {
        'skills': list(extract_keywords(resume_text)),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'job_fit_score': job_fit_score,
        'job_description': job_description,
        'resume_text': resume_text
    }


def find_job_category(resume_text):
    # Load datasets from the data folder
    resume_csv = "data/UpdatedResumeDataSet.csv"
    job_csv = "data/job_title_des.csv"
    df_resume = pd.read_csv(resume_csv)
    df_job = pd.read_csv(job_csv)

    # Prepare training data: X = resume text, y = category labels
    X = df_resume['Resume']
    y = df_resume['Category']

    # Create the pipeline with TF-IDF vectorization, chi² feature selection, and Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english')),
        ('chi2', SelectKBest(chi2, k=1000)),
        ('clf', LogisticRegression(max_iter=1000))
    ])

    # Fit the pipeline on the entire dataset for prediction
    pipeline.fit(X, y)

    # Predict the category and probabilities for the input resume
    predicted_proba = pipeline.predict_proba([resume_text])[0]
    classes = pipeline.named_steps['clf'].classes_

    # Sort indices by probability in descending order and take the top 10
    sorted_indices = np.argsort(-predicted_proba)
    top_indices = sorted_indices[:10]
    top_categories = [classes[j] for j in top_indices]

    return top_categories

if __name__ == '__main__':
    app.run(debug=True)
