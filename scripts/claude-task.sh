#!/bin/bash
# Riona AI - Claude Code Task Runner

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root
PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
cd $PROJECT_ROOT

# Function to run Claude task
run_task() {
    echo -e "${BLUE}Running: $1${NC}"
    claude "$2"
    echo -e "${GREEN}✓ Completed: $1${NC}\n"
}

# Main menu
echo -e "${YELLOW}Riona AI - Claude Code Task Runner${NC}"
echo "=================================="
echo "1. Build Complete Feature"
echo "2. Backend Development"
echo "3. Frontend Development"
echo "4. Testing Suite"
echo "5. Debug & Fix Issues"
echo "6. Code Review"
echo "7. Documentation Update"
echo "8. Performance Optimization"
echo "9. Custom Task"
echo "0. Exit"
echo "=================================="
read -p "Select task: " choice

case $choice in
    1)
        echo -e "${BLUE}Building Complete Feature${NC}"
        read -p "Feature name: " feature
        run_task "Planning" "Create detailed plan for $feature feature including database schema, API endpoints, and UI components"
        run_task "Backend" "Implement backend API for $feature following the plan"
        run_task "Frontend" "Create React components for $feature with TypeScript"
        run_task "Testing" "Write comprehensive tests for $feature"
        run_task "Documentation" "Update documentation for $feature"
        ;;
    
    2)
        echo -e "${BLUE}Backend Development${NC}"
        read -p "What to build: " backend_task
        run_task "Backend API" "As a backend expert, implement $backend_task with proper error handling, validation, and tests"
        ;;
    
    3)
        echo -e "${BLUE}Frontend Development${NC}"
        read -p "Component/Feature: " frontend_task
        run_task "Frontend" "As a React specialist, create $frontend_task with TypeScript, Tailwind styling, and proper state management"
        ;;
    
    4)
        echo -e "${BLUE}Testing Suite${NC}"
        run_task "Unit Tests" "Write unit tests for all untested functions"
        run_task "Integration Tests" "Create integration tests for API endpoints"
        run_task "Component Tests" "Add React component tests"
        ;;
    
    5)
        echo -e "${BLUE}Debug & Fix${NC}"
        run_task "Analysis" "Analyze the codebase for bugs and issues"
        run_task "Fixes" "Fix all identified issues with proper error handling"
        ;;
    
    6)
        echo -e "${BLUE}Code Review${NC}"
        run_task "Security Review" "Review code for security vulnerabilities"
        run_task "Performance Review" "Identify performance bottlenecks"
        run_task "Code Quality" "Check code quality and suggest improvements"
        ;;
    
    7)
        echo -e "${BLUE}Documentation${NC}"
        run_task "API Docs" "Update API documentation"
        run_task "README" "Update README with latest changes"
        run_task "Code Comments" "Add missing code comments"
        ;;
    
    8)
        echo -e "${BLUE}Performance Optimization${NC}"
        run_task "Analysis" "Analyze performance bottlenecks"
        run_task "Optimization" "Optimize identified performance issues"
        ;;
    
    9)
        echo -e "${BLUE}Custom Task${NC}"
        read -p "Enter task: " custom
        claude "$custom"
        ;;
    
    0)
        echo "Exiting..."
        exit 0
        ;;
esac

echo -e "${GREEN}All tasks completed!${NC}"
