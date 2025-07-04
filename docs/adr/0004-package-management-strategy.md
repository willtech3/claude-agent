# 4. Package Management Strategy

Date: 2025-01-04

## Status

Accepted

## Context

In a monorepo with multiple languages (TypeScript/JavaScript and Python), we need consistent and efficient package management that:
- Supports workspace/monorepo features
- Provides fast dependency resolution
- Enables code sharing between packages
- Has good caching for CI/CD
- Is actively maintained

We have two ecosystems to consider:
- Node.js packages for frontend and shared types
- Python packages for backend and agent

## Decision

### JavaScript/TypeScript: npm workspaces
- Use npm (v9+) with native workspace support
- Leverage workspace protocol for internal dependencies
- Single lockfile at root for consistency

### Python: uv
- Use uv for Python dependency management
- Modern, fast alternative to pip/poetry
- Built in Rust for performance
- Compatible with pyproject.toml standard

### Package Structure
```
package.json (root) - npm workspaces config
├── frontend/package.json
├── shared/package.json
└── backend/pyproject.toml - uv config
```

### Dependency Management Rules
1. Pin major versions in package files
2. Use lockfiles for reproducible builds
3. Regular dependency updates via automation
4. Security scanning for vulnerabilities

## Consequences

**Positive:**
- npm workspaces is native and well-supported
- uv is extremely fast (10-100x faster than pip)
- Both tools have excellent caching
- Consistent with modern standards
- Good CI/CD integration
- Simplified development workflow

**Negative:**
- uv is relatively new (but stable)
- Two different package managers to learn
- Potential version conflicts between ecosystems
- Some tools may not support uv yet
- Migration effort if changing tools later