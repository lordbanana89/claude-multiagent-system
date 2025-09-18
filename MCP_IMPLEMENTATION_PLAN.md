# MCP Implementation Plan

## Current System Status

- Existing MCP files: 9 Python files with MCP/bridge functionality
- Database: SQLite with 5 tables (activities, agent_states, components, conflicts, decisions)
- Missing: capabilities, resources, prompts tables
- API Server: Running on port 8099 without JSON-RPC support
- Hooks: Basic pattern matching in mcp_bridge.py, no JSON-RPC
- Frontend: React dashboard with basic MCP status display
- No JSON-RPC implementation found in codebase
- No capabilities endpoint exists
- No resources or prompts system implemented

## Implementation Priority Guide

### Must Have (Core MCP Compliance)
- JSON-RPC 2.0 protocol
- Three primitives: Tools, Resources, Prompts
- Capability negotiation
- Hook integration (9 events)
- Idempotency support
- Dry-run mode for testing

### Should Have (Safety & Quality)
- Uniform error model
- Path protection for file access
- X-Request-ID tracing
- Basic performance metrics
- Request timeouts
- Audit logging

### Nice to Have (Future Optimization)
- Advanced caching strategies
- WebSocket real-time updates
- Multi-provider support (OpenAI, Google, Microsoft)
- Complex queue systems
- PostgreSQL migration

## Phase 0: Prerequisites and Baseline

- Create and validate master recovery prompt
  - Purpose: Ensure project continuity if conversation is reset or compacted
  - File: MCP_MASTER_RECOVERY_PROMPT.md
  - Contains: Complete project context, specifications, and recovery procedures
  - Validation: Test prompt can reconstruct full context from zero

- Install required Python dependencies
  - Purpose: Ensure all necessary libraries are available before starting
  - Command: pip3 install authlib jsonschema aiohttp websockets cryptography
  - Verify installation: python3 -c "import authlib, jsonschema, aiohttp, websockets, cryptography; print('All dependencies OK')"
  - Document versions for reproducibility

- Collect baseline performance metrics
  - Purpose: Measure current system performance for comparison after MCP implementation
  - Metrics to collect:
    - Average response time for /api/mcp/status endpoint
    - Database query execution times for activities table
    - Memory usage of mcp_api_server_optimized.py process
    - CPU usage during typical operations
    - Number of requests per minute handled
  - Store baseline in file: baseline_metrics.json
  - Command to collect: python3 collect_baseline_metrics.py

- Create automated database backup script
  - Purpose: Protect data during development and schema changes
  - Script name: backup_mcp_database.sh
  - Backup location: /tmp/mcp_backups/
  - Run before each phase that modifies database
  - Include timestamp in backup filename

- Document current API endpoints and responses
  - Purpose: Clear reference for what exists before changes
  - Document all endpoints in mcp_api_server_optimized.py
  - Save example responses for each endpoint
  - Store in file: current_api_documentation.md

## Phase 1: Foundation Setup

- Create mcp_server_v2.py implementing JSON-RPC 2.0 protocol
  - Purpose: Replace current pattern matching with standard JSON-RPC communication
  - Endpoints affected: All current endpoints will migrate to JSON-RPC format
  - Must support methods: initialize, tools/list, resources/list, prompts/list, tools/call
  - Add idempotency support: Store idempotency_key with results for 24 hours
  - Add X-Request-ID header propagation for tracing through system
  - Implement uniform error model: {"code": -32000, "message": "error", "data": {"type": "validation", "details": {}}}
  - Add request timeout: 30 seconds default, configurable per tool

- Create mcp_client_v2.py for hook integration
  - Purpose: Bridge between Claude Code hooks and MCP server
  - Must handle all 9 hook events: SessionStart, SessionEnd, PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, SubagentStop, PreCompact
  - Input: JSON from stdin as per Claude Code hook specification
  - Output: JSON response with continue, stopReason, suppressOutput, systemMessage fields

