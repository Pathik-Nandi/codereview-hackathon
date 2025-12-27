"""
RAG Database Service - Handles all RAG-related database operations.

This service manages:
- rag_insights
- rag_similar_pr_references
- rag_learned_patterns
- rag_recommendations
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from utils.logger import logger


class RAGDatabaseService:
    """Service for managing RAG-enhanced data structures."""
    
    def save_rag_insights(
        self,
        session: Session,
        pr_analysis_id: int,
        analysis_result: Dict[str, Any]
    ) -> Optional[int]:
        """
        Save RAG insights to structured tables.
        
        Args:
            session: Database session
            pr_analysis_id: ID of the PR analysis record
            analysis_result: Complete analysis result from agents
            
        Returns:
            rag_insights.id if successful, None otherwise
        """
        try:
            # Get the repository name from the current PR
            from models.database import PRAnalysis
            current_pr = session.query(PRAnalysis).get(pr_analysis_id)
            repository = current_pr.repository if current_pr else None
            
            # Extract RAG data from analysis result
            rag_data = self._extract_rag_data(analysis_result)
            
            if not rag_data:
                logger.warning(f"No RAG data found for PR analysis {pr_analysis_id}")
                return None
            
            # Insert into rag_insights table
            insight_id = self._insert_rag_insights(session, pr_analysis_id, rag_data)
            
            if not insight_id:
                return None
            
            # Save similar PR references
            if rag_data.get('similar_prs') and repository:
                self._save_similar_pr_references(
                    session,
                    insight_id,
                    rag_data['similar_prs'],
                    repository
                )
            
            # Save recommendations
            recommendations_list = rag_data.get('recommendations_list', [])
            logger.info(f"DEBUG: recommendations_list has {len(recommendations_list)} items")
            logger.info(f"DEBUG: recommendations_list content: {recommendations_list[:2] if recommendations_list else 'EMPTY'}")
            
            if recommendations_list:
                self._save_recommendations(
                    session,
                    insight_id,
                    recommendations_list
                )
            else:
                logger.warning(f"No recommendations to save for insight {insight_id}")
            
            # Save learned patterns (with error handling to prevent transaction rollback)
            try:
                self._save_learned_patterns(
                    session,
                    insight_id,
                    pr_analysis_id,
                    rag_data
                )
            except Exception as pattern_error:
                logger.error(f"Failed to save patterns, but continuing: {pattern_error}")
                # Don't re-raise - we want insights and recommendations to still be saved
            
            # Update pr_analysis with RAG metrics
            self._update_pr_analysis_rag_metrics(
                session,
                pr_analysis_id,
                rag_data
            )
            
            logger.info(f"RAG insights saved successfully for PR analysis {pr_analysis_id}")
            return insight_id
            
        except Exception as e:
            logger.error(f"Error saving RAG insights: {e}")
            return None
    
    def _extract_rag_data(self, analysis_result: Dict) -> Optional[Dict]:
        """Extract RAG data from analysis result."""
        try:
            # Debug: Check what we received
            logger.info(f"DEBUG: analysis_result keys: {list(analysis_result.keys())}")
            logger.info(f"DEBUG: analysis_result type: {type(analysis_result)}")
            
            # Get RAG Enhanced Agent data
            agent_breakdown = analysis_result.get('agent_breakdown', {})
            logger.info(f"DEBUG: agent_breakdown type: {type(agent_breakdown)}")
            logger.info(f"DEBUG: agent_breakdown keys: {list(agent_breakdown.keys()) if hasattr(agent_breakdown, 'keys') else 'N/A'}")
            
            rag_agent_data = agent_breakdown.get('RAG Enhanced Agent', {})
            
            if not rag_agent_data:
                logger.warning(f"DEBUG: No rag_agent_data found. agent_breakdown keys: {analysis_result.get('agent_breakdown', {}).keys() if hasattr(analysis_result.get('agent_breakdown', {}), 'keys') else 'N/A'}")
                return None
            
            metadata = rag_agent_data.get('metadata', {})
            rag_insights = metadata.get('rag_insights', {})
            
            logger.info(f"DEBUG: metadata keys: {metadata.keys() if hasattr(metadata, 'keys') else 'N/A'}")
            logger.info(f"DEBUG: rag_insights type: {type(rag_insights)}")
            
            if not rag_insights:
                return None
            
            # Extract structured data
            extracted_data = {
                # Models used
                'embedding_model': metadata.get('embedding_model', 'all-MiniLM-L6-v2'),
                'llm_model': metadata.get('llm_model', 'gpt-4o-mini'),
                'vector_db_used': 'ChromaDB',
                
                # Full text and summary
                'full_text': rag_insights.get('full_text', ''),
                'summary': rag_insights.get('summary', '')[:1000] if rag_insights.get('summary') else None,
                
                # Context usage
                'context_used': rag_insights.get('context_used', False),
                'similar_prs_found': metadata.get('similar_prs_found', 0),
                'similar_prs_referenced': rag_insights.get('similar_prs_referenced', 0),
                'context_confidence_score': metadata.get('average_similarity', 0.0),
                
                # Insights
                'recommendations': rag_insights.get('recommendations', ''),
                'lessons_learned': rag_insights.get('lessons_learned', ''),
                'potential_pitfalls': rag_insights.get('potential_pitfalls', ''),
                'best_practices_suggested': rag_insights.get('best_practices', ''),
                
                # Scores
                'novelty_score': self._calculate_novelty_score(metadata),
                'risk_score': self._calculate_risk_score(rag_insights, analysis_result),
                'complexity_assessment': self._assess_complexity(analysis_result),
                
                # Metadata
                'generation_time_ms': metadata.get('generation_time_ms', 0),
                'tokens_used': metadata.get('tokens_used', 0),
                
                # Similar PRs (for rag_similar_pr_references)
                'similar_prs': metadata.get('similar_prs', []),
                
                # Recommendations list (for rag_recommendations)
                'recommendations_list': self._parse_recommendations(rag_insights.get('recommendations', ''))
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting RAG data: {e}")
            return None
    
    def _insert_rag_insights(
        self,
        session: Session,
        pr_analysis_id: int,
        rag_data: Dict
    ) -> Optional[int]:
        """Insert RAG insights into database."""
        try:
            insert_sql = text("""
                INSERT INTO rag_insights (
                    pr_analysis_id, embedding_model, llm_model, vector_db_used,
                    full_text, summary,
                    context_used, similar_prs_found, similar_prs_referenced, context_confidence_score,
                    recommendations, lessons_learned, potential_pitfalls, best_practices_suggested,
                    novelty_score, risk_score, complexity_assessment,
                    generated_at, generation_time_ms, tokens_used
                ) VALUES (
                    :pr_analysis_id, :embedding_model, :llm_model, :vector_db_used,
                    :full_text, :summary,
                    :context_used, :similar_prs_found, :similar_prs_referenced, :context_confidence_score,
                    :recommendations, :lessons_learned, :potential_pitfalls, :best_practices_suggested,
                    :novelty_score, :risk_score, :complexity_assessment,
                    NOW(), :generation_time_ms, :tokens_used
                ) RETURNING id
            """)
            
            result = session.execute(insert_sql, {
                'pr_analysis_id': pr_analysis_id,
                'embedding_model': rag_data['embedding_model'],
                'llm_model': rag_data['llm_model'],
                'vector_db_used': rag_data['vector_db_used'],
                'full_text': rag_data['full_text'],
                'summary': rag_data['summary'],
                'context_used': rag_data['context_used'],
                'similar_prs_found': rag_data['similar_prs_found'],
                'similar_prs_referenced': rag_data['similar_prs_referenced'],
                'context_confidence_score': rag_data['context_confidence_score'],
                'recommendations': rag_data['recommendations'],
                'lessons_learned': rag_data['lessons_learned'],
                'potential_pitfalls': rag_data['potential_pitfalls'],
                'best_practices_suggested': rag_data['best_practices_suggested'],
                'novelty_score': rag_data['novelty_score'],
                'risk_score': rag_data['risk_score'],
                'complexity_assessment': rag_data['complexity_assessment'],
                'generation_time_ms': rag_data['generation_time_ms'],
                'tokens_used': rag_data['tokens_used']
            })
            
            insight_id = result.fetchone()[0]
            return insight_id
            
        except Exception as e:
            logger.error(f"Error inserting RAG insights: {e}")
            return None
    
    def _save_similar_pr_references(
        self,
        session: Session,
        rag_insight_id: int,
        similar_prs: List[Dict],
        repository: str
    ):
        """Save similar PR references."""
        try:
            from models.database import PRAnalysis
            
            for similar_pr in similar_prs[:10]:  # Limit to top 10
                # Get PR database ID from PR number
                pr_number = similar_pr.get('pr_number')
                if not pr_number:
                    continue
                
                # Look up the PR in the database using the provided repository
                pr_analysis = session.query(PRAnalysis).filter_by(
                    repository=repository,
                    pr_number=pr_number
                ).first()
                
                if not pr_analysis:
                    # PR not in database yet, skip
                    logger.debug(f"Similar PR #{pr_number} not in database yet, skipping reference")
                    continue
                
                # Extract pattern if mentioned in lesson
                lesson = similar_pr.get('lesson', '')
                pattern = self._extract_pattern_from_lesson(lesson)
                
                insert_sql = text("""
                    INSERT INTO rag_similar_pr_references (
                        rag_insight_id, referenced_pr_analysis_id,
                        similarity_score, similarity_type,
                        used_in_analysis, contributed_to_recommendation,
                        lesson_extracted, pattern_identified
                    ) VALUES (
                        :rag_insight_id, :referenced_pr_id,
                        :similarity_score, :similarity_type,
                        :used_in_analysis, :contributed_to_recommendation,
                        :lesson_extracted, :pattern_identified
                    )
                    ON CONFLICT (rag_insight_id, referenced_pr_analysis_id) DO NOTHING
                """)
                
                session.execute(insert_sql, {
                    'rag_insight_id': rag_insight_id,
                    'referenced_pr_id': pr_analysis.id,  # Use database ID
                    'similarity_score': similar_pr.get('similarity', 0.0),
                    'similarity_type': similar_pr.get('type', 'context'),
                    'used_in_analysis': True,
                    'contributed_to_recommendation': bool(lesson),
                    'lesson_extracted': lesson[:1000] if lesson else '',  # Limit length
                    'pattern_identified': pattern
                })
            
        except Exception as e:
            logger.error(f"Error saving similar PR references: {e}")
            # Don't raise - allow the main transaction to continue
    
    def _save_recommendations(
        self,
        session: Session,
        rag_insight_id: int,
        recommendations: List[Dict]
    ):
        """Save individual recommendations."""
        logger.info(f"DEBUG: _save_recommendations called with {len(recommendations)} recommendations for insight {rag_insight_id}")
        try:
            for idx, rec in enumerate(recommendations):
                logger.info(f"DEBUG: Saving recommendation {idx+1}: {rec.get('title', 'NO TITLE')[:100]}")
                insert_sql = text("""
                    INSERT INTO rag_recommendations (
                        rag_insight_id, recommendation_type, priority,
                        title, description, reasoning,
                        applies_to_files, applies_to_lines, related_issues
                    ) VALUES (
                        :rag_insight_id, :recommendation_type, :priority,
                        :title, :description, :reasoning,
                        CAST(:applies_to_files AS jsonb), CAST(:applies_to_lines AS jsonb), CAST(:related_issues AS jsonb)
                    )
                """)
                
                # Ensure JSON fields are proper JSON strings
                applies_to_files = rec.get('files', '[]')
                applies_to_lines = rec.get('lines', '[]')
                related_issues = rec.get('issues', '[]')
                
                # If they're not strings, convert to JSON
                import json
                if not isinstance(applies_to_files, str):
                    applies_to_files = json.dumps(applies_to_files)
                if not isinstance(applies_to_lines, str):
                    applies_to_lines = json.dumps(applies_to_lines)
                if not isinstance(related_issues, str):
                    related_issues = json.dumps(related_issues)
                
                session.execute(insert_sql, {
                    'rag_insight_id': rag_insight_id,
                    'recommendation_type': rec.get('type', 'general'),
                    'priority': rec.get('priority', 'medium'),
                    'title': rec.get('title', ''),
                    'description': rec.get('description', ''),
                    'reasoning': rec.get('reasoning', ''),
                    'applies_to_files': applies_to_files,
                    'applies_to_lines': applies_to_lines,
                    'related_issues': related_issues
                })
            
        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")
    
    def _save_learned_patterns(
        self,
        session: Session,
        rag_insight_id: int,
        pr_analysis_id: int,
        rag_data: Dict
    ):
        """Save learned patterns extracted from lessons and pitfalls."""
        logger.info(f"DEBUG: _save_learned_patterns called for insight {rag_insight_id}")
        try:
            patterns = []
            
            # Extract patterns from lessons learned
            lessons = rag_data.get('lessons_learned', '')
            if lessons:
                patterns.extend(self._extract_patterns_from_text(
                    lessons, 
                    'lesson'
                ))
            
            # Extract patterns from potential pitfalls
            pitfalls = rag_data.get('potential_pitfalls', '')
            if pitfalls:
                patterns.extend(self._extract_patterns_from_text(
                    pitfalls,
                    'pitfall'
                ))
            
            # Extract patterns from best practices
            best_practices = rag_data.get('best_practices_suggested', '')
            if best_practices:
                patterns.extend(self._extract_patterns_from_text(
                    best_practices,
                    'best_practice'
                ))
            
            logger.info(f"DEBUG: Extracted {len(patterns)} patterns")
            
            # Save each pattern
            for pattern in patterns:
                # Check if pattern already exists
                check_sql = text("""
                    SELECT id, times_observed, example_prs 
                    FROM rag_learned_patterns 
                    WHERE pattern_name = :pattern_name 
                    AND pattern_category = :pattern_category
                    LIMIT 1
                """)
                
                existing = session.execute(check_sql, {
                    'pattern_name': pattern['name'][:200],
                    'pattern_category': pattern['category']
                }).fetchone()
                
                if existing:
                    # Update existing pattern
                    update_sql = text("""
                        UPDATE rag_learned_patterns 
                        SET times_observed = times_observed + 1,
                            last_observed_in_pr = :last_observed_in_pr,
                            last_observed_at = NOW(),
                            updated_at = NOW(),
                            example_prs = (
                                SELECT jsonb_agg(DISTINCT elem)
                                FROM (
                                    SELECT elem FROM jsonb_array_elements(
                                        COALESCE(example_prs, '[]'::jsonb)
                                    ) elem
                                    UNION
                                    SELECT :pr_id::text::jsonb
                                ) t(elem)
                                LIMIT 10
                            )
                        WHERE id = :pattern_id
                    """)
                    
                    session.execute(update_sql, {
                        'pattern_id': existing.id,
                        'last_observed_in_pr': pr_analysis_id,
                        'pr_id': pr_analysis_id
                    })
                else:
                    # Insert new pattern
                    insert_sql = text("""
                        INSERT INTO rag_learned_patterns (
                            pattern_name, pattern_category, pattern_type,
                            description, typical_symptoms, typical_causes,
                            recommended_solution, times_observed,
                            first_observed_in_pr, last_observed_in_pr,
                            first_observed_at, last_observed_at,
                            avg_severity_when_found, confidence_score,
                            is_validated, is_active,
                            example_prs, affected_repositories, affected_authors,
                            created_at, updated_at
                        ) VALUES (
                            :pattern_name, :pattern_category, :pattern_type,
                            :description, :typical_symptoms, :typical_causes,
                            :recommended_solution, :times_observed,
                            :first_observed_in_pr, :last_observed_in_pr,
                            NOW(), NOW(),
                            :avg_severity_when_found, :confidence_score,
                            :is_validated, :is_active,
                            CAST(:example_prs AS jsonb), CAST(:affected_repositories AS jsonb), CAST(:affected_authors AS jsonb),
                            NOW(), NOW()
                        )
                    """)
                    
                    # Prepare JSON fields as proper JSON strings
                    import json
                    example_prs_json = json.dumps([pr_analysis_id])
                    affected_repos_json = json.dumps([])
                    affected_authors_json = json.dumps([])
                    
                    session.execute(insert_sql, {
                        'pattern_name': pattern['name'][:200],
                        'pattern_category': pattern['category'],
                        'pattern_type': pattern['type'],
                        'description': pattern['description'][:1000],
                        'typical_symptoms': pattern.get('symptoms', '')[:1000],
                        'typical_causes': pattern.get('causes', '')[:1000],
                        'recommended_solution': pattern.get('solution', '')[:1000],
                        'times_observed': 1,
                        'first_observed_in_pr': pr_analysis_id,
                        'last_observed_in_pr': pr_analysis_id,
                        'avg_severity_when_found': 'medium',
                        'confidence_score': 0.7,
                        'is_validated': False,
                        'is_active': True,
                        'example_prs': example_prs_json,
                        'affected_repositories': affected_repos_json,
                        'affected_authors': affected_authors_json
                    })
                
            logger.info(f"DEBUG: Saved {len(patterns)} learned patterns")
            
        except Exception as e:
            logger.error(f"Error saving learned patterns: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _extract_patterns_from_text(
        self,
        text: str,
        pattern_type: str
    ) -> List[Dict]:
        """Extract patterns from text (lessons, pitfalls, best practices)."""
        patterns = []
        lines = text.split('\n')
        
        current_pattern = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if self._is_pattern_start(line):
                if current_pattern:
                    patterns.append(current_pattern)
                current_pattern = self._create_pattern_from_line(line, pattern_type)
            elif current_pattern:
                # Continuation of current pattern description
                current_pattern['description'] += ' ' + line.strip('*').strip()
        
        if current_pattern:
            patterns.append(current_pattern)
        
        return patterns[:20]  # Limit to 20 patterns
    
    def _is_pattern_start(self, line: str) -> bool:
        """Check if line is the start of a new pattern."""
        if not line:
            return False
        return line[0].isdigit() or line.startswith(('-', '•', '*'))
    
    def _create_pattern_from_line(self, line: str, pattern_type: str) -> Dict:
        """Create a pattern dictionary from a line."""
        # Extract the pattern name/title
        clean_line = line.lstrip('0123456789.-•*) ').strip()
        
        # Split on first colon if exists (e.g., "**Title**: description")
        if ':' in clean_line:
            parts = clean_line.split(':', 1)
            name = parts[0].strip('*').strip()
            description = parts[1].strip() if len(parts) > 1 else clean_line
        else:
            name = clean_line[:100].strip('*').strip()
            description = clean_line
        
        return {
            'name': name,
            'category': self._categorize_pattern(name),
            'type': pattern_type,
            'description': description,
            'symptoms': '',
            'causes': '',
            'solution': ''
        }
    
    def _categorize_pattern(self, pattern_name: str) -> str:
        """Categorize a pattern based on its name."""
        name_lower = pattern_name.lower()
        
        if any(word in name_lower for word in ['test', 'testing', 'coverage']):
            return 'testing'
        elif any(word in name_lower for word in ['description', 'document', 'comment']):
            return 'documentation'
        elif any(word in name_lower for word in ['security', 'vulnerability', 'auth']):
            return 'security'
        elif any(word in name_lower for word in ['performance', 'optimize', 'speed']):
            return 'performance'
        elif any(word in name_lower for word in ['error', 'exception', 'handling']):
            return 'error_handling'
        elif any(word in name_lower for word in ['code quality', 'style', 'naming']):
            return 'code_quality'
        else:
            return 'general'
    
    def _update_pr_analysis_rag_metrics(
        self,
        session: Session,
        pr_analysis_id: int,
        rag_data: Dict
    ):
        """Update pr_analysis with RAG metrics for fast queries."""
        try:
            # Extract pattern names from similar PRs
            patterns = set()
            for pr in rag_data.get('similar_prs', []):
                pattern = self._extract_pattern_from_lesson(pr.get('lesson', ''))
                if pattern:
                    patterns.add(pattern)
            
            import json
            patterns_json = json.dumps(list(patterns)) if patterns else '[]'
            
            update_sql = text("""
                UPDATE pr_analysis
                SET has_rag_insights = TRUE,
                    rag_risk_score = :risk_score,
                    rag_novelty_score = :novelty_score,
                    rag_similar_prs_count = :similar_prs_count,
                    rag_recommendations_count = :recommendations_count,
                    rag_patterns_identified = CAST(:patterns AS jsonb)
                WHERE id = :pr_analysis_id
            """)
            
            session.execute(update_sql, {
                'pr_analysis_id': pr_analysis_id,
                'risk_score': rag_data['risk_score'],
                'novelty_score': rag_data['novelty_score'],
                'similar_prs_count': rag_data['similar_prs_referenced'],
                'recommendations_count': len(rag_data.get('recommendations_list', [])),
                'patterns': patterns_json
            })
            
        except Exception as e:
            logger.error(f"Error updating pr_analysis RAG metrics: {e}")
    
    # Helper methods
    
    def _calculate_novelty_score(self, metadata: Dict) -> float:
        """Calculate novelty score based on similar PRs found."""
        similar_count = metadata.get('similar_prs_found', 0)
        
        if similar_count == 0:
            return 1.0
        elif similar_count <= 2:
            return 0.8
        elif similar_count <= 5:
            return 0.6
        elif similar_count <= 10:
            return 0.4
        else:
            return 0.2
    
    def _calculate_risk_score(self, rag_insights: Dict, analysis_result: Dict) -> float:
        """Calculate risk score based on issues and patterns."""
        # Get issue counts
        critical = analysis_result.get('critical_issues', 0)
        high = analysis_result.get('high_issues', 0)
        medium = analysis_result.get('medium_issues', 0)
        
        # Calculate base risk from issues
        issue_risk = min(1.0, (critical * 0.3 + high * 0.15 + medium * 0.05) / 10)
        
        # Check for risk keywords in insights
        risk_keywords = ['security', 'vulnerability', 'critical', 'dangerous', 'unsafe', 'risk']
        pitfalls = rag_insights.get('potential_pitfalls', '').lower()
        
        keyword_risk = sum(0.1 for keyword in risk_keywords if keyword in pitfalls)
        keyword_risk = min(0.5, keyword_risk)
        
        # Combine
        total_risk = min(1.0, issue_risk + keyword_risk)
        return round(total_risk, 2)
    
    def _assess_complexity(self, analysis_result: Dict) -> str:
        """Assess PR complexity."""
        files_changed = analysis_result.get('files_changed', 0)
        lines_changed = analysis_result.get('lines_added', 0) + analysis_result.get('lines_deleted', 0)
        
        if files_changed > 20 or lines_changed > 1000:
            return 'High'
        elif files_changed > 10 or lines_changed > 500:
            return 'Medium'
        else:
            return 'Low'
    
    def _extract_pattern_from_lesson(self, lesson: str) -> Optional[str]:
        """Extract pattern name from lesson text."""
        if not lesson:
            return None
        
        # Common patterns to look for
        patterns = [
            'Missing Error Handling',
            'Missing Input Validation',
            'Hardcoded Credentials',
            'SQL Injection',
            'Missing Test Coverage',
            'Code Duplication',
            'Long Method',
            'Deep Nesting',
            'Magic Numbers'
        ]
        
        lesson_lower = lesson.lower()
        for pattern in patterns:
            if pattern.lower() in lesson_lower:
                return pattern
        
        return None
    
    def _parse_recommendations(self, recommendations_text: str) -> List[Dict]:
        """Parse recommendations text into structured list."""
        logger.info(f"DEBUG: _parse_recommendations called with text length: {len(recommendations_text) if recommendations_text else 0}")
        logger.info(f"DEBUG: recommendations_text sample: {recommendations_text[:300] if recommendations_text else 'EMPTY'}")
        
        if not recommendations_text:
            return []
        
        recommendations = []
        lines = recommendations_text.split('\n')
        
        current_rec = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new recommendation (starts with number or bullet)
            if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                if current_rec:
                    recommendations.append(current_rec)
                
                # Remove number/bullet
                title = line.lstrip('0123456789.-•) ').strip()
                current_rec = {
                    'title': title[:500],
                    'description': title,
                    'type': 'focus_area',
                    'priority': 'medium',
                    'reasoning': '',
                    'files': '[]',
                    'lines': '[]',
                    'issues': '[]'
                }
            elif current_rec:
                # Continuation of current recommendation
                current_rec['description'] += ' ' + line
        
        if current_rec:
            recommendations.append(current_rec)
        
        logger.info(f"DEBUG: _parse_recommendations returning {len(recommendations)} recommendations")
        return recommendations[:20]  # Limit to 20 recommendations
    
    def get_rag_insights_for_pr(self, session: Session, pr_analysis_id: int) -> Optional[Dict]:
        """Get RAG insights for a specific PR."""
        try:
            query = text("""
                SELECT 
                    ri.*,
                    COUNT(DISTINCT ref.id) as reference_count,
                    COUNT(DISTINCT rec.id) as recommendation_count
                FROM rag_insights ri
                LEFT JOIN rag_similar_pr_references ref ON ri.id = ref.rag_insight_id
                LEFT JOIN rag_recommendations rec ON ri.id = rec.rag_insight_id
                WHERE ri.pr_analysis_id = :pr_analysis_id
                GROUP BY ri.id
            """)
            
            result = session.execute(query, {'pr_analysis_id': pr_analysis_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return dict(row._mapping)
            
        except Exception as e:
            logger.error(f"Error fetching RAG insights: {e}")
            return None
    
    def get_similar_prs_for_insight(
        self,
        session: Session,
        rag_insight_id: int
    ) -> List[Dict]:
        """Get similar PR references for an insight."""
        try:
            query = text("""
                SELECT 
                    ref.*,
                    pa.pr_number,
                    pa.pr_title,
                    pa.author_email,
                    pa.repository
                FROM rag_similar_pr_references ref
                JOIN pr_analysis pa ON ref.referenced_pr_analysis_id = pa.id
                WHERE ref.rag_insight_id = :rag_insight_id
                ORDER BY ref.similarity_score DESC
            """)
            
            result = session.execute(query, {'rag_insight_id': rag_insight_id})
            return [dict(row._mapping) for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching similar PRs: {e}")
            return []
