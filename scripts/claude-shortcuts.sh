#!/bin/bash
# Quick Claude Commands for Riona AI

# Make scripts executable
chmod +x claude-*.sh

# Feature Building
alias claude-feature='claude "build complete feature with backend API, frontend components, and tests for"'

# Backend Tasks
alias claude-api='claude "create REST API endpoint with validation, error handling, and tests for"'
alias claude-db='claude "design and implement database schema for"'
alias claude-service='claude "implement service layer with business logic for"'

# Frontend Tasks
alias claude-component='claude "create React component with TypeScript and Tailwind for"'
alias claude-ui='claude "build user interface with responsive design for"'
alias claude-state='claude "implement state management using Zustand for"'

# Testing
alias claude-test='claude "write comprehensive tests for"'
alias claude-test-all='claude "analyze codebase and add missing tests"'

# Debugging
alias claude-fix='claude "debug and fix"'
alias claude-error='claude "analyze this error and provide solution:"'

# Code Quality
alias claude-review='claude "review code for security, performance, and best practices in"'
alias claude-refactor='claude "refactor for better performance and maintainability"'

# Documentation
alias claude-docs='claude "update documentation for"'
alias claude-readme='claude "update README with"'

# Git Operations
alias claude-commit='claude "review changes and suggest commit message"'
alias claude-pr='claude "create pull request description for current changes"'

# Project Analysis
alias claude-status='claude "analyze project status and list priorities"'
alias claude-todos='claude "find all TODO comments and create action plan"'

# AI/Instagram Specific
alias claude-instagram='claude "implement Instagram integration for"'
alias claude-ai='claude "add AI-powered features for"'
alias claude-scheduler='claude "implement scheduling system for"'

echo "Claude shortcuts loaded! Examples:"
echo "  claude-feature 'user authentication'"
echo "  claude-api 'profile management'"
echo "  claude-component 'ProfileCard'"
echo "  claude-fix 'TypeScript errors'"
