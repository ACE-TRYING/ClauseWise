
import { useState } from "react";

function severityLabel(value) {
  const level = (value || "low").toLowerCase();

  if (level === "high") return "Needs attention";
  if (level === "medium") return "Worth checking";
  return "Informational";
}

function ClauseCard({ clause, index }) {
  const [expanded, setExpanded] = useState(false);

  const original = (clause.sentence || "").trim();
  const simplified = (clause.simplified || "").trim();

  // Never present the original sentence as its own simplification.
  const hasRealExplanation =
    simplified.length > 0 &&
    simplified.replace(/\s+/g, " ").toLowerCase() !==
      original.replace(/\s+/g, " ").toLowerCase();

  const severity = (clause.severity || "low").toLowerCase();

  return (
    <article className="result-clause">
      <div className="result-clause-top">
        <div className={`result-number ${severity}`}>
          {String(index + 1).padStart(2, "0")}
        </div>

        <div className="result-clause-title">
          <span className={`result-tag ${severity}`}>
            {severityLabel(severity)}
          </span>
          <h3>{clause.type || "Contract clause"}</h3>
        </div>

        <button
          className="result-expand"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
        >
          {expanded ? "Less detail −" : "Read more +"}
        </button>
      </div>

      <div className="result-explanation">
        <span className="result-small-label">IN EVERYDAY LANGUAGE</span>

        {hasRealExplanation ? (
          <p>{simplified}</p>
        ) : (
          <p className="explanation-missing">
            A simpler explanation hasn't been generated for this clause yet.
            The original wording is available below.
          </p>
        )}
      </div>

      {expanded && (
        <div className="result-details">
          <div className="result-detail-block">
            <span className="result-small-label">WHAT THE CONTRACT SAYS</span>
            <p className="result-original">{original || "Original wording unavailable."}</p>
          </div>

          {clause.why && (
            <div className="result-detail-block">
              <span className="result-small-label">WHY IT MATTERS</span>
              <p>{clause.why}</p>
            </div>
          )}

          {clause.tip && (
            <div className="result-detail-block">
              <span className="result-small-label">WHAT YOU SHOULD CHECK</span>
              <p>{clause.tip}</p>
            </div>
          )}

          {clause.matched && (
            <div className="result-matched">
              Detected phrase: <strong>{clause.matched}</strong>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export default function Dashboard({ data, name, onBack }) {
  const [showFullText, setShowFullText] = useState(false);

  const clauses = data.clauses || [];
  const sentences = data.sentences || [];

  const count = (severity) =>
    clauses.filter(
      (clause) => (clause.severity || "").toLowerCase() === severity
    ).length;

  const highCount = count("high");
  const mediumCount = count("medium");
  const lowCount = count("low");

  const level = (data.level || "low").toLowerCase();

  const overview = {
    high: {
      heading: "Some terms deserve your attention.",
      description:
        "We found clauses that may place important responsibilities or restrictions on you. Read these carefully before making a decision.",
    },
    medium: {
      heading: "A few terms are worth checking.",
      description:
        "Some clauses may affect your rights or responsibilities. Take a moment to understand what they mean.",
    },
    low: {
      heading: "No major warning was detected.",
      description:
        "Our rule-based checks found relatively few concerning phrases. This does not guarantee that the contract is safe.",
    },
  };

  const currentOverview = overview[level] || overview.low;

  return (
    <main className="results-page">

      <button className="results-back" onClick={onBack}>
        ← Analyse another document
      </button>

      <header className="results-intro">
        <span className="results-eyebrow">YOUR CONTRACT REVIEW</span>
        <h1>Let's make sense<br />of the fine print.</h1>
        <p>
          We've reviewed <strong>{name || "your document"}</strong>.
          Here's what we think you should look at.
        </p>
      </header>

      <section className={`results-overview ${level}`}>
        <div className="overview-topline">
          <span className="overview-label">THE OVERALL PICTURE</span>
          <span className={`overview-status ${level}`}>
            {level === "high"
              ? "Attention needed"
              : level === "medium"
              ? "Review recommended"
              : "Fewer concerns detected"}
          </span>
        </div>

        <h2>{currentOverview.heading}</h2>
        <p>{data.summary || currentOverview.description}</p>

        <div className="overview-counts">
          <div>
            <strong>{highCount}</strong>
            <span>Needs attention</span>
          </div>
          <div>
            <strong>{mediumCount}</strong>
            <span>Worth checking</span>
          </div>
          <div>
            <strong>{lowCount}</strong>
            <span>Informational</span>
          </div>
        </div>

        <div className="overview-footnote">
          Based on {clauses.length} detected clauses and {data.word_count || 0} words.
          This is a rule-based indicator, not a legal risk assessment.
        </div>
      </section>

      <section className="results-list-section">
        <div className="results-section-heading">
          <div>
            <span className="results-eyebrow">YOUR READING LIST</span>
            <h2>Things to look at</h2>
            <p>Start with the important points. Open any item to see its original wording.</p>
          </div>

          <span className="results-total">
            {clauses.length} {clauses.length === 1 ? "finding" : "findings"}
          </span>
        </div>

        {clauses.length === 0 ? (
          <div className="results-empty">
            <span>✦</span>
            <h3>Nothing was flagged by our checks.</h3>
            <p>
              This doesn't mean every term is harmless. Read the full agreement
              before signing.
            </p>
          </div>
        ) : (
          <div className="results-clause-list">
            {clauses.map((clause, index) => (
              <ClauseCard
                key={`${clause.type}-${index}`}
                clause={clause}
                index={index}
              />
            ))}
          </div>
        )}
      </section>

      <section className="full-text-section">
        <button
          className="full-text-toggle"
          onClick={() => setShowFullText(!showFullText)}
          aria-expanded={showFullText}
        >
          <span>
            <strong>Read the complete document</strong>
            <small>{sentences.length} extracted sentences</small>
          </span>
          <span>{showFullText ? "−" : "+"}</span>
        </button>

        {showFullText && (
          <div className="full-text-content">
            {sentences.map((sentence, index) => {
              const matching = clauses.find(
                (clause) => clause.sentence === sentence
              );

              return (
                <p
                  key={index}
                  className={
                    matching
                      ? `full-text-highlight ${(matching.severity || "low").toLowerCase()}`
                      : ""
                  }
                >
                  {sentence}
                </p>
              );
            })}
          </div>
        )}
      </section>

      <aside className="results-note">
        <span>ⓘ</span>
        <p>
          <strong>A note before you decide.</strong>
          ClauseWise uses rule-based checks to identify potentially important
          wording. It can miss risks or flag phrases without understanding
          their full legal context. This is not legal advice. Consult a
          qualified professional if you are unsure.
        </p>
      </aside>

      <button className="results-finish-button" onClick={onBack}>
        Review another document <span>→</span>
      </button>

    </main>
  );
}
