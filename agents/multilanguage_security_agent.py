"""Multi-language security analysis agent."""
from typing import List, Dict, Optional, Any
import subprocess
import json
import re
from models.pr_event import PREvent
from models.analysis_result import Issue, IssueType, Severity
from agents.base_agent import BaseAgent


class MultiLanguageSecurityAgent(BaseAgent):
    """Agent that performs security analysis across multiple languages."""
    
    # Security message constants
    MSG_PATH_TRAVERSAL = 'Potential path traversal vulnerability'
    
    LANGUAGE_EXTENSIONS = {
        'python': ['.py'],
        'java': ['.java'],
        'scala': ['.scala'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'nodejs': ['.js', '.mjs']
    }
    
    def __init__(self, config: dict):
        """Initialize the multi-language security agent."""
        super().__init__("Multi-Language Security Agent", config)
        self.languages_config = config.get('languages', {})
        self.fail_on_high = config.get('fail_on_high_severity', True)
    
    def _analyze_impl(self, pr_event: PREvent) -> List[Issue]:
        """Run security analysis on PR files for all supported languages."""
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
                self.logger.info(f"Skipping {language} security analysis - not enabled")
                continue
            
            self.logger.info(f"Security analysis for {len(files)} {language} file(s)")
            
            # Always run pattern-based security analysis first
            issues.extend(self._pattern_based_security_analysis(files, language))
            
            # Run language-specific security analysis (tool-based)
            if language == 'python':
                issues.extend(self._analyze_python_security(files, lang_config))
            elif language == 'java':
                issues.extend(self._analyze_java_security(files, lang_config))
            elif language == 'scala':
                issues.extend(self._analyze_scala_security(files, lang_config))
            elif language in ['javascript', 'typescript', 'nodejs']:
                issues.extend(self._analyze_js_security(files, lang_config, language))
        
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
    
    # ========== PATTERN-BASED SECURITY ANALYSIS ==========
    
    def _pattern_based_security_analysis(self, files: List, language: str) -> List[Issue]:
        """Pattern-based security analysis for all languages.

        Dispatcher that delegates checks to focused helper functions to keep
        cognitive complexity low while preserving the original detection
        behaviour.
        """
        issues: List[Issue] = []

        for file in files:
            if not file.patch:
                continue
            issues.extend(self._analyze_security_patch_file(file, language))

        return issues

    def _analyze_security_patch_file(self, file, language: str) -> List[Issue]:
        """Analyze a single file patch for security patterns using small checks."""
        issues: List[Issue] = []
        patch_lines = file.patch.split('\n')
        line_number = 0

        for i, line in enumerate(patch_lines):
            if line.startswith('@@'):
                try:
                    line_number = int(line.split('+')[1].split(',')[0])
                except (IndexError, ValueError):
                    line_number = 0
                continue

            if not line.startswith('+'):
                if line.startswith('-'):
                    continue
                line_number += 1
                continue

            code = line[1:].strip()

            # Collect issues from small focused checks
            issues.extend(self._check_command_injection(code, file, line_number, language))
            issues.extend(self._check_path_traversal(code, file, line_number, language))
            issues.extend(self._check_weak_crypto(code, file, line_number, language))
            issues.extend(self._check_xxe(code, patch_lines, i, file, line_number, language))
            issues.extend(self._check_insecure_deserialization(code, file, line_number, language))
            issues.extend(self._check_ldap_injection(code, file, line_number, language))

            line_number += 1

        return issues

    def _check_command_injection(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        # Dispatch to language-specific checkers to lower cognitive complexity
        if language == 'python':
            return self._check_command_injection_python(code, file, line_number)
        if language == 'java':
            return self._check_command_injection_java(code, file, line_number)
        if language in ['javascript', 'typescript', 'nodejs']:
            return self._check_command_injection_js(code, file, line_number)
        return []

    def _check_command_injection_python(self, code: str, file, line_number: int) -> List[Issue]:
        issues: List[Issue] = []
        if 'os.system(' in code or 'subprocess.call(' in code or 'subprocess.Popen(' in code:
            if 'shell=False' not in code:
                issues.append(self._create_security_issue(
                    'COMMAND_INJECTION',
                    'Potential command injection vulnerability',
                    file.filename,
                    line_number,
                    'Use subprocess with shell=False and pass arguments as list',
                    'python'
                ))
        return issues

    def _check_command_injection_java(self, code: str, file, line_number: int) -> List[Issue]:
        issues: List[Issue] = []
        if 'Runtime.getRuntime().exec(' in code or 'ProcessBuilder(' in code:
            issues.append(self._create_security_issue(
                'COMMAND_INJECTION',
                'Potential command injection vulnerability',
                file.filename,
                line_number,
                'Validate and sanitize all user inputs before executing commands',
                'java'
            ))
        return issues

    def _check_command_injection_js(self, code: str, file, line_number: int) -> List[Issue]:
        issues: List[Issue] = []
        if 'exec(' in code or 'execSync(' in code or 'spawn(' in code:
            if 'shell:' in code and 'true' in code:
                issues.append(self._create_security_issue(
                    'COMMAND_INJECTION',
                    'Potential command injection with shell enabled',
                    file.filename,
                    line_number,
                    'Avoid using shell: true, sanitize inputs',
                    'javascript'
                ))
        return issues

    def _check_path_traversal(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        # Dispatch to language-specific handlers
        if language == 'python':
            return self._check_path_traversal_python(code, file, line_number)
        if language == 'java':
            return self._check_path_traversal_java(code, file, line_number)
        if language in ['javascript', 'typescript', 'nodejs']:
            return self._check_path_traversal_js(code, file, line_number)
        return []

    def _check_path_traversal_python(self, code: str, file, line_number: int) -> List[Issue]:
        issues: List[Issue] = []
        if ('open(' in code or 'file(' in code) and ('..' in code or 'request' in code.lower()):
            issues.append(self._create_security_issue(
                'PATH_TRAVERSAL',
                self.MSG_PATH_TRAVERSAL,
                file.filename,
                line_number,
                'Validate file paths, use os.path.abspath() and check within allowed directory',
                'python'
            ))
        return issues

    def _check_path_traversal_java(self, code: str, file, line_number: int) -> List[Issue]:
        issues: List[Issue] = []
        if ('new File(' in code or 'Paths.get(' in code or 'FileInputStream(' in code) and '..' in code:
            issues.append(self._create_security_issue(
                'PATH_TRAVERSAL',
                self.MSG_PATH_TRAVERSAL,
                file.filename,
                line_number,
                'Validate file paths, use Path.normalize() and verify within allowed directory',
                'java'
            ))
        return issues

    def _check_path_traversal_js(self, code: str, file, line_number: int) -> List[Issue]:
        issues: List[Issue] = []
        if ('fs.readFile' in code or 'fs.writeFile' in code or 'require(' in code) and ('..' in code or 'req.' in code):
            issues.append(self._create_security_issue(
                'PATH_TRAVERSAL',
                self.MSG_PATH_TRAVERSAL,
                file.filename,
                line_number,
                'Validate file paths, use path.resolve() and verify within allowed directory',
                'javascript'
            ))
        return issues

    def _check_weak_crypto(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        weak_crypto_patterns = {
            'python': ['md5(', 'sha1(', 'MODE_ECB', 'DES.new('],
            'java': ['MessageDigest.getInstance("MD5")', 'MessageDigest.getInstance("SHA-1")', 
                     'getInstance("DES")', 'ECB'],
            'javascript': ['crypto.createHash("md5")', 'crypto.createHash("sha1")', 'DES'],
            'typescript': ['crypto.createHash("md5")', 'crypto.createHash("sha1")', 'DES']
        }

        if language in weak_crypto_patterns:
            for pattern in weak_crypto_patterns[language]:
                if pattern in code:
                    issues.append(self._create_security_issue(
                        'WEAK_CRYPTO',
                        f'Weak cryptographic algorithm detected: {pattern}',
                        file.filename,
                        line_number,
                        'Use strong algorithms: SHA-256, SHA-384, SHA-512, AES-GCM',
                        language,
                        severity=Severity.HIGH
                    ))
                    break

        return issues

    def _check_xxe(self, code: str, patch_lines: List[str], i: int, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        xxe_patterns = {
            'python': ['etree.parse(', 'xml.dom.minidom.parse(', 'xml.sax.parse('],
            'java': ['DocumentBuilderFactory.newInstance()', 'SAXParserFactory.newInstance()', 
                     'XMLInputFactory.newInstance('],
            'javascript': ['xml2js.parseString', 'DOMParser().parseFromString'],
            'typescript': ['xml2js.parseString', 'DOMParser().parseFromString']
        }

        if language in xxe_patterns:
            for pattern in xxe_patterns[language]:
                issue = self._xxe_pattern_check(pattern, code, patch_lines, i, file, line_number, language)
                if issue:
                    issues.append(issue)
                    break

        return issues

    def _xxe_pattern_check(self, pattern: str, code: str, patch_lines: List[str], i: int, file, line_number: int, language: str) -> Optional[Issue]:
        """Check a single XXE pattern and return an Issue or None."""
        if pattern not in code:
            return None

        protection_found = False
        for j in range(max(0, i-5), min(len(patch_lines), i+5)):
            if 'setFeature' in patch_lines[j] or 'resolve_entities=False' in patch_lines[j]:
                protection_found = True
                break

        if not protection_found:
            return self._create_security_issue(
                'XXE_VULNERABILITY',
                'Potential XML External Entity (XXE) vulnerability',
                file.filename,
                line_number,
                'Disable external entity processing in XML parser configuration',
                language,
                severity=Severity.HIGH
            )
        return None

    def _check_insecure_deserialization(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        if language == 'python':
            if 'pickle.loads(' in code or 'yaml.load(' in code:
                if 'Loader=' not in code:
                    issues.append(self._create_security_issue(
                        'INSECURE_DESERIALIZATION',
                        'Insecure deserialization detected',
                        file.filename,
                        line_number,
                        'Use yaml.safe_load() or validate pickle data source',
                        language,
                        severity=Severity.CRITICAL
                    ))

        elif language == 'java':
            if 'ObjectInputStream(' in code or '.readObject()' in code:
                issues.append(self._create_security_issue(
                    'INSECURE_DESERIALIZATION',
                    'Potential insecure deserialization',
                    file.filename,
                    line_number,
                    'Validate serialized data, use allowlist for classes',
                    language,
                    severity=Severity.HIGH
                ))

        return issues

    def _check_ldap_injection(self, code: str, file, line_number: int, language: str) -> List[Issue]:
        issues: List[Issue] = []
        if language == 'java' and ('LdapContext' in code or 'search(' in code) and ('+' in code or 'concat' in code.lower()):
            issues.append(self._create_security_issue(
                'LDAP_INJECTION',
                'Potential LDAP injection vulnerability',
                file.filename,
                line_number,
                'Use parameterized LDAP queries, escape special characters',
                language,
                severity=Severity.HIGH
            ))

        return issues
    
    def _create_security_issue(self, code: str, message: str, file: str, line: int, 
                               suggestion: str, language: str, severity: Severity = Severity.MEDIUM) -> Issue:
        """Helper to create security issue."""
        return Issue(
            type=IssueType.SECURITY,
            severity=severity,
            message=message,
            file=file,
            line=line,
            code=code,
            suggestion=suggestion,
            metadata={'tool': 'pattern-analysis', 'language': language}
        )
    
    # ========== PYTHON SECURITY ==========
    
    def _analyze_python_security(self, files: List, config: dict) -> List[Issue]:
        """Analyze Python files for security issues."""
        issues = []
        tools = config.get('tools', ['bandit', 'safety'])
        
        if 'bandit' in tools:
            issues.extend(self._run_bandit(files))
        
        if 'safety' in tools:
            issues.extend(self._run_safety())
        
        return issues
    
    def _run_bandit(self, files: List) -> List[Issue]:
        """Run Bandit security scanner on Python files."""
        issues = []
        file_paths = [f.filename for f in files]
        
        try:
            result = subprocess.run(
                ['bandit', '-f', 'json', '-r'] + file_paths,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for result_item in data.get('results', []):
                    issues.append(Issue(
                        type=IssueType.SECURITY,
                        severity=self._map_bandit_severity(result_item.get('issue_severity')),
                        message=result_item.get('issue_text', ''),
                        file=result_item.get('filename', ''),
                        line=result_item.get('line_number'),
                        code=result_item.get('test_id'),
                        metadata={
                            'tool': 'bandit',
                            'language': 'python',
                            'confidence': result_item.get('issue_confidence')
                        }
                    ))
                    
        except FileNotFoundError:
            self.logger.warning("Bandit not installed. Install: pip install bandit")
        except Exception as e:
            self.logger.error(f"Bandit error: {e}")
        
        return issues
    
    def _run_safety(self) -> List[Issue]:
        """Run Safety to check for vulnerable dependencies."""
        issues = []
        
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for vuln in data:
                    issues.append(Issue(
                        type=IssueType.SECURITY,
                        severity=Severity.HIGH,
                        message=f"Vulnerable dependency: {vuln.get('package', '')} {vuln.get('installed_version', '')}",
                        file='requirements.txt',
                        code=vuln.get('vulnerability_id'),
                        suggestion=f"Upgrade to {vuln.get('vulnerable_spec', '')}",
                        metadata={'tool': 'safety', 'language': 'python'}
                    ))
                    
        except FileNotFoundError:
            self.logger.warning("Safety not installed. Install: pip install safety")
        except Exception as e:
            self.logger.error(f"Safety error: {e}")
        
        return issues
    
    # ========== JAVA SECURITY ==========
    
    def _analyze_java_security(self, files: List, config: dict) -> List[Issue]:
        """Analyze Java files for security issues."""
        issues = []
        tools = config.get('tools', ['spotbugs', 'dependency-check'])
        
        if 'spotbugs' in tools:
            issues.extend(self._run_spotbugs(files))
        
        if 'dependency-check' in tools:
            issues.extend(self._run_dependency_check('java'))
        
        return issues
    
    def _run_spotbugs(self, files: List) -> List[Issue]:
        """Run SpotBugs on Java compiled classes."""
        issues = []
        
        try:
            # SpotBugs requires compiled .class files
            # Command: spotbugs -textui -xml:withMessages -output spotbugs.xml target/classes
            _result = subprocess.run(
                ['spotbugs', '-textui', '-xml:withMessages', '-output', 'spotbugs.xml', 'target/classes'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Note: XML output parsing for security bugs can be implemented if needed
            self.logger.info("SpotBugs analysis completed")
            
        except FileNotFoundError:
            self.logger.warning("SpotBugs not installed. Install: https://spotbugs.github.io/")
        except Exception as e:
            self.logger.error(f"SpotBugs error: {e}")
        
        return issues
    
    def _run_dependency_check(self, language: str) -> List[Issue]:
        """Run OWASP Dependency Check."""
        issues = []
        
        try:
            # dependency-check --scan . --format JSON --out dependency-check-report.json
            result = subprocess.run(
                ['dependency-check', '--scan', '.', '--format', 'JSON', '--out', 'dependency-check-report.json'],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                with open('dependency-check-report.json', 'r') as f:
                    data = json.load(f)
                    
                    for dependency in data.get('dependencies', []):
                        for vuln in dependency.get('vulnerabilities', []):
                            issues.append(Issue(
                                type=IssueType.SECURITY,
                                severity=self._map_cvss_to_severity(vuln.get('cvssv3', {}).get('baseScore', 0)),
                                message=vuln.get('description', ''),
                                file=dependency.get('fileName', ''),
                                code=vuln.get('name'),
                                metadata={
                                    'tool': 'dependency-check',
                                    'language': language,
                                    'cvss': vuln.get('cvssv3', {}).get('baseScore')
                                }
                            ))
                            
        except FileNotFoundError:
            self.logger.warning("OWASP Dependency Check not installed")
        except Exception as e:
            self.logger.error(f"Dependency Check error: {e}")
        
        return issues
    
    # ========== SCALA SECURITY ==========
    
    def _analyze_scala_security(self, files: List, config: dict) -> List[Issue]:
        """Analyze Scala files for security issues."""
        issues = []
        tools = config.get('tools', ['spotbugs', 'dependency-check'])
        
        # Scala can use SpotBugs and Dependency Check (same as Java)
        if 'spotbugs' in tools:
            issues.extend(self._run_spotbugs(files))
        
        if 'dependency-check' in tools:
            issues.extend(self._run_dependency_check('scala'))
        
        return issues
    
    # ========== JAVASCRIPT/TYPESCRIPT/NODE.JS SECURITY ==========
    
    def _analyze_js_security(self, files: List, config: dict, language: str) -> List[Issue]:
        """Analyze JavaScript/TypeScript/Node.js files for security issues."""
        issues = []
        tools = config.get('tools', ['npm-audit', 'eslint-plugin-security'])
        
        if 'npm-audit' in tools:
            issues.extend(self._run_npm_audit(language))
        
        if 'eslint-plugin-security' in tools:
            issues.extend(self._run_eslint_security(files, language))
        
        if 'snyk' in tools:
            issues.extend(self._run_snyk(language))
        
        return issues
    
    def _run_npm_audit(self, language: str) -> List[Issue]:
        """Run npm audit to check for vulnerable dependencies."""
        issues = []
        
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for vuln_id, vuln_data in data.get('vulnerabilities', {}).items():
                    issues.append(Issue(
                        type=IssueType.SECURITY,
                        severity=self._map_npm_severity(vuln_data.get('severity')),
                        message=f"Vulnerable package: {vuln_data.get('name', '')} - {vuln_data.get('title', '')}",
                        file='package.json',
                        code=vuln_id,
                        suggestion=f"Update to {vuln_data.get('fixAvailable', {}).get('version', 'latest')}",
                        metadata={'tool': 'npm-audit', 'language': language}
                    ))
                    
        except FileNotFoundError:
            self.logger.warning("npm not installed")
        except Exception as e:
            self.logger.error(f"npm audit error: {e}")
        
        return issues
    
    def _run_eslint_security(self, files: List, language: str) -> List[Issue]:
        """Run ESLint with security plugin."""
        issues = []
        file_paths = [f.filename for f in files]
        
        try:
            # Requires eslint-plugin-security installed
            result = subprocess.run(
                ['eslint', '-f', 'json', '--plugin', 'security'] + file_paths,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                issues.extend(self._parse_eslint_security_output(data, language))
                            
        except FileNotFoundError:
            self.logger.warning("ESLint security plugin not installed. Install: npm install -g eslint-plugin-security")
        except Exception as e:
            self.logger.error(f"ESLint security error: {e}")
        
        return issues

    def _parse_eslint_security_output(self, data: List[Dict[str, Any]], language: str) -> List[Issue]:
        """Parse ESLint security JSON output and return Issue list."""
        issues: List[Issue] = []
        for file_result in data:
            filename = file_result.get('filePath', '')
            for message in file_result.get('messages', []):
                if (message.get('ruleId') or '').startswith('security/'):
                    issues.append(Issue(
                        type=IssueType.SECURITY,
                        severity=Severity.MEDIUM if message.get('severity') == 2 else Severity.LOW,
                        message=message.get('message', ''),
                        file=filename,
                        line=message.get('line'),
                        column=message.get('column'),
                        code=message.get('ruleId'),
                        metadata={'tool': 'eslint-security', 'language': language}
                    ))
        return issues
    
    def _run_snyk(self, language: str) -> List[Issue]:
        """Run Snyk security scanner."""
        issues = []
        
        try:
            result = subprocess.run(
                ['snyk', 'test', '--json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for vuln in data.get('vulnerabilities', []):
                    issues.append(Issue(
                        type=IssueType.SECURITY,
                        severity=self._map_snyk_severity(vuln.get('severity')),
                        message=f"{vuln.get('title', '')} in {vuln.get('packageName', '')}",
                        file='package.json',
                        code=vuln.get('id'),
                        suggestion=vuln.get('fixedIn', [''])[0] if vuln.get('fixedIn') else None,
                        metadata={'tool': 'snyk', 'language': language}
                    ))
                    
        except FileNotFoundError:
            self.logger.warning("Snyk not installed. Install: npm install -g snyk")
        except Exception as e:
            self.logger.error(f"Snyk error: {e}")
        
        return issues
    
    # ========== HELPER METHODS ==========
    
    def _map_bandit_severity(self, bandit_severity: str) -> Severity:
        """Map Bandit severity to our severity."""
        mapping = {
            'HIGH': Severity.HIGH,
            'MEDIUM': Severity.MEDIUM,
            'LOW': Severity.LOW
        }
        return mapping.get(bandit_severity.upper(), Severity.MEDIUM)
    
    def _map_npm_severity(self, npm_severity: str) -> Severity:
        """Map npm audit severity to our severity."""
        mapping = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'moderate': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO
        }
        return mapping.get(npm_severity.lower(), Severity.MEDIUM)
    
    def _map_snyk_severity(self, snyk_severity: str) -> Severity:
        """Map Snyk severity to our severity."""
        mapping = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW
        }
        return mapping.get(snyk_severity.lower(), Severity.MEDIUM)
    
    def _map_cvss_to_severity(self, cvss_score: float) -> Severity:
        """Map CVSS score to severity."""
        if cvss_score >= 9.0:
            return Severity.CRITICAL
        elif cvss_score >= 7.0:
            return Severity.HIGH
        elif cvss_score >= 4.0:
            return Severity.MEDIUM
        elif cvss_score > 0:
            return Severity.LOW
        return Severity.INFO
