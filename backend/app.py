from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import os
import uuid
import json
import pdfplumber
import re
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import LogisticRegression

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# -------------------- LARGE BUZZWORDS --------------------
BUZZWORDS = {"you", "this", "actionable", "multiple", "closely", "the", "departments", "strategies", "uncover", "decisions", "across","growing"
    "candidate","ideal candidate","experience","experienced","proficient","expert","expertise","looking",
    "seek","opportunity","requirement","passionate","previous","appreciation","ideal","ideal teacher","lesson plan",
    "strong","classroom","activity","results-driven","self-starter","team player","dynamic","innovative","proactive",
    "fast-paced","growth-oriented","detail-oriented","motivated","strategic","visionary","competitive","leadership",
    "collaborative","resourceful","synergy","core competencies","excellent communication","customer-focused",
    "client-centric","proven track record","highly effective","driven","dedicated","skilled","creative",
    "results-oriented","proven success","industry-leading","cutting-edge","leveraged","extensive","deadline-oriented",
    "customer satisfaction","mission-driven","management","manager","responsibility","responsibilities","search",
    "technique","engine","track","record","performance","visibility","initiative","managerial","business acumen",
    "revenue","previous experience","interpersonal skills","people person","outgoing","energetic","hardworking",
    "go-getter","professional","vibrant","game-changer","superstar","rockstar","ninja","hero","guru"
}

# -------------------- LARGE SKILL_MAP (from all industries) --------------------
SKILL_MAP = {
    "python": ["python", "python programming", "python scripting", "py"],
    "java": ["java programming", "jdk", "j2ee", "jakarta ee"],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "dotnet", ".net", "asp.net"],
    "javascript": ["javascript", "js", "typescript", "node.js", "nodejs", "react", "angular", "vue", "svelte", "express"],
    "web application development": ["web dev", "web development", "frontend backend", "full stack", "website creation"],
    "software architecture": ["system design", "software design", "application architecture"],
    "ui/ux design": ["user interface", "user experience", "wireframing", "prototyping", "figma", "adobe xd", "sketch"],
    "database": ["sql", "mysql", "postgresql", "nosql", "mongodb", "mariadb", "oracle"],
    "cloud computing": ["aws", "amazon web services", "azure", "google cloud", "gcp", "cloud services", "amazon cloud"],
    "docker container": ["docker", "containers", "kubernetes", "container orchestration", "k8s"],
    "machine learning": ["machine learning","ml","predictive modeling","supervised learning","unsupervised learning",
                         "deep learning","neural networks","artificial intelligence","ai","tensorflow","pytorch"],
    "data analysis": ["data analytics","data visualization","data interpretation","big data","data mining","pandas","numpy"],
    "devops": ["ci/cd","continuous integration","continuous deployment","jenkins","ansible","chef","puppet"],
    "api development": ["rest api","graphql","web services","soap api"],
    "cybersecurity": ["information security","network security","penetration testing","ethical hacking","ceh"],
    "qa testing": ["quality assurance","quality control","software testing","test automation","selenium","cypress"],
    "project management": ["pmp","scrum","agile","kanban","project manager","waterfall"],
    "business analysis": ["business analyst","requirements analysis","ba","feasibility study"],
    "sales": ["selling","business development","sales strategy","account management"],
    "marketing": ["digital marketing","seo","search engine optimization","content marketing","social media marketing",
                  "sem","ppc","marketing campaigns","brand management","marketing strategy"],
    "human resources": ["hr","talent acquisition","recruitment","employee relations","people operations","hiring"],
    "finance": ["financial analysis","financial modeling","accounting","budgeting","forecasting","investment analysis","taxation"],
    "customer service": ["client support","customer relations","call center","customer care","crm"],
    "supply chain management": ["inventory management","logistics","warehouse management","scm"],
    "patient care": ["patient management","clinical care","patient handling","bedside care"],
    "nursing": ["registered nurse","rn","nursing care","critical care","bsn"],
    "medical coding": ["icd-10","billing coding","medical billing","cpt"],
    "healthcare management": ["healthcare administration","medical management","hospital management","clinic management"],
    "teaching": ["education","instruction","pedagogy","classroom instruction","educator"],
    "curriculum development": ["curriculum design","lesson planning","syllabus creation"],
    "training": ["staff training","employee training","corporate training","workshop facilitation"],
    "tutoring": ["academic coaching","private tutoring","student mentorship","homeschooling"],
    "graphic design": ["adobe photoshop","illustrator","indesign","visual design","coreldraw","xd"],
    "video editing": ["film editing","premiere pro","final cut pro","davinci resolve","video production"],
    "content creation": ["copywriting","blog writing","content writing","ghostwriting","script writing"],
    "journalism": ["reporting","news writing","investigative journalism","editorial"],
    "civil engineering": ["structural engineering","infrastructure","construction engineering"],
    "mechanical engineering": ["cad","solidworks","autocad","thermodynamics","ansys"],
    "electrical engineering": ["circuit design","pcb","electronics","power systems"],
    "chemical engineering": ["process engineering","industrial chemistry","process design"],
    "legal": ["law","litigation","legal research","legal documentation","paralegal","contract law"],
    "logistics": ["supply chain","distribution","freight","transportation management","fleet management"],
    "data entry": ["typing","clerical","form entry","spreadsheet data entry"],
    "administrative support": ["office administration","executive assistance","office management","admin tasks"],
    "account management": ["client management","relationship management","account manager"],
    "event planning": ["event coordination","conference planning","wedding planning"],
    "culinary arts": ["cooking","baking","food preparation","menu design","food plating"]
}

