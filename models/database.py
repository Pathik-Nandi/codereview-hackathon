"""Database models for PR analysis persistence."""
from datetime import datetime
import uuid
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, 
    Boolean, ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Constants
CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"


class PRAnalysis(Base):
    """Main table to store PR analysis results."""
    __tablename__ = 'pr_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # PR Identification
    repository = Column(String(255), nullable=False, index=True)
    pr_id = Column(Integer, index=True)  # GitHub's unique PR ID (globally unique)
    pr_number = Column(Integer, nullable=False, index=True)  # PR number within repo (e.g., #123)
    pr_title = Column(String(500))
    pr_description = Column(Text)
    pr_url = Column(String(500), index=True)
    
    # PR Author Information
    author_login = Column(String(255), nullable=False, index=True)
    author_email = Column(String(255), index=True)
    author_name = Column(String(255))
    author_id = Column(Integer)
    
    # PR Metadata
    base_branch = Column(String(255))
    head_branch = Column(String(255))
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    is_draft = Column(Boolean, default=False)
    
    # Analysis Results
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Agent Breakdown
    static_analysis_issues = Column(Integer, default=0)
    security_issues = Column(Integer, default=0)
    code_quality_issues = Column(Integer, default=0)
    context_issues = Column(Integer, default=0)
    coverage_issues = Column(Integer, default=0)
    
    # Coverage Metrics
    estimated_coverage = Column(Float)
    test_to_code_ratio = Column(Float)
    complexity_score = Column(Float)
    
    # Quality Scores (0-100)
    overall_quality_score = Column(Float)
    security_score = Column(Float)
    maintainability_score = Column(Float)
    
    # RAG Enhanced Analysis
    has_rag_insights = Column(Boolean, default=False)  # Whether RAG analysis was performed
    rag_risk_score = Column(Float)  # Risk score from RAG analysis (0-1)
    rag_novelty_score = Column(Float)  # Novelty score from RAG analysis (0-1)
    rag_similar_prs_count = Column(Integer, default=0)  # Number of similar PRs found
    rag_recommendations_count = Column(Integer, default=0)  # Number of recommendations
    rag_patterns_identified = Column(JSON)  # List of patterns identified
    rag_insights = Column(JSON)  # Stores complete RAG Enhanced Agent insights
    
    # Analysis Metadata
    analysis_duration_ms = Column(Integer)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    analyzer_version = Column(String(50))
    
    # PR Timestamps
    pr_created_at = Column(DateTime)
    pr_updated_at = Column(DateTime)
    
    # Relationships
    issues = relationship("PRIssue", back_populates="analysis", cascade=CASCADE_ALL_DELETE_ORPHAN)
    metrics = relationship("PRMetrics", back_populates="analysis", uselist=False, cascade=CASCADE_ALL_DELETE_ORPHAN)
    
    # Composite indexes and constraints for common queries
    __table_args__ = (
        Index('idx_repo_pr', 'repository', 'pr_number', unique=True),  # Unique constraint on repo+pr_number
        Index('idx_repo_pr_id', 'repository', 'pr_id'),  # Index for GitHub ID lookups
        Index('idx_author_date', 'author_login', 'analyzed_at'),
        Index('idx_author_email', 'author_email'),  # Index for email searches
        Index('idx_email_repo', 'author_email', 'repository'),  # Composite for email+repo queries
        Index('idx_email_date', 'author_email', 'analyzed_at'),  # Composite for email+date analytics
    )
    
    def __repr__(self):
        return f"<PRAnalysis(id={self.id}, repo={self.repository}, pr={self.pr_number})>"


class PRIssue(Base):
    """Table to store individual issues found in PR analysis."""
    __tablename__ = 'pr_issues'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pr_analysis_id = Column(Integer, ForeignKey('pr_analysis.id'), nullable=False, index=True)
    
    # Issue Classification
    agent_name = Column(String(100), nullable=False, index=True)
    issue_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), index=True)  # critical, high, medium, low
    category = Column(String(100))  # security, quality, style, coverage, etc.
    
    # Issue Location
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer)
    line_content = Column(Text)
    
    # Issue Details
    title = Column(String(500))
    description = Column(Text)
    recommendation = Column(Text)
    
    # Additional Context
    code_snippet = Column(Text)
    # 'metadata' is a reserved attribute on declarative base classes (MetaData instance).
    # Use a different Python attribute name while keeping the DB column named 'metadata'.
    issue_metadata = Column('metadata', JSON)  # Store agent-specific metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("PRAnalysis", back_populates="issues")
    
    def __repr__(self):
        return f"<PRIssue(id={self.id}, type={self.issue_type}, severity={self.severity})>"


