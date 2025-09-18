# Manna Financial Platform - Monorepo Setup

## Overview

This document describes the modern monorepo structure implemented for the Manna Financial Management Platform. The setup includes workspace configuration, linting, formatting, git hooks, and CI/CD pipelines.

## Repository Structure

```
manna/
├── .github/workflows/       # CI/CD pipelines
├── .husky/                  # Git hooks
├── packages/
│   ├── frontend/           # Next.js 14+ application
│   ├── backend/            # FastAPI Python application
│   └── shared/             # Shared TypeScript types and utilities
├── scripts/                # Development and setup scripts
├── data/                   # Raw financial data (preserved)
├── reports/               # Generated reports (preserved)
├── tools/                 # Plaid API tools (preserved)
├── docker-compose.yml     # Development services
├── package.json           # Root workspace configuration
├── pnpm-workspace.yaml    # pnpm workspace definition
└── tsconfig.json          # Root TypeScript configuration
```

## Package Manager

**pnpm** - Chosen for its superior performance and efficient dependency management for monorepos.

## Workspaces Configuration

### Root Package Configuration
- **package.json** - Defines workspace structure and shared development scripts
- **pnpm-workspace.yaml** - pnpm-specific workspace configuration

### Individual Packages
- **@manna/frontend** - Next.js 14+ application with TypeScript
- **@manna/backend** - FastAPI application with Python 3.11+
- **@manna/shared** - Shared TypeScript types and utilities

## Development Tools

### Code Quality
- **ESLint** - JavaScript/TypeScript linting with @typescript-eslint
- **Prettier** - Code formatting with consistent rules
- **TypeScript** - Type checking across all packages

### Git Hooks (Husky)
- **pre-commit** - Runs lint-staged for automatic code formatting and linting
- **lint-staged** - Processes only staged files for efficiency

### CI/CD Pipeline (GitHub Actions)
- **Linting and Formatting** - ESLint and Prettier checks
- **Type Checking** - TypeScript validation
- **Testing** - Frontend and backend test suites
- **Docker Builds** - Container image building and caching

## Docker Configuration

### Development Services
- **PostgreSQL 15** - Primary database
- **Redis 7** - Caching and session storage
- **Backend** - FastAPI development server
- **Frontend** - Next.js development server

### Multi-stage Dockerfiles
- Optimized for both development and production
- Security best practices with non-root users
- Efficient layer caching

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.11+ (conda environment 'manna')
- Docker and Docker Compose
- pnpm (installed automatically if needed)

### Initial Setup
```bash
# 1. Activate conda environment
conda activate manna

# 2. Run setup script
./scripts/setup.sh

# 3. Copy and update environment variables
cp .env.sample .env
# Edit .env with your actual values

# 4. Start development services
pnpm dev
```

### Available Commands

#### Root Level Commands
```bash
pnpm install          # Install all dependencies
pnpm build            # Build all packages
pnpm dev              # Start development servers
pnpm lint             # Run linting
pnpm lint:fix         # Fix linting issues
pnpm format           # Format all code
pnpm format:check     # Check code formatting
pnpm type-check       # Run TypeScript checks
pnpm test             # Run all tests
pnpm clean            # Clean all build artifacts
```

#### Package-Specific Commands
```bash
# Frontend
cd packages/frontend
pnpm dev              # Start Next.js dev server
pnpm build            # Build for production

# Backend  
cd packages/backend
pnpm dev              # Start FastAPI dev server
python -m pytest     # Run tests

# Shared
cd packages/shared
pnpm build            # Build shared package
pnpm dev              # Watch mode for development
```

## Configuration Files

### TypeScript
- **tsconfig.json** - Root configuration with shared settings
- **packages/*/tsconfig.json** - Package-specific configurations
- **packages/shared/tsconfig.build.json** - Build-specific configuration

### ESLint & Prettier
- **.eslintrc.json** - ESLint configuration with TypeScript support
- **.prettierrc** - Prettier formatting rules
- **.prettierignore** - Files to exclude from formatting

### Git
- **.gitignore** - Updated for monorepo structure
- **.husky/pre-commit** - Git hook for pre-commit checks
- **.lintstagedrc** - Staged file processing configuration

## Environment Management

### Environment Variables
- **.env.sample** - Template with all required variables
- **.env** - Local environment file (gitignored)

### Development vs Production
- Development configuration in docker-compose.yml
- Production configuration can be created as docker-compose.prod.yml

## Best Practices

### Dependency Management
- Use workspace references for internal packages (`@manna/shared`: `workspace:*`)
- Install shared dev dependencies at root level
- Keep package-specific dependencies in their respective packages

### Code Organization
- Shared types and utilities in `@manna/shared`
- Frontend-specific code in `@manna/frontend`
- Backend-specific code in `@manna/backend`

### Development Workflow
1. Make changes in appropriate packages
2. Run tests and linting locally
3. Commit triggers pre-commit hooks
4. Push triggers CI/CD pipeline
5. All checks must pass before merging

## Preserved Legacy Structure

The following directories have been preserved from the original structure:
- **data/** - Raw transaction and financial data
- **reports/** - Generated financial reports
- **tools/** - Plaid API implementation

These are integrated with the new backend package through Docker volume mounts.

## Next Steps

1. Update `.env` with actual configuration values
2. Set up database migrations in the backend package
3. Implement authentication and authorization
4. Add comprehensive test coverage
5. Set up production deployment configuration
6. Configure monitoring and logging
7. Implement security scanning in CI/CD

## Troubleshooting

### Common Issues

**pnpm not found**: Install with `npm install -g pnpm`

**TypeScript errors**: Ensure `@manna/shared` is built with `pnpm build`

**Docker permission issues**: Add user to docker group or use sudo

**Pre-commit hooks not working**: Reinstall with `pnpm prepare`

### Getting Help

- Check package-specific README files
- Review CI/CD logs for build issues
- Ensure all prerequisites are installed
- Verify environment variables are set correctly

## Performance Notes

- pnpm provides faster installs and better disk usage
- Docker layer caching optimizes build times
- Git hooks only process changed files
- TypeScript project references enable incremental compilation