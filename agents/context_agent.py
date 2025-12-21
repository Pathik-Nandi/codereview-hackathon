"""Context agent for understanding code changes in context."""
from typing import List
from models.pr_event import PREvent
from models.analysis_result import Issue, IssueType, Severity
from agents.base_agent import BaseAgent


class ContextAgent(BaseAgent):
    """Agent that analyzes code changes in context."""
    
    def __init__(self, config: dict):
        """Initialize the context agent."""
        super().__init__("Context Agent", config)
        self.analyze_dependencies = config.get('analyze_dependencies', True)
        self.analyze_test_coverage = config.get('analyze_test_coverage', True)
        self.check_breaking_changes = config.get('check_breaking_changes', True)
    
    def _analyze_impl(self, pr_event: PREvent) -> List[Issue]:
        """Analyze code changes in context."""
        issues = []
        
        # Check for breaking changes
        if self.check_breaking_changes:
            issues.extend(self._detect_breaking_changes(pr_event))
        
        # Check test coverage
        if self.analyze_test_coverage:
            issues.extend(self._check_test_coverage(pr_event))
        
        # Analyze dependencies
        if self.analyze_dependencies:
            issues.extend(self._analyze_dependency_changes(pr_event))
        
        return issues
    
    def _detect_breaking_changes(self, pr_event: PREvent) -> List[Issue]:
        """Detect potential breaking changes."""
        issues = []
        
        code_extensions = ['.py', '.java', '.scala', '.js', '.jsx', '.ts', '.tsx', '.go', '.rb', '.php']
        
        for file in pr_event.files:
            if not any(file.filename.endswith(ext) for ext in code_extensions):
                continue
            
            # Check if API/interface files are modified with deletions
            is_api_file = (
                'api' in file.filename.lower() or 
                '__init__' in file.filename or
                'interface' in file.filename.lower() or
                'controller' in file.filename.lower() or
                'service' in file.filename.lower()
            )
            
            if is_api_file and file.status == 'modified' and file.deletions > 0:
                issues.append(Issue(
                    type=IssueType.CONTEXT,
                    severity=Severity.MEDIUM,
                    message="Potential breaking change in public API/interface",
                    file=file.filename,
                    suggestion="Ensure backward compatibility or update version accordingly",
                    metadata={'deletions': file.deletions}
                ))
        
        return issues
    
    def _check_test_coverage(self, pr_event: PREvent) -> List[Issue]:
        """Check if code changes include tests."""
        issues = []
        
        # Define code file extensions
        code_extensions = ['.py', '.java', '.scala', '.js', '.jsx', '.ts', '.tsx', '.go', '.rb', '.php', '.cpp', '.c', '.cs']
        
        code_files = [
            f for f in pr_event.files 
            if any(f.filename.endswith(ext) for ext in code_extensions)
            and 'test' not in f.filename.lower()
            and '/test/' not in f.filename.lower()
            and f.status in ['added', 'modified']
        ]
        
        test_files = [
            f for f in pr_event.files 
            if any(f.filename.endswith(ext) for ext in code_extensions)
            and ('test' in f.filename.lower() or '/test/' in f.filename.lower())
        ]
        
        # If code files are added/modified but no test files
        if code_files and not test_files:
            issues.append(Issue(
                type=IssueType.CONTEXT,
                severity=Severity.MEDIUM,
                message="Code changes without corresponding test updates",
                file="N/A",
                suggestion="Add or update tests for the new/modified code",
                metadata={
                    'code_files_changed': len(code_files),
                    'test_files_changed': len(test_files)
                }
            ))
        
        return issues
    
    def _analyze_dependency_changes(self, pr_event: PREvent) -> List[Issue]:
        """Analyze changes to dependency files."""
        issues = []
        
        dependency_files = [
            f for f in pr_event.files 
            if f.filename in ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']
        ]
        
        for dep_file in dependency_files:
            if dep_file.status == 'modified':
                # Warn about dependency changes
                if dep_file.additions > dep_file.deletions:
                    issues.append(Issue(
                        type=IssueType.CONTEXT,
                        severity=Severity.LOW,
                        message=f"New dependencies added to {dep_file.filename}",
                        file=dep_file.filename,
                        suggestion="Ensure new dependencies are necessary and well-maintained",
                        metadata={
                            'additions': dep_file.additions,
                            'deletions': dep_file.deletions
                        }
                    ))
        
        return issues
    
    def _collect_metrics(self, pr_event: PREvent, issues: List[Issue]) -> dict:
        """Collect context-specific metrics."""
        metrics = super()._collect_metrics(pr_event, issues)
        
        test_files = sum(1 for f in pr_event.files if 'test' in f.filename.lower())
        code_files = sum(1 for f in pr_event.files if f.filename.endswith('.py'))
        
        metrics.update({
            'test_files_changed': test_files,
            'code_files_changed': code_files,
            'test_ratio': round(test_files / code_files, 2) if code_files > 0 else 0
        })
        
        return metrics
