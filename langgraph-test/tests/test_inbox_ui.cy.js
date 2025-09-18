/**
 * UI Testing Suite for Inbox System Interface
 * End-to-End tests using Cypress for inbox user interface validation
 */

describe('Inbox System UI Tests', () => {
  const baseUrl = 'http://localhost:3000'; // Adjust based on actual UI server
  const testAgent = 'ui-test-agent';

  beforeEach(() => {
    // Setup test environment before each test
    cy.visit(`${baseUrl}/inbox`);

    // Mock authentication if needed
    cy.window().then((win) => {
      win.localStorage.setItem('authToken', 'test-token');
      win.localStorage.setItem('agentId', testAgent);
    });

    // Intercept API calls for consistent testing
    cy.intercept('GET', `/api/inbox/${testAgent}`, {
      fixture: 'inbox-messages.json'
    }).as('getInboxMessages');

    cy.intercept('POST', '/api/messages/*/status', {
      statusCode: 200,
      body: { success: true }
    }).as('updateMessageStatus');

    cy.intercept('POST', '/api/messages/*/archive', {
      statusCode: 200,
      body: { success: true }
    }).as('archiveMessage');
  });

  describe('Inbox Layout and Navigation', () => {
    it('should display inbox header with agent information', () => {
      cy.get('[data-testid="inbox-header"]').should('be.visible');
      cy.get('[data-testid="agent-id"]').should('contain', testAgent);
      cy.get('[data-testid="inbox-title"]').should('contain', 'Inbox');
    });

    it('should show message count and statistics', () => {
      cy.get('[data-testid="message-count"]').should('be.visible');
      cy.get('[data-testid="unread-count"]').should('be.visible');
      cy.get('[data-testid="inbox-stats"]').should('be.visible');
    });

    it('should display navigation tabs for different message categories', () => {
      const categories = ['all', 'urgent', 'tasks', 'questions', 'information'];

      categories.forEach(category => {
        cy.get(`[data-testid="tab-${category}"]`)
          .should('be.visible')
          .and('contain', category);
      });
    });

    it('should have working search functionality', () => {
      cy.get('[data-testid="message-search"]').should('be.visible');
      cy.get('[data-testid="search-input"]').type('test message');
      cy.get('[data-testid="search-button"]').click();

      // Should filter messages based on search
      cy.get('[data-testid="message-list"]').should('be.visible');
    });
  });

  describe('Message List Display', () => {
    it('should display messages in list format', () => {
      cy.wait('@getInboxMessages');

      cy.get('[data-testid="message-list"]').should('be.visible');
      cy.get('[data-testid="message-item"]').should('have.length.greaterThan', 0);
    });

    it('should show message preview information', () => {
      cy.get('[data-testid="message-item"]').first().within(() => {
        cy.get('[data-testid="message-sender"]').should('be.visible');
        cy.get('[data-testid="message-subject"]').should('be.visible');
        cy.get('[data-testid="message-preview"]').should('be.visible');
        cy.get('[data-testid="message-timestamp"]').should('be.visible');
        cy.get('[data-testid="message-priority"]').should('be.visible');
      });
    });

    it('should highlight unread messages', () => {
      cy.get('[data-testid="message-item"]')
        .filter('.unread')
        .should('have.class', 'unread-message');
    });

    it('should show priority indicators correctly', () => {
      // Test urgent messages have red indicator
      cy.get('[data-testid="message-item"]')
        .filter('[data-priority="urgent"]')
        .find('[data-testid="priority-indicator"]')
        .should('have.class', 'priority-urgent');

      // Test high priority messages have orange indicator
      cy.get('[data-testid="message-item"]')
        .filter('[data-priority="high"]')
        .find('[data-testid="priority-indicator"]')
        .should('have.class', 'priority-high');
    });
  });

  describe('Message Interaction', () => {
    it('should open message details when clicked', () => {
      cy.get('[data-testid="message-item"]').first().click();

      cy.get('[data-testid="message-modal"]').should('be.visible');
      cy.get('[data-testid="message-full-content"]').should('be.visible');
      cy.get('[data-testid="message-metadata"]').should('be.visible');
    });

    it('should mark message as read when opened', () => {
      cy.get('[data-testid="message-item"]')
        .filter('.unread')
        .first()
        .click();

      cy.wait('@updateMessageStatus');

      // Message should no longer have unread styling
      cy.get('[data-testid="message-modal"]').within(() => {
        cy.get('[data-testid="close-modal"]').click();
      });

      cy.get('[data-testid="message-item"]')
        .first()
        .should('not.have.class', 'unread');
    });

    it('should provide message action buttons', () => {
      cy.get('[data-testid="message-item"]').first().click();

      cy.get('[data-testid="message-modal"]').within(() => {
        cy.get('[data-testid="action-acknowledge"]').should('be.visible');
        cy.get('[data-testid="action-respond"]').should('be.visible');
        cy.get('[data-testid="action-archive"]').should('be.visible');
        cy.get('[data-testid="action-escalate"]').should('be.visible');
      });
    });

    it('should handle message acknowledgment', () => {
      cy.get('[data-testid="message-item"]').first().click();

      cy.get('[data-testid="action-acknowledge"]').click();
      cy.wait('@updateMessageStatus');

      // Should show success message
      cy.get('[data-testid="success-toast"]')
        .should('be.visible')
        .and('contain', 'Message acknowledged');
    });

    it('should open response composer', () => {
      cy.get('[data-testid="message-item"]').first().click();

      cy.get('[data-testid="action-respond"]').click();

      cy.get('[data-testid="response-composer"]').should('be.visible');
      cy.get('[data-testid="response-textarea"]').should('be.visible');
      cy.get('[data-testid="send-response"]').should('be.visible');
      cy.get('[data-testid="cancel-response"]').should('be.visible');
    });

    it('should send response message', () => {
      cy.intercept('POST', '/api/messages', {
        statusCode: 201,
        body: { success: true, message_id: 'response-001' }
      }).as('sendResponse');

      cy.get('[data-testid="message-item"]').first().click();
      cy.get('[data-testid="action-respond"]').click();

      cy.get('[data-testid="response-textarea"]')
        .type('This is a test response message');

      cy.get('[data-testid="send-response"]').click();
      cy.wait('@sendResponse');

      cy.get('[data-testid="success-toast"]')
        .should('be.visible')
        .and('contain', 'Response sent');
    });

    it('should archive messages', () => {
      cy.get('[data-testid="message-item"]').first().click();

      cy.get('[data-testid="action-archive"]').click();

      // Should show confirmation dialog
      cy.get('[data-testid="confirm-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-archive"]').click();

      cy.wait('@archiveMessage');

      cy.get('[data-testid="success-toast"]')
        .should('be.visible')
        .and('contain', 'Message archived');
    });
  });

  describe('Bulk Operations', () => {
    it('should allow selecting multiple messages', () => {
      cy.get('[data-testid="select-all-checkbox"]').check();

      cy.get('[data-testid="message-item"]').each(($el) => {
        cy.wrap($el).find('[data-testid="message-checkbox"]').should('be.checked');
      });
    });

    it('should show bulk action toolbar when messages selected', () => {
      cy.get('[data-testid="message-checkbox"]').first().check();
      cy.get('[data-testid="message-checkbox"]').eq(1).check();

      cy.get('[data-testid="bulk-actions-toolbar"]').should('be.visible');
      cy.get('[data-testid="bulk-action-count"]').should('contain', '2 selected');
    });

    it('should perform bulk archive operation', () => {
      cy.intercept('POST', '/api/messages/bulk/archive', {
        statusCode: 200,
        body: { success: true, archived_count: 2 }
      }).as('bulkArchive');

      cy.get('[data-testid="message-checkbox"]').first().check();
      cy.get('[data-testid="message-checkbox"]').eq(1).check();

      cy.get('[data-testid="bulk-action-archive"]').click();
      cy.get('[data-testid="confirm-bulk-archive"]').click();

      cy.wait('@bulkArchive');

      cy.get('[data-testid="success-toast"]')
        .should('contain', '2 messages archived');
    });

    it('should perform bulk mark as read operation', () => {
      cy.intercept('POST', '/api/messages/bulk/mark-read', {
        statusCode: 200,
        body: { success: true, updated_count: 3 }
      }).as('bulkMarkRead');

      cy.get('[data-testid="select-all-checkbox"]').check();
      cy.get('[data-testid="bulk-action-mark-read"]').click();

      cy.wait('@bulkMarkRead');

      cy.get('[data-testid="success-toast"]')
        .should('contain', 'marked as read');
    });
  });

  describe('Filtering and Sorting', () => {
    it('should filter messages by category', () => {
      cy.get('[data-testid="tab-urgent"]').click();

      cy.get('[data-testid="message-item"]').each(($el) => {
        cy.wrap($el).should('have.attr', 'data-category', 'urgent');
      });
    });

    it('should filter messages by priority', () => {
      cy.get('[data-testid="priority-filter"]').select('high');

      cy.get('[data-testid="message-item"]').each(($el) => {
        cy.wrap($el).should('have.attr', 'data-priority', 'high');
      });
    });

    it('should sort messages by date', () => {
      cy.get('[data-testid="sort-selector"]').select('date-desc');

      // Verify messages are sorted by newest first
      cy.get('[data-testid="message-timestamp"]')
        .then(($timestamps) => {
          const timestamps = Array.from($timestamps).map(el => new Date(el.textContent));
          const sortedTimestamps = [...timestamps].sort((a, b) => b - a);
          expect(timestamps).to.deep.equal(sortedTimestamps);
        });
    });

    it('should sort messages by priority', () => {
      cy.get('[data-testid="sort-selector"]').select('priority');

      // Verify urgent messages appear first
      cy.get('[data-testid="message-item"]')
        .first()
        .should('have.attr', 'data-priority', 'urgent');
    });
  });

  describe('Real-time Updates', () => {
    it('should update message count when new message arrives', () => {
      cy.get('[data-testid="message-count"]').invoke('text').then((initialCount) => {
        // Simulate new message via WebSocket
        cy.window().then((win) => {
          win.dispatchEvent(new CustomEvent('new-message', {
            detail: {
              message_id: 'realtime-001',
              from_agent: 'realtime-sender',
              content: 'Real-time test message'
            }
          }));
        });

        // Message count should increase
        cy.get('[data-testid="message-count"]')
          .should('not.contain', initialCount);
      });
    });

    it('should show notification for new urgent messages', () => {
      cy.window().then((win) => {
        win.dispatchEvent(new CustomEvent('new-urgent-message', {
          detail: {
            message_id: 'urgent-realtime-001',
            from_agent: 'urgent-sender',
            content: 'URGENT: Critical system alert',
            priority: 'urgent'
          }
        }));
      });

      cy.get('[data-testid="urgent-notification"]')
        .should('be.visible')
        .and('contain', 'New urgent message');
    });

    it('should update message status in real-time', () => {
      cy.window().then((win) => {
        win.dispatchEvent(new CustomEvent('message-status-update', {
          detail: {
            message_id: 'msg-001',
            new_status: 'acknowledged',
            agent_id: testAgent
          }
        }));
      });

      cy.get('[data-testid="message-item"][data-message-id="msg-001"]')
        .find('[data-testid="message-status"]')
        .should('contain', 'acknowledged');
    });
  });

  describe('Accessibility', () => {
    it('should be keyboard navigable', () => {
      cy.get('body').tab();
      cy.focused().should('have.attr', 'data-testid', 'message-search');

      cy.focused().tab();
      cy.focused().should('have.attr', 'data-testid').and('match', /tab-/);

      cy.focused().tab();
      cy.focused().should('have.attr', 'data-testid', 'message-item');
    });

    it('should have proper ARIA labels', () => {
      cy.get('[data-testid="message-item"]')
        .first()
        .should('have.attr', 'role', 'listitem')
        .and('have.attr', 'aria-label');

      cy.get('[data-testid="message-checkbox"]')
        .first()
        .should('have.attr', 'aria-label', 'Select message');
    });

    it('should support screen reader announcements', () => {
      cy.get('[data-testid="message-item"]').first().click();
      cy.get('[data-testid="action-acknowledge"]').click();

      cy.get('[role="status"]')
        .should('contain', 'Message acknowledged successfully');
    });
  });

  describe('Error Handling', () => {
    it('should show error message when API fails', () => {
      cy.intercept('GET', `/api/inbox/${testAgent}`, {
        statusCode: 500,
        body: { error: 'Internal server error' }
      }).as('getInboxError');

      cy.reload();
      cy.wait('@getInboxError');

      cy.get('[data-testid="error-message"]')
        .should('be.visible')
        .and('contain', 'Failed to load messages');
    });

    it('should handle network connectivity issues', () => {
      cy.intercept('POST', '/api/messages/*/status', {
        forceNetworkError: true
      }).as('networkError');

      cy.get('[data-testid="message-item"]').first().click();
      cy.get('[data-testid="action-acknowledge"]').click();

      cy.wait('@networkError');

      cy.get('[data-testid="error-toast"]')
        .should('be.visible')
        .and('contain', 'Network error');
    });

    it('should show retry option for failed operations', () => {
      cy.intercept('POST', '/api/messages/*/archive', {
        statusCode: 500,
        body: { error: 'Server error' }
      }).as('archiveError');

      cy.get('[data-testid="message-item"]').first().click();
      cy.get('[data-testid="action-archive"]').click();
      cy.get('[data-testid="confirm-archive"]').click();

      cy.wait('@archiveError');

      cy.get('[data-testid="retry-button"]').should('be.visible');
    });
  });

  describe('Performance', () => {
    it('should load messages within acceptable time', () => {
      const startTime = Date.now();

      cy.visit(`${baseUrl}/inbox`);
      cy.wait('@getInboxMessages');

      cy.get('[data-testid="message-list"]').should('be.visible');

      cy.then(() => {
        const loadTime = Date.now() - startTime;
        expect(loadTime).to.be.lessThan(2000); // 2 seconds max
      });
    });

    it('should handle large message lists efficiently', () => {
      // Mock large dataset
      cy.intercept('GET', `/api/inbox/${testAgent}`, {
        fixture: 'large-inbox-messages.json'
      }).as('getLargeInbox');

      cy.reload();
      cy.wait('@getLargeInbox');

      // Should implement virtual scrolling for performance
      cy.get('[data-testid="message-list"]').should('be.visible');
      cy.get('[data-testid="message-item"]').should('have.length.lessThan', 50); // Virtual scrolling
    });
  });
});

// Fixture files would be created at:
// cypress/fixtures/inbox-messages.json
// cypress/fixtures/large-inbox-messages.json