class PRMetrics(Base):
    """Table to store detailed metrics for each PR."""
    __tablename__ = 'pr_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pr_analysis_id = Column(Integer, ForeignKey('pr_analysis.id'), nullable=False, unique=True)
    
    # Coverage Metrics
    code_files_changed = Column(Integer, default=0)
    test_files_changed = Column(Integer, default=0)
    total_test_methods = Column(Integer, default=0)
    code_lines_added = Column(Integer, default=0)
    test_lines_added = Column(Integer, default=0)
    estimated_coverage_percent = Column(Float)
    coverage_status = Column(String(20))  # PASS, FAIL, UNKNOWN
    
    # Complexity Metrics
    average_complexity = Column(Float)
    max_complexity = Column(Integer)
    total_complexity = Column(Integer)
    high_complexity_methods = Column(Integer, default=0)
    
    # Code Quality Metrics
    duplicate_code_blocks = Column(Integer, default=0)
    long_methods_count = Column(Integer, default=0)
    deep_nesting_count = Column(Integer, default=0)
    magic_numbers_count = Column(Integer, default=0)
    
    # Security Metrics
    hardcoded_secrets = Column(Integer, default=0)
    sql_injection_risks = Column(Integer, default=0)
    command_injection_risks = Column(Integer, default=0)
    weak_crypto_usage = Column(Integer, default=0)
    
    # Pattern Detection Counts
    todo_comments = Column(Integer, default=0)
    system_out_println = Column(Integer, default=0)
    console_log = Column(Integer, default=0)
    eval_usage = Column(Integer, default=0)
    
    # Code Style Metrics
    naming_violations = Column(Integer, default=0)
    formatting_issues = Column(Integer, default=0)
    comment_density = Column(Float)
    
    # Relationships
    analysis = relationship("PRAnalysis", back_populates="metrics")
    
    def __repr__(self):
        return f"<PRMetrics(id={self.id}, coverage={self.estimated_coverage_percent}%)>"


