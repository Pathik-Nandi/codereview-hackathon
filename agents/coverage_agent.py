"""Coverage and quality metrics agent (SonarQube-like analysis without SonarQube)."""
from typing import List, Dict, Optional
import re
from models.pr_event import PREvent
from models.analysis_result import Issue, IssueType, Severity
from agents.base_agent import BaseAgent


class CoverageAgent(BaseAgent):
    """Agent that analyzes code coverage and generates quality metrics."""
    # Path and extension constants
    TEST_PATH_PATTERN = '/test/'
    JAVA_EXTENSION = '.java'
    
    def __init__(self, config: dict):
        """Initialize the coverage agent."""
        super().__init__("Coverage & Metrics Agent", config)
        self.min_coverage = config.get('min_coverage_threshold', 80.0)
        self.check_coverage = config.get('check_coverage', True)
        self.analyze_complexity = config.get('analyze_complexity', True)
    
    def _analyze_impl(self, pr_event: PREvent) -> List[Issue]:
        """Analyze code coverage and metrics for PR."""
        issues = []
        
        # Check if we can analyze coverage
        if self.check_coverage:
            issues.extend(self._analyze_coverage_from_patch(pr_event))
        
        # Analyze code complexity
        if self.analyze_complexity:
            issues.extend(self._estimate_complexity(pr_event))
        
        return issues
    
    def _analyze_coverage_from_patch(self, pr_event: PREvent) -> List[Issue]:
        """Estimate coverage based on patch analysis (pattern-based)."""
        issues = []
        # 1) Validate added/modified test files contain tests
        for file in pr_event.files:
            if not file.patch:
                continue

            if not self._is_test_file(file.filename):
                continue

            issue = self._check_test_file_has_tests(file)
            if issue:
                issues.append(issue)

        # 2) Collect code and test file groups
        code_files = self._get_code_files(pr_event)
        test_files = self._get_test_files(pr_event)

        # 3) Evaluate overall coverage estimate and report if below threshold
        coverage_issue = self._evaluate_coverage(code_files, test_files)
        if coverage_issue:
            issues.append(coverage_issue)

        return issues

    def _is_test_file(self, filename: str) -> bool:
        """Return True if the filename appears to be a test file."""
        lname = filename.lower()
        return 'test' in lname or self.TEST_PATH_PATTERN in lname

    def _check_test_file_has_tests(self, file) -> Optional[Issue]:
        """Return an Issue if a newly added test file has no test methods, else None."""
        # Only analyze added/modified test files
        if file.status not in ('added', 'modified'):
            return None

        test_count = self._count_tests_in_patch(file.patch, file.filename)
        if test_count == 0 and file.status == 'added':
            return Issue(
                type=IssueType.CONTEXT,
                severity=Severity.MEDIUM,
                message="Test file added but no test methods found",
                file=file.filename,
                suggestion="Add actual test methods (@Test annotations for Java, def test_* for Python)",
                metadata={'test_count': 0}
            )

        return None

    def _get_code_files(self, pr_event: PREvent) -> List:
        """Return list of code files (non-test) that were added/modified and are of recognized extensions."""
        return [
            f for f in pr_event.files
            if f.status in ['added', 'modified']
            and not self._is_test_file(f.filename)
            and (f.filename.endswith(self.JAVA_EXTENSION) or f.filename.endswith('.py') or
                 f.filename.endswith('.js') or f.filename.endswith('.ts'))
        ]

    def _get_test_files(self, pr_event: PREvent) -> List:
        """Return list of files that appear to be tests."""
        return [f for f in pr_event.files if self._is_test_file(f.filename)]

    def _evaluate_coverage(self, code_files: List, test_files: List) -> Optional[Issue]:
        """Estimate coverage from file counts and return an Issue if below threshold."""
        if not code_files:
            return None

        coverage_ratio = len(test_files) / len(code_files) if code_files else 0
        estimated_coverage = min(coverage_ratio * 100, 100)

        if estimated_coverage < self.min_coverage:
            return Issue(
                type=IssueType.CONTEXT,
                severity=Severity.HIGH if estimated_coverage < 50 else Severity.MEDIUM,
                message=f"Low test coverage detected: ~{estimated_coverage:.0f}% (estimated)",
                file="N/A",
                suggestion=f"Add more test files to reach {self.min_coverage}% coverage threshold",
                metadata={
                    'estimated_coverage': round(estimated_coverage, 1),
                    'code_files': len(code_files),
                    'test_files': len(test_files),
                    'threshold': self.min_coverage
                }
            )

        return None
    
    def _count_tests_in_patch(self, patch: str, filename: str) -> int:
        """Count test methods in patch."""
        test_count = 0
        
        if filename.endswith(self.JAVA_EXTENSION):
            # Count @Test annotations
            test_count = patch.count('@Test')
        elif filename.endswith('.py'):
            # Count test_ methods
            test_count = len(re.findall(r'def test_\w+', patch))
        elif filename.endswith(('.js', '.ts', '.jsx', '.tsx')):
            # Count test/it blocks
            test_count = len(re.findall(r'(test|it)\s*\(', patch))
        
        return test_count
    
    def _estimate_complexity(self, pr_event: PREvent) -> List[Issue]:
        """Estimate code complexity from patch (McCabe complexity approximation)."""
        issues = []
        
        for file in pr_event.files:
            if not file.patch:
                continue
            
            # Skip test files
            if 'test' in file.filename.lower():
                continue
            
            # Count complexity indicators in added lines
            patch_lines = [line for line in file.patch.split('\n') if line.startswith('+')]
            
            complexity_score = 0
            for line in patch_lines:
                code = line[1:].strip()
                
                # Count decision points (McCabe complexity indicators)
                complexity_score += code.count('if ')
                complexity_score += code.count('else if')
                complexity_score += code.count('elif ')
                complexity_score += code.count('for ')
                complexity_score += code.count('while ')
                complexity_score += code.count('case ')
                complexity_score += code.count('catch ')
                complexity_score += code.count('&&')
                complexity_score += code.count('||')
                complexity_score += code.count(' and ')
                complexity_score += code.count(' or ')
                complexity_score += code.count('?')  # Ternary operator
            
            # If complexity is high, report it
            if complexity_score > 15:
                issues.append(Issue(
                    type=IssueType.QUALITY,
                    severity=Severity.MEDIUM if complexity_score < 25 else Severity.HIGH,
                    message=f"High cyclomatic complexity detected: ~{complexity_score} decision points",
                    file=file.filename,
                    suggestion="Consider refactoring to reduce complexity (target: <15)",
                    metadata={
                        'estimated_complexity': complexity_score,
                        'lines_added': len(patch_lines)
                    }
                ))
        
        return issues
    
    def _collect_metrics(self, pr_event: PREvent, issues: List[Issue]) -> dict:
        """Collect coverage and quality metrics (SonarQube-like)."""
        metrics = super()._collect_metrics(pr_event, issues)
        
        # Count test files and code files
        test_files = [f for f in pr_event.files if 'test' in f.filename.lower() or self.TEST_PATH_PATTERN in f.filename.lower()]
        code_files = [
            f for f in pr_event.files 
            if f.status in ['added', 'modified']
            and 'test' not in f.filename.lower()
            and (f.filename.endswith(self.JAVA_EXTENSION) or f.filename.endswith('.py') or 
                 f.filename.endswith('.js') or f.filename.endswith('.ts'))
        ]
        
        # Count total test methods
        total_tests = 0
        for test_file in test_files:
            if test_file.patch:
                total_tests += self._count_tests_in_patch(test_file.patch, test_file.filename)
        
        # Estimate coverage
        coverage_ratio = len(test_files) / len(code_files) if code_files else 1.0
        estimated_coverage = min(coverage_ratio * 100, 100)
        
        # Calculate code to test ratio
        code_lines = sum(f.additions for f in code_files)
        test_lines = sum(f.additions for f in test_files)
        
        metrics.update({
            'estimated_coverage': round(estimated_coverage, 1),
            'code_files_changed': len(code_files),
            'test_files_changed': len(test_files),
            'total_test_methods': total_tests,
            'code_lines_added': code_lines,
            'test_lines_added': test_lines,
            'test_to_code_ratio': round(test_lines / code_lines, 2) if code_lines > 0 else 0,
            'coverage_status': 'PASS' if estimated_coverage >= self.min_coverage else 'FAIL'
        })
        
        return metrics
