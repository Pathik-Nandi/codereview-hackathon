-- ============================================================================
-- PR Review System - Table Creation Script
-- ============================================================================
-- Description: Create all database tables for the PR Review System
-- Version: 1.0
-- Date: 2025-12-28
-- Usage: psql -U postgres -d pr_analysis -f create_tables.sql
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Users Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'developer',
    github_username VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT valid_role CHECK (role IN ('developer', 'admin', 'reviewer', 'manager'))
);

-- ----------------------------------------------------------------------------
-- PR Analysis Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pr_analysis (
    id SERIAL PRIMARY KEY,
    pr_number INTEGER NOT NULL,
    repository VARCHAR(500) NOT NULL,
    title VARCHAR(1000),
    description TEXT,
    author_login VARCHAR(255),
    author_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    state VARCHAR(50),
    analysis_status VARCHAR(50),
    is_merged BOOLEAN DEFAULT FALSE,
    analysis_result JSONB,
    issues_found INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    suggestions INTEGER DEFAULT 0,
    files_changed INTEGER DEFAULT 0,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    overall_quality_score FLOAT,
    security_score FLOAT,
    maintainability_score FLOAT,
    complexity_score FLOAT,
    test_coverage_score FLOAT,
    documentation_score FLOAT,
    rag_insights TEXT,
    rag_similar_prs_count INTEGER DEFAULT 0,
    rag_recommendations_count INTEGER DEFAULT 0,
    rag_risk_score FLOAT,
    rag_novelty_score FLOAT,
    rag_patterns_learned JSONB DEFAULT '[]',
    full_text TEXT,
    static_analysis_result JSONB,
    security_analysis_result JSONB,
    quality_analysis_result JSONB,
    context_analysis_result JSONB,
    coverage_analysis_result JSONB,
    analyzed_by VARCHAR(255),
    analysis_version VARCHAR(50),
    processing_time_ms INTEGER,
    analyzed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_pr_per_repo UNIQUE (pr_number, repository),
    CONSTRAINT valid_scores CHECK (
        overall_quality_score IS NULL OR (overall_quality_score >= 0 AND overall_quality_score <= 100)
    ),
    CONSTRAINT valid_rag_scores CHECK (
        (rag_risk_score IS NULL OR (rag_risk_score >= 0 AND rag_risk_score <= 1)) AND
        (rag_novelty_score IS NULL OR (rag_novelty_score >= 0 AND rag_novelty_score <= 1))
    )
);

-- ----------------------------------------------------------------------------
-- User Statistics Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_statistics (
    id SERIAL PRIMARY KEY,
    author_login VARCHAR(255) UNIQUE NOT NULL,
    author_email VARCHAR(255),
    total_prs INTEGER DEFAULT 0,
    merged_prs INTEGER DEFAULT 0,
    rejected_prs INTEGER DEFAULT 0,
    open_prs INTEGER DEFAULT 0,
    avg_quality_score FLOAT,
    avg_security_score FLOAT,
    avg_maintainability_score FLOAT,
    avg_complexity_score FLOAT,
    avg_test_coverage_score FLOAT,
    avg_rag_risk_score FLOAT,
    avg_rag_novelty_score FLOAT,
    avg_issues_per_pr FLOAT,
    total_critical_issues INTEGER DEFAULT 0,
    total_warnings INTEGER DEFAULT 0,
    total_suggestions INTEGER DEFAULT 0,
    total_files_changed INTEGER DEFAULT 0,
    total_additions INTEGER DEFAULT 0,
    total_deletions INTEGER DEFAULT 0,
    common_patterns JSONB DEFAULT '[]',
    best_practices JSONB DEFAULT '[]',
    areas_for_improvement JSONB DEFAULT '[]',
    language_distribution JSONB DEFAULT '{}',
    first_pr_date TIMESTAMP WITH TIME ZONE,
    last_pr_date TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT positive_pr_counts CHECK (
        total_prs >= 0 AND merged_prs >= 0 AND rejected_prs >= 0 AND open_prs >= 0
    )
);