- Update database schema in /tmp/mcp_state.db
  - Purpose: Support new MCP features (resources, prompts, capabilities)
  - Add tables: capabilities, resources, prompts, resource_access_log
  - Maintain backward compatibility with existing activities, components, agent_states tables

- Create capability negotiation module
  - Purpose: Establish feature support between client and server at session start
  - Protocol version: 2025-06-18 (latest official MCP specification)
  - Negotiate support for: tools, resources, prompts, streaming, batch operations
  - Store negotiated capabilities in database with session_id

## Phase 2: Core MCP Primitives Implementation

- Implement Tools primitive with schema validation
  - Purpose: Replace pattern matching with properly defined tool schemas
  - Each tool must have: name, description, inputSchema (JSON Schema), outputSchema
  - Validation: Use jsonschema library for input/output validation
  - Migration: Convert existing 8 tools (log_activity, check_conflicts, register_component, update_status, heartbeat, request_collaboration, propose_decision, find_component_owner)
  - Complex activity: Requires deep system check of current tool implementations
  - Add dry_run parameter to all tools for safe testing without side effects
  - Use JSON Schema $ref for common fields (timestamp, agent_name, session_id)

- Implement Resources primitive
  - Purpose: Provide structured access to project data via URIs
  - URI schemes to support: file://, db://, api://, config://
  - Resource types: text, json, binary, schema
  - Access control: Read-only by default, write requires explicit permission
  - Examples:
    - file:///project/README.md - Project documentation
    - db://schema/complete - Full database schema
    - api://swagger/spec - API documentation
    - config://agents/supervisor - Agent configuration
  - Path protection for file:// URIs:
    - Normalize paths and resolve symlinks
    - Whitelist project root directory only
    - Blacklist: .git/, .env, *.key, id_rsa*, ~/.ssh/
    - Log all access attempts with success/failure

- Implement Prompts primitive
  - Purpose: Provide reusable command templates and workflows
  - Each prompt must have: name, description, arguments[], template
  - Support variable substitution in templates
  - Categories: deployment, testing, development, maintenance
  - Store prompts in database for dynamic updates

## Phase 3: Hook Integration

- Configure SessionStart hook for MCP initialization
  - Purpose: Establish MCP connection when Claude Code session begins
  - File: .claude/hooks/settings.json
  - Command: python3 mcp_client_v2.py init
  - Perform capability negotiation
  - Load available tools, resources, prompts into session context

- Configure PreToolUse hook for tool authorization
  - Purpose: Validate and authorize tool execution before it happens
  - Matcher: "mcp__*" to catch all MCP tools
  - Command: python3 mcp_client_v2.py validate-tool
  - Check tool permissions based on tool name and parameters
  - Return permission decision: allow or deny with reason

- Configure PostToolUse hook for result processing
  - Purpose: Log tool execution results and trigger follow-up actions
  - Matcher: "mcp__*" for MCP tools
  - Command: python3 mcp_client_v2.py process-result
  - Log to database with session_id, tool_name, input, output, timestamp
  - Check for errors and provide feedback to Claude

- Configure UserPromptSubmit hook for prompt suggestions
  - Purpose: Suggest relevant prompts based on user input
  - Command: python3 mcp_client_v2.py suggest-prompts
  - Analyze user intent from prompt text
  - Return matching prompts with descriptions

## Phase 4: Security and Authorization

- Implement OAuth 2.1 authentication for remote servers
  - Purpose: Required by MCP specification for HTTP transport as of June 2025
  - Follow RFC 8707 for Resource Indicators
  - MCP servers act as OAuth Resource Servers
  - Store OAuth tokens securely with encryption

- Implement consent flow for dangerous operations
  - Purpose: Prevent unauthorized execution of destructive operations
  - Operations requiring consent: delete, drop, remove, production deployments
  - Store consent decisions with expiry time
  - UI component in React dashboard for consent management

