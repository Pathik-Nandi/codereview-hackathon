"""Auto-merge decision agent for evaluating PRs for automatic merging."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from utils.logger import logger
from utils.config import config


class AutoMergeAgent:
    """
    Agent responsible for deciding whether a PR should be automatically merged.
    
    Evaluates PRs based on configurable conditions including:
    - Code quality scores
    - Security scores
    - Issue counts and severity
    - Review approvals
    - CI/CD status checks
    - PR metadata (size, description, etc.)
    """
    
    def __init__(self):
        """Initialize the auto-merge agent."""
        self.logger = logger.bind(agent="auto_merge")
        self.config = config.get('auto_merge', {})
        self.enabled = self.config.get('enabled', False)
        self.mode = self.config.get('mode', 'conditional')
        self.conditions = self.config.get('conditions', {})
        
        self.logger.info(
            "Auto-merge agent initialized",
            enabled=self.enabled,
            mode=self.mode
        )
    
    def should_auto_merge(
        self,
        pr_analysis: Dict,
        pr_details: Dict,
        reviews: Optional[List[Dict]] = None,
        status_checks: Optional[Dict] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Determine if a PR should be automatically merged.
        
        Args:
            pr_analysis: Analysis results from the review agents
            pr_details: PR metadata from GitHub
            reviews: List of PR reviews with approval status
            status_checks: CI/CD status check results
            
        Returns:
            Tuple of (should_merge, reason, details):
            - should_merge: Boolean indicating if PR should be merged
            - reason: String explanation of the decision
            - details: Dictionary with evaluation details
        """
        if not self.enabled:
            return False, "Auto-merge is disabled in configuration", {}
        
        if self.mode == 'never':
            return False, "Auto-merge mode is set to 'never'", {}
        
        if self.mode == 'always':
            self.logger.warning("Auto-merge mode is 'always' - merging without checks!")
            return True, "Auto-merge mode is set to 'always'", {}
        
        # Mode is 'conditional' - evaluate all conditions
        evaluation = {
            'checks_passed': [],
            'checks_failed': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # 1. Check repository allowlist
        repository = pr_details.get('repository', {}).get('full_name', '')
        if not self._check_repository_allowed(repository, evaluation):
            return False, f"Repository '{repository}' not in allowed list", evaluation
        
        # 2. Check user allowlist
        author = pr_details.get('user', {}).get('login', '')
        if not self._check_user_allowed(author, evaluation):
            return False, f"User '{author}' not in allowed list", evaluation
        
        # 3. Check WIP/Draft status
        if not self._check_wip_status(pr_details, evaluation):
            return False, "PR is marked as WIP or in draft state", evaluation
        
        # 4. Check quality scores
        if not self._check_quality_scores(pr_analysis, evaluation):
            return False, "Quality score requirements not met", evaluation
        
        # 5. Check issue counts
        if not self._check_issue_counts(pr_analysis, evaluation):
            return False, "Issue count thresholds exceeded", evaluation
        
        # 6. Check approvals
        if reviews is not None and not self._check_approvals(reviews, evaluation):
            return False, "Approval requirements not met", evaluation
        
        # 7. Check status checks (CI/CD)
        if status_checks is not None and not self._check_status_checks(status_checks, evaluation):
            return False, "CI/CD status checks not passing", evaluation
        
        # 8. Check PR size
        if not self._check_pr_size(pr_analysis, evaluation):
            return False, "PR size exceeds limits", evaluation
        
        # 9. Check for breaking changes
        if not self._check_breaking_changes(pr_analysis, evaluation):
            return False, "PR contains breaking changes", evaluation
        
        # All checks passed
        passed_count = len(evaluation['checks_passed'])
        self.logger.info(
            "PR passed all auto-merge checks",
            repository=repository,
            pr_number=pr_details.get('number'),
            checks_passed=passed_count
        )
        
        return True, f"All {passed_count} auto-merge conditions met", evaluation
    
    def _check_repository_allowed(self, repository: str, evaluation: Dict) -> bool:
        """Check if repository is in the allowed list."""
        allowed_repos = self.config.get('allowed_repositories', [])
        
        # Empty list means all repositories are allowed
        if not allowed_repos:
            evaluation['checks_passed'].append({
                'check': 'repository_allowlist',
                'status': 'passed',
                'message': 'All repositories allowed'
            })
            return True
        
        if repository in allowed_repos:
            evaluation['checks_passed'].append({
                'check': 'repository_allowlist',
                'status': 'passed',
                'message': f"Repository '{repository}' is allowed"
            })
            return True
        
        evaluation['checks_failed'].append({
            'check': 'repository_allowlist',
            'status': 'failed',
            'message': f"Repository '{repository}' not in allowed list",
            'allowed_repositories': allowed_repos
        })
        return False
    
    def _check_user_allowed(self, user: str, evaluation: Dict) -> bool:
        """Check if user is in the allowed list."""
        allowed_users = self.config.get('allowed_users', [])
        
        # Empty list means all users are allowed
        if not allowed_users:
            evaluation['checks_passed'].append({
                'check': 'user_allowlist',
                'status': 'passed',
                'message': 'All users allowed'
            })
            return True
        
        if user in allowed_users:
            evaluation['checks_passed'].append({
                'check': 'user_allowlist',
                'status': 'passed',
                'message': f"User '{user}' is allowed"
            })
            return True
        
        evaluation['checks_failed'].append({
            'check': 'user_allowlist',
            'status': 'failed',
            'message': f"User '{user}' not in allowed list",
            'allowed_users': allowed_users
        })
        return False
    
    def _check_wip_status(self, pr_details: Dict, evaluation: Dict) -> bool:
        """Check if PR is marked as WIP or draft."""
        allow_wip = self.conditions.get('allow_wip_prs', False)
        
        title = pr_details.get('title', '').lower()
        is_draft = pr_details.get('draft', False)
        is_wip = 'wip' in title or '[wip]' in title or 'work in progress' in title
        
        if not allow_wip and (is_draft or is_wip):
            evaluation['checks_failed'].append({
                'check': 'wip_status',
                'status': 'failed',
                'message': 'PR is marked as WIP or draft',
                'is_draft': is_draft,
                'is_wip': is_wip
            })
            return False
        
        evaluation['checks_passed'].append({
            'check': 'wip_status',
            'status': 'passed',
            'message': 'PR is not WIP or draft'
        })
        return True
    
    def _check_quality_scores(self, pr_analysis: Dict, evaluation: Dict) -> bool:
        """Check if quality scores meet minimum thresholds."""
        scores = pr_analysis.get('scores', {})
        
        min_quality = self.conditions.get('min_quality_score', 85.0)
        min_security = self.conditions.get('min_security_score', 95.0)
        min_maintainability = self.conditions.get('min_maintainability_score', 70.0)
        
        quality_score = scores.get('overall_quality_score', 0)
        security_score = scores.get('security_score', 0)
        maintainability_score = scores.get('maintainability_score', 0)
        
        checks = [
            ('quality_score', quality_score, min_quality, 'Overall quality'),
            ('security_score', security_score, min_security, 'Security'),
            ('maintainability_score', maintainability_score, min_maintainability, 'Maintainability')
        ]
        
        all_passed = True
        for check_name, actual, minimum, label in checks:
            if actual >= minimum:
                evaluation['checks_passed'].append({
                    'check': check_name,
                    'status': 'passed',
                    'message': f'{label} score {actual} >= {minimum}',
                    'actual': actual,
                    'required': minimum
                })
            else:
                evaluation['checks_failed'].append({
                    'check': check_name,
                    'status': 'failed',
                    'message': f'{label} score {actual} < {minimum}',
                    'actual': actual,
                    'required': minimum
                })
                all_passed = False
        
        return all_passed
    
    def _check_issue_counts(self, pr_analysis: Dict, evaluation: Dict) -> bool:
        """Check if issue counts are within acceptable limits."""
        issues = pr_analysis.get('issues', [])
        
        max_critical = self.conditions.get('max_critical_issues', 0)
        max_high = self.conditions.get('max_high_issues', 0)
        max_medium = self.conditions.get('max_medium_issues', 5)
        max_total = self.conditions.get('max_total_issues', 20)
        
        # Count issues by severity
        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        high_count = sum(1 for i in issues if i.get('severity') == 'high')
        medium_count = sum(1 for i in issues if i.get('severity') == 'medium')
        total_count = len(issues)
        
        checks = [
            ('critical_issues', critical_count, max_critical, 'Critical issues'),
            ('high_issues', high_count, max_high, 'High severity issues'),
            ('medium_issues', medium_count, max_medium, 'Medium severity issues'),
            ('total_issues', total_count, max_total, 'Total issues')
        ]
        
        all_passed = True
        for check_name, actual, maximum, label in checks:
            if actual <= maximum:
                evaluation['checks_passed'].append({
                    'check': check_name,
                    'status': 'passed',
                    'message': f'{label}: {actual} <= {maximum}',
                    'actual': actual,
                    'limit': maximum
                })
            else:
                evaluation['checks_failed'].append({
                    'check': check_name,
                    'status': 'failed',
                    'message': f'{label}: {actual} > {maximum}',
                    'actual': actual,
                    'limit': maximum
                })
                all_passed = False
        
        return all_passed
    
    def _check_approvals(self, reviews: List[Dict], evaluation: Dict) -> bool:
        """Check if PR has required approvals."""
        require_approval = self.conditions.get('require_approval', True)
        min_approvals = self.conditions.get('min_approvals', 1)
        
        if not require_approval:
            evaluation['checks_passed'].append({
                'check': 'approvals',
                'status': 'passed',
                'message': 'Approvals not required'
            })
            return True
        
        # Count approved reviews
        approved_count = sum(1 for r in reviews if r.get('state') == 'APPROVED')
        changes_requested = sum(1 for r in reviews if r.get('state') == 'CHANGES_REQUESTED')
        
        if changes_requested > 0:
            evaluation['checks_failed'].append({
                'check': 'approvals',
                'status': 'failed',
                'message': f'{changes_requested} review(s) requested changes',
                'changes_requested': changes_requested
            })
            return False
        
        if approved_count >= min_approvals:
            evaluation['checks_passed'].append({
                'check': 'approvals',
                'status': 'passed',
                'message': f'{approved_count} approval(s) (required: {min_approvals})',
                'approved_count': approved_count,
                'required': min_approvals
            })
            return True
        
        evaluation['checks_failed'].append({
            'check': 'approvals',
            'status': 'failed',
            'message': f'Only {approved_count} approval(s), need {min_approvals}',
            'approved_count': approved_count,
            'required': min_approvals
        })
        return False
    
    def _check_status_checks(self, status_checks: Dict, evaluation: Dict) -> bool:
        """Check if CI/CD status checks are passing."""
        state = status_checks.get('state', 'unknown')
        
        if state == 'success':
            evaluation['checks_passed'].append({
                'check': 'status_checks',
                'status': 'passed',
                'message': 'All CI/CD checks passing',
                'total_checks': status_checks.get('total_count', 0)
            })
            return True
        
        evaluation['checks_failed'].append({
            'check': 'status_checks',
            'status': 'failed',
            'message': f'CI/CD checks state: {state}',
            'state': state,
            'total_checks': status_checks.get('total_count', 0)
        })
        return False
    
    def _check_pr_size(self, pr_analysis: Dict, evaluation: Dict) -> bool:
        """Check if PR size is within acceptable limits."""
        metrics = pr_analysis.get('metrics', {})
        
        max_files = self.conditions.get('max_files_changed', 50)
        max_lines = self.conditions.get('max_lines_changed', 1000)
        
        files_changed = metrics.get('files_changed', 0)
        lines_changed = metrics.get('lines_added', 0) + metrics.get('lines_deleted', 0)
        
        checks = [
            ('files_changed', files_changed, max_files, 'Files changed'),
            ('lines_changed', lines_changed, max_lines, 'Lines changed')
        ]
        
        all_passed = True
        for check_name, actual, maximum, label in checks:
            if actual <= maximum:
                evaluation['checks_passed'].append({
                    'check': check_name,
                    'status': 'passed',
                    'message': f'{label}: {actual} <= {maximum}',
                    'actual': actual,
                    'limit': maximum
                })
            else:
                evaluation['checks_failed'].append({
                    'check': check_name,
                    'status': 'failed',
                    'message': f'{label}: {actual} > {maximum}',
                    'actual': actual,
                    'limit': maximum
                })
                all_passed = False
        
        return all_passed
    
    def _check_breaking_changes(self, pr_analysis: Dict, evaluation: Dict) -> bool:
        """Check for breaking changes if configured."""
        check_breaking = self.conditions.get('check_breaking_changes', True)
        
        if not check_breaking:
            evaluation['checks_passed'].append({
                'check': 'breaking_changes',
                'status': 'passed',
                'message': 'Breaking changes check disabled'
            })
            return True
        
        # Look for breaking change issues from context agent
        issues = pr_analysis.get('issues', [])
        breaking_issues = [
            i for i in issues 
            if 'breaking' in i.get('description', '').lower() or
               'breaking' in i.get('title', '').lower()
        ]
        
        if not breaking_issues:
            evaluation['checks_passed'].append({
                'check': 'breaking_changes',
                'status': 'passed',
                'message': 'No breaking changes detected'
            })
            return True
        
        evaluation['checks_failed'].append({
            'check': 'breaking_changes',
            'status': 'failed',
            'message': f'Found {len(breaking_issues)} potential breaking change(s)',
            'breaking_issues_count': len(breaking_issues)
        })
        return False
    
    def get_merge_config(self) -> Dict:
        """
        Get merge configuration settings.
        
        Returns:
            Dictionary with merge method and post-merge actions
        """
        return {
            'merge_method': self.config.get('merge_method', 'squash'),
            'delete_branch': self.config.get('delete_branch', True),
            'post_merge_comment': self.config.get('post_merge_comment', True)
        }
