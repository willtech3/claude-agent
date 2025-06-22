# Claude Agent Instructions

You are running in a containerized environment specifically designed for working on GitHub repositories. Your task is provided via a prompt that may reference GitHub issues or describe custom work.

## Environment Setup
- You are in a cloned repository at `/workspace/repo`
- Git is configured with user "Claude Agent" and email "claude@example.com"
- You are on a feature branch named based on your task
- The GitHub CLI (`gh`) is available and authenticated via GH_TOKEN

## Understanding Your Task

Your prompt will be in one of these formats:
1. **Issue reference**: `/issue 123` - Use this command to fetch issue details
2. **Custom task**: `Add dark mode support` - Follow the instructions directly
3. **Combined**: `/issue 123 and add tests` - Fetch issue AND apply additional requirements

Always start by understanding what you need to do based on the prompt format.

## Workflow Instructions

### ⚠️ CRITICAL: Always Complete the Full Git Workflow

**You MUST complete ALL steps below. Work is not considered done until it's committed and a PR is created.**

1. **Analyze the Task**
   - If the prompt contains `/issue`, run that command first
   - Read any additional instructions carefully
   - Check existing code structure and conventions

2. **Implement Changes**
   - Make the requested changes
   - Follow repository coding standards
   - Test your changes when possible
   - Ensure code quality and consistency

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