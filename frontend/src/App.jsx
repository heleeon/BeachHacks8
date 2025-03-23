import { useState } from 'react'
import axios from "axios";
import './App.css'

function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeSkills, setResumeSkills] = useState([]);
  const [jobFitScore, setJobFitScore] = useState(null);
  const [error, setError] = useState(null);

  const handleJobDescriptionChange = (e) => {
    setJobDescription(e.target.value);
  };

  const handleResumeChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const analyzeJobAndResume = async () => {
    if (!resumeFile || !jobDescription) {
      setError("Please upload a resume and paste a job description.");
      return;
    }
  
    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("job_description", jobDescription);
  
    try {
      const response = await axios.post("http://127.0.0.1:5000/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      if (response.data.result_id) {
        // First fetch the results
        const resultResponse = await axios.get(
          `http://127.0.0.1:5000/results/${response.data.result_id}`
        );
        
        // Update the state with the results
        setResumeSkills(resultResponse.data.skills);
        setJobFitScore(resultResponse.data.job_fit_score);
        
        // Open results in new tab
        const resultUrl = `http://127.0.0.1:5000/results/${response.data.result_id}`;
        window.open(resultUrl, '_blank');
      }
    } catch (err) {
      setError("Error analyzing data: " + err.message);
    }
  };
  

  return (
    <div>
      <h1>Job Skill Match</h1>
      <div>
        <textarea
          placeholder="Paste Job Description Here"
          value={jobDescription}
          onChange={handleJobDescriptionChange}
          rows="10"
          cols="50"
        />
      </div>
      <div>
        <input type="file" onChange={handleResumeChange} />
      </div>
      <div>
        <button onClick={analyzeJobAndResume}>Analyze</button>
      </div>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <div>
        <h3>Resume Skills: {resumeSkills.length > 0 ? resumeSkills.join(", ") : "No skills detected"}</h3>
        <h3>Job Fit Score: {jobFitScore !== null ? `${jobFitScore}%` : "Not available"}</h3>
      </div>
    </div>
  );
};

export default App;
