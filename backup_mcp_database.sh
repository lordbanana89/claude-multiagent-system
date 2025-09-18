#!/bin/bash

# MCP Database Backup Script
# Purpose: Create timestamped backups of MCP database before changes

# Configuration
DB_PATH="/tmp/mcp_state.db"
BACKUP_DIR="/tmp/mcp_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/mcp_state_${TIMESTAMP}.db.backup"

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database not found at $DB_PATH"
    exit 1
fi

# Create backup
echo "Creating backup of MCP database..."
echo "Source: $DB_PATH"
echo "Destination: $BACKUP_FILE"

# Use SQLite backup command for safe backup
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Check if backup was successful
if [ -f "$BACKUP_FILE" ]; then
    # Get file sizes
    ORIGINAL_SIZE=$(ls -lh "$DB_PATH" | awk '{print $5}')
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')

    echo "Backup successful!"
    echo "Original size: $ORIGINAL_SIZE"
    echo "Backup size: $BACKUP_SIZE"

    # Verify backup integrity
    echo "Verifying backup integrity..."
    if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo "Backup integrity check passed"
    else
        echo "Warning: Backup integrity check failed"
        exit 1
    fi

    # List recent backups
    echo ""
    echo "Recent backups (last 5):"
    ls -lt "$BACKUP_DIR"/*.db.backup 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ")"}'

    # Clean up old backups (keep last 10)
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*.db.backup 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 10 ]; then
        echo ""
        echo "Cleaning up old backups (keeping last 10)..."
        ls -t "$BACKUP_DIR"/*.db.backup | tail -n +11 | xargs rm -f
        echo "Cleanup complete"
    fi
else
    echo "Error: Backup failed"
    exit 1
fi

echo ""
echo "Backup completed: $BACKUP_FILE"