-- ----------------------------------------------------------------------------
-- User Analytics Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_analytics (
    id SERIAL PRIMARY KEY,
    author_login VARCHAR(255) NOT NULL,
    author_email VARCHAR(255),
    author_name VARCHAR(255),
    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    total_prs_analyzed INTEGER DEFAULT 0,
    avg_quality_score FLOAT,
    avg_security_score FLOAT,
    avg_maintainability_score FLOAT,
    avg_coverage FLOAT,
    avg_complexity FLOAT,
    total_issues INTEGER DEFAULT 0,
    avg_issues_per_pr FLOAT,
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    total_files_changed INTEGER DEFAULT 0,
    total_lines_added INTEGER DEFAULT 0,
    total_lines_deleted INTEGER DEFAULT 0,
    avg_files_per_pr FLOAT,
    avg_lines_per_pr FLOAT,
    quality_trend JSONB,
    security_trend JSONB,
    coverage_trend JSONB,
    rag_risk_trend JSONB,
    rag_novelty_trend JSONB,
    avg_rag_risk_score FLOAT,
    avg_rag_novelty_score FLOAT,
    total_rag_insights INTEGER DEFAULT 0,
    total_similar_prs_found INTEGER DEFAULT 0,
    total_rag_recommendations INTEGER DEFAULT 0,
    high_risk_prs JSONB DEFAULT '[]',
    novel_contributions JSONB DEFAULT '[]',
    patterns_learned JSONB DEFAULT '[]',
    rag_insights_summary JSONB,
    best_practices JSONB DEFAULT '[]',
    bad_practices JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    agent_breakdown JSONB,
    issue_distribution JSONB,
    
    CONSTRAINT valid_period CHECK (period_end IS NULL OR period_start IS NULL OR period_end >= period_start)
);

-- ----------------------------------------------------------------------------
-- RAG Insights Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_insights (
    id SERIAL PRIMARY KEY,
    pr_analysis_id INTEGER NOT NULL,
    insight_type VARCHAR(50),
    full_text TEXT,
    summary TEXT,
    risk_score FLOAT,
    novelty_score FLOAT,
    confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pr_analysis_rag FOREIGN KEY (pr_analysis_id) 
        REFERENCES pr_analysis (id) 
        ON DELETE CASCADE,
    CONSTRAINT valid_rag_scores CHECK (
        (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1)) AND
        (novelty_score IS NULL OR (novelty_score >= 0 AND novelty_score <= 1)) AND
        (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1))
    )
);

-- ----------------------------------------------------------------------------
-- RAG Learned Patterns Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_learned_patterns (
    id SERIAL PRIMARY KEY,
    rag_insight_id INTEGER NOT NULL,
    pattern_type VARCHAR(100),
    pattern_name VARCHAR(255),
    description TEXT,
    frequency INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rag_insight_patterns FOREIGN KEY (rag_insight_id) 
        REFERENCES rag_insights (id) 
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- RAG Recommendations Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_recommendations (
    id SERIAL PRIMARY KEY,
    rag_insight_id INTEGER NOT NULL,
    recommendation_text TEXT NOT NULL,
    priority VARCHAR(50),
    category VARCHAR(100),
    is_implemented BOOLEAN DEFAULT FALSE,
    implementation_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rag_insight_recommendations FOREIGN KEY (rag_insight_id) 
        REFERENCES rag_insights (id) 
        ON DELETE CASCADE,
    CONSTRAINT valid_priority CHECK (priority IN ('high', 'medium', 'low', NULL))
);

-- ----------------------------------------------------------------------------
-- RAG Similar PR References Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_similar_pr_references (
    id SERIAL PRIMARY KEY,
    rag_insight_id INTEGER NOT NULL,
    similar_pr_number INTEGER NOT NULL,
    similar_pr_repository VARCHAR(500),
    similarity_score FLOAT,
    reference_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rag_insight_similar FOREIGN KEY (rag_insight_id) 
        REFERENCES rag_insights (id) 
        ON DELETE CASCADE,
    CONSTRAINT valid_similarity CHECK (
        similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)
    )
);

-- ----------------------------------------------------------------------------
-- Best Practices Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS best_practices (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    language VARCHAR(50),
    frequency_count INTEGER DEFAULT 0,
    last_seen_in_pr INTEGER,
    example_code TEXT,
    example_prs JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- User Sessions Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    logged_out_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) 
        REFERENCES users (id) 
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- PR Issues Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pr_issues (
    id SERIAL PRIMARY KEY,
    pr_analysis_id INTEGER NOT NULL,
    issue_type VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    file_path VARCHAR(1000),
    line_number INTEGER,
    detected_by_agent VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pr_analysis_issues FOREIGN KEY (pr_analysis_id) 
        REFERENCES pr_analysis (id) 
        ON DELETE CASCADE,
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info'))
);