- Add path traversal protection
  - Purpose: Prevent access to files outside project directory
  - Validate all file:// URIs against project root
  - Block access to sensitive paths: .git, .env, private keys
  - Log all access attempts for audit

- Implement rate limiting for resource access
  - Purpose: Prevent resource exhaustion from excessive requests
  - Limits: 100 requests per minute per session
  - Cache frequently accessed resources
  - Return 429 status with retry-after header when limit exceeded

- Create audit logging system
  - Purpose: Track all MCP operations for compliance and debugging
  - Log format: timestamp, session_id, user, operation, parameters, result
  - Store in separate audit_log table
  - Retention: 30 days by default, configurable

## Phase 5: API Migration

- Update /api/mcp/status endpoint
  - Purpose: Include new MCP capabilities in status response
  - Add fields: capabilities, available_resources_count, available_prompts_count
  - Maintain backward compatibility with current response structure

- Create /api/mcp/resources endpoint
  - Purpose: List and access available resources
  - Methods: GET (list), GET with URI (fetch specific resource)
  - Response: JSON with resource metadata and content
  - Pagination: limit and offset parameters

- Create /api/mcp/prompts endpoint
  - Purpose: Discover and use prompt templates
  - Methods: GET (list all), GET by name, POST (execute with arguments)
  - Response: Prompt definition or execution result

- Create /api/mcp/capabilities endpoint
  - Purpose: Query current session capabilities
  - Method: GET
  - Response: Negotiated capabilities and protocol version

## Phase 6: Frontend Updates

- Update MultiTerminal.tsx to display MCP status
  - Purpose: Show users current MCP connection state and capabilities
  - Display: Protocol version, connected servers, available tools count
  - Location: In existing MCP Status widget

- Create ResourceExplorer component
  - Purpose: Browse and preview available resources
  - Features: Tree view for URIs, preview pane, search functionality
  - Location: New tab in main dashboard

- Create PromptLibrary component
  - Purpose: Browse and execute available prompts
  - Features: Category filter, search, parameter input form
  - Location: New tab in main dashboard

- Add MCP activity feed to dashboard
  - Purpose: Real-time display of MCP operations
  - Display: Tool executions, resource access, prompt usage
  - Update mechanism: WebSocket or polling fallback

## Phase 7: Testing and Validation

- Create comprehensive test suite for JSON-RPC communication
  - Purpose: Ensure protocol compliance
  - Test cases: Valid requests, malformed JSON, unknown methods, error handling
  - Framework: pytest with async support
  - Complex activity: Requires deep system check of all communication paths
  - Test idempotency: Same idempotency_key returns cached result
  - Test dry_run: Verify no state changes occur with dry_run=true

- Test tool migration from pattern matching to schema-based
  - Purpose: Ensure no functionality regression
  - Compare outputs: Old system vs new system for same inputs
  - Test all 8 existing tools with various parameter combinations

- Test resource access with different URI schemes
  - Purpose: Validate URI parsing and resource retrieval
  - Test cases: Valid URIs, invalid URIs, non-existent resources, access denied
  - Verify caching and rate limiting work correctly

- Test security measures
  - Purpose: Ensure system is secure against common attacks
  - Test cases: Path traversal attempts, SQL injection, command injection
  - Verify audit logging captures all attempts

## Phase 8: Documentation and Migration

- Create migration guide for existing system users
  - Purpose: Help users transition from current system to MCP-compliant version
  - Include: Configuration changes needed, new features available, breaking changes
  - Format: Step-by-step instructions with examples

- Document all MCP endpoints and their usage
  - Purpose: Enable developers to integrate with the system
  - Include: Request/response formats, authentication, error codes
  - Format: OpenAPI specification and markdown documentation

- Create troubleshooting guide
  - Purpose: Help diagnose common issues with MCP integration
  - Include: Connection problems, permission errors, performance issues
  - Format: FAQ style with solutions

