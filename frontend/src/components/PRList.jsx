import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import prService from '../services/prService';
import './PRList.css';

const PRList = ({ onPRClick = () => {} }) => {
  const { user } = useAuth();
  const [prs, setPRs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    limit: 50,
  });

  useEffect(() => {
    fetchPRs();
  }, []);

  const fetchPRs = async () => {
    setLoading(true);
    setError('');

    const result = await prService.getPRList(
      user.email,
      filters.startDate || null,
      filters.endDate || null,
      filters.limit
    );

    if (result.success) {
      setPRs(result.data.prs || []);
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const applyFilters = () => {
    fetchPRs();
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  const getIssuesBadgeColor = (issues) => {
    if (issues === 0) return '#4caf50';
    if (issues <= 5) return '#ff9800';
    return '#f44336';
  };

  if (loading) {
    return (
      <div className="pr-list-loading">
        <div className="spinner"></div>
        <p>Loading PRs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pr-list-error">
        <p>❌ {error}</p>
        <button onClick={fetchPRs} className="btn-retry">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="pr-list-container">
      <div className="pr-list-header">
        <h2>Pull Requests</h2>
        <div className="pr-filters">
          <input
            type="date"
            name="startDate"
            value={filters.startDate}
            onChange={handleFilterChange}
            placeholder="Start Date"
          />
          <input
            type="date"
            name="endDate"
            value={filters.endDate}
            onChange={handleFilterChange}
            placeholder="End Date"
          />
          <input
            type="number"
            name="limit"
            value={filters.limit}
            onChange={handleFilterChange}
            placeholder="Limit"
            min="10"
            max="200"
          />
          <button onClick={applyFilters} className="btn-filter">
            Apply Filters
          </button>
        </div>
      </div>

      {prs.length === 0 ? (
        <div className="pr-list-empty">
          <p>No pull requests found</p>
        </div>
      ) : (
        <div className="pr-list-stats">
          <div className="stat-card">
            <span className="stat-value">{prs.length}</span>
            <span className="stat-label">Total PRs</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">
              {(prs.reduce((sum, pr) => sum + (pr.overall_quality_score || 0), 0) / prs.length).toFixed(1)}
            </span>
            <span className="stat-label">Avg Quality Score</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">
              {prs.filter((pr) => pr.critical_issues === 0).length}
            </span>
            <span className="stat-label">No Critical Issues</span>
          </div>
        </div>
      )}

      <div className="pr-list">
        {prs.map((pr) => (
          <div
            key={`${pr.repository}-${pr.pr_number}`}
            className="pr-card"
            onClick={() => onPRClick(pr)}
          >
            <div className="pr-card-header">
              <h3>#{pr.pr_number} {pr.pr_title}</h3>
              <span className="pr-repository">{pr.repository}</span>
            </div>

            <div className="pr-card-body">
              <div className="pr-metrics">
                <div className="pr-metric">
                  <span className="metric-label">Quality Score</span>
                  <span
                    className="metric-value"
                    style={{ color: getScoreColor(pr.overall_quality_score) }}
                  >
                    {pr.overall_quality_score?.toFixed(1) || 'N/A'}
                  </span>
                </div>

                <div className="pr-metric">
                  <span className="metric-label">Security Score</span>
                  <span
                    className="metric-value"
                    style={{ color: getScoreColor(pr.security_score) }}
                  >
                    {pr.security_score?.toFixed(1) || 'N/A'}
                  </span>
                </div>

                <div className="pr-metric">
                  <span className="metric-label">Issues</span>
                  <span
                    className="metric-badge"
                    style={{ backgroundColor: getIssuesBadgeColor(pr.total_issues) }}
                  >
                    {pr.total_issues || 0}
                  </span>
                </div>

                <div className="pr-metric">
                  <span className="metric-label">Critical</span>
                  <span
                    className="metric-badge critical"
                    style={{ backgroundColor: pr.critical_issues > 0 ? '#f44336' : '#4caf50' }}
                  >
                    {pr.critical_issues || 0}
                  </span>
                </div>
              </div>

              <div className="pr-stats">
                <span className="pr-stat">
                  📝 {pr.files_changed || 0} files
                </span>
                <span className="pr-stat">
                  ➕ {pr.lines_added || 0} added
                </span>
                <span className="pr-stat">
                  ➖ {pr.lines_deleted || 0} deleted
                </span>
                <span className="pr-stat">
                  📅 {new Date(pr.analyzed_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="pr-card-footer">
              <span className="pr-author">By: {pr.author_login}</span>
              <a
                href={pr.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="pr-link"
                onClick={(e) => e.stopPropagation()}
              >
                View on GitHub →
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PRList;
