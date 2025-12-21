// PR Analysis API Service
const API_BASE_URL = 'http://localhost:5000/api';

class PRService {
  /**
   * Get authentication token
   */
  getToken() {
    return localStorage.getItem('token');
  }

  /**
   * Get list of PRs for a user by email
   */
  async getPRList(email, startDate = null, endDate = null, limit = 100) {
    try {
      const token = this.getToken();
      const response = await fetch(`${API_BASE_URL}/prs/list`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          email,
          start_date: startDate,
          end_date: endDate,
          limit,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch PR list');
      }

      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get detailed information about a specific PR
   */
  async getPRDetails(repository, prNumber) {
    try {
      const token = this.getToken();
      const response = await fetch(`${API_BASE_URL}/prs/details`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          repository,
          pr_number: prNumber,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch PR details');
      }

      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get analytics for a user
   */
  async getUserAnalytics(email, days = 30) {
    try {
      const token = this.getToken();
      const url = `${API_BASE_URL}/analytics/user/summary`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, days }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch user analytics');
      }

      return { success: true, data };
    } catch (error) {
      console.error('getUserAnalytics error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get user recommendations
   */
  async getUserRecommendations(email, days = 90) {
    try {
      const token = this.getToken();
      const url = `${API_BASE_URL}/analytics/user/recommendations`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, days }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch recommendations');
      }

      return { success: true, data };
    } catch (error) {
      console.error('getUserRecommendations error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get user trends
   */
  async getUserTrends(email, days = 180) {
    try {
      const token = this.getToken();
      const url = `${API_BASE_URL}/analytics/user/trends`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, days }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch trends');
      }

      return { success: true, data };
    } catch (error) {
      console.error('getUserTrends error:', error);
      return { success: false, error: error.message };
    }
  }
}

export default new PRService();