# -------------------- LARGE skill_weights --------------------
skill_weights = {
    "python": 2.0, "java": 2.0, "c++": 2.0, "c#": 2.0, "javascript": 2.0,
    "web application development": 2.5, "software architecture": 2.5,
    "ui/ux design": 2.5, "database": 2.0, "cloud computing": 2.0,
    "docker container": 2.0, "machine learning": 2.5, "data analysis": 2.5,
    "devops": 2.0, "api development": 2.0, "cybersecurity": 2.5, "qa testing": 2.0,
    "project management": 2.5, "business analysis": 2.0, "sales": 2.0, "marketing": 2.5,
    "human resources": 2.0, "finance": 2.5, "customer service": 2.0,
    "supply chain management": 2.5, "patient care": 2.5, "nursing": 2.5,
    "medical coding": 2.0, "healthcare management": 2.5, "teaching": 2.5,
    "curriculum development": 2.0, "training": 2.0, "tutoring": 1.5,
    "graphic design": 2.0, "video editing": 2.0, "content creation": 2.0,
    "journalism": 2.0, "civil engineering": 2.5, "mechanical engineering": 2.5,
    "electrical engineering": 2.5, "chemical engineering": 2.5, "legal": 2.5,
    "logistics": 2.0, "data entry": 1.5, "administrative support": 1.5,
    "account management": 2.0, "event planning": 2.0, "culinary arts": 2.0,
    "business analysis": 2.0
}

# -------------------- HELPER FUNCTIONS --------------------
def extract_text_from_pdf(file_path):
    text = ''
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ''
                text += page_text
        return text.strip()
    except Exception as e:
        print(f"Error extracting text with pdfplumber: {e}")
        return ""

def tokenize_and_filter(text: str):
    """
    Regex-based approach: only keep alpha tokens, skip BUZZWORDS, unify synonyms from SKILL_MAP
    """
    tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    # skip if in BUZZWORDS
    filtered = [t for t in tokens if t not in BUZZWORDS]
    # unify synonyms from skill map
    unified = [unify_skill_map(t) for t in filtered]
    return set(unified)

def unify_skill_map(word: str) -> str:
    """
    Check if a word or partial of word is in any SKILL_MAP variant => unify to canonical skill
    e.g. 'aws environment' => 'cloud computing' if partial match
    """
    # example partial match approach:
    for canonical, variants in SKILL_MAP.items():
        for variant in variants:
            if variant in word or word in variant:
                return canonical
    return word

