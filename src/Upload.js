
import { useRef, useState } from "react";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function Upload({ onResult }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pastedText, setPastedText] = useState("");
  const [activeTab, setActiveTab] = useState("upload");
  const [selectedFile, setSelectedFile] = useState(null);

  const inputRef = useRef(null);

  async function analyzeFile(file) {
    if (!file) return;

    setError("");

    const extension = file.name.toLowerCase().split(".").pop();

    if (!["pdf", "txt"].includes(extension)) {
      setError("Please select a PDF or TXT file.");
      return;
    }

    if (file.size === 0) {
      setError("The selected file is empty.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size must be 10 MB or less.");
      return;
    }

    setLoading(true);

    const form = new FormData();
    form.append("file", file);

    try {
      const response = await fetch(
        "http://localhost:8000/analyze",
        {
          method: "POST",
          body: form,
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail || "The document could not be analysed."
        );
      }

      onResult(result, file.name);
    } catch (err) {
      setError(
        err.message ||
        "Could not connect to the backend. Make sure it is running."
      );
    } finally {
      setLoading(false);
    }
  }

  async function analyzePastedText() {
    const cleanedText = pastedText.trim();

    if (!cleanedText) {
      setError("Please paste your contract text first.");
      return;
    }

    const textFile = new File(
      [cleanedText],
      "pasted-contract.txt",
      { type: "text/plain" }
    );

    await analyzeFile(textFile);
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0];

    if (file) {
      setSelectedFile(file);
      setError("");
    }
  }

  const wordCount = pastedText.trim()
    ? pastedText.trim().split(/\s+/).length
    : 0;

  return (
    <main className="landing">

      <section className="hero">
        <div className="hero-eyebrow">
          <span className="eyebrow-icon">✦</span>
          YOUR CONTRACT, MADE CLEARER
        </div>

        <h1>
          Don't just sign.
          <br />
          <span>Understand first.</span>
        </h1>

        <p className="hero-description">
          Contracts shouldn't feel like a foreign language.
          Understand important clauses, discover potential
          red flags, and make more informed decisions.
        </p>

        <div className="hero-trust">
          <span><span className="trust-check">✓</span> Simple explanations</span>
          <span><span className="trust-check">✓</span> Clause detection</span>
          <span><span className="trust-check">✓</span> Quick analysis</span>
        </div>
      </section>

      <section className="analyzer-card">

        <div className="analyzer-heading">
          <div>
            <span className="section-kicker">GET STARTED</span>
            <h2>Analyse your contract</h2>
            <p>Choose how you'd like to share your document.</p>
          </div>

          <div className="document-icon">▤</div>
        </div>

        <div className="analyzer-tabs">
          <button
            className={`analyzer-tab ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("upload");
              setError("");
            }}
            disabled={loading}
          >
            <span>↑</span>
            Upload document
          </button>

          <button
            className={`analyzer-tab ${activeTab === "paste" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("paste");
              setError("");
            }}
            disabled={loading}
          >
            <span>▤</span>
            Paste text
          </button>
        </div>

        {activeTab === "upload" && (
          <div className="upload-panel">

            <div
              className={`upload-dropzone ${selectedFile ? "has-file" : ""}`}
              onClick={() => !loading && inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" ||
                  event.key === " "
                ) {
                  event.preventDefault();
                  inputRef.current?.click();
                }
              }}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                hidden
                onChange={handleFileChange}
                disabled={loading}
              />

              <div className="upload-icon">
                {selectedFile ? "✓" : "↑"}
              </div>

              {selectedFile ? (
                <>
                  <h3>{selectedFile.name}</h3>
                  <p>
                    {(selectedFile.size / 1024).toFixed(1)} KB · Ready to analyse
                  </p>
                  <span className="browse-link">Choose another file</span>
                </>
              ) : (
                <>
                  <h3>Drop your document here</h3>
                  <p>or <span className="browse-link">browse files</span> from your device</p>
                  <span className="file-types">PDF or TXT · Maximum 10 MB</span>
                </>
              )}
            </div>

            <button
              className="primary-button"
              onClick={() => analyzeFile(selectedFile)}
              disabled={loading || !selectedFile}
            >
              {loading ? "Analysing document..." : "Analyse document"}
              {!loading && <span>→</span>}
            </button>
          </div>
        )}

        {activeTab === "paste" && (
          <div className="paste-panel">
            <label htmlFor="contract-text">
              CONTRACT TEXT
            </label>

            <textarea
              id="contract-text"
              className="contract-input"
              placeholder="Paste your agreement, terms and conditions, or any contract text here..."
              value={pastedText}
              onChange={(event) => {
                setPastedText(event.target.value);
                setError("");
              }}
              disabled={loading}
            />

            <div className="textarea-meta">
              <span>{wordCount} words</span>
              <span>Your text is processed for this analysis</span>
            </div>

            <button
              className="primary-button"
              onClick={analyzePastedText}
              disabled={loading || !pastedText.trim()}
            >
              {loading ? "Analysing text..." : "Analyse pasted text"}
              {!loading && <span>→</span>}
            </button>
          </div>
        )}

        {loading && (
          <div className="loading-message">
            <span className="loading-spinner"></span>
            Analysing your document. This may take a moment...
          </div>
        )}

        {error && (
          <div className="error-message">
            <span>!</span>
            {error}
          </div>
        )}

        <div className="privacy-note">
          <span>⌑</span>
          Informational analysis only. Not legal advice.
        </div>
      </section>

      <section className="features" id="how-it-works">
        <div className="feature-card">
          <div className="feature-icon blue">⌕</div>
          <h3>Find important clauses</h3>
          <p>Identify contract terms that deserve a closer look.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon lavender">文</div>
          <h3>Understand the language</h3>
          <p>Get simpler explanations of selected legal wording.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon peach">⚑</div>
          <h3>Spot potential concerns</h3>
          <p>See detected clauses grouped by their heuristic severity.</p>
        </div>
      </section>

      <section className="disclaimer">
        <strong>A note about your results</strong>
        <p>
          ClauseWise uses rule-based detection to highlight potentially
          important contract language. It may miss clauses or flag
          phrases that are not relevant in context. Always review the
          original agreement and consult a qualified legal professional
          when needed.
        </p>
      </section>

    </main>
  );
}
