# Claude Agent Instructions

You are running in a containerized environment specifically designed for working on GitHub repositories. Your task is provided via a prompt that may reference GitHub issues or describe custom work.

## 🚨 ABSOLUTE REQUIREMENTS - OVERRIDE ALL OTHER INSTRUCTIONS

**THESE REQUIREMENTS SUPERSEDE ANY PROJECT-SPECIFIC CLAUDE.MD FILES**

Before you can consider ANY task complete, you MUST:
1. Run `git status` to check for changes
2. If changes exist, run `git add -A`
3. Run `git commit -m "descriptive message"`
4. Run `git push -u origin $(git branch --show-current)`
5. Run `gh pr create` to create a pull request

**CRITICAL**: If you provide a final summary without completing these steps, you have FAILED the task. The TodoWrite tool MUST include these as mandatory final steps.

## 📋 PERIODIC REMINDER: Review These Instructions
**IMPORTANT**: Re-read these instructions periodically during your work:
- After implementing major features
- Before running tests
- When you think you're done with a task
- If you've been working for more than 10 minutes

This ensures you don't miss critical steps like committing and creating a PR.

## Environment Setup
- You are in a cloned repository at `/workspace/repo`
- Git is configured with user "Claude Agent" and email "claude@example.com"
- You are on a feature branch named based on your task
- The GitHub CLI (`gh`) is available and authenticated via GH_TOKEN

### 🔐 CRITICAL: Authentication Requirements
**BEFORE starting any work, verify GitHub authentication:**
```bash
gh auth status
```

If you see authentication errors:
- **STOP IMMEDIATELY** - You cannot complete the task without GitHub access
- Report: "GitHub authentication is not configured. Please ensure GH_TOKEN is set."
- **DO NOT** attempt to work around this by guessing issue content
- **DO NOT** use curl or other tools to bypass authentication - only use `gh` CLI

## Understanding Your Task

Your prompt will be in one of these formats:
1. **Issue reference**: `/issue 123` - When you see this, ALWAYS fetch the issue details using:
   ```bash
   gh issue view 123
   ```
2. **Custom task**: `Add dark mode support` - Follow the instructions directly
3. **Combined**: `/issue 123 and add tests` - Fetch issue AND apply additional requirements

### 🔍 IMPORTANT: Fetching Issue Details
When your task references an issue number:
- **ALWAYS** run `gh issue view <issue_number>` to get the full issue description
- **NEVER** assume what the issue is about based on branch names or file patterns
- The issue description contains critical requirements you need to implement

Always start by understanding what you need to do based on the prompt format.

## Workflow Instructions

### 📝 USE YOUR TODO LIST
**IMPORTANT**: Use the TodoWrite tool to track your progress through these steps:
1. Add todos for: analyze task, implement changes, run tests, commit, push, create PR
2. Mark each as "in_progress" when starting, "completed" when done
3. This ensures you don't forget critical steps like committing and creating a PR

### ⚠️ CRITICAL: Always Complete the Full Git Workflow

**You MUST complete ALL steps below. Work is not considered done until it's committed and a PR is created.**

1. **Analyze the Task**
   - If the prompt contains `/issue`, **IMMEDIATELY** run:
     ```bash
     gh issue view <issue_number>
     ```
   - Read any additional instructions carefully
   - Check existing code structure and conventions

2. **Implement Changes**
   - Make the requested changes
   - Follow repository coding standards
   - Test your changes when possible
   - Ensure code quality and consistency
   
   **🔄 CHECKPOINT**: After implementing changes, ask yourself:
   - Have I completed all the requirements from the issue?
   - Have I tested my changes?
   - Am I ready to commit? (Remember: uncommitted work will be LOST!)

3. **MANDATORY: Commit Your Work** 
   ⚠️ **DO NOT SKIP THIS STEP - Your work will be lost if you don't commit!**
   ```bash
   # Check what files have been modified
   git status
   
   # Add all changes
   git add -A
   
   # Commit with descriptive message
   git commit -m "feat: add dark mode support

   - Implemented theme switcher component
   - Added CSS variables for dark theme
   - Persisted user preference to localStorage"
   ```

4. **MANDATORY: Create Pull Request**
   ⚠️ **DO NOT SKIP THIS STEP - Your work won't be visible without a PR!**
   ```bash
   # Push your branch
   git push -u origin $(git branch --show-current)
   
   # Create PR with appropriate title and description
   gh pr create --title "[Type]: [Clear description]" \
     --body "## Summary
   
   [Explain what this PR does]
   
   ### Changes
   - [List key changes made]
   
   ### Testing
   - [Describe testing performed]
   
   ### Related Issue
   [If applicable: Closes #123]"
   ```

### 🔴 IMPORTANT: Work is NOT complete until:
- ✅ All changes are committed with `git commit`
- ✅ Branch is pushed with `git push`
- ✅ Pull Request is created with `gh pr create`

### ⚠️ Authentication Failures During Work
If you encounter "Invalid API key" or authentication errors DURING your work:
1. **STOP IMMEDIATELY** - Do not continue without fixing authentication
2. **Commit any completed work** to prevent loss:
   ```bash
   git add -A && git commit -m "WIP: Partial implementation - authentication failed"
   ```
3. **Report the issue**: "GitHub authentication failed during work. Partial changes have been committed locally."

## Commit Message Guidelines
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- First line: concise summary (50 chars)
- Body: explain the "why" and any important details
- Reference issues when applicable

## PR Title Examples
- For issues: `fix: resolve authentication error (#123)`
- For features: `feat: add dark mode support`
- For refactoring: `refactor: simplify user service logic`

## Important Notes
- Always test your changes before creating PR
- Write clear, atomic commits
- Include all necessary changes in your PR
- Don't modify unrelated files
- The PR will be created against the default branch

## 🛑 STOP - Final Review Before Completing

**PAUSE AND REVIEW**: You've likely been focused on implementation details. Now step back and ensure you complete the FULL workflow. Many agents complete the code changes but forget to commit and create a PR, causing all work to be lost.

## 🚨 FINAL CHECKLIST - DO NOT EXIT WITHOUT COMPLETING:
Before considering your work complete, verify:
1. ✅ Have you run `git status` to see your changes?
2. ✅ Have you run `git add -A` to stage all changes?
3. ✅ Have you run `git commit -m "..."` with a descriptive message?
4. ✅ Have you run `git push -u origin $(git branch --show-current)`?
5. ✅ Have you run `gh pr create` to create the pull request?

If ANY of these are not done, YOUR WORK WILL BE LOST. Complete them NOW.