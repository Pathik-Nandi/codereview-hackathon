"""Multi-language code quality analysis agent."""
from typing import List, Dict, Any
import subprocess
import json
import re
from models.pr_event import PREvent
from models.analysis_result import Issue, IssueType, Severity
from agents.base_agent import BaseAgent


class MultiLanguageCodeQualityAgent(BaseAgent):
    """Agent that analyzes code quality metrics across multiple languages."""
    
    LANGUAGE_EXTENSIONS = {
        'python': ['.py'],
        'java': ['.java'],
        'scala': ['.scala'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'nodejs': ['.js', '.mjs']
    }
    
    def __init__(self, config: dict):
        """Initialize the multi-language code quality agent."""
        super().__init__("Multi-Language Code Quality Agent", config)
        self.languages_config = config.get('languages', {})
        self.complexity_threshold = config.get('complexity_threshold', 10)
        self.maintainability_threshold = config.get('maintainability_threshold', 20)
    
    def _analyze_impl(self, pr_event: PREvent) -> List[Issue]:
        """Run code quality analysis on PR files for all supported languages."""
        issues = []
        
        # Group files by language
        files_by_language = self._group_files_by_language(pr_event.files)
        
        # Analyze each language
        for language, files in files_by_language.items():
            if not files:
                continue
                
            lang_config = self.languages_config.get(language, {})
            # Enable pattern-based analysis by default
            if not lang_config.get('enabled', True):
                self.logger.info(f"Skipping {language} quality analysis - not enabled")
                continue
            
            self.logger.info(f"Quality analysis for {len(files)} {language} file(s)")
            
            # Always run pattern-based quality analysis first
            issues.extend(self._pattern_based_quality_analysis(files, language))
            
            # Run language-specific quality analysis (tool-based)
            if language == 'python':
                issues.extend(self._analyze_python_quality(files, lang_config))
            elif language == 'java':
                issues.extend(self._analyze_java_quality(files, lang_config))
            elif language == 'scala':
                issues.extend(self._analyze_scala_quality(files, lang_config))
            elif language in ['javascript', 'typescript', 'nodejs']:
                issues.extend(self._analyze_js_quality(files, lang_config, language))
        
        return issues
    
    def _group_files_by_language(self, files: List) -> Dict[str, List]:
        """Group files by their programming language."""
        grouped = {lang: [] for lang in self.LANGUAGE_EXTENSIONS.keys()}
        
        for file in files:
            if file.status == 'removed':
                continue
                
            filename = file.filename.lower()
            for language, extensions in self.LANGUAGE_EXTENSIONS.items():
                if any(filename.endswith(ext) for ext in extensions):
                    grouped[language].append(file)
                    break
        
        return grouped
    
    # ========== PATTERN-BASED QUALITY ANALYSIS ==========
    
    def _pattern_based_quality_analysis(self, files: List, language: str) -> List[Issue]:
        """Pattern-based code quality analysis for all languages.

        This dispatcher delegates checks to small helper methods to keep the
        cognitive complexity of this function low while preserving the
        original behaviour.
        """
        issues: List[Issue] = []

        for file in files:
            if not file.patch:
                continue
            issues.extend(self._analyze_patch_file(file, language))

        return issues

    def _analyze_patch_file(self, file, language: str) -> List[Issue]:
        """Analyze a single file patch and run a set of small checks.

        Each check is a thin wrapper that inspects a single added line and
        returns zero-or-more issues.
        """
        issues: List[Issue] = []
        patch_lines = file.patch.split('\n')
        line_number = 0

        # Keep some lightweight state for multi-line checks
        in_method = False
        method_start_line = 0
        current_method_lines = 0
        nesting_level = 0
        nesting_reported_at_line = {}

        for i, raw in enumerate(patch_lines):
            # Handle hunk headers which set the starting line number
            if raw.startswith('@@'):
                try:
                    line_number = int(raw.split('+')[1].split(',')[0])
                    nesting_level = 0
                except (IndexError, ValueError):
                    line_number = 0
                continue

            # We only inspect added lines (starts with '+')
            if not raw.startswith('+'):
                if raw.startswith('-'):
                    continue
                line_number += 1
                # Update nesting context for context lines in brace-based langs
                if language in ['java', 'javascript', 'typescript', 'scala']:
                    nesting_level = self._update_nesting_for_context_line(raw, language, nesting_level)
                continue

            # Delegate processing of the added line to a small helper that
            # returns updated state and any issues found for the line.
            state = {
                'in_method': in_method,
                'method_start_line': method_start_line,
                'current_method_lines': current_method_lines,
                'nesting_level': nesting_level,
                'nesting_reported_at_line': nesting_reported_at_line
            }
            updated_state, line_issues = self._process_added_line(raw, i, patch_lines, file, language, line_number, state)
            issues.extend(line_issues)
            # Update state for multi-line checks
            in_method = updated_state['in_method']
            method_start_line = updated_state['method_start_line']
            current_method_lines = updated_state['current_method_lines']
            nesting_level = updated_state['nesting_level']
            nesting_reported_at_line = updated_state['nesting_reported_at_line']
            line_number += 1

        return issues

    def _check_magic_numbers(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        if not code or code.startswith('//') or code.startswith('#') or code.startswith('*'):
            return issues

        numbers = re.findall(r'\b(\d{3,}|\d+\.\d+)\b', code)
        for num in numbers:
            if num not in ['100', '1000', '200', '404', '500', '0.0', '1.0', '2.0']:
                if '=' in code or 'return' in code:
                    issues.append(self._create_quality_issue(
                        'MAGIC_NUMBER',
                        f'Magic number detected: {num}',
                        file.filename,
                        line_number,
                        'Replace with named constant',
                        language,
                        Severity.LOW
                    ))
                    break
        return issues

    def _update_nesting_for_context_line(self, line: str, language: str, current_nesting: int) -> int:
        """Update nesting level for context lines (non-added/removed lines)."""
        if language in ['java', 'javascript', 'typescript', 'scala']:
            current_nesting += line.count('{') - line.count('}')
            return max(0, current_nesting)
        return current_nesting

    def _check_deep_nesting(self, code: str, original_code: str, file, line_number: int,
                           language: str, nesting_reported_at_line: dict, nesting_level: int) -> List[Issue]:
        issues: List[Issue] = []
        if language == 'python':
            indent_count = len(original_code) - len(original_code.lstrip())
            spaces_per_level = 4
            nesting = indent_count // spaces_per_level
            if nesting > 4 and nesting not in nesting_reported_at_line.get(file.filename, set()):
                issues.append(self._create_quality_issue(
                    'DEEP_NESTING',
                    f'Deep nesting detected (level {nesting})',
                    file.filename,
                    line_number,
                    'Extract nested logic into separate methods',
                    language,
                    Severity.MEDIUM
                ))
                nesting_reported_at_line.setdefault(file.filename, set()).add(nesting)

        elif language in ['java', 'javascript', 'typescript', 'scala']:
            nesting_level += code.count('{') - code.count('}')
            nesting_level = max(0, nesting_level)
            if nesting_level > 4 and line_number not in nesting_reported_at_line.get(file.filename, set()):
                issues.append(self._create_quality_issue(
                    'DEEP_NESTING',
                    f'Deep nesting detected (level {nesting_level})',
                    file.filename,
                    line_number,
                    'Extract nested logic into separate methods',
                    language,
                    Severity.MEDIUM
                ))
                nesting_reported_at_line.setdefault(file.filename, set()).add(line_number)

        return issues

    def _check_long_method(self, code: str, file, line_number: int, language: str,
                           in_method: bool, method_start_line: int, current_method_lines: int):
        """Lightweight long-method detection that returns updated method state.

        Returns a tuple (in_method, method_start_line, current_method_lines, issue_or_none)
        or None on failure.
        """
    # Delegate to language-specific helpers to reduce cognitive complexity
        if language == 'python':
            return self._long_method_python(code, file, line_number, in_method, method_start_line, current_method_lines)
        if language in ['java', 'scala']:
            return self._long_method_brace(code, file, line_number, in_method, method_start_line, current_method_lines, language)
        if language in ['javascript', 'typescript']:
            return self._long_method_js(code, file, line_number, in_method, method_start_line, current_method_lines)
        return (in_method, method_start_line, current_method_lines, None)

    def _long_method_python(self, code, file, line_number, in_method, method_start_line, current_method_lines):
        possible_issue = None
        if code.startswith('def '):
            in_method = True
            method_start_line = line_number
            current_method_lines = 0
        elif in_method:
            current_method_lines += 1
            if code and not code.startswith(' ') and not code.startswith('\t'):
                if current_method_lines > 50:
                    possible_issue = self._create_quality_issue(
                        'LONG_METHOD',
                        f'Method too long ({current_method_lines} lines)',
                        file.filename,
                        method_start_line,
                        'Break down into smaller methods (max 50 lines)',
                        'python',
                        Severity.MEDIUM
                    )
                in_method = False
        return (in_method, method_start_line, current_method_lines, possible_issue)

    def _long_method_brace(self, code, file, line_number, in_method, method_start_line, current_method_lines, language):
        possible_issue = None
        if ('public ' in code or 'private ' in code or 'protected ' in code) and '(' in code and '{' in code:
            in_method = True
            method_start_line = line_number
            current_method_lines = 0
        elif in_method:
            current_method_lines += 1
            if '}' in code:
                if current_method_lines > 50:
                    possible_issue = self._create_quality_issue(
                        'LONG_METHOD',
                        f'Method too long ({current_method_lines} lines)',
                        file.filename,
                        method_start_line,
                        'Break down into smaller methods (max 50 lines)',
                        language,
                        Severity.MEDIUM
                    )
                in_method = False
        return (in_method, method_start_line, current_method_lines, possible_issue)

    def _long_method_js(self, code, file, line_number, in_method, method_start_line, current_method_lines):
        possible_issue = None
        if 'function ' in code or '=>' in code or (': (' in code):
            in_method = True
            method_start_line = line_number
            current_method_lines = 0
        elif in_method:
            current_method_lines += 1
            if '}' in code:
                if current_method_lines > 50:
                    possible_issue = self._create_quality_issue(
                        'LONG_METHOD',
                        f'Function too long ({current_method_lines} lines)',
                        file.filename,
                        method_start_line,
                        'Break down into smaller functions (max 50 lines)',
                        'javascript',
                        Severity.MEDIUM
                    )
                in_method = False
        return (in_method, method_start_line, current_method_lines, possible_issue)

    def _process_added_line(self, raw: str, i: int, patch_lines: List[str], file, language: str, line_number: int, state: dict):
        """Process a single added line and return (updated_state, issues).

        updated_state is a dict with the same keys as the incoming state.
        """
        issues: List[Issue] = []
        code = raw[1:].strip()
        original_code = raw[1:]

        # Run checks
        issues.extend(self._check_magic_numbers(code, file, line_number, language))
        issues.extend(self._check_deep_nesting(code, original_code, file, line_number,
                                               language, state.get('nesting_reported_at_line', {}), state.get('nesting_level', 0)))
        in_method, method_start_line, current_method_lines, possible_issue = self._check_long_method(
            code, file, line_number, language, state.get('in_method', False), state.get('method_start_line', 0), state.get('current_method_lines', 0)
        )
        if possible_issue:
            issues.append(possible_issue)

        issues.extend(self._check_complex_boolean(code, file, line_number, language))
        issues.extend(self._check_long_parameter_list(code, file, line_number, language))
        issues.extend(self._check_duplicate_strings(code, patch_lines, i, file, line_number, language))
        issues.extend(self._check_empty_catch(code, patch_lines, i, file, line_number, language))

        updated_state = {
            'in_method': in_method,
            'method_start_line': method_start_line,
            'current_method_lines': current_method_lines,
            'nesting_level': state.get('nesting_level', 0) + code.count('{') - code.count('}'),
            'nesting_reported_at_line': state.get('nesting_reported_at_line', {})
        }

        return updated_state, issues

    def _check_complex_boolean(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        if language in ['python', 'java', 'javascript', 'typescript', 'scala']:
            and_count = code.count(' and ') + code.count(' && ')
            or_count = code.count(' or ') + code.count(' || ')
            if and_count + or_count > 3:
                issues.append(self._create_quality_issue(
                    'COMPLEX_BOOLEAN',
                    'Complex boolean expression',
                    file.filename,
                    line_number,
                    'Simplify or extract into named boolean variables',
                    language,
                    Severity.LOW
                ))
        return issues

    def _check_long_parameter_list(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        if '(' in code and ')' in code:
            params_section = code[code.find('(')+1:code.find(')')]
            param_count = len([p for p in params_section.split(',') if p.strip()])
            if param_count > 5:
                issues.append(self._create_quality_issue(
                    'LONG_PARAMETER_LIST',
                    f'Too many parameters ({param_count})',
                    file.filename,
                    line_number,
                    'Consider using a parameter object or builder pattern',
                    language,
                    Severity.LOW
                ))
        return issues

    def _check_duplicate_strings(self, code: str, patch_lines: List[str], i: int, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        string_literals = re.findall(r'["\']([^"\']{10,})["\']', code)
        if string_literals:
            for literal in string_literals:
                count = 0
                for j in range(max(0, i-10), min(len(patch_lines), i+10)):
                    if literal in patch_lines[j]:
                        count += 1
                if count > 2:
                    issues.append(self._create_quality_issue(
                        'DUPLICATE_STRING',
                        f'Duplicate string literal: "{literal[:30]}..."',
                        file.filename,
                        line_number,
                        'Extract to a constant',
                        language,
                        Severity.LOW
                    ))
                    break
        return issues

    def _check_empty_catch(self, code: str, patch_lines: List[str], i: int, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        if language == 'python':
            if code.strip() == 'pass' and i > 0 and 'except' in patch_lines[i-1]:
                issues.append(self._create_quality_issue(
                    'EMPTY_CATCH',
                    'Empty exception handler',
                    file.filename,
                    line_number,
                    'Add logging or proper error handling',
                    language,
                    Severity.MEDIUM
                ))
        elif language in ['java', 'javascript', 'typescript', 'scala']:
            if code.strip() == '{}' and i > 0 and 'catch' in patch_lines[i-1]:
                issues.append(self._create_quality_issue(
                    'EMPTY_CATCH',
                    'Empty catch block',
                    file.filename,
                    line_number,
                    'Add logging or proper error handling',
                    language,
                    Severity.MEDIUM
                ))
        return issues
    
    def _create_quality_issue(self, code: str, message: str, file: str, line: int, 
                             suggestion: str, language: str, severity: Severity) -> Issue:
        """Helper to create quality issue."""
        return Issue(
            type=IssueType.QUALITY,
            severity=severity,
            message=message,
            file=file,
            line=line,
            code=code,
            suggestion=suggestion,
            metadata={'tool': 'pattern-analysis', 'language': language}
        )
    
    # ========== PYTHON QUALITY ==========
    
    def _analyze_python_quality(self, files: List, config: dict) -> List[Issue]:
        """Analyze Python code quality."""
        issues = []
        tools = config.get('tools', ['radon'])
        
        if 'radon' in tools:
            issues.extend(self._run_radon_complexity(files))
            issues.extend(self._run_radon_maintainability(files))
        
        return issues
    
    def _run_radon_complexity(self, files: List) -> List[Issue]:
        """Run Radon for cyclomatic complexity."""
        issues = []
        
        for file in files:
            try:
                result = subprocess.run(
                    ['radon', 'cc', '-j', file.filename],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    data = json.loads(result.stdout)
                    issues.extend(self._parse_radon_complexity_data(data))
                                
            except FileNotFoundError:
                self.logger.warning("Radon not installed. Install: pip install radon")
            except Exception as e:
                self.logger.error(f"Radon complexity error: {e}")
        
        return issues
    
    def _run_radon_maintainability(self, files: List) -> List[Issue]:
        """Run Radon for maintainability index."""
        issues = []
        
        for file in files:
            try:
                result = subprocess.run(
                    ['radon', 'mi', '-j', file.filename],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    data = json.loads(result.stdout)
                    
                    for filename, metrics in data.items():
                        mi_score = metrics.get('mi', 100)
                        if mi_score < self.maintainability_threshold:
                            issues.append(Issue(
                                type=IssueType.QUALITY,
                                severity=Severity.MEDIUM,
                                message=f"Low maintainability index ({mi_score:.2f})",
                                file=filename,
                                suggestion="Improve code structure and documentation",
                                metadata={'tool': 'radon', 'language': 'python', 'maintainability_index': mi_score}
                            ))
                            
            except FileNotFoundError:
                self.logger.warning("Radon not installed. Install: pip install radon")
            except Exception as e:
                self.logger.error(f"Radon maintainability error: {e}")
        
        return issues

    def _parse_radon_complexity_data(self, data: Dict) -> List[Issue]:
        """Parse radon cc JSON and return Issue list."""
        issues: List[Issue] = []
        for filename, functions in data.items():
            for func in functions:
                complexity = func.get('complexity', 0)
                if complexity > self.complexity_threshold:
                    issues.append(Issue(
                        type=IssueType.QUALITY,
                        severity=self._map_complexity_severity(complexity),
                        message=f"High complexity ({complexity}) in {func.get('name', '')}",
                        file=filename,
                        line=func.get('lineno'),
                        suggestion="Consider refactoring to reduce complexity",
                        metadata={'tool': 'radon', 'language': 'python', 'complexity': complexity}
                    ))
        return issues
    
    # ========== JAVA QUALITY ==========
    
    def _analyze_java_quality(self, files: List, config: dict) -> List[Issue]:
        """Analyze Java code quality."""
        issues = []
        tools = config.get('tools', ['pmd'])
        
        if 'pmd' in tools:
            issues.extend(self._run_pmd_quality(files))
        
        return issues
    
    def _run_pmd_quality(self, files: List) -> List[Issue]:
        """Run PMD for Java quality analysis."""
        issues = []
        file_paths = [f.filename for f in files]
        
        try:
            # PMD with design and codesize rulesets
            result = subprocess.run(
                ['pmd', '-d', ','.join(file_paths), '-f', 'json', 
                 '-R', 'category/java/design.xml,category/java/codesize.xml'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for file_result in data.get('files', []):
                    filename = file_result.get('filename', '')
                    
                    for violation in file_result.get('violations', []):
                        issues.append(Issue(
                            type=IssueType.QUALITY,
                            severity=self._map_pmd_priority_to_severity(violation.get('priority')),
                            message=violation.get('description', ''),
                            file=filename,
                            line=violation.get('beginline'),
                            code=violation.get('rule'),
                            metadata={'tool': 'pmd', 'language': 'java'}
                        ))
                        
        except FileNotFoundError:
            self.logger.warning("PMD not installed. Install: https://pmd.github.io/")
        except Exception as e:
            self.logger.error(f"PMD quality error: {e}")
        
        return issues
    
    # ========== SCALA QUALITY ==========
    
    def _analyze_scala_quality(self, files: List, config: dict) -> List[Issue]:
        """Analyze Scala code quality."""
        issues = []
        tools = config.get('tools', ['scalastyle'])
        
        if 'scalastyle' in tools:
            issues.extend(self._run_scalastyle_quality(files))
        
        return issues
    
    def _run_scalastyle_quality(self, _files: List) -> List[Issue]:
        """Run Scalastyle for Scala quality analysis.
        
        Args:
            _files: List of files (unused, reserved for future implementation)
        """
        issues = []
        
        try:
            # Scalastyle focuses on style and quality
            self.logger.info("Scalastyle quality analysis")
            # Implementation similar to static analysis agent
            
        except Exception as e:
            self.logger.error(f"Scalastyle quality error: {e}")
        
        return issues
    
    # ========== JAVASCRIPT/TYPESCRIPT QUALITY ==========
    
    def _analyze_js_quality(self, files: List, config: dict, language: str) -> List[Issue]:
        """Analyze JavaScript/TypeScript code quality."""
        issues = []
        tools = config.get('tools', ['eslint'])
        
        if 'eslint' in tools:
            issues.extend(self._run_eslint_quality(files, language))
        
        return issues
    
    def _run_eslint_quality(self, files: List, language: str) -> List[Issue]:
        """Run ESLint with complexity rules."""
        issues = []
        file_paths = [f.filename for f in files]
        
        try:
            # ESLint with complexity plugin
            result = subprocess.run(
                ['eslint', '-f', 'json', '--plugin', 'complexity'] + file_paths,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                issues.extend(self._parse_eslint_output(data, language))
                            
        except FileNotFoundError:
            self.logger.warning("ESLint not installed. Install: npm install -g eslint")
        except Exception as e:
            self.logger.error(f"ESLint quality error: {e}")
        
        return issues

    def _parse_eslint_output(self, data: List[Dict[str, Any]], language: str) -> List[Issue]:
        """Parse ESLint JSON output and return Issue list (only complexity/quality rules)."""
        issues: List[Issue] = []
        for file_result in data:
            filename = file_result.get('filePath', '')
            for message in file_result.get('messages', []):
                rule_id = message.get('ruleId', '')
                if 'complexity' in (rule_id or '') or 'max-' in (rule_id or ''):
                    issues.append(Issue(
                        type=IssueType.QUALITY,
                        severity=Severity.MEDIUM if message.get('severity') == 2 else Severity.LOW,
                        message=message.get('message', ''),
                        file=filename,
                        line=message.get('line'),
                        column=message.get('column'),
                        code=rule_id,
                        metadata={'tool': 'eslint', 'language': language}
                    ))
        return issues
    
    # ========== HELPER METHODS ==========
    
    def _map_complexity_severity(self, complexity: int) -> Severity:
        """Map cyclomatic complexity to severity."""
        if complexity > 20:
            return Severity.HIGH
        elif complexity > 15:
            return Severity.MEDIUM
        return Severity.LOW
    
    def _map_pmd_priority_to_severity(self, priority: int) -> Severity:
        """Map PMD priority to severity."""
        priority_map = {
            1: Severity.CRITICAL,
            2: Severity.HIGH,
            3: Severity.MEDIUM,
            4: Severity.LOW,
            5: Severity.INFO
        }
        return priority_map.get(priority, Severity.MEDIUM)
