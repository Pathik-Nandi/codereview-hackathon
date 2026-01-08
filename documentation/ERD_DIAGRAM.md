# Entity Relationship Diagram (ERD)
# PR Analysis System - Complete Database Schema

---

## Visual ERD with All Fields

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                  pr_analysis                                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)                                                 │
│     repository (VARCHAR(255)) [NOT NULL, INDEXED]                                │
│     pr_id (INTEGER) [INDEXED]                                                    │
│     pr_number (INTEGER) [NOT NULL, INDEXED]                                      │
│     pr_title (VARCHAR(500))                                                      │
│     pr_description (TEXT)                                                        │
│     pr_url (VARCHAR(500)) [INDEXED]                                              │
│                                                                                  │
│     author_login (VARCHAR(255)) [NOT NULL, INDEXED]                              │
│     author_email (VARCHAR(255)) [INDEXED]                                        │
│     author_name (VARCHAR(255))                                                   │
│     author_id (INTEGER)                                                          │
│                                                                                  │
│     base_branch (VARCHAR(255))                                                   │
│     head_branch (VARCHAR(255))                                                   │
│     files_changed (INTEGER, DEFAULT 0)                                           │
│     lines_added (INTEGER, DEFAULT 0)                                             │
│     lines_deleted (INTEGER, DEFAULT 0)                                           │
│     is_draft (BOOLEAN, DEFAULT FALSE)                                            │
│                                                                                  │
│     total_issues (INTEGER, DEFAULT 0)                                            │
│     critical_issues (INTEGER, DEFAULT 0)                                         │
│     high_issues (INTEGER, DEFAULT 0)                                             │
│     medium_issues (INTEGER, DEFAULT 0)                                           │
│     low_issues (INTEGER, DEFAULT 0)                                              │
│                                                                                  │
│     static_analysis_issues (INTEGER, DEFAULT 0)                                  │
│     security_issues (INTEGER, DEFAULT 0)                                         │
│     code_quality_issues (INTEGER, DEFAULT 0)                                     │
│     context_issues (INTEGER, DEFAULT 0)                                          │
│     coverage_issues (INTEGER, DEFAULT 0)                                         │
│                                                                                  │
│     estimated_coverage (FLOAT)                                                   │
│     test_to_code_ratio (FLOAT)                                                   │
│     complexity_score (FLOAT)                                                     │
│                                                                                  │
│     overall_quality_score (FLOAT)                                                │
│     security_score (FLOAT)                                                       │
│     maintainability_score (FLOAT)                                                │
│                                                                                  │
│     has_rag_insights (BOOLEAN, DEFAULT FALSE)                                    │
│     rag_risk_score (FLOAT)                                                       │
│     rag_novelty_score (FLOAT)                                                    │
│     rag_similar_prs_count (INTEGER, DEFAULT 0)                                   │
│     rag_recommendations_count (INTEGER, DEFAULT 0)                               │
│     rag_patterns_identified (JSON)                                               │
│     rag_insights (JSON)                                                          │
│                                                                                  │
│     analysis_duration_ms (INTEGER)                                               │
│     analyzed_at (DATETIME, DEFAULT NOW) [INDEXED]                                │
│     analyzer_version (VARCHAR(50))                                               │
│                                                                                  │
│     pr_created_at (DATETIME)                                                     │
│     pr_updated_at (DATETIME)                                                     │
│                                                                                  │
│ UNIQUE(repository, pr_number) - idx_repo_pr                                      │
│ INDEX(repository, pr_id) - idx_repo_pr_id                                        │
│ INDEX(author_login, analyzed_at) - idx_author_date                               │
│ INDEX(author_email, repository) - idx_email_repo                                 │
└──────────────────────────────────────────────────────────────────────────────────┘
                      │
                      │ 1:M (CASCADE DELETE)
                      ├──────────────────────────────────────────────┐
                      │                                              │
                      ▼                                              ▼
