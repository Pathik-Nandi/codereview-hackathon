import { useState, useEffect } from 'react';
import prService from '../services/prService';
import './PRDetails.css';

const PRDetails = ({ pr, onClose }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchPRDetails();
  }, [pr]);

  const fetchPRDetails = async () => {
    setLoading(true);
    setError('');

    const result = await prService.getPRDetails(pr.repository, pr.pr_number);

    if (result.success) {
      setDetails(result.data);
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  if (loading) {
    return (
      <div className="pr-details-modal">
        <div className="pr-details-content loading">
          <div className="spinner"></div>
          <p>Loading PR details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pr-details-modal">
        <div className="pr-details-content error">
          <p>❌ {error}</p>
          <button onClick={onClose} className="btn-close">
            Close
          </button>
        </div>
      </div>
    );
  }

  // Extract PR data and issues from the API response
  const prData = details?.pr || {};
  const issues = details?.issues || [];
  const totalIssues = details?.total_issues || issues.length || 0;

  return (
    <div className="pr-details-modal" onClick={onClose}>
      <div className="pr-details-content" onClick={(e) => e.stopPropagation()}>
        <div className="pr-details-header">
          <div>
            <h2>#{pr.pr_number} {pr.pr_title}</h2>
            <span className="pr-repository-badge">{pr.repository}</span>
          </div>
          <button onClick={onClose} className="btn-close-icon">
            ✕
          </button>
        </div>

        <div className="pr-details-tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'issues' ? 'active' : ''}`}
            onClick={() => setActiveTab('issues')}
          >
            Issues ({totalIssues})
          </button>
          <button
            className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('analysis')}
          >
            Analysis
          </button>
          {prData.rag_insights && (
            <button
              className={`tab ${activeTab === 'rag' ? 'active' : ''}`}
              onClick={() => setActiveTab('rag')}
            >
              🤖 RAG Insights
            </button>
          )}
        </div>

        <div className="pr-details-body">
          {activeTab === 'overview' && (
            <div className="tab-content">
              <div className="score-cards">
                <div className="score-card">
                  <h3>Quality Score</h3>
                  <div className="score-value large">
                    {prData.overall_quality_score?.toFixed(1) || 'N/A'}
                  </div>
                </div>
                <div className="score-card">
                  <h3>Security Score</h3>
                  <div className="score-value large">
                    {prData.security_score?.toFixed(1) || 'N/A'}
                  </div>
                </div>
                <div className="score-card">
                  <h3>Maintainability</h3>
                  <div className="score-value large">
                    {prData.maintainability_score?.toFixed(1) || 'N/A'}
                  </div>
                </div>
              </div>

              <div className="info-section">
                <h3>PR Information</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Author:</span>
                    <span className="info-value">{prData.author_login || pr.author_login}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Files Changed:</span>
                    <span className="info-value">{prData.code_metrics?.files_changed || prData.files_changed || 0}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Lines Added:</span>
                    <span className="info-value text-success">+{prData.code_metrics?.lines_added || prData.lines_added || 0}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Lines Deleted:</span>
                    <span className="info-value text-danger">-{prData.code_metrics?.lines_deleted || prData.lines_deleted || 0}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Analyzed At:</span>
                    <span className="info-value">
                      {prData.analyzed_at ? new Date(prData.analyzed_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {prData.issues_by_severity && (
                <div className="info-section">
                  <h3>Issues by Severity</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">🔴 Critical:</span>
                      <span className="info-value">{prData.issues_by_severity.critical}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">🟠 High:</span>
                      <span className="info-value">{prData.issues_by_severity.high}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">🟡 Medium:</span>
                      <span className="info-value">{prData.issues_by_severity.medium}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">🟢 Low:</span>
                      <span className="info-value">{prData.issues_by_severity.low}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'issues' && (
            <div className="tab-content">
              {issues && issues.length > 0 ? (
                <div className="issues-list">
                  {issues.map((issue, index) => (
                    <div key={index} className={`issue-card ${issue.severity?.toLowerCase()}`}>
                      <div className="issue-header">
                        <span className={`severity-badge ${issue.severity?.toLowerCase()}`}>
                          {issue.severity}
                        </span>
                        <span className="issue-type">{issue.issue_type || issue.category}</span>
                      </div>
                      <h4 className="issue-title">{issue.title || issue.issue_type}</h4>
                      <p className="issue-message">{issue.description}</p>
                      {issue.file_path && (
                        <div className="issue-location">
                          <span>📄 {issue.file_path}</span>
                          {issue.line_number && <span>Line {issue.line_number}</span>}
                        </div>
                      )}
                      {issue.recommendation && (
                        <div className="issue-recommendation">
                          <strong>💡 Recommendation:</strong> {issue.recommendation}
                        </div>
                      )}
                      {issue.agent_name && (
                        <div className="issue-agent">
                          <small>🤖 Detected by: {issue.agent_name}</small>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>✅ No issues found!</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="tab-content">
              <div className="analysis-sections">
                {/* PR Metadata */}
                <div className="analysis-section">
                  <h3>📋 PR Metadata</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">PR Number:</span>
                      <span className="info-value">#{prData.pr_number}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Repository:</span>
                      <span className="info-value">{prData.repository}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Author:</span>
                      <span className="info-value">{prData.author_name || prData.author_login}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Email:</span>
                      <span className="info-value">{prData.author_email}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Base Branch:</span>
                      <span className="info-value">{prData.base_branch}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Head Branch:</span>
                      <span className="info-value">{prData.head_branch}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Created:</span>
                      <span className="info-value">
                        {prData.pr_created_at ? new Date(prData.pr_created_at).toLocaleString() : 'N/A'}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Updated:</span>
                      <span className="info-value">
                        {prData.pr_updated_at ? new Date(prData.pr_updated_at).toLocaleString() : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Code Metrics */}
                {prData.code_metrics && (
                  <div className="analysis-section">
                    <h3>📊 Code Metrics</h3>
                    <div className="info-grid">
                      <div className="info-item">
                        <span className="info-label">Files Changed:</span>
                        <span className="info-value">{prData.code_metrics.files_changed || 0}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Lines Added:</span>
                        <span className="info-value text-success">+{prData.code_metrics.lines_added || 0}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Lines Deleted:</span>
                        <span className="info-value text-danger">-{prData.code_metrics.lines_deleted || 0}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Complexity Score:</span>
                        <span className="info-value">{prData.code_metrics.complexity_score || 'N/A'}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Coverage:</span>
                        <span className="info-value">
                          {prData.code_metrics.estimated_coverage ? `${prData.code_metrics.estimated_coverage}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Test/Code Ratio:</span>
                        <span className="info-value">{prData.code_metrics.test_to_code_ratio || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Quality Scores */}
                <div className="analysis-section">
                  <h3>🎯 Quality Scores</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Overall Quality:</span>
                      <span className="info-value">{prData.overall_quality_score || 'N/A'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Security:</span>
                      <span className="info-value">{prData.security_score || 'N/A'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Maintainability:</span>
                      <span className="info-value">{prData.maintainability_score || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                {/* Issues Breakdown */}
                {prData.issues_by_severity && (
                  <div className="analysis-section">
                    <h3>⚠️ Issues by Severity</h3>
                    <div className="info-grid">
                      <div className="info-item">
                        <span className="info-label">🔴 Critical:</span>
                        <span className="info-value">{prData.issues_by_severity.critical}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">🟠 High:</span>
                        <span className="info-value">{prData.issues_by_severity.high}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">🟡 Medium:</span>
                        <span className="info-value">{prData.issues_by_severity.medium}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">🟢 Low:</span>
                        <span className="info-value">{prData.issues_by_severity.low}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Issues by Agent */}
                {prData.issues_by_agent && (
                  <div className="analysis-section">
                    <h3>🤖 Issues by Agent</h3>
                    <div className="info-grid">
                      <div className="info-item">
                        <span className="info-label">Static Analysis:</span>
                        <span className="info-value">{prData.issues_by_agent.static_analysis}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Security:</span>
                        <span className="info-value">{prData.issues_by_agent.security}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Code Quality:</span>
                        <span className="info-value">{prData.issues_by_agent.code_quality}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Context:</span>
                        <span className="info-value">{prData.issues_by_agent.context}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Coverage:</span>
                        <span className="info-value">{prData.issues_by_agent.coverage}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'rag' && prData.rag_insights && (
            <div className="tab-content">
              <div className="rag-insights-container">
                {/* RAG Scores */}
                <div className="rag-scores-section">
                  <div className="score-cards">
                    <div className="score-card rag-card">
                      <h3>🎯 Risk Score</h3>
                      <div className={`score-value large ${prData.rag_insights.risk_score > 0.7 ? 'high-risk' : prData.rag_insights.risk_score > 0.4 ? 'medium-risk' : 'low-risk'}`}>
                        {(prData.rag_insights.risk_score * 100).toFixed(0)}%
                      </div>
                      <p className="score-description">
                        {prData.rag_insights.risk_score > 0.7 ? 'High risk detected' : 
                         prData.rag_insights.risk_score > 0.4 ? 'Moderate risk' : 'Low risk'}
                      </p>
                    </div>
                    <div className="score-card rag-card">
                      <h3>✨ Novelty Score</h3>
                      <div className={`score-value large ${prData.rag_insights.novelty_score > 0.8 ? 'high-novelty' : prData.rag_insights.novelty_score > 0.5 ? 'medium-novelty' : 'low-novelty'}`}>
                        {(prData.rag_insights.novelty_score * 100).toFixed(0)}%
                      </div>
                      <p className="score-description">
                        {prData.rag_insights.novelty_score > 0.8 ? 'Highly innovative' : 
                         prData.rag_insights.novelty_score > 0.5 ? 'Moderately novel' : 'Common pattern'}
                      </p>
                    </div>
                    <div className="score-card rag-card">
                      <h3>🔍 Complexity</h3>
                      <div className="score-value large">{prData.rag_insights.complexity_assessment || 'N/A'}</div>
                      <p className="score-description">Assessed complexity level</p>
                    </div>
                  </div>
                </div>

                {/* RAG Analysis - Full Text */}
                {prData.rag_insights.full_text && (
                  <div className="rag-section">
                    <h3>🤖 RAG Analysis</h3>
                    <div className="rag-text-content" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                      {prData.rag_insights.full_text}
                    </div>
                  </div>
                )}

                {/* Summary (fallback if no full_text) */}
                {!prData.rag_insights.full_text && prData.rag_insights.summary && (
                  <div className="rag-section">
                    <h3>📝 Summary</h3>
                    <p className="rag-text">{prData.rag_insights.summary}</p>
                  </div>
                )}

                {/* Similar PRs */}
                {prData.rag_insights.similar_prs && prData.rag_insights.similar_prs.length > 0 && (
                  <div className="rag-section">
                    <h3>🔗 Similar PRs ({prData.rag_insights.similar_prs_found})</h3>
                    <div className="similar-prs-list">
                      {prData.rag_insights.similar_prs.map((similarPR, index) => (
                        <div key={index} className="similar-pr-card">
                          <div className="similar-pr-header">
                            <span className="similar-pr-number">#{similarPR.pr_number || 'N/A'}</span>
                            <span className="similarity-score">{(similarPR.similarity_score * 100).toFixed(0)}% similar</span>
                          </div>
                          {similarPR.similarity_type && (
                            <div className="similarity-type">Type: {similarPR.similarity_type}</div>
                          )}
                          {similarPR.lesson_extracted && (
                            <div className="lesson-learned">
                              <strong>💡 Lesson:</strong> {similarPR.lesson_extracted}
                            </div>
                          )}
                          {similarPR.pattern_identified && (
                            <div className="pattern-identified">
                              <strong>🔍 Pattern:</strong> {similarPR.pattern_identified}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {prData.rag_insights.detailed_recommendations && prData.rag_insights.detailed_recommendations.length > 0 && (
                  <div className="rag-section">
                    <h3>💡 RAG Recommendations ({prData.rag_insights.detailed_recommendations.length})</h3>
                    <div className="recommendations-list">
                      {prData.rag_insights.detailed_recommendations.map((rec, index) => (
                        <div key={index} className={`recommendation-card priority-${rec.priority}`}>
                          <div className="recommendation-header">
                            <span className={`priority-badge ${rec.priority}`}>{rec.priority}</span>
                            <span className="recommendation-type">{rec.type}</span>
                          </div>
                          <h4 className="recommendation-title">{rec.title}</h4>
                          <p className="recommendation-description">{rec.description}</p>
                          {rec.reasoning && (
                            <div className="recommendation-reasoning">
                              <strong>Why:</strong> {rec.reasoning}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Lessons Learned - only show if no full_text */}
                {!prData.rag_insights.full_text && prData.rag_insights.lessons_learned && (
                  <div className="rag-section">
                    <h3>📚 Lessons Learned</h3>
                    <div className="rag-text-content">
                      {prData.rag_insights.lessons_learned}
                    </div>
                  </div>
                )}

                {/* Potential Pitfalls - only show if no full_text */}
                {!prData.rag_insights.full_text && prData.rag_insights.potential_pitfalls && (
                  <div className="rag-section">
                    <h3>⚠️ Potential Pitfalls</h3>
                    <div className="rag-text-content">
                      {prData.rag_insights.potential_pitfalls}
                    </div>
                  </div>
                )}

                {/* Best Practices - only show if no full_text */}
                {!prData.rag_insights.full_text && prData.rag_insights.best_practices_suggested && (
                  <div className="rag-section">
                    <h3>✅ Best Practices Suggested</h3>
                    <div className="rag-text-content">
                      {prData.rag_insights.best_practices_suggested}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="pr-details-footer">
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
          <a
            href={pr.pr_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            View on GitHub →
          </a>
        </div>
      </div>
    </div>
  );
};

export default PRDetails;
