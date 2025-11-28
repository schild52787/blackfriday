# CLAUDE.md - AI Assistant Guide for Blackfriday Repository

## Project Overview

**Project Name:** blackfriday
**Description:** Black Friday Travel
**Repository:** schild52787/blackfriday
**Current Status:** Early stage development

This repository is dedicated to building a black friday travel-related application. The codebase is in its initial stages with foundational structure being established.

---

## Repository Structure

```
blackfriday/
├── README.md           # Project overview and documentation
└── CLAUDE.md          # This file - AI assistant guidance
```

### Current State
- **Initial Commit:** 837673e - Basic repository setup
- **Main Files:** README.md containing project description
- **Development Stage:** Foundation/Planning phase

---

## Git Workflow & Branch Conventions

### Branch Naming Convention

**CRITICAL:** All AI assistant development branches MUST follow this pattern:
```
claude/claude-md-{session-id}
```

**Current Development Branch:** `claude/claude-md-mij3enxhk00r4vu9-01294RzQDdzEVLvpYqrPP5uo`

### Branch Rules
1. **ALWAYS** develop on the designated `claude/` branch
2. **NEVER** push to branches without the `claude/` prefix (will fail with 403)
3. **CREATE** the branch locally if it doesn't exist
4. **COMMIT** regularly with clear, descriptive messages
5. **PUSH** using: `git push -u origin <branch-name>`

### Git Operations Best Practices

**Pushing Changes:**
```bash
git push -u origin claude/claude-md-{session-id}
```
- Retry up to 4 times on network failures with exponential backoff (2s, 4s, 8s, 16s)
- Branch must start with `claude/` and match session ID

**Fetching/Pulling:**
```bash
git fetch origin <branch-name>
git pull origin <branch-name>
```
- Prefer fetching specific branches
- Retry with exponential backoff on network failures

**Commit Messages:**
- Use clear, descriptive commit messages
- Focus on the "why" rather than just the "what"
- Format: `<type>: <description>`
  - Examples: `feat: add user authentication`, `fix: resolve login bug`, `docs: update API documentation`

---

## Development Conventions

### Code Style & Best Practices

1. **Simplicity First**
   - Avoid over-engineering solutions
   - Only make changes that are directly requested or clearly necessary
   - Three similar lines of code is better than a premature abstraction

2. **Security**
   - Watch for common vulnerabilities (XSS, SQL injection, command injection, OWASP top 10)
   - Validate at system boundaries (user input, external APIs)
   - Don't add unnecessary validation for internal code

3. **Error Handling**
   - Only add error handling where genuinely needed
   - Trust internal code and framework guarantees
   - Focus on boundary conditions

4. **Documentation**
   - Only add comments where logic isn't self-evident
   - Don't add docstrings to unchanged code
   - Keep documentation focused and relevant

5. **Backwards Compatibility**
   - No unnecessary compatibility hacks
   - Delete unused code completely (no `// removed` comments)
   - No renaming of unused variables with underscores

---

## File Operations Guidelines

### Tool Preferences

**ALWAYS use specialized tools over bash commands:**
- **Reading files:** Use `Read` tool (NOT `cat/head/tail`)
- **Editing files:** Use `Edit` tool (NOT `sed/awk`)
- **Creating files:** Use `Write` tool (NOT `echo >` or `cat <<EOF`)
- **Searching files:** Use `Glob` tool (NOT `find/ls`)
- **Searching content:** Use `Grep` tool (NOT `grep/rg`)

**File Creation Policy:**
- **PREFER** editing existing files over creating new ones
- **ONLY** create new files when absolutely necessary
- **AVOID** creating unnecessary documentation files

---

## Task Management

### Using TODO Lists

For complex tasks (3+ steps or non-trivial work), use the TodoWrite tool to:
1. Plan and break down the task
2. Track progress in real-time
3. Give visibility to users

**Task States:**
- `pending`: Not yet started
- `in_progress`: Currently working on (ONE at a time)
- `completed`: Successfully finished

**Important:**
- Mark tasks complete IMMEDIATELY after finishing
- Don't batch completions
- Only mark complete when FULLY accomplished (tests passing, no errors)
- Keep exactly ONE task in_progress at any time

---

## Project-Specific Guidance

### Expected Technology Stack
(To be determined as project develops)

Consider common travel application technologies:
- **Backend:** Node.js, Python, Go, or similar
- **Frontend:** React, Vue, Next.js, or similar
- **Database:** PostgreSQL, MongoDB, or similar
- **APIs:** Travel booking APIs, pricing APIs
- **Deployment:** Cloud platforms (AWS, GCP, Azure)

### Typical Features for Travel Applications
- Flight/hotel search and booking
- Price comparison and alerts
- Itinerary management
- User accounts and preferences
- Payment processing
- Deal aggregation
- Notifications for deals

### Development Workflow (Once Established)

1. **Before Making Changes:**
   - Read relevant files first
   - Understand existing code
   - Check for similar patterns in codebase

2. **Making Changes:**
   - Use TodoWrite for complex tasks
   - Make focused, minimal changes
   - Test as you go
   - Commit logically grouped changes

3. **After Changes:**
   - Verify tests pass (when testing is set up)
   - Review your changes
   - Push to the designated claude/ branch

---

## Communication Guidelines

### With Users
- Be concise and direct
- Focus on technical accuracy
- Output text for communication (NOT bash echo or code comments)
- Use GitHub-flavored markdown for formatting
- Avoid emojis unless explicitly requested

### Code References
When referencing code, use the pattern: `file_path:line_number`

Example: "User authentication is handled in `src/auth/login.js:45`"

---

## Testing Conventions
(To be established as project develops)

When testing infrastructure is added:
- Run tests before committing
- Fix all test failures before marking tasks complete
- Add tests for new features
- Maintain existing test coverage

---

## Deployment & CI/CD
(To be established as project develops)

Future considerations:
- Continuous Integration setup
- Automated testing
- Deployment pipelines
- Environment configurations

---

## Quick Reference Commands

### Git Operations
```bash
# Check current status
git status

# Create and checkout new branch
git checkout -b claude/claude-md-{session-id}

# Stage changes
git add .

# Commit with message
git commit -m "feat: add new feature"

# Push to remote
git push -u origin claude/claude-md-{session-id}

# View recent commits
git log --oneline -10
```

### Development Commands
(To be added as project structure develops)

---

## Important Reminders

1. ✅ **DO:** Use specialized tools for file operations
2. ✅ **DO:** Read files before editing them
3. ✅ **DO:** Keep changes focused and minimal
4. ✅ **DO:** Commit and push to claude/ branches
5. ✅ **DO:** Use TodoWrite for complex tasks

6. ❌ **DON'T:** Create unnecessary files
7. ❌ **DON'T:** Over-engineer solutions
8. ❌ **DON'T:** Push to non-claude/ branches
9. ❌ **DON'T:** Use bash for file operations
10. ❌ **DON'T:** Add unnecessary abstractions

---

## Future Updates

This document should be updated as the project evolves to include:
- Technology stack details once chosen
- Build and test commands
- Deployment procedures
- API documentation references
- Architecture decisions and patterns
- Common troubleshooting steps
- Performance considerations
- Security guidelines specific to the application

---

## Contact & Resources

**Repository:** schild52787/blackfriday
**Current Branch:** claude/claude-md-mij3enxhk00r4vu9-01294RzQDdzEVLvpYqrPP5uo

For questions about Claude Code itself:
- Use `/help` command
- Report issues at: https://github.com/anthropics/claude-code/issues

---

**Last Updated:** 2025-11-28
**Document Version:** 1.0.0