-- ----------------------------------------------------------------------------
-- PR Metrics Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pr_metrics (
    id SERIAL PRIMARY KEY,
    pr_analysis_id INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT,
    metric_category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pr_analysis_metrics FOREIGN KEY (pr_analysis_id) 
        REFERENCES pr_analysis (id) 
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- Feedback Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    pr_number INTEGER NOT NULL,
    repository VARCHAR(500) NOT NULL,
    user_email VARCHAR(255),
    feedback_type VARCHAR(50),
    rating INTEGER,
    comment TEXT,
    analysis_helpful BOOLEAN,
    suggestions_followed BOOLEAN,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_rating CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
    CONSTRAINT valid_feedback_type CHECK (
        feedback_type IN ('positive', 'negative', 'neutral', 'suggestion', 'bug_report')
    ),
    CONSTRAINT fk_pr_analysis FOREIGN KEY (pr_number, repository) 
        REFERENCES pr_analysis (pr_number, repository) 
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- Analysis History Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_history (
    id SERIAL PRIMARY KEY,
    pr_number INTEGER NOT NULL,
    repository VARCHAR(500) NOT NULL,
    analysis_version VARCHAR(50),
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analysis_snapshot JSONB,
    scores_snapshot JSONB,
    triggered_by VARCHAR(255),
    trigger_reason VARCHAR(500),
    
    CONSTRAINT fk_pr_analysis_history FOREIGN KEY (pr_number, repository) 
        REFERENCES pr_analysis (pr_number, repository) 
        ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_github_username ON users(github_username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active) WHERE is_active = TRUE;

-- PR Analysis
CREATE INDEX IF NOT EXISTS idx_pr_analysis_pr_number ON pr_analysis(pr_number);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_repository ON pr_analysis(repository);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_author_login ON pr_analysis(author_login);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_author_email ON pr_analysis(author_email);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_state ON pr_analysis(state);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_created_at ON pr_analysis(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_repo_author ON pr_analysis(repository, author_login);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_result_gin ON pr_analysis USING GIN (analysis_result);
CREATE INDEX IF NOT EXISTS idx_pr_analysis_patterns_gin ON pr_analysis USING GIN (rag_patterns_learned);

-- User Statistics
CREATE INDEX IF NOT EXISTS idx_user_statistics_author_login ON user_statistics(author_login);
CREATE INDEX IF NOT EXISTS idx_user_statistics_author_email ON user_statistics(author_email);
CREATE INDEX IF NOT EXISTS idx_user_statistics_updated_at ON user_statistics(updated_at DESC);

-- User Analytics
CREATE INDEX IF NOT EXISTS idx_user_analytics_author_login ON user_analytics(author_login);
CREATE INDEX IF NOT EXISTS idx_user_analytics_analysis_date ON user_analytics(analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_user_analytics_period ON user_analytics(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_user_analytics_quality_trend_gin ON user_analytics USING GIN (quality_trend);

-- RAG Tables
CREATE INDEX IF NOT EXISTS idx_rag_insights_pr_analysis ON rag_insights(pr_analysis_id);
CREATE INDEX IF NOT EXISTS idx_rag_insights_type ON rag_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_rag_patterns_insight ON rag_learned_patterns(rag_insight_id);
CREATE INDEX IF NOT EXISTS idx_rag_recommendations_insight ON rag_recommendations(rag_insight_id);
CREATE INDEX IF NOT EXISTS idx_rag_similar_insight ON rag_similar_pr_references(rag_insight_id);

-- Best Practices
CREATE INDEX IF NOT EXISTS idx_best_practices_category ON best_practices(category);
CREATE INDEX IF NOT EXISTS idx_best_practices_language ON best_practices(language);

-- User Sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active) WHERE is_active = TRUE;

-- PR Issues
CREATE INDEX IF NOT EXISTS idx_pr_issues_pr_analysis ON pr_issues(pr_analysis_id);
CREATE INDEX IF NOT EXISTS idx_pr_issues_severity ON pr_issues(severity);

-- PR Metrics
CREATE INDEX IF NOT EXISTS idx_pr_metrics_pr_analysis ON pr_metrics(pr_analysis_id);
CREATE INDEX IF NOT EXISTS idx_pr_metrics_name ON pr_metrics(metric_name);

-- Feedback
CREATE INDEX IF NOT EXISTS idx_feedback_pr ON feedback(pr_number, repository);
CREATE INDEX IF NOT EXISTS idx_feedback_user_email ON feedback(user_email);

-- Analysis History
CREATE INDEX IF NOT EXISTS idx_analysis_history_pr ON analysis_history(pr_number, repository);
CREATE INDEX IF NOT EXISTS idx_analysis_history_analyzed_at ON analysis_history(analyzed_at DESC);

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
