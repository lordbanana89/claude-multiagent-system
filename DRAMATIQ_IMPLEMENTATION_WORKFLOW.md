# 🚀 DRAMATIQ IMPLEMENTATION WORKFLOW

## 📋 PROGETTO: Sostituzione Sistema Queue Agent con Dramatiq

### 🎯 OBIETTIVO PRINCIPALE
Sostituire il sistema fragile di notifiche tmux subprocess con Dramatiq task queue per garantire affidabilità, retry automatico e scalabilità.

---

## 📊 TASK BREAKDOWN DETTAGLIATO

### **FASE 1: SETUP E PREPARAZIONE (1-2 giorni)**

#### **TASK 1.1: Environment Setup**
- **Responsabile**: Backend API Agent
- **Descrizione**: Installazione e configurazione Dramatiq + Redis
- **Deliverables**:
  - `pip install 'dramatiq[redis]'`
  - Verifica Redis connection
  - Test basic actor functionality
- **Criteri Successo**: Dramatiq workers avviabili senza errori
- **Dipendenze**: Nessuna
- **Priority**: HIGH

#### **TASK 1.2: Project Structure Analysis**
- **Responsabile**: Database Agent
- **Descrizione**: Analisi dettagliata file esistenti per integration points
- **Deliverables**:
  - Mapping completo functions da sostituire
  - Identificazione dependencies
  - Schema database modifications needed
- **Criteri Successo**: Documento completo integration points
- **Dipendenze**: Nessuna
- **Priority**: HIGH

#### **TASK 1.3: Redis Configuration Optimization**
- **Responsabile**: Backend API Agent
- **Descrizione**: Ottimizzazione Redis per task queue workload
- **Deliverables**:
  - Redis config file optimized
  - Memory allocation settings
  - Persistence configuration
- **Criteri Successo**: Redis performance metrics baseline
- **Dipendenze**: TASK 1.1
- **Priority**: MEDIUM

---

### **FASE 2: CORE DRAMATIQ ACTORS (2-3 giorni)**

#### **TASK 2.1: Core Actor Framework**
- **Responsabile**: Backend API Agent
- **Descrizione**: Creazione sistema base Dramatiq actors
- **Deliverables**:
  - `dramatiq_queue_manager.py` - Core actor definitions
  - `process_agent_request` actor
  - `notify_supervisor_request` actor
  - `execute_approved_command` actor
- **Criteri Successo**: Actors processano test messages
- **Dipendenze**: TASK 1.1, TASK 1.2
- **Priority**: HIGH

#### **TASK 2.2: Notification System Replacement**
- **Responsabile**: Frontend UI Agent
- **Descrizione**: Sostituisce `_notify_supervisor_new_request` con Dramatiq
- **Deliverables**:
  - Robust tmux notification actor
  - Error handling e retry logic
  - Message formatting standardization
- **Criteri Successo**: 100% message delivery guarantee
- **Dipendenze**: TASK 2.1
- **Priority**: HIGH

#### **TASK 2.3: Request Processing Pipeline**
- **Responsabile**: Backend API Agent
- **Descrizione**: Pipeline completa processing richieste agent
- **Deliverables**:
  - Auto-approval logic in Dramatiq
  - Manual approval workflow
  - Execution confirmation system
- **Criteri Successo**: Zero pending requests accumulation
- **Dipendenze**: TASK 2.1, TASK 2.2
- **Priority**: HIGH

#### **TASK 2.4: Error Handling & Recovery**
- **Responsabile**: Testing Agent
- **Descrizione**: Sistema robusto gestione errori e recovery
- **Deliverables**:
  - Dead letter queue implementation
  - Automatic retry with exponential backoff
  - Failure notification system
- **Criteri Successo**: Nessun message perso durante failures
- **Dipendenze**: TASK 2.1, TASK 2.2, TASK 2.3
- **Priority**: MEDIUM

---

### **FASE 3: INTEGRATION E TESTING (2-3 giorni)**

#### **TASK 3.1: AgentRequestManager Integration**
- **Responsabile**: Database Agent
- **Descrizione**: Integrazione Dramatiq con sistema esistente AgentRequestManager
- **Deliverables**:
  - Modified `agent_request_manager.py`
  - Dramatiq queue integration
  - Backward compatibility maintenance
- **Criteri Successo**: Existing functionality unchanged + Dramatiq benefits
- **Dipendenze**: TASK 2.1, TASK 2.3
- **Priority**: HIGH

#### **TASK 3.2: AgentRequestMonitor Replacement**
- **Responsabile**: Backend API Agent
- **Descrizione**: Sostituzione completa `agent_request_monitor.py`
- **Deliverables**:
  - New `dramatiq_request_monitor.py`
  - Parallel deployment capability
  - Performance comparison tools
- **Criteri Successo**: Monitor rileva 100% requests + processing via Dramatiq
- **Dipendenze**: TASK 2.1, TASK 2.2, TASK 3.1
- **Priority**: HIGH

