#!/bin/bash
# Multi-Agent System Control Script

AGENTS_DIR="/Users/erik/Desktop/claude-multiagent-system"

case "$1" in
    start)
        echo "Starting Multi-Agent System..."

        # Start agent responders
        echo "Starting agent responders..."
        bash "$AGENTS_DIR/start_all_responders.sh"
        sleep 2

        # Start supervisor daemon
        echo "Starting supervisor daemon..."
        python3 "$AGENTS_DIR/supervisor_daemon.py" > /tmp/supervisor.log 2>&1 &
        echo "  Supervisor PID: $!"
        sleep 2

        echo "System started successfully!"
        python3 "$AGENTS_DIR/check_status.py"
        ;;

    stop)
        echo "Stopping Multi-Agent System..."

        # Kill supervisor daemon
        pkill -f supervisor_daemon
        echo "Supervisor daemon stopped"

        # Kill agent responders
        pkill -f agent_responder
        echo "Agent responders stopped"

        echo "System stopped"
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    status)
        python3 "$AGENTS_DIR/check_status.py"
        ;;

    monitor)
        python3 "$AGENTS_DIR/monitor_dashboard.py"
        ;;

    logs)
        echo "=== Supervisor Log ==="
        tail -20 /tmp/supervisor.log
        echo ""
        echo "=== Agent Logs ==="
        for agent in master backend-api database frontend-ui; do
            if [ -f "/tmp/${agent}.log" ]; then
                echo "--- $agent ---"
                tail -5 "/tmp/${agent}.log"
            fi
        done
        ;;

    clean)
        echo "Cleaning system..."
        rm -f /tmp/supervisor.log
        rm -f /tmp/*.log
        rm -f "$AGENTS_DIR/supervisor_state.json"
        echo "  Old Database: $(sqlite3 "$AGENTS_DIR/langgraph-test/shared_inbox.db" 'SELECT COUNT(*) FROM inbox;') tasks"
        sqlite3 "$AGENTS_DIR/langgraph-test/shared_inbox.db" "DELETE FROM inbox; DELETE FROM heartbeat; DELETE FROM coordination_log;"
        echo "  Database cleaned"
        ;;

    *)
        echo "Multi-Agent System Control"
        echo "Usage: $0 {start|stop|restart|status|monitor|logs|clean}"
        echo ""
        echo "  start   - Start all agents and supervisor"
        echo "  stop    - Stop all agents and supervisor"
        echo "  restart - Restart the system"
        echo "  status  - Show current system status"
        echo "  monitor - Launch interactive dashboard"
        echo "  logs    - Show recent logs"
        echo "  clean   - Clean database and logs"
        exit 1
        ;;
esac