- Write developer guide for creating custom MCP servers
  - Purpose: Enable extension of the system with new capabilities
  - Include: Protocol specification, example server implementation, best practices
  - Format: Tutorial with code examples

## Phase 9: Transport Layer Implementation

- Implement STDIO transport as primary mechanism
  - Purpose: Default transport mechanism per MCP specification
  - Bidirectional JSON-RPC messages over stdin/stdout
  - Required for local Claude Code integration

- Implement HTTP with Server-Sent Events (SSE)
  - Purpose: Support remote MCP servers
  - HTTP for requests, SSE for server-initiated messages
  - Required OAuth 2.1 authentication for security

- Add Streamable HTTP transport support
  - Purpose: Latest MCP specification update for improved efficiency
  - Replaces HTTP+SSE for better performance
  - Support JSON-RPC batching for multiple operations

## Phase 10: Industry Standard Compliance

- Add support for OpenAI MCP integration
  - Purpose: OpenAI adopted MCP in March 2025
  - Support ChatGPT desktop app format
  - Compatible with OpenAI Agents SDK

- Add support for Google Gemini MCP
  - Purpose: Google DeepMind confirmed support in April 2025
  - Follow Gemini-specific MCP extensions
  - Test with Gemini model endpoints

- Add Microsoft Copilot Studio compatibility
  - Purpose: Microsoft native MCP support as of May 2025
  - Support one-click server connections
  - Implement tracing and analytics hooks

## Phase 11: Performance Optimization

- Implement connection pooling for database
  - Purpose: Reduce connection overhead for frequent queries
  - Pool size: 10 connections minimum, 50 maximum
  - Connection timeout: 30 seconds
  - Current bottleneck: Single connection per request in mcp_api_server_optimized.py

- Add Redis caching for frequently accessed resources
  - Purpose: Reduce database load and improve response time
  - Cache TTL: 300 seconds for resources, 60 seconds for tool results
  - Cache key pattern: mcp:resource:{uri_hash}, mcp:tool:{tool_name}:{param_hash}
  - Cache idempotent results: Store by idempotency_key for 24 hours

- Optimize database queries with proper indexing
  - Purpose: Improve query performance for large datasets
  - Indexes needed: activities(timestamp, agent), resources(uri), prompts(category)
  - Complex activity: Requires analysis of query patterns from logs
  - Add created_at INTEGER epoch for fast time-based queries

- Implement WebSocket support for real-time updates
  - Purpose: Replace polling with efficient push mechanism
  - Endpoint: ws://localhost:8099/ws
  - Events: tool_executed, resource_updated, prompt_used
  - Fallback: Continue supporting HTTP polling for compatibility

- Add essential performance metrics
  - Purpose: Track system health and identify bottlenecks
  - Key metrics to collect:
    - tool_latency_ms per tool (p50, p95, p99)
    - tool_error_rate by error type
    - cache_hit_ratio for Redis
    - request_rate per endpoint
  - Store in time-series format for trending
  - Simple dashboard showing last 24 hours

## Phase 12: Migration and Cutover

- Direct migration from old to new system
  - Purpose: Clean switch to MCP v2 in development environment
  - Stop old mcp_api_server_optimized.py
  - Start new mcp_server_v2.py on same port 8099
  - Update all references in codebase

- Update all configuration files
  - Purpose: Point everything to new MCP implementation
  - Update claude_mcp_config.json
  - Update hook settings in .claude/hooks/settings.toml
  - Update frontend environment variables

- Verify complete system functionality
  - Purpose: Ensure everything works with new MCP
  - Test all agent communications
  - Verify frontend displays correctly
  - Check all tools execute properly
  - Confirm resources and prompts accessible

- Clean up old code
  - Purpose: Remove deprecated pattern matching system
  - Archive old mcp_bridge.py as mcp_bridge_legacy.py
  - Remove pattern matching functions
  - Update all imports and references

- Document migration completion
  - Purpose: Clear record of what changed
  - List all modified files
  - Document new endpoints
  - Update README with new architecture