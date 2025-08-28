class InvoicePOMatcher {
    constructor() {
        this.sessionId = null;
        this.apiBase = 'http://localhost:5000/api';
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const sendButton = document.getElementById('send-button');
        const queryInput = document.getElementById('query-input');
        const quickButtons = document.querySelectorAll('.quick-btn');

        sendButton.addEventListener('click', () => this.sendQuery());
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendQuery();
        });

        quickButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                queryInput.value = query;
                this.sendQuery();
            });
        });
    }

    async sendQuery() {
        const queryInput = document.getElementById('query-input');
        const query = queryInput.value.trim();
        
        if (!query) return;

        this.addMessage(query, 'user');
        queryInput.value = '';
        
        // Show loading
        const loadingId = this.addMessage('🤔 Analyzing... <div class="loading"></div>', 'system');
        
        try {
            const response = await fetch(`${this.apiBase}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    session_id: this.sessionId
                })
            });

            const result = await response.json();
            
            // Update session ID
            if (result.session_id) {
                this.sessionId = result.session_id;
                document.getElementById('session-id').textContent = 
                    result.session_id.substring(0, 8) + '...';
            }

            // Remove loading message
            this.removeMessage(loadingId);
            
            // Display results
            this.displayResults(result);
            
            // Update audit log
            this.updateAuditLog(result.audit_trail);
            
        } catch (error) {
            this.removeMessage(loadingId);
            this.addMessage(`❌ Error: ${error.message}`, 'system');
        }
    }

    displayResults(result) {
        let html = `
            <div class="response-section">
                <h4>📋 Analysis Results</h4>
                <p>${result.explanation}</p>
            </div>
        `;

        if (result.evidence && Object.keys(result.evidence).length > 0) {
            html += `
                <div class="evidence-section">
                    <div class="evidence-title">📊 Evidence</div>
                    ${this.formatEvidence(result.evidence)}
                </div>
            `;
        }

        if (result.match_score !== undefined) {
            const scoreClass = result.match_score > 0.7 ? 'high' : 
                             result.match_score > 0.4 ? 'medium' : 'low';
            html += `
                <div class="match-score ${scoreClass}">
                    Match Score: ${(result.match_score * 100).toFixed(0)}%
                </div>
            `;
        }

        html += `
            <div class="confidence-section">
                <strong>Verifier Confidence:</strong> ${(result.verifier_confidence * 100).toFixed(0)}%
            </div>
        `;

        if (result.recommendations && result.recommendations.length > 0) {
            html += `
                <div class="recommendations-section">
                    <strong>🎯 Recommendations:</strong>
                    <ul>
                        ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Add approval actions if applicable
        if (this.isApprovableQuery(result)) {
            html += this.generateApprovalActions(result);
        }

        this.addMessage(html, 'system');
    }

    formatEvidence(evidence) {
        let html = '<div class="evidence-grid">';
        
        for (const [key, value] of Object.entries(evidence)) {
            if (value !== null && value !== undefined) {
                html += `
                    <div class="evidence-item">
                        <strong>${key.replace(/_/g, ' ').toUpperCase()}:</strong> ${value}
                    </div>
                `;
            }
        }
        
        html += '</div>';
        return html;
    }

    isApprovableQuery(result) {
        return result.query_plan && 
               result.query_plan.query_type === 'invoice_analysis' &&
               !result.requires_human_review;
    }

    generateApprovalActions(result) {
        // Extract invoice ID from agent results
        let invoiceId = 'INV-123'; // Default fallback
        if (result.agent_results && result.agent_results.po_matching && 
            result.agent_results.po_matching.invoice) {
            invoiceId = result.agent_results.po_matching.invoice.invoice_id;
        }

        return `
            <div class="approval-actions">
                <h5>⚡ Available Actions</h5>
                <button class="approval-btn approve-btn" onclick="app.approveInvoice('${invoiceId}')">
                    ✅ Approve Invoice
                </button>
                <button class="approval-btn reject-btn" onclick="app.rejectInvoice('${invoiceId}')">
                    ❌ Request Review
                </button>
            </div>
        `;
    }

    async approveInvoice(invoiceId) {
        try {
            const response = await fetch(`${this.apiBase}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    invoice_id: invoiceId,
                    session_id: this.sessionId
                })
            });

            const result = await response.json();
            this.addMessage(`✅ ${result.message}`, 'system');
            
        } catch (error) {
            this.addMessage(`❌ Approval failed: ${error.message}`, 'system');
        }
    }

    rejectInvoice(invoiceId) {
        this.addMessage(`📝 Invoice ${invoiceId} has been flagged for manual review.`, 'system');
    }

    addMessage(content, type) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageId = 'msg-' + Date.now();
        
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message ${type}-message`;
        messageDiv.innerHTML = content;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageId;
    }

    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }

    updateAuditLog(auditTrail) {
        if (!auditTrail || auditTrail.length === 0) return;
        
        const auditLog = document.getElementById('audit-log');
        auditLog.innerHTML = '';
        
        // Show last 5 audit entries
        const recentEntries = auditTrail.slice(-5).reverse();
        
        recentEntries.forEach(entry => {
            const auditItem = document.createElement('div');
            auditItem.className = 'audit-item';
            
            const timestamp = new Date(entry.timestamp).toLocaleTimeString();
            auditItem.innerHTML = `
                <div class="timestamp">${timestamp}</div>
                <div class="agent">${entry.agent}</div>
                <div class="action">${entry.action_type}</div>
            `;
            
            auditLog.appendChild(auditItem);
        });
    }
}

// Initialize the application
const app = new InvoicePOMatcher();

// Demo data population
document.addEventListener('DOMContentLoaded', () => {
    // Add welcome message
    setTimeout(() => {
        app.addMessage(`
            <h4>🤖 Welcome to Invoice-PO Matcher!</h4>
            <p>I'm an AI system that can help you understand why invoices were flagged and assist with approvals.</p>
            <p><strong>Try asking:</strong></p>
            <ul>
                <li>"Why was invoice INV-123 flagged?"</li>
                <li>"Show me all discrepancies for INV-123"</li>
                <li>"Approve invoice INV-123"</li>
            </ul>
        `, 'system');
    }, 500);
});