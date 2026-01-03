import { useState, useEffect } from 'react';
import prService from '../services/prService';
import './PRDetails.css';

const PRDetails = ({ pr, onClose, isInline = false }) => {
  const [details, setDetails] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingComments, setLoadingComments] = useState(false);
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

  const fetchPRComments = async () => {
    if (comments.length > 0) return; // Already loaded
    
    setLoadingComments(true);
    // First load: fetch comments WITHOUT code context for speed
    const result = await prService.getPRComments(pr.repository, pr.pr_number, false);

    if (result.success) {
      setComments(result.data.comments || []);
    } else {
      console.error('Failed to fetch comments:', result.error);
    }

    setLoadingComments(false);
  };

  // Load code context for all comments (lazy load on demand)
  const loadCodeContext = async () => {
    if (comments.some(c => c.code_context)) return; // Already loaded
    
    setLoadingComments(true);
    const result = await prService.getPRCommentsWithCode(pr.repository, pr.pr_number);

    if (result.success) {
      setComments(result.data.comments || []);
    } else {
      console.error('Failed to fetch code context:', result.error);
    }

    setLoadingComments(false);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'comments') {
      fetchPRComments();
    }
  };

  if (loading) {
    return (
      <div className={isInline ? "pr-details-inline loading" : "pr-details-modal"}>
        <div className={isInline ? "pr-details-inline-content loading" : "pr-details-content loading"}>
          <div className="spinner"></div>
          <p>Loading PR details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={isInline ? "pr-details-inline error" : "pr-details-modal"}>
        <div className={isInline ? "pr-details-inline-content error" : "pr-details-content error"}>
          <p>❌ {error}</p>
          {!isInline && (
            <button onClick={onClose} className="btn-close">
              Close
            </button>
          )}
        </div>
      </div>
    );
  }

  // Extract PR data and issues from the API response
  const prData = details?.pr || {};
  const issues = details?.issues || [];
  const totalIssues = details?.total_issues || issues.length || 0;

  const containerClass = isInline ? "pr-details-inline" : "pr-details-modal";
  const contentClass = isInline ? "pr-details-inline-content" : "pr-details-content";

  return (
    <div className={containerClass} onClick={!isInline ? onClose : undefined}>
      <div className={contentClass} onClick={(e) => !isInline && e.stopPropagation()}>
        {!isInline && (
          <div className="pr-details-header">
            <div>
              <h2>#{pr.pr_number} {pr.pr_title}</h2>
              <span className="pr-repository-badge">{pr.repository}</span>
            </div>
            <button onClick={onClose} className="btn-close-icon">
              ✕
            </button>
          </div>
        )}

        <div className="pr-details-tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => handleTabChange('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'issues' ? 'active' : ''}`}
            onClick={() => handleTabChange('issues')}
          >
            Issues ({totalIssues})
          </button>
          <button
            className={`tab ${activeTab === 'comments' ? 'active' : ''}`}
            onClick={() => handleTabChange('comments')}
          >
            💬 Comments ({loadingComments ? '...' : comments.length})
          </button>
          <button
            className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
            onClick={() => handleTabChange('analysis')}
          >
            Analysis
          </button>
          {prData.rag_insights && (
            <button
              className={`tab ${activeTab === 'rag' ? 'active' : ''}`}
              onClick={() => handleTabChange('rag')}
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

          {activeTab === 'comments' && (
            <div className="tab-content">
              {loadingComments ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading comments...</p>
                </div>
              ) : comments && comments.length > 0 ? (
                  <div className="github-style-comments">
                  {/* Show "Load Code Context" button if code not loaded yet */}
                  {comments.length > 0 && !comments[0].code_context && (
                    <div className="load-code-banner">
                      <button 
                        className="btn-load-code" 
                        onClick={loadCodeContext}
                        disabled={loadingComments}
                      >
                        {loadingComments ? '⏳ Loading...' : '📄 Show Code Context'}
                      </button>
                      <span className="banner-hint">Click to view GitHub code for all comments</span>
                    </div>
                  )}
                  
                  {/* Group comments by file */}
                  {Object.entries(
                    comments.reduce((acc, comment) => {
                      const file = comment.file_path || 'General Comments';
                      if (!acc[file]) acc[file] = [];
                      acc[file].push(comment);
                      return acc;
                    }, {})
                  ).map(([file, fileComments]) => (
                    <div key={file} className="file-diff-view">
                      <div className="file-diff-header">
                        <span className="file-icon">📄</span>
                        <span className="file-path">{file}</span>
                        <span className="file-stats">{fileComments.length} comment{fileComments.length !== 1 ? 's' : ''}</span>
                      </div>
                      
                      <div className="diff-content">
                        {fileComments.map((comment, idx) => (
                          <div key={comment.id} className="code-comment-block">
                            
                            {/* Display code context if available */}
                            {comment.code_context && comment.code_context.lines && (
                              <div className="code-block">
                                {comment.code_context.lines.map((line) => (
                                  <div 
                                    key={line.line_number} 
                                    className={`code-line ${line.is_target ? 'target-line' : ''}`}
                                  >
                                    <div className="line-number">{line.line_number}</div>
                                    <div className="line-content">
                                      <pre><code>{line.content}</code></pre>
                                    </div>
                                    {line.is_target && (
                                      <div className="line-comment-indicator">
                                        <div className={`comment-bubble ${comment.issue_severity?.toLowerCase() || ''}`}>
                                          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                            <path d="M1.75 1h12.5c.966 0 1.75.784 1.75 1.75v9.5A1.75 1.75 0 0 1 14.25 14H8.061l-2.574 2.573A1.458 1.458 0 0 1 3 15.543V14H1.75A1.75 1.75 0 0 1 0 12.25v-9.5C0 1.784.784 1 1.75 1ZM1.5 2.75v9.5c0 .138.112.25.25.25h2a.75.75 0 0 1 .75.75v2.19l2.72-2.72a.749.749 0 0 1 .53-.22h6.5a.25.25 0 0 0 .25-.25v-9.5a.25.25 0 0 0-.25-.25H1.75a.25.25 0 0 0-.25.25Z"></path>
                                          </svg>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {/* Fallback: Show line number only if no code context */}
                            {!comment.code_context && comment.line_number && (
                              <div className="code-line-with-comment">
                                <div className="line-number">{comment.line_number}</div>
                                <div className="line-indicator">
                                  <div className={`comment-indicator ${comment.issue_severity?.toLowerCase() || ''}`}>
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                      <path d="M1.75 1h12.5c.966 0 1.75.784 1.75 1.75v9.5A1.75 1.75 0 0 1 14.25 14H8.061l-2.574 2.573A1.458 1.458 0 0 1 3 15.543V14H1.75A1.75 1.75 0 0 1 0 12.25v-9.5C0 1.784.784 1 1.75 1ZM1.5 2.75v9.5c0 .138.112.25.25.25h2a.75.75 0 0 1 .75.75v2.19l2.72-2.72a.749.749 0 0 1 .53-.22h6.5a.25.25 0 0 0 .25-.25v-9.5a.25.25 0 0 0-.25-.25H1.75a.25.25 0 0 0-.25.25Z"></path>
                                    </svg>
                                  </div>
                                </div>
                              </div>
                            )}
                            
                            {/* GitHub-style comment thread */}
                            <div className="comment-thread">
                              <div className="comment-thread-header">
                                <div className="comment-meta">
                                  <span className="comment-author">
                                    <svg className="avatar-icon" width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                                      <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Zm7-3.25v2.992l2.028.812a.75.75 0 0 1-.557 1.392l-2.5-1A.751.751 0 0 1 7 8.25v-3.5a.75.75 0 0 1 1.5 0Z"></path>
                                    </svg>
                                    Code Review Bot
                                  </span>
                                  <span className="comment-timestamp">
                                    {comment.posted_at ? new Date(comment.posted_at).toLocaleDateString() : 'Recently'}
                                  </span>
                                  {comment.issue_severity && (
                                    <span className={`severity-label ${comment.issue_severity.toLowerCase()}`}>
                                      {comment.issue_severity}
                                    </span>
                                  )}
                                  {comment.issue_type && (
                                    <span className="issue-type-label">{comment.issue_type}</span>
                                  )}
                                </div>
                                {comment.was_resolved && (
                                  <span className="resolved-badge">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                      <path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path>
                                    </svg>
                                    Resolved
                                  </span>
                                )}
                              </div>
                              
                              <div className="comment-body-github">
                                <div className="comment-text">{comment.comment_body}</div>
                                
                                {/* Reactions and actions */}
                                <div className="comment-actions">
                                  <div className="comment-reactions">
                                    {comment.reactions_count > 0 && (
                                      <span className="reaction-count">
                                        👍 {comment.reactions_count}
                                      </span>
                                    )}
                                    {comment.replies_count > 0 && (
                                      <span className="reply-count">
                                        💬 {comment.replies_count} {comment.replies_count === 1 ? 'reply' : 'replies'}
                                      </span>
                                    )}
                                  </div>
                                  {comment.github_url && (
                                    <a
                                      href={comment.github_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="github-link-btn"
                                    >
                                      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                        <path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path>
                                      </svg>
                                      View on GitHub
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>💬 No review comments found for this PR</p>
                  <small>Comments will appear here when code reviews are posted</small>
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