def compute_weighted_match_percentage(resume_skills: set, job_skills: set) -> float:
    total_weight = 0.0
    matched_weight = 0.0
    for skill in job_skills:
        w = skill_weights.get(skill, 1.0)  # default weight 1.0
        total_weight += w
        if skill in resume_skills:
            matched_weight += w
    if total_weight == 0:
        return 0.0
    return (matched_weight / total_weight) * 100

def analyze_resume(resume_text, job_description):
    resume_keywords = tokenize_and_filter(resume_text)
    job_keywords = tokenize_and_filter(job_description)

    matched_skills = resume_keywords.intersection(job_keywords)
    missing_skills = job_keywords - resume_keywords
    job_fit_score = round(compute_weighted_match_percentage(resume_keywords, job_keywords), 2)

    return {
        "skills": list(resume_keywords),
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
        "job_fit_score": job_fit_score,
        "job_description": job_description,
        "resume_text": resume_text
    }

def find_job_category(resume_text):
    """
    Predict top 10 categories from Kaggle's resume dataset using a logistic regression pipeline.
    """
    try:
        df_resume = pd.read_csv("data/UpdatedResumeDataSet.csv")
    except:
        return ["Unknown Category (CSV not found)"]

    X = df_resume['Resume']
    y = df_resume['Category']

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english')),
        ('chi2', SelectKBest(chi2, k=1000)),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    pipeline.fit(X, y)

    predicted_proba = pipeline.predict_proba([resume_text])[0]
    classes = pipeline.named_steps['clf'].classes_
    sorted_indices = np.argsort(-predicted_proba)
    top_indices = sorted_indices[:9]
    top_cats = [classes[j] for j in top_indices]
    return top_cats


# -------------------- FLASK APP --------------------
@app.route("/")
def home():
    return "Welcome to the Job Match App (keyword + skill_map approach)!"
@app.route('/edit-resume', methods=['GET', 'POST'])
def edit_resume():
    if request.method == 'POST':
        edited_text = request.form['edited_resume']
        action = request.form.get('action')

        with open('resume_text.txt', 'w', encoding='utf-8') as f:
            f.write(edited_text)

        if action == 'save_analyze':
            try:
                with open('job_description.txt', 'r', encoding='utf-8') as f:
                    job_description = f.read()
            except FileNotFoundError:
                return "<h2>Error: job_description.txt not found.</h2>"

            result = analyze_resume(edited_text, job_description)
            recommended_cats = find_job_category(edited_text)
            result["recommended_job"] = recommended_cats

            result_id = str(uuid.uuid4())
            result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
            with open(result_path, 'w') as f:
                json.dump(result, f)

            return redirect(url_for('get_results', result_id=result_id))

        return redirect(url_for('edit_resume', saved=1))

    try:
        with open('resume_text.txt', 'r', encoding='utf-8') as f:
            resume_text = f.read()
    except FileNotFoundError:
        resume_text = "No resume loaded."

    return render_template('edit_resume.html', resume_text=resume_text)

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
    job_description = request.form.get('job_description')
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400

    if 'resume' not in request.files:
        return jsonify({'error': 'Resume file is required'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    resume_text = extract_text_from_pdf(file_path)
    if not resume_text:
        return jsonify({'error': 'Failed to extract text from PDF'}), 500

    # ✅ Save the resume and job description for reuse in edit/analyze
    with open('resume_text.txt', 'w', encoding='utf-8') as f:
        f.write(resume_text)

    with open('job_description.txt', 'w', encoding='utf-8') as f:
        f.write(job_description)

    # Analyze
    result = analyze_resume(resume_text, job_description)
    recommended_cats = find_job_category(resume_text)
    result["recommended_job"] = recommended_cats

    result_id = str(uuid.uuid4())
    result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
    with open(result_path, 'w') as f:
        json.dump(result, f)

    return jsonify({
        "result_id": result_id,
        "redirect_url": f"/results/{result_id}"
    })

if __name__ == '__main__':
    app.run(debug=True)