┌────────────────────────────────────────────────┐  ┌────────────────────────────────────────────┐
│              pr_issues                         │  │            pr_metrics                      │
├────────────────────────────────────────────────┤  ├────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)               │  │ PK  id (INTEGER, AUTO_INCREMENT)           │
│ FK  pr_analysis_id → pr_analysis.id [INDEXED]  │  │ FK  pr_analysis_id → pr_analysis.id [UNQ]  │
│                                                │  │                                            │
│     agent_name (VARCHAR(100)) [NOT NULL, IDX]  │  │ # Coverage Metrics                         │
│     issue_type (VARCHAR(100)) [NOT NULL, IDX]  │  │     code_files_changed (INT, DEFAULT 0)    │
│     severity (VARCHAR(20)) [INDEXED]           │  │     test_files_changed (INT, DEFAULT 0)    │
│     category (VARCHAR(100))                    │  │     total_test_methods (INT, DEFAULT 0)    │
│                                                │  │     code_lines_added (INT, DEFAULT 0)      │
│     file_path (VARCHAR(500)) [NOT NULL]        │  │     test_lines_added (INT, DEFAULT 0)      │
│     line_number (INTEGER)                      │  │     estimated_coverage_percent (FLOAT)     │
│     line_content (TEXT)                        │  │     coverage_status (VARCHAR(20))          │
│                                                │  │                                            │
│     title (VARCHAR(500))                       │  │ # Complexity Metrics                       │
│     description (TEXT)                         │  │     average_complexity (FLOAT)             │
│     recommendation (TEXT)                      │  │     max_complexity (INTEGER)               │
│                                                │  │     total_complexity (INTEGER)             │
│     code_snippet (TEXT)                        │  │     high_complexity_methods (INT, DEF 0)   │
│     metadata (JSON)                            │  │                                            │
│                                                │  │ # Code Quality Metrics                     │
│     created_at (DATETIME, DEFAULT NOW)         │  │     duplicate_code_blocks (INT, DEF 0)     │
│                                                │  │     long_methods_count (INT, DEFAULT 0)    │
│ INDEX(pr_analysis_id)                          │  │     deep_nesting_count (INT, DEFAULT 0)    │
│ INDEX(agent_name)                              │  │     magic_numbers_count (INT, DEFAULT 0)   │
│ INDEX(severity)                                │  │                                            │
│ INDEX(issue_type)                              │  │ # Security Metrics                         │
└────────────────────────────────────────────────┘  │     hardcoded_secrets (INT, DEFAULT 0)     │
                      │                             │     sql_injection_risks (INT, DEFAULT 0)   │
                      │ 1:M                         │     command_injection_risks (INT, DEF 0)   │
                      ▼                             │     weak_crypto_usage (INT, DEFAULT 0)     │
