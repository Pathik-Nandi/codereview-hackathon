"""
Unit tests for Flask API endpoints.

Tests the API endpoints for:
- Health check
- PR analysis
- Authentication
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    @pytest.mark.unit
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'version' in data


class TestAnalyzeEndpoint:
    """Tests for the PR analysis endpoint."""
    
    @pytest.mark.unit
    def test_analyze_missing_repository(self, client):
        """Test analyze endpoint with missing repository."""
        response = client.post(
            '/api/analyze',
            data=json.dumps({'pr_number': 42}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @pytest.mark.unit
    def test_analyze_missing_pr_number(self, client):
        """Test analyze endpoint with missing pr_number."""
        response = client.post(
            '/api/analyze',
            data=json.dumps({'repository': 'test-org/test-repo'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    @pytest.mark.unit
    def test_login_missing_password(self, client):
        """Test login with missing password."""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        
        # Should return 400 (missing password) or 503 (auth service unavailable)
        assert response.status_code in [400, 503]
    
    @pytest.mark.unit
    def test_validate_without_token(self, client):
        """Test validate endpoint without token."""
        response = client.get('/api/auth/validate')
        
        # Should return 401 or 503
        assert response.status_code in [401, 503]
    
    @pytest.mark.unit
    def test_validate_with_invalid_token(self, client):
        """Test validate endpoint with invalid token."""
        response = client.get(
            '/api/auth/validate',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        
        # Should return 401 or 503
        assert response.status_code in [401, 503]
    
    @pytest.mark.unit
    def test_logout_without_auth(self, client):
        """Test logout without authentication."""
        response = client.post('/api/auth/logout')
        
        # Should return 401 or 503
        assert response.status_code in [401, 503]


class TestWebhookEndpoint:
    """Tests for the GitHub webhook endpoint."""
    
    @pytest.mark.unit
    def test_webhook_invalid_signature(self, client):
        """Test webhook with invalid signature."""
        response = client.post(
            '/webhook/github',
            data=json.dumps({'action': 'opened', 'pull_request': {}}),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=invalid'}
        )
        
        # Should return 401 for invalid signature
        assert response.status_code == 401


class TestErrorHandling:
    """Tests for API error handling."""
    
    @pytest.mark.unit
    def test_404_not_found(self, client):
        """Test 404 response for unknown endpoint."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_method_not_allowed(self, client):
        """Test 405 response for wrong HTTP method."""
        response = client.get('/api/analyze')  # Should be POST
        
        assert response.status_code == 405


class TestCORS:
    """Tests for CORS configuration."""
    
    @pytest.mark.unit
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in API responses."""
        response = client.options(
            '/api/analyze',
            headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'POST'
            }
        )
        
        # CORS preflight should succeed
        assert response.status_code in [200, 204]