class UserStatistics(Base):
    """Aggregated statistics per user for dashboard analytics."""
    __tablename__ = 'user_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User Information
    author_login = Column(String(255), unique=True, nullable=False, index=True)
    author_email = Column(String(255), index=True)  # Add index for email searches
    author_name = Column(String(255))
    
    # PR Counts
    total_prs = Column(Integer, default=0)
    total_issues_found = Column(Integer, default=0)
    
    # Issue Distribution
    critical_issues_total = Column(Integer, default=0)
    high_issues_total = Column(Integer, default=0)
    medium_issues_total = Column(Integer, default=0)
    low_issues_total = Column(Integer, default=0)
    
    # Average Scores
    avg_quality_score = Column(Float)
    avg_security_score = Column(Float)
    avg_maintainability_score = Column(Float)
    avg_coverage = Column(Float)
    avg_complexity = Column(Float)
    
    # RAG Metrics (Aggregated from RAG insights)
    total_rag_insights = Column(Integer, default=0)  # PRs with RAG insights
    avg_rag_risk_score = Column(Float)  # Average risk score across PRs
    avg_rag_novelty_score = Column(Float)  # Average novelty score
    total_similar_prs_referenced = Column(Integer, default=0)  # Total similar PRs found
    total_rag_recommendations = Column(Integer, default=0)  # Total recommendations given
    total_patterns_identified = Column(Integer, default=0)  # Unique patterns identified
    high_risk_prs_count = Column(Integer, default=0)  # PRs with risk_score > 0.7
    novel_prs_count = Column(Integer, default=0)  # PRs with novelty_score > 0.8
    most_common_patterns = Column(JSON)  # Top 5 patterns for this user
    learning_velocity = Column(Float)  # How often new patterns emerge (patterns/PR)
    
    # Trend Indicators
    quality_trend = Column(String(20))  # improving, declining, stable
    security_trend = Column(String(20))
    coverage_trend = Column(String(20))
    rag_risk_trend = Column(String(20))  # RAG risk trend
    rag_novelty_trend = Column(String(20))  # Novelty trend
    
    # Best/Worst Metrics
    best_pr_id = Column(Integer)  # PR with highest quality score
    worst_pr_id = Column(Integer)  # PR with lowest quality score
    
    # Common Issues (Top 5)
    common_issues = Column(JSON)  # {"MAGIC_NUMBER": 45, "DEEP_NESTING": 32, ...}
    
    # Improvement Areas
    improvement_areas = Column(JSON)  # ["Code Coverage", "Security Practices", ...]
    strengths = Column(JSON)  # ["Clean Code", "Good Documentation", ...]
    
    # Activity Metadata
    first_pr_date = Column(DateTime)
    last_pr_date = Column(DateTime, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserStatistics(login={self.author_login}, prs={self.total_prs})>"


class BestPractice(Base):
    """Table to store best practices recommendations based on analysis patterns."""
    __tablename__ = 'best_practices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Practice Information
    category = Column(String(100), nullable=False, index=True)  # security, quality, coverage, etc.
    issue_type = Column(String(100), nullable=False, index=True)
    priority = Column(String(20))  # critical, high, medium, low
    
    # Content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    example_bad = Column(Text)  # Bad practice example
    example_good = Column(Text)  # Good practice example
    
    # Applicability
    languages = Column(JSON)  # ["Java", "Python", "JavaScript"]
    tags = Column(JSON)  # ["security", "sql-injection", "input-validation"]
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BestPractice(id={self.id}, title={self.title})>"


class UserAnalytics(Base):
    """Table to store user analytics snapshots generated by analytics agent."""
    __tablename__ = 'user_analytics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User Information
    author_login = Column(String(255), nullable=False, index=True)
    author_email = Column(String(255), index=True)
    author_name = Column(String(255))
    
    # Analysis Period
    analysis_date = Column(DateTime, nullable=False, index=True)  # When this analysis was run
    period_start = Column(DateTime)  # Start of analysis period
    period_end = Column(DateTime)  # End of analysis period
    total_prs_analyzed = Column(Integer, default=0)
    
    # Quality Metrics
    avg_quality_score = Column(Float)
    avg_security_score = Column(Float)
    avg_maintainability_score = Column(Float)
    avg_coverage = Column(Float)
    avg_complexity = Column(Float)
    
    # Issue Statistics
    total_issues = Column(Integer, default=0)
    avg_issues_per_pr = Column(Float)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Code Metrics
    total_files_changed = Column(Integer, default=0)
    total_lines_added = Column(Integer, default=0)
    total_lines_deleted = Column(Integer, default=0)
    avg_files_per_pr = Column(Float)
    avg_lines_per_pr = Column(Float)
    
    # Trends (JSON for storing trend analysis)
    quality_trend = Column(JSON)  # {direction: 'improving', change: 5.2, recent_avg: 85, older_avg: 79.8}
    security_trend = Column(JSON)
    coverage_trend = Column(JSON)
    
    # RAG Trends and Metrics
    rag_risk_trend = Column(JSON)  # {direction: 'improving', change: -0.15, recent_avg: 0.35, older_avg: 0.50}
    rag_novelty_trend = Column(JSON)  # Trend in novelty scores
    avg_rag_risk_score = Column(Float)  # Average RAG risk score in this period
    avg_rag_novelty_score = Column(Float)  # Average novelty score in this period
    total_rag_insights = Column(Integer, default=0)  # PRs with RAG insights in period
    total_similar_prs_found = Column(Integer, default=0)  # Total similar PRs referenced
    total_rag_recommendations = Column(Integer, default=0)  # Total RAG recommendations given
    high_risk_prs = Column(JSON)  # Array of high-risk PR numbers with details
    novel_contributions = Column(JSON)  # Array of novel PRs with details
    patterns_learned = Column(JSON)  # Patterns identified in this period
    rag_insights_summary = Column(JSON)  # {lessons_learned: [], pitfalls_avoided: [], best_practices: []}
    
    # Best/Bad Practices (JSON arrays)
    best_practices = Column(JSON)  # Array of best practice objects
    bad_practices = Column(JSON)  # Array of bad practice objects
    recommendations = Column(JSON)  # Array of recommendation objects
    
    # Agent Breakdown
    agent_breakdown = Column(JSON)  # Issue distribution by agent
    issue_distribution = Column(JSON)  # Issue distribution by severity
    
    # Metadata
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_user_analytics_login_date', 'author_login', 'analysis_date'),
        Index('idx_user_analytics_email_date', 'author_email', 'analysis_date'),
    )
    
    def __repr__(self):
        return f"<UserAnalytics(id={self.id}, author={self.author_login}, date={self.analysis_date})>"


class User(Base):
    """User authentication table."""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile Information
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade=CASCADE_ALL_DELETE_ORPHAN)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class UserSession(Base):
    """User session tracking table."""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Session Information
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Session Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    logged_out_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_token_active', 'session_token', 'is_active'),
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at', 'is_active'),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