┌────────────────────────────────────────────────┐  │                                            │
│             pr_comments                        │  │ # Pattern Detection Counts                 │
├────────────────────────────────────────────────┤  │     todo_comments (INT, DEFAULT 0)         │
│ PK  id (INTEGER, AUTO_INCREMENT)               │  │     system_out_println (INT, DEFAULT 0)    │
│ FK  pr_analysis_id → pr_analysis.id [INDEXED]  │  │     console_log (INT, DEFAULT 0)           │
│ FK  pr_issue_id → pr_issues.id [INDEXED]       │  │     eval_usage (INT, DEFAULT 0)            │
│                                                │  │                                            │
│     github_comment_id (VARCHAR(100)) [INDEXED] │  │ # Code Style Metrics                       │
│     github_review_id (VARCHAR(100)) [INDEXED]  │  │     naming_violations (INT, DEFAULT 0)     │
│     comment_type (VARCHAR(20)) [NOT NULL, IDX] │  │     formatting_issues (INT, DEFAULT 0)     │
│                                                │  │     comment_density (FLOAT)                │
│     file_path (VARCHAR(500))                   │  │                                            │
│     line_number (INTEGER)                      │  │ UNIQUE(pr_analysis_id) - One-to-One        │
│     commit_sha (VARCHAR(40))                   │  └────────────────────────────────────────────┘
│                                                │
│     comment_body (TEXT) [NOT NULL]             │
│     comment_preview (VARCHAR(200))             │
│                                                │
│     issue_severity (VARCHAR(20))               │
│     issue_type (VARCHAR(100))                  │
│                                                │
│     posted_successfully (BOOLEAN, DEFAULT TRUE)│
│     post_error (TEXT)                          │
│     review_event (VARCHAR(20))                 │
│                                                │
│     github_url (VARCHAR(500))                  │
│     github_response (JSON)                     │
│                                                │
│     reactions_count (INT, DEFAULT 0)           │
│     replies_count (INT, DEFAULT 0)             │
│     was_edited (BOOLEAN, DEFAULT FALSE)        │
│     was_resolved (BOOLEAN, DEFAULT FALSE)      │
│     resolved_at (DATETIME)                     │
│                                                │
│     agent_version (VARCHAR(50))                │
│     config_used (JSON)                         │
│                                                │
│     created_at (DATETIME, DEFAULT NOW) [IDX]   │
│     posted_at (DATETIME, DEFAULT NOW)          │
│     last_checked_at (DATETIME)                 │
│                                                │
│ INDEX(pr_analysis_id, comment_type)            │
│ INDEX(pr_analysis_id, file_path)               │
│ INDEX(issue_severity, posted_successfully)     │
│ INDEX(posted_at, comment_type)                 │
│ INDEX(github_comment_id, github_review_id)     │
└────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────┐
│                                rag_insights                                      │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)                                                 │
│ FK  pr_analysis_id → pr_analysis.id [UNIQUE] - One-to-One                        │
│                                                                                  │
│     embedding_model (VARCHAR(100))                                               │
│     llm_model (VARCHAR(100))                                                     │
│     vector_db_used (VARCHAR(50))                                                 │
│                                                                                  │
│     full_text (TEXT)                                                             │
│     summary (TEXT)                                                               │
│                                                                                  │
│     context_used (BOOLEAN, DEFAULT FALSE) [INDEXED]                              │
│     similar_prs_found (INTEGER, DEFAULT 0)                                       │
│     similar_prs_referenced (INTEGER, DEFAULT 0)                                  │
│     context_confidence_score (FLOAT)                                             │
│                                                                                  │
│     recommendations (TEXT)                                                       │
│     lessons_learned (TEXT)                                                       │
│     potential_pitfalls (TEXT)                                                    │
│     best_practices_suggested (TEXT)                                              │
│                                                                                  │
│     novelty_score (FLOAT) [INDEXED]                                              │
│     risk_score (FLOAT) [INDEXED DESC]                                            │
│     complexity_assessment (VARCHAR(50))                                          │
│                                                                                  │
│     generated_at (DATETIME, DEFAULT NOW) [INDEXED DESC]                          │
│     generation_time_ms (INTEGER)                                                 │
│     tokens_used (INTEGER)                                                        │
│                                                                                  │
│ UNIQUE(pr_analysis_id) - unique_pr_rag_insight                                   │
│ INDEX(pr_analysis_id) - idx_rag_pr_analysis                                      │
│ INDEX(risk_score DESC) - idx_rag_risk_score                                      │
│ INDEX(novelty_score) - idx_rag_novelty                                           │
│ INDEX(context_used) - idx_rag_context_used                                       │
└──────────────────────────────────────────────────────────────────────────────────┘
                      │
                      │ 1:M (CASCADE DELETE)
                      ├────────────────────────────────────────────┐
                      │                                            │
                      ▼                                            ▼
┌────────────────────────────────────────────────┐  ┌────────────────────────────────────────────┐
│       rag_similar_pr_references                │  │         rag_recommendations                │
├────────────────────────────────────────────────┤  ├────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)               │  │ PK  id (INTEGER, AUTO_INCREMENT)           │
│ FK  rag_insight_id → rag_insights.id [INDEXED] │  │ FK  rag_insight_id → rag_insights.id [IDX] │
│ FK  referenced_pr_analysis_id → pr_analysis.id │  │ FK  derived_from_pattern_id →              │
│                                [INDEXED]        │  │         rag_learned_patterns.id [INDEXED]  │
│                                                │  │                                            │
│     similarity_score (FLOAT) [NOT NULL, IDX]   │  │     recommendation_type (VARCHAR(100))     │
│     similarity_type (VARCHAR(50))              │  │     priority (VARCHAR(20)) [INDEXED]       │
│                                                │  │     title (VARCHAR(500)) [NOT NULL]        │
│     used_in_analysis (BOOLEAN, DEFAULT TRUE)   │  │     description (TEXT) [NOT NULL]          │
│     contributed_to_recommendation (BOOL, DEF F)│  │     reasoning (TEXT)                       │
│                                                │  │                                            │
│     lesson_extracted (TEXT)                    │  │     applies_to_files (JSON)                │
│     pattern_identified (VARCHAR(255)) [INDEXED]│  │     applies_to_lines (JSON)                │
│                                                │  │     related_issues (JSON)                  │
│     created_at (DATETIME, DEFAULT NOW) [IDX]   │  │     derived_from_similar_prs (JSON)        │
│                                                │  │                                            │
│ UNIQUE(rag_insight_id, referenced_pr_analysis) │  │     was_helpful (BOOLEAN) [INDEXED]        │
│ INDEX(rag_insight_id) - idx_similar_rag_ins    │  │     feedback_comment (TEXT)                │
│ INDEX(referenced_pr_analysis_id)               │  │     was_actioned (BOOLEAN)                 │
│ INDEX(similarity_score DESC)                   │  │                                            │
│ INDEX(pattern_identified)                      │  │     created_at (DATETIME, DEFAULT NOW)     │
│ INDEX(created_at DESC)                         │  │                                            │
└────────────────────────────────────────────────┘  │ INDEX(rag_insight_id) - idx_rec_rag_ins    │
                                                    │ INDEX(recommendation_type) - idx_rec_type  │
                                                    │ INDEX(priority) - idx_rec_priority         │
                                                    │ INDEX(derived_from_pattern_id)             │
                                                    │ INDEX(was_helpful) - idx_rec_helpful       │
                                                    └────────────────────────────────────────────┘
                                                                     │
                                                                     │ M:1 (SET NULL on delete)
                                                                     ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          rag_learned_patterns                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)                                                 │
