import { useState, useEffect } from 'react';
import prService from '../services/prService';
import './Analytics.css';

// Helper functions
const getScoreClass = (score) => {
  if (!score) return '';
  if (score >= 90) return 'excellent';
  if (score >= 80) return 'good';
  if (score >= 70) return 'fair';
  if (score >= 60) return 'poor';
  return 'critical';
};

const getTrendIcon = (trend) => {
  if (!trend) return '➡️ ';
  const trendLower = trend.toLowerCase();
  if (trendLower === 'improving' || trendLower === 'up') return '📈 ';
  if (trendLower === 'declining' || trendLower === 'down') return '📉 ';
  return '➡️ ';
};

const Analytics = ({ userEmail }) => {
  const [data, setData] = useState({
    summary: null,
    recommendations: null,
    trends: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAnalytics = async () => {
    if (!userEmail) {
      setLoading(false);
      setError('No user login provided');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const [summaryResult, recommendationsResult, trendsResult] = await Promise.all([
        prService.getUserAnalytics(userEmail),
        prService.getUserRecommendations(userEmail),
        prService.getUserTrends(userEmail),
      ]);

      setData({
        summary: summaryResult.success ? summaryResult.data : null,
        recommendations: recommendationsResult.success ? recommendationsResult.data : null,
        trends: trendsResult.success ? trendsResult.data : null
      });

      // Set loading to false first to show something
      setLoading(false);

      if (!summaryResult.success && !recommendationsResult.success && !trendsResult.success) {
        const errors = [
          summaryResult.error,
          recommendationsResult.error,
          trendsResult.error
        ].filter(Boolean);
        
        setError(errors.length > 0 ? errors[0] : 'No analytics data available. Analyze some pull requests first!');
      }
    } catch (err) {
      setError(`Failed to load analytics data: ${err.message}`);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userEmail]);

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner"></div>
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <div className="error-icon">📊</div>
        <p>{error}</p>
        <button onClick={fetchAnalytics} className="btn-retry">
          🔄 Retry
        </button>
      </div>
    );
  }

  const { summary, recommendations, trends } = data;
  
  // Check if we have any data at all
  const hasData = (summary && Object.keys(summary).length > 0) || 
                  (recommendations && Object.keys(recommendations).length > 0) || 
                  (trends && Object.keys(trends).length > 0);
  
  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h2>📊 Analytics Dashboard</h2>
        <p className="analytics-subtitle">User: {userEmail}</p>
      </div>

      {/* Show message if no data */}
      {!hasData && (
        <div className="analytics-section">
          <h3>⚠️ No Analytics Data</h3>
          <p>No analytics data available yet. Analyze some pull requests first!</p>
          <button onClick={fetchAnalytics} className="btn-retry">
            🔄 Retry
          </button>
        </div>
      )}

      {/* Performance Summary Section */}
      {summary && Object.keys(summary).length > 0 && (
        <div className="analytics-section">
          <h3><span className="section-icon">🎯</span> Performance Summary</h3>
          <p className="section-subtitle">Last {summary.period_days || 30} days</p>
          
          <div className="performance-grid">
            <div className="performance-card">
              <div className="card-icon quality">🎯</div>
              <div className="card-label">Average Quality Score</div>
              <div className={`card-value ${getScoreClass(summary.code_scores?.overall_quality?.average)}`}>
                {summary.code_scores?.overall_quality?.average?.toFixed(1) || 'N/A'}
              </div>
            </div>

            <div className="performance-card">
              <div className="card-icon security">🔒</div>
              <div className="card-label">Average Security Score</div>
              <div className={`card-value ${getScoreClass(summary.code_scores?.security?.average)}`}>
                {summary.code_scores?.security?.average?.toFixed(1) || 'N/A'}
              </div>
            </div>

            <div className="performance-card">
              <div className="card-icon count">📝</div>
              <div className="card-label">Total PRs Analyzed</div>
              <div className="card-value">{summary.total_prs || 0}</div>
            </div>

            <div className="performance-card">
              <div className="card-icon issues">⚠️</div>
              <div className="card-label">Avg Issues per PR</div>
              <div className="card-value">
                {summary.quality_metrics?.avg_issues_per_pr?.toFixed(1) || 'N/A'}
              </div>
            </div>
          </div>

          {/* Severity Distribution */}
          {summary.quality_metrics?.severity_distribution && (
            <div className="severity-section">
              <h4>Issue Severity Distribution</h4>
              <div className="severity-bars">
                {Object.entries(summary.quality_metrics.severity_distribution).map(([severity, count]) => (
                  <div key={severity} className="severity-bar-item">
                    <div className="severity-bar-label">
                      <span className={`severity-badge ${severity.toLowerCase()}`}>{severity}</span>
                      <span className="severity-count">{count}</span>
                    </div>
                    <div className="severity-bar-bg">
                      <div 
                        className={`severity-bar-fill ${severity.toLowerCase()}`}
                        style={{ width: `${Math.min((count / summary.total_prs) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Best Practices */}
          {summary.top_best_practices && summary.top_best_practices.length > 0 && (
            <div className="practices-section">
              <h4>✅ Top Best Practices</h4>
              <div className="practices-list">
                {summary.top_best_practices.map((practice, index) => (
                  <div key={index} className="practice-item best">
                    <span className="practice-icon">✅</span>
                    <span className="practice-text">
                      {typeof practice === 'string' 
                        ? practice 
                        : practice.title || practice.category || practice.description || JSON.stringify(practice)}
                    </span>
                    {practice.count && <span className="practice-count">{practice.count}x</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bad Practices */}
          {summary.top_bad_practices && summary.top_bad_practices.length > 0 && (
            <div className="practices-section">
              <h4>⚠️ Areas for Improvement</h4>
              <div className="practices-list">
                {summary.top_bad_practices.map((practice, index) => (
                  <div key={index} className="practice-item bad">
                    <span className="practice-icon">⚠️</span>
                    <span className="practice-text">
                      {typeof practice === 'string' 
                        ? practice 
                        : practice.title || practice.category || practice.description || JSON.stringify(practice)}
                    </span>
                    {practice.count && <span className="practice-count">{practice.count}x</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendations Section */}
      {recommendations && recommendations.recommendations && recommendations.recommendations.length > 0 && (
        <div className="analytics-section">
          <h3><span className="section-icon">💡</span> Personalized Recommendations</h3>
          <p className="section-subtitle">{recommendations.total_recommendations} recommendations found</p>
          
          <div className="recommendations-list">
            {recommendations.recommendations.map((rec, index) => (
              <div key={index} className={`recommendation-item ${rec.priority?.toLowerCase() || 'medium'}`}>
                <div className="recommendation-header">
                  <h4 className="recommendation-title">{rec.area || rec.category || 'Improvement'}</h4>
                  <span className={`priority-badge ${rec.priority?.toLowerCase() || 'medium'}`}>
                    {rec.priority ? rec.priority.toUpperCase() : 'MEDIUM'}
                  </span>
                </div>
                <p className="recommendation-description">
                  {rec.recommendation || 
                   (rec.actions && rec.actions.length > 0 ? rec.actions[0] : 'No details available')}
                </p>
                {rec.current_score !== undefined && (
                  <div className="recommendation-scores">
                    <span>Current: {rec.current_score}</span>
                    {rec.target_score !== undefined && <span>Target: {rec.target_score}</span>}
                    {rec.gap !== undefined && <span>Gap: {rec.gap}</span>}
                  </div>
                )}
                <div className="recommendation-meta">
                  {rec.expected_impact && <span>💥 Impact: {rec.expected_impact}</span>}
                  {rec.estimated_effort && <span>⏱️ Effort: {rec.estimated_effort}</span>}
                </div>
                {rec.actions && rec.actions.length > 1 && (
                  <details className="recommendation-actions">
                    <summary>View all action items ({rec.actions.length})</summary>
                    <ul>
                      {rec.actions.map((action, idx) => (
                        <li key={idx}>{action}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trends Section */}
      {trends && trends.trend_analysis && trends.trend_analysis.status === 'analyzed' && (
        <div className="analytics-section">
          <h3><span className="section-icon">📈</span> Trends Analysis</h3>
          <p className="section-subtitle">Last {trends.analysis_period_days || 180} days</p>
          
          <div className="trends-grid">
            {/* Quality Trend */}
            {trends.trend_analysis.quality && (
              <div className="trend-card">
                <div className="trend-header">
                  <h4 className="trend-title">Code Quality</h4>
                  <span className={`trend-indicator ${trends.trend_analysis.quality.direction?.toLowerCase() || 'stable'}`}>
                    {getTrendIcon(trends.trend_analysis.quality.direction)}
                    {trends.trend_analysis.quality.direction || 'Stable'}
                  </span>
                </div>
                <div className="trend-details">
                  <div className="trend-stat">
                    <span className="trend-label">Recent Average</span>
                    <span className="trend-value">
                      {trends.trend_analysis.quality.recent_avg?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className="trend-stat">
                    <span className="trend-label">Change</span>
                    <span className={`trend-value ${trends.trend_analysis.quality.change >= 0 ? 'positive' : 'negative'}`}>
                      {trends.trend_analysis.quality.change > 0 ? '+' : ''}
                      {trends.trend_analysis.quality.change?.toFixed(1) || '0'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Security Trend */}
            {trends.trend_analysis.security && (
              <div className="trend-card">
                <div className="trend-header">
                  <h4 className="trend-title">Security</h4>
                  <span className={`trend-indicator ${trends.trend_analysis.security.direction?.toLowerCase() || 'stable'}`}>
                    {getTrendIcon(trends.trend_analysis.security.direction)}
                    {trends.trend_analysis.security.direction || 'Stable'}
                  </span>
                </div>
                <div className="trend-details">
                  <div className="trend-stat">
                    <span className="trend-label">Recent Average</span>
                    <span className="trend-value">
                      {trends.trend_analysis.security.recent_avg?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className="trend-stat">
                    <span className="trend-label">Change</span>
                    <span className={`trend-value ${trends.trend_analysis.security.change >= 0 ? 'positive' : 'negative'}`}>
                      {trends.trend_analysis.security.change > 0 ? '+' : ''}
                      {trends.trend_analysis.security.change?.toFixed(1) || '0'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Coverage Trend */}
            {trends.trend_analysis.coverage && (
              <div className="trend-card">
                <div className="trend-header">
                  <h4 className="trend-title">Test Coverage</h4>
                  <span className={`trend-indicator ${trends.trend_analysis.coverage.direction?.toLowerCase() || 'stable'}`}>
                    {getTrendIcon(trends.trend_analysis.coverage.direction)}
                    {trends.trend_analysis.coverage.direction || 'Stable'}
                  </span>
                </div>
                <div className="trend-details">
                  <div className="trend-stat">
                    <span className="trend-label">Recent Average</span>
                    <span className="trend-value">
                      {trends.trend_analysis.coverage.recent_avg?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                  <div className="trend-stat">
                    <span className="trend-label">Change</span>
                    <span className={`trend-value ${trends.trend_analysis.coverage.change >= 0 ? 'positive' : 'negative'}`}>
                      {trends.trend_analysis.coverage.change > 0 ? '+' : ''}
                      {trends.trend_analysis.coverage.change?.toFixed(1) || '0'}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Show message if trends data is insufficient */}
      {trends && trends.trend_analysis && trends.trend_analysis.status === 'insufficient_data' && (
        <div className="analytics-section">
          <h3><span className="section-icon">📈</span> Trends Analysis</h3>
          <p className="section-subtitle">{trends.trend_analysis.message || 'Not enough data for trend analysis'}</p>
        </div>
      )}
    </div>
  );
};

export default Analytics;
