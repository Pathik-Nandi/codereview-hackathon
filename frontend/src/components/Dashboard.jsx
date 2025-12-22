import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import PRList from './PRList';
import PRDetails from './PRDetails';
import Analytics from './Analytics';
import './Auth.css';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedPR, setSelectedPR] = useState(null);
  const [showPRDetails, setShowPRDetails] = useState(false);

  const handleLogout = async () => {
    await logout();
  };

  const handlePRClick = (pr) => {
    setSelectedPR(pr);
    setShowPRDetails(true);
  };

  const handleClosePRDetails = () => {
    setShowPRDetails(false);
    setSelectedPR(null);
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Code Review Dashboard</h1>
        <div className="user-info">
          <div className="user-details">
            <p className="user-name">{user?.full_name || user?.username}</p>
            <p className="user-email">{user?.email}</p>
          </div>
          <button onClick={handleLogout} className="btn-secondary">
            Logout
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'prs' ? 'active' : ''}`}
          onClick={() => setActiveTab('prs')}
        >
          📝 Pull Requests
        </button>
        <button 
          className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          📈 Analytics
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="welcome-card">
            <h2>Welcome to Code Review System! 🎉</h2>
            <p>You have successfully logged in with UUID-based authentication.</p>
            <div className="user-id">
              <strong>Your User ID (UUID):</strong> {user?.user_id}
            </div>
            <div className="quick-actions">
              <button 
                className="action-button"
                onClick={() => setActiveTab('prs')}
              >
                View Your Pull Requests →
              </button>
              <button 
                className="action-button"
                onClick={() => setActiveTab('analytics')}
              >
                View Analytics →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'prs' && (
          <PRList userEmail={user?.email} onPRClick={handlePRClick} />
        )}

        {activeTab === 'analytics' && (
          <Analytics userEmail={user?.email} />
        )}
      </div>

      {showPRDetails && selectedPR && (
        <PRDetails pr={selectedPR} onClose={handleClosePRDetails} />
      )}
    </div>
  );
};

export default Dashboard;