│                                                                                  │
│     pattern_name (VARCHAR(255)) [NOT NULL, UNIQUE INDEXED]                       │
│     pattern_category (VARCHAR(100)) [INDEXED]                                    │
│     pattern_type (VARCHAR(100))                                                  │
│                                                                                  │
│     description (TEXT) [NOT NULL]                                                │
│     typical_symptoms (TEXT)                                                      │
│     typical_causes (TEXT)                                                        │
│     recommended_solution (TEXT)                                                  │
│                                                                                  │
│     times_observed (INTEGER, DEFAULT 0) [INDEXED DESC]                           │
│ FK  first_observed_in_pr → pr_analysis.id [SET NULL]                             │
│ FK  last_observed_in_pr → pr_analysis.id [SET NULL]                              │
│     first_observed_at (DATETIME)                                                 │
│     last_observed_at (DATETIME)                                                  │
│                                                                                  │
│     avg_severity_when_found (VARCHAR(20))                                        │
│     avg_issues_caused (INTEGER)                                                  │
│                                                                                  │
│     affected_repositories (JSON)                                                 │
│     affected_authors (JSON)                                                      │
│                                                                                  │
│     confidence_score (FLOAT) [INDEXED DESC]                                      │
│     is_validated (BOOLEAN, DEFAULT FALSE)                                        │
│     is_active (BOOLEAN, DEFAULT TRUE) [INDEXED]                                  │
│                                                                                  │
│     example_prs (JSON)                                                           │
│                                                                                  │
│     created_at (DATETIME, DEFAULT NOW)                                           │
│     updated_at (DATETIME, DEFAULT NOW)                                           │
│                                                                                  │
│ UNIQUE(pattern_name) - rag_learned_patterns_pattern_name_key                     │
│ INDEX(pattern_name) - idx_pattern_name                                           │
│ INDEX(pattern_category) - idx_pattern_category                                   │
│ INDEX(times_observed DESC) - idx_pattern_times_observed                          │
│ INDEX(confidence_score DESC) - idx_pattern_confidence                            │
│ INDEX(is_active) - idx_pattern_active                                            │
└──────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────┐
│                             user_statistics                                      │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)                                                 │
│                                                                                  │
│     author_login (VARCHAR(255)) [NOT NULL, UNIQUE INDEXED]                       │
│     author_email (VARCHAR(255)) [INDEXED]                                        │
│     author_name (VARCHAR(255))                                                   │
│                                                                                  │
│     total_prs (INTEGER, DEFAULT 0)                                               │
│     total_issues_found (INTEGER, DEFAULT 0)                                      │
│                                                                                  │
│     critical_issues_total (INTEGER, DEFAULT 0)                                   │
│     high_issues_total (INTEGER, DEFAULT 0)                                       │
│     medium_issues_total (INTEGER, DEFAULT 0)                                     │
│     low_issues_total (INTEGER, DEFAULT 0)                                        │
│                                                                                  │
│     avg_quality_score (FLOAT)                                                    │
│     avg_security_score (FLOAT)                                                   │
│     avg_maintainability_score (FLOAT)                                            │
│     avg_coverage (FLOAT)                                                         │
│     avg_complexity (FLOAT)                                                       │
│                                                                                  │
│     total_rag_insights (INTEGER, DEFAULT 0)                                      │
│     avg_rag_risk_score (FLOAT)                                                   │
│     avg_rag_novelty_score (FLOAT)                                                │
│     total_similar_prs_referenced (INTEGER, DEFAULT 0)                            │
│     total_rag_recommendations (INTEGER, DEFAULT 0)                               │
│     total_patterns_identified (INTEGER, DEFAULT 0)                               │
│     high_risk_prs_count (INTEGER, DEFAULT 0)                                     │
│     novel_prs_count (INTEGER, DEFAULT 0)                                         │
│     most_common_patterns (JSON)                                                  │
│     learning_velocity (FLOAT)                                                    │
│                                                                                  │
│     quality_trend (VARCHAR(20))                                                  │
│     security_trend (VARCHAR(20))                                                 │
│     coverage_trend (VARCHAR(20))                                                 │
│     rag_risk_trend (VARCHAR(20))                                                 │
│     rag_novelty_trend (VARCHAR(20))                                              │
│                                                                                  │
│     best_pr_id (INTEGER)                                                         │
│     worst_pr_id (INTEGER)                                                        │
│                                                                                  │
│     first_pr_at (DATETIME)                                                       │
│     last_pr_at (DATETIME)                                                        │
│     created_at (DATETIME, DEFAULT NOW)                                           │
│     updated_at (DATETIME, DEFAULT NOW)                                           │
│                                                                                  │
│ UNIQUE(author_login) - idx_user_stats_login                                      │
│ INDEX(author_email) - idx_user_stats_email                                       │
└──────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────┐
│                          pr_comment_statistics                                   │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)                                                 │
│                                                                                  │
│     date (DATETIME) [NOT NULL, INDEXED]                                          │
│     period_type (VARCHAR(20))  # 'daily', 'weekly', 'monthly'                    │
│                                                                                  │
│     total_comments_posted (INTEGER, DEFAULT 0)                                   │
│     summary_comments (INTEGER, DEFAULT 0)                                        │
│     inline_comments (INTEGER, DEFAULT 0)                                         │
│     review_comments (INTEGER, DEFAULT 0)                                         │
│                                                                                  │
│     successful_posts (INTEGER, DEFAULT 0)                                        │
│     failed_posts (INTEGER, DEFAULT 0)                                            │
│     success_rate (FLOAT)                                                         │
│                                                                                  │
│     critical_comments (INTEGER, DEFAULT 0)                                       │
│     high_comments (INTEGER, DEFAULT 0)                                           │
│     medium_comments (INTEGER, DEFAULT 0)                                         │
│     low_comments (INTEGER, DEFAULT 0)                                            │
│                                                                                  │
│     security_comments (INTEGER, DEFAULT 0)                                       │
│     quality_comments (INTEGER, DEFAULT 0)                                        │
│     complexity_comments (INTEGER, DEFAULT 0)                                     │
│     coverage_comments (INTEGER, DEFAULT 0)                                       │
│                                                                                  │
│     avg_reactions_per_comment (FLOAT)                                            │
│     avg_replies_per_comment (FLOAT)                                              │
│     total_reactions (INTEGER, DEFAULT 0)                                         │
│     total_replies (INTEGER, DEFAULT 0)                                           │
│                                                                                  │
│     comments_resolved (INTEGER, DEFAULT 0)                                       │
│     comments_edited (INTEGER, DEFAULT 0)                                         │
│     resolution_rate (FLOAT)                                                      │
│     avg_resolution_time_hours (FLOAT)                                            │
│                                                                                  │
│     request_changes_count (INTEGER, DEFAULT 0)                                   │
│     comment_only_count (INTEGER, DEFAULT 0)                                      │
│     approve_count (INTEGER, DEFAULT 0)                                           │
│                                                                                  │
│     avg_post_time_ms (INTEGER)                                                   │
│                                                                                  │
│     created_at (DATETIME, DEFAULT NOW)                                           │
│                                                                                  │
│ INDEX(date, period_type) - idx_comment_stats_date                                │
└──────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────┐
│                                    users                                         │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PK  id (UUID)                                                                    │
│                                                                                  │
│     username (VARCHAR(255)) [NOT NULL, UNIQUE INDEXED]                           │
│     email (VARCHAR(255)) [NOT NULL, UNIQUE INDEXED]                              │
│     password_hash (VARCHAR(255)) [NOT NULL]                                      │
│                                                                                  │
│     full_name (VARCHAR(255))                                                     │
│     avatar_url (VARCHAR(500))                                                    │
│                                                                                  │
│     role (VARCHAR(50), DEFAULT 'developer')  # admin, reviewer, developer        │
│                                                                                  │
│     is_active (BOOLEAN, DEFAULT TRUE) [INDEXED]                                  │
│     is_verified (BOOLEAN, DEFAULT FALSE)                                         │
│     email_verified (BOOLEAN, DEFAULT FALSE)                                      │
│                                                                                  │
│     github_username (VARCHAR(255))                                               │
│     github_user_id (INTEGER)                                                     │
│                                                                                  │
│     preferences (JSON)                                                           │
│                                                                                  │
│     created_at (DATETIME, DEFAULT NOW)                                           │
│     updated_at (DATETIME, DEFAULT NOW)                                           │
│     last_login_at (DATETIME)                                                     │
│                                                                                  │
│ UNIQUE(username) - users_username_key                                            │
│ UNIQUE(email) - users_email_key                                                  │
│ INDEX(email, is_active) - idx_user_email_active                                  │
│ INDEX(username, is_active) - idx_user_username_active                            │
└──────────────────────────────────────────────────────────────────────────────────┘
                      │
                      │ 1:M (CASCADE DELETE)
                      ▼
