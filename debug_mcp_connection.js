#!/usr/bin/env node
/**
 * Debug script per verificare la connessione MCP
 * Esegue test sistematici per identificare il problema
 */

const fetch = require('node-fetch');
const sqlite3 = require('sqlite3').verbose();

async function testAPI() {
    console.log('🔍 Testing MCP Connection Chain\n');

    // 1. Test API endpoint
    console.log('1️⃣  Testing API endpoint...');
    try {
        const response = await fetch('http://localhost:5001/api/mcp/status');
        const data = await response.json();
        console.log('✅ API responds:', {
            server_running: data.server_running,
            active_agents: data.stats?.active_agents,
            agent_count: data.agent_states?.length
        });

        // Check agent states
        if (data.agent_states && data.agent_states.length > 0) {
            console.log('   Agent states:');
            data.agent_states.slice(0, 3).forEach(agent => {
                console.log(`   - ${agent.agent}: ${agent.status}`);
            });
        }
    } catch (error) {
        console.log('❌ API Error:', error.message);
        return false;
    }

    // 2. Test Database directly
    console.log('\n2️⃣  Testing Database directly...');
    const db = new sqlite3.Database('mcp_system.db');

    return new Promise((resolve) => {
        db.all("SELECT agent, status FROM agent_states", (err, rows) => {
            if (err) {
                console.log('❌ Database Error:', err);
                resolve(false);
            } else {
                console.log('✅ Database has', rows.length, 'agents');
                rows.slice(0, 3).forEach(row => {
                    console.log(`   - ${row.agent}: ${row.status}`);
                });

                // 3. Test what frontend expects
                console.log('\n3️⃣  Frontend expectations:');
                console.log('   - Expects: agent_states array');
                console.log('   - Each agent needs: {agent, status, last_seen}');
                console.log('   - Status should be "active" for green badge');

                const activeCount = rows.filter(r => r.status === 'active').length;
                console.log(`\n✅ Summary: ${activeCount}/${rows.length} agents are active`);

                if (activeCount === rows.length) {
                    console.log('✅ All agents should show "MCP: Connected"');
                } else {
                    console.log('⚠️  Some agents may show "MCP: Disconnected"');
                }
            }
            db.close();
            resolve(true);
        });
    });
}

// Run if executed directly
if (require.main === module) {
    testAPI().then(success => {
        if (success) {
            console.log('\n✅ Backend configuration looks correct');
            console.log('📝 Next: Check browser console for frontend errors');
        } else {
            console.log('\n❌ Backend configuration has issues');
        }
    });
}

module.exports = { testAPI };