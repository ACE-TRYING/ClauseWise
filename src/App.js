
import { useState } from "react";
import Upload from "./Upload";
import Dashboard from "./Dashboard";
import "./App.css";

export default function App() {
  const [data, setData] = useState(null);
  const [name, setName] = useState("");

  function handleResult(result, filename) {
    setData(result);
    setName(filename);
  }

  function handleBack() {
    setData(null);
    setName("");
  }

  return (
    <div className="app-shell">
      <header className="navbar">
        <div className="nav-inner">
          <div className="brand">
            <div className="brand-icon">C</div>
            <span>Clause<span className="brand-light">Wise</span></span>
          </div>

          <div className="nav-right">
            <span className="nav-status">
              <span className="status-dot"></span>
              AI-assisted contract insights
            </span>
            <a href="#how-it-works" className="nav-link">
              How it works
            </a>
          </div>
        </div>
      </header>

      {data ? (
        <Dashboard
          data={data}
          name={name}
          onBack={handleBack}
        />
      ) : (
        <Upload onResult={handleResult} />
      )}

      <footer className="footer">
        <div className="footer-inner">
          <div className="brand footer-brand">
            <div className="brand-icon small">C</div>
            <span>Clause<span className="brand-light">Wise</span></span>
          </div>

          <p>
            Understand the fine print. Make more informed decisions.
          </p>

          <span className="footer-copy">
            © {new Date().getFullYear()} ClauseWise
          </span>
        </div>
      </footer>
    </div>
  );
}