┌────────────────────────────────────────────────┐
│             user_sessions                      │
├────────────────────────────────────────────────┤
│ PK  id (INTEGER, AUTO_INCREMENT)               │
│ FK  user_id → users.id [INDEXED]               │
│                                                │
│     session_token (VARCHAR(500)) [NOT NULL,    │
│                                   UNIQUE, IDX] │
│                                                │
│     ip_address (VARCHAR(50))                   │
│     user_agent (VARCHAR(500))                  │
│                                                │
│     is_active (BOOLEAN, DEFAULT TRUE)          │
│                                                │
│     created_at (DATETIME, DEFAULT NOW)         │
│     expires_at (DATETIME) [NOT NULL, INDEXED]  │
│     last_activity (DATETIME, DEFAULT NOW)      │
│     logged_out_at (DATETIME)                   │
│                                                │
│ UNIQUE(session_token) - user_sessions_token_key│
│ INDEX(session_token, is_active)                │
│ INDEX(user_id, is_active)                      │
│ INDEX(expires_at, is_active)                   │
└────────────────────────────────────────────────┘
```

---

## Relationship Legend

### Cardinality Notation:
- **1:1** - One-to-One relationship
- **1:M** - One-to-Many relationship
- **M:1** - Many-to-One relationship
- **M:M** - Many-to-Many relationship (through junction table)

### Foreign Key Actions:
- **CASCADE DELETE** - When parent is deleted, children are automatically deleted
- **SET NULL** - When parent is deleted, foreign key in child is set to NULL
- **RESTRICT** - Prevents deletion of parent if children exist

---

## Complete Relationship Map

```
                    ┌─────────────────────────┐
                    │      pr_analysis        │
                    │    (Central Table)      │
                    └──────────┬──────────────┘
                               │
                               │
        ┌──────────────────────┼──────────────────────┬─────────────────────┐
        │                      │                      │                     │
        │ 1:M (CASCADE)        │ 1:1 (CASCADE)        │ 1:M (CASCADE)       │ 1:1 (CASCADE)
        │                      │                      │                     │
        ▼                      ▼                      ▼                     ▼
   ┌──────────┐         ┌──────────┐          ┌───────────┐       ┌──────────────┐
   │pr_issues │         │pr_metrics│          │pr_comments│       │rag_insights  │
   └──────────┘         └──────────┘          └─────┬─────┘       └──────┬───────┘
        │                                            │                    │
        │ 1:M                                        │                    │ 1:M (CASCADE)
        └────────────────────────────────────────────┘       ┌────────────┼────────────┐
               (pr_comments can link to pr_issues)           │            │            │
                                                              ▼            ▼            ▼
                                                    ┌──────────────┐ ┌──────────┐ ┌─────────┐
                                                    │rag_similar_  │ │   rag_   │ │  rag_   │
                                                    │pr_references │ │recommend-│ │learned_ │
                                                    │              │ │ ations   │ │patterns │
                                                    └──────────────┘ └─────┬────┘ └────┬────┘
                                                                           │           │
                                                                           │ M:1       │
                                                                           │ (SET NULL)│
                                                                           └───────────┘

        ┌─────────────────────────┐
        │  rag_similar_pr_refs    │───► References other pr_analysis records
        │                         │     (Similar PRs from database)
        └─────────────────────────┘

        ┌─────────────────────────┐
        │ rag_learned_patterns    │───► References pr_analysis
        │                         │     (first/last observed PRs, SET NULL)
        └─────────────────────────┘


                    ┌─────────────────────────┐
                    │         users           │
                    └──────────┬──────────────┘
                               │
                               │ 1:M (CASCADE)
                               ▼
                    ┌─────────────────────────┐
                    │    user_sessions        │
                    └─────────────────────────┘


        Aggregated/Computed Tables (No direct FK relationships):
        
        ┌─────────────────────────┐         ┌─────────────────────────┐
        │   user_statistics       │         │ pr_comment_statistics   │
        │ (Computed from          │         │ (Computed from          │
        │  pr_analysis)           │         │  pr_comments)           │
        └─────────────────────────┘         └─────────────────────────┘
