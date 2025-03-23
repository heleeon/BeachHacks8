import { useState } from 'react';
import axios from "axios";
import './App.css';

function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [buttonText, setButtonText] = useState("Submit Resume / CV (.pdf, .doc, etc)");
  const [resultUrl, setResultUrl] = useState(null);
  const [error, setError] = useState(null);

  const handleJobDescriptionChange = (e) => {
    setJobDescription(e.target.value);
  };

  const handleResumeChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!resumeFile || !jobDescription) {
      setError("Please upload a resume and enter a job description.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("job_description", jobDescription);

    try {
      setLoading(true);
      setButtonText("Analyzing...");

      const response = await axios.post("http://127.0.0.1:5000/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.result_id) {
        const resultUrl = `http://127.0.0.1:5000/results/${response.data.result_id}`;
        setResultUrl(resultUrl);
        setButtonText("See Results");
        setLoading(false);
      } else {
        throw new Error("Unexpected server response");
      }
    } catch (err) {
      setError("Error analyzing data: " + err.message);
      setLoading(false);
      setButtonText("Submit Resume / CV (.pdf, .doc, etc)");
    }
  };

  const handleClick = () => {
    if (resultUrl) {
      window.open(resultUrl, '_blank');
    } else {
      handleSubmit();
    }
  };

  return (
    <div className="app-container">
      <h1 className="typewriter-container">SharkAI Resume Matcher</h1>

      <textarea
        className="job-input"
        placeholder="Paste Job Description Here"
        value={jobDescription}
        onChange={handleJobDescriptionChange}
      />

      <div className="file-upload-container">
        <input
          type="file"
          className="file-input"
          id="resume-upload"
          onChange={handleResumeChange}
          accept=".pdf,.doc,.docx"
        />
        <label
          htmlFor="resume-upload"
          className={`upload-button ${buttonText === "See Results" ? "upload-complete" : ""}`}
          onClick={handleClick}
        >
          {loading ? "Analyzing..." : buttonText}
        </label>
      </div>

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default App;