#### **TASK 3.3: Streamlit UI Integration**
- **Responsabile**: Frontend UI Agent
- **Descrizione**: Aggiorna interfaccia web per Dramatiq monitoring
- **Deliverables**:
  - Dramatiq queue status display
  - Worker performance metrics
  - Real-time task processing view
- **Criteri Successo**: Admin può monitorare Dramatiq via web interface
- **Dipendenze**: TASK 3.1, TASK 3.2
- **Priority**: MEDIUM

#### **TASK 3.4: Performance Testing**
- **Responsabile**: Testing Agent
- **Descrizione**: Testing completo performance Dramatiq vs sistema attuale
- **Deliverables**:
  - Load testing suite
  - Performance benchmarks
  - Reliability metrics comparison
- **Criteri Successo**: Dramatiq 10x better reliability metrics
- **Dipendenze**: TASK 3.1, TASK 3.2, TASK 3.3
- **Priority**: MEDIUM

---

### **FASE 4: DEPLOYMENT E CUTOVER (1-2 giorni)**

#### **TASK 4.1: Parallel Deployment**
- **Responsabile**: Supervisor Agent
- **Descrizione**: Deploy Dramatiq in parallel con sistema esistente
- **Deliverables**:
  - Feature flag system
  - A/B testing configuration
  - Rollback procedures
- **Criteri Successo**: Both systems running simultaneously
- **Dipendenze**: TASK 3.1, TASK 3.2, TASK 3.4
- **Priority**: HIGH

#### **TASK 4.2: Migration Testing**
- **Responsabile**: Testing Agent
- **Descrizione**: Testing completo migration path
- **Deliverables**:
  - Migration test scripts
  - Data integrity verification
  - End-to-end workflow testing
- **Criteri Successo**: Zero data loss durante migration
- **Dipendenze**: TASK 4.1
- **Priority**: HIGH

#### **TASK 4.3: Production Cutover**
- **Responsabile**: Master Agent
- **Descrizione**: Switch definitivo a Dramatiq system
- **Deliverables**:
  - Legacy system shutdown
  - Dramatiq full activation
  - Monitor system health
- **Criteri Successo**: Sistema operativo al 100% su Dramatiq
- **Dipendenze**: TASK 4.1, TASK 4.2
- **Priority**: HIGH

#### **TASK 4.4: Legacy Cleanup**
- **Responsabile**: Database Agent
- **Descrizione**: Rimozione codice legacy e cleanup
- **Deliverables**:
  - Removed old tmux subprocess code
  - Updated documentation
  - Code repository cleanup
- **Criteri Successo**: Codebase clean e optimized
- **Dipendenze**: TASK 4.3
- **Priority**: LOW

---

### **FASE 5: MONITORING E OPTIMIZATION (Ongoing)**

#### **TASK 5.1: Production Monitoring**
- **Responsabile**: Supervisor Agent
- **Descrizione**: Monitoring continuo sistema Dramatiq
- **Deliverables**:
  - Performance dashboards
  - Alert system setup
  - Health check automation
- **Criteri Successo**: 99.9% uptime guarantee
- **Dipendenze**: TASK 4.3
- **Priority**: MEDIUM

#### **TASK 5.2: Performance Optimization**
- **Responsabile**: Backend API Agent
- **Descrizione**: Ottimizzazioni continue performance
- **Deliverables**:
  - Worker scaling automation
  - Queue optimization
  - Memory usage optimization
- **Criteri Successo**: Consistent performance under load
- **Dipendenze**: TASK 5.1
- **Priority**: LOW

---

## 🎯 CRITICAL PATH

```
TASK 1.1 → TASK 2.1 → TASK 2.2 → TASK 2.3 → TASK 3.1 → TASK 3.2 → TASK 4.1 → TASK 4.2 → TASK 4.3
```

## ⏱️ TIMELINE ESTIMATE

- **FASE 1**: 1-2 giorni
- **FASE 2**: 2-3 giorni
- **FASE 3**: 2-3 giorni
- **FASE 4**: 1-2 giorni
- **FASE 5**: Ongoing

**TOTALE**: 6-10 giorni lavorativi

## 🔍 SUCCESS METRICS

1. **Reliability**: 100% message delivery (vs attuale ~60%)
2. **Performance**: <1s response time per notifications
3. **Scalability**: Support 100+ concurrent agent requests
4. **Zero Downtime**: Migration senza interruzioni servizio
5. **Error Rate**: <0.1% task failures

## 🚨 RISK MITIGATION

- **Parallel Deployment**: Sistema legacy come fallback
- **Feature Flags**: Switch immediato in caso problemi
- **Comprehensive Testing**: Ogni component testato isolatamente
- **Rollback Plan**: Procedure automatizzate rollback

---

## 📞 COMUNICAZIONE

- **Daily Standups**: Supervisor coordina progresso
- **Milestone Reviews**: Master Agent approva deliverables
- **Emergency Escalation**: Immediate notification su blockers

---

**Documento creato**: 2025-09-17
**Owner**: Master Agent
**Approved by**: [Da definire]
**Version**: 1.0