```

---

## Detailed Relationship Descriptions

### 1. pr_analysis → pr_issues (1:M, CASCADE DELETE)
- **Parent**: `pr_analysis.id`
- **Child**: `pr_issues.pr_analysis_id`
- **Type**: One PR Analysis has Many Issues
- **Cascade**: Deleting a PR deletes all its issues

### 2. pr_analysis → pr_metrics (1:1, CASCADE DELETE)
- **Parent**: `pr_analysis.id`
- **Child**: `pr_metrics.pr_analysis_id` (UNIQUE)
- **Type**: One PR Analysis has One Metrics record
- **Cascade**: Deleting a PR deletes its metrics

### 3. pr_analysis → pr_comments (1:M, CASCADE DELETE)
- **Parent**: `pr_analysis.id`
- **Child**: `pr_comments.pr_analysis_id`
- **Type**: One PR Analysis has Many Comments
- **Cascade**: Deleting a PR deletes all its comments

### 4. pr_issues → pr_comments (1:M)
- **Parent**: `pr_issues.id`
- **Child**: `pr_comments.pr_issue_id` (OPTIONAL)
- **Type**: One Issue can have Many Comments
- **Note**: This is an optional relationship; comments can exist without linking to specific issues

### 5. pr_analysis → rag_insights (1:1, CASCADE DELETE)
- **Parent**: `pr_analysis.id`
- **Child**: `rag_insights.pr_analysis_id` (UNIQUE)
- **Type**: One PR Analysis has One RAG Insight
- **Cascade**: Deleting a PR deletes its RAG insights

### 6. rag_insights → rag_similar_pr_references (1:M, CASCADE DELETE)
- **Parent**: `rag_insights.id`
- **Child**: `rag_similar_pr_references.rag_insight_id`
- **Type**: One RAG Insight references Many Similar PRs
- **Cascade**: Deleting RAG insight deletes all its references

### 7. rag_similar_pr_references → pr_analysis (M:1)
- **Parent**: `pr_analysis.id`
- **Child**: `rag_similar_pr_references.referenced_pr_analysis_id`
- **Type**: Many References can point to One PR Analysis
- **Note**: This creates a self-referencing relationship where current PRs reference past PRs

### 8. rag_insights → rag_recommendations (1:M, CASCADE DELETE)
- **Parent**: `rag_insights.id`
- **Child**: `rag_recommendations.rag_insight_id`
- **Type**: One RAG Insight has Many Recommendations
- **Cascade**: Deleting RAG insight deletes all its recommendations

### 9. rag_recommendations → rag_learned_patterns (M:1, SET NULL)
- **Parent**: `rag_learned_patterns.id`
- **Child**: `rag_recommendations.derived_from_pattern_id` (OPTIONAL)
- **Type**: Many Recommendations can derive from One Pattern
- **Cascade**: Deleting a pattern sets recommendation's pattern reference to NULL

### 10. rag_learned_patterns → pr_analysis (M:1, SET NULL)
- **Parent**: `pr_analysis.id`
- **Child**: `rag_learned_patterns.first_observed_in_pr` (OPTIONAL)
- **Child**: `rag_learned_patterns.last_observed_in_pr` (OPTIONAL)
- **Type**: Pattern tracks first/last observed PRs
- **Cascade**: Deleting a PR sets pattern's PR reference to NULL

### 11. users → user_sessions (1:M, CASCADE DELETE)
- **Parent**: `users.id`
- **Child**: `user_sessions.user_id`
- **Type**: One User has Many Sessions
- **Cascade**: Deleting a user deletes all their sessions

---

## Unique Constraints

1. **pr_analysis**: `(repository, pr_number)` - One analysis per PR in each repo
2. **rag_insights**: `pr_analysis_id` - One RAG insight per PR
3. **rag_similar_pr_references**: `(rag_insight_id, referenced_pr_analysis_id)` - No duplicate references
4. **rag_learned_patterns**: `pattern_name` - Each pattern has unique name
5. **users**: `username`, `email` - Unique usernames and emails
6. **user_sessions**: `session_token` - Unique session tokens
7. **user_statistics**: `author_login` - One stats record per author

---

## Key Indexes for Performance

### High-Traffic Query Indexes:
1. **pr_analysis**:
   - `(repository, pr_number)` - UNIQUE - Primary lookup
   - `(author_login, analyzed_at)` - User timeline queries
   - `(author_email)` - Email-based searches

2. **pr_issues**:
   - `(pr_analysis_id)` - Get all issues for a PR
   - `(severity)` - Filter by severity
   - `(agent_name)` - Group by agent

3. **rag_insights**:
   - `(risk_score DESC)` - High-risk PRs first
   - `(novelty_score)` - Novel PRs
   - `(generated_at DESC)` - Recent analyses

4. **rag_similar_pr_references**:
   - `(similarity_score DESC)` - Most similar first
   - `(pattern_identified)` - Group by pattern

5. **rag_learned_patterns**:
   - `(times_observed DESC)` - Most common patterns
   - `(confidence_score DESC)` - Most confident patterns

---

## Data Types Summary

- **Primary Keys**: INTEGER (AUTO_INCREMENT) except `users.id` (UUID)
- **Foreign Keys**: INTEGER (matching parent PK)
- **Text Fields**: VARCHAR (short), TEXT (long), JSON (structured)
- **Numbers**: INTEGER, FLOAT, DOUBLE PRECISION
- **Booleans**: BOOLEAN (true/false/null)
- **Dates**: DATETIME/TIMESTAMP WITHOUT TIME ZONE

---

## Field Naming Conventions

- **Primary Keys**: `id`
- **Foreign Keys**: `<parent_table>_id` (e.g., `pr_analysis_id`)
- **Booleans**: `is_*`, `has_*`, `was_*` (e.g., `is_active`, `has_rag_insights`)
- **Timestamps**: `*_at` (e.g., `created_at`, `analyzed_at`)
- **Counts**: `*_count`, `total_*` (e.g., `issues_count`, `total_prs`)
- **Averages**: `avg_*` (e.g., `avg_quality_score`)

---

## Storage Considerations

### Large Text Fields:
- `pr_analysis.pr_description` (TEXT)
- `pr_issues.description`, `pr_issues.recommendation` (TEXT)
- `rag_insights.full_text`, `rag_insights.recommendations` (TEXT)
- `pr_comments.comment_body` (TEXT)

### JSON Fields (Flexible Schema):
- `pr_analysis.rag_patterns_identified`, `rag_insights` (JSON)
- `pr_issues.metadata`, `pr_comments.github_response` (JSON)
- `rag_recommendations.applies_to_files`, `related_issues` (JSON)
- `rag_learned_patterns.affected_repositories`, `example_prs` (JSON)
- `user_statistics.most_common_patterns` (JSON)
- `users.preferences` (JSON)

### Indexed Fields (for fast queries):
- All Foreign Keys
- `repository`, `pr_number`, `author_login`, `author_email`
- `severity`, `issue_type`, `agent_name`
- `risk_score`, `novelty_score`, `similarity_score`
- `is_active`, `context_used`, `was_helpful`

---

## Summary Statistics

- **Total Tables**: 11 (shown in ERD)
- **Total Relationships**: 11 foreign key relationships
- **Unique Constraints**: 7
- **Composite Keys**: 3
- **Cascade Deletes**: 6 relationships
- **Set Null**: 3 relationships
- **JSON Fields**: 15+ fields for flexible storage
- **Indexed Columns**: 50+ indexes for performance

