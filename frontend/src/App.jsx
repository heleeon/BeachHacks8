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
        style={{
          fontFamily: 'inherit',
          letterSpacing: 'normal',
          lineHeight: '1.5',
          padding: '10px',
          whiteSpace: 'pre-wrap'
        }}
      />
      </div>
      <div>
        <input type="file" onChange={handleResumeChange} />
      </div>
      <div>
        <button onClick={analyzeJobAndResume}>Analyze</button>
      </div>
      {error && <p style={{ color: "red" }}>{error}</p>}
      
    </div>
  );
};
function createCloud() {
  const cloud = document.createElement('div');
  cloud.className = 'moving-cloud';
  
  // Apply background image styles
  cloud.style.backgroundImage = 'url("https://openclipart.org/download/193560/1400625045.svg")';
  cloud.style.backgroundSize = 'contain';  // Changed to 'contain' to show whole image
  cloud.style.backgroundPosition = 'center';  // Center the background image
  cloud.style.backgroundRepeat = 'no-repeat';
  
  // Random cloud size
  const size = Math.random() * (150 - 50) + 50;
  cloud.style.width = `${size}px`;
  cloud.style.height = `${size}px`;
  
  cloud.style.top = `${Math.random() * 80}vh`;
  const duration = Math.random() * (120 - 60) + 60;
  cloud.style.animationDuration = `${duration}s`;
  
  document.getElementById('root').appendChild(cloud);
  
  cloud.addEventListener('animationend', () => {
    cloud.remove();
  });
}

// Create new clouds periodically
setInterval(createCloud, 10000); // Creates a new cloud every 10 seconds

// Initial clouds
for(let i = 0; i < 5; i++) {
  setTimeout(createCloud, i * 1000);
}

export default App;
