---
name: security-scan
description: Deep security analysis of code - usage: /security-scan <file_path or directory>
---

Perform a comprehensive security analysis of `$ARGUMENTS`.

Use the **security-reviewer** subagent to conduct a thorough security review.

## Security Scan Process

1. **Identify the scope** - File, directory, or entire codebase
2. **Map the attack surface**:
   - Entry points (APIs, user inputs, file uploads)
   - Data flows (where sensitive data travels)
   - External integrations (databases, APIs, services)

3. **Scan for vulnerabilities** using the OWASP Top 10 framework:
   - A01: Broken Access Control
   - A02: Cryptographic Failures
   - A03: Injection
   - A04: Insecure Design
   - A05: Security Misconfiguration
   - A06: Vulnerable Components
   - A07: Authentication Failures
   - A08: Data Integrity Failures
   - A09: Logging Failures
   - A10: Server-Side Request Forgery

4. **Check for language-specific issues**
5. **Review dependencies** if package files are present

## Output Format

```markdown
# Security Scan Report: [target]

## Executive Summary
- **Risk Level**: [Critical/High/Medium/Low]
- **Findings**: X Critical, Y High, Z Medium
- **Recommendation**: [Brief action item]

## Attack Surface

### Entry Points
- [Endpoint/Input]: [Risk level]

### Sensitive Data
- [Data type]: [How it's handled]

## Findings

### CRITICAL

#### [Finding Title]
**OWASP Category**: [Category]
**Location**: `file.py:line`
**CWE**: [CWE ID if applicable]

**Vulnerable Code**:
```code
// The vulnerable code
```

**Attack Scenario**:
[How an attacker could exploit this]

**Remediation**:
```code
// The secure code
```

**References**:
- [Link to documentation]

---

### HIGH
[Similar format]

### MEDIUM
[Similar format]

### LOW / INFORMATIONAL
[Similar format]

## Recommendations

### Immediate Actions
1. [Critical fix]
2. [Critical fix]

### Short-term Improvements
1. [Important improvement]

### Best Practices to Adopt
1. [Security practice]

## Dependencies Review
[If package.json, requirements.txt, etc. exist]

- [Package]: [Version] - [Known vulnerabilities]
```

## Guidelines

- Prioritize findings by exploitability and impact
- Provide working secure code, not just warnings
- Consider the deployment context (internal vs public)
- Check for secrets in code and config files
- Look for patterns, not just individual instances
- Reference authoritative sources (OWASP, CWE, etc.)
