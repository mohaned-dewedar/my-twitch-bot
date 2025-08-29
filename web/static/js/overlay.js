/**
 * CherryBott Overlay JavaScript
 * Handles auto-refresh, animations, and dynamic updates
 */

class OverlayManager {
    constructor(config = {}) {
        this.config = {
            refreshInterval: config.refreshInterval || 15000,
            apiUrl: config.apiUrl || '',
            enableAnimations: config.enableAnimations !== false,
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 5000
        };
        
        this.retryCount = 0;
        this.refreshTimer = null;
        this.lastUpdateTime = Date.now();
        
        this.init();
    }
    
    init() {
        this.setupAutoRefresh();
        this.setupAnimations();
        this.setupErrorHandling();
        
        console.log('CherryBott Overlay initialized');
    }
    
    setupAutoRefresh() {
        if (!this.config.apiUrl) return;
        
        this.refreshTimer = setInterval(() => {
            this.refreshData();
        }, this.config.refreshInterval);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
            }
        });
    }
    
    async refreshData() {
        try {
            const response = await fetch(this.config.apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateLeaderboard(data);
            this.retryCount = 0; // Reset retry count on success
            
        } catch (error) {
            console.warn('Failed to refresh data:', error);
            this.handleRefreshError(error);
        }
    }
    
    updateLeaderboard(data) {
        // For now, just reload the page to update content
        // In future versions, we could update the DOM dynamically
        if (this.hasDataChanged(data)) {
            this.fadeOut(() => {
                window.location.reload();
            });
        }
    }
    
    hasDataChanged(newData) {
        // Simple check - in production, we'd store previous data and compare
        const now = Date.now();
        const timeSinceLastUpdate = now - this.lastUpdateTime;
        
        // Only refresh if enough time has passed
        if (timeSinceLastUpdate > this.config.refreshInterval * 0.8) {
            this.lastUpdateTime = now;
            return true;
        }
        
        return false;
    }
    
    handleRefreshError(error) {
        this.retryCount++;
        
        if (this.retryCount >= this.config.maxRetries) {
            console.error('Max retries reached. Stopping auto-refresh.');
            this.showErrorIndicator();
            return;
        }
        
        // Exponential backoff for retries
        const delay = this.config.retryDelay * Math.pow(2, this.retryCount - 1);
        setTimeout(() => {
            this.refreshData();
        }, delay);
    }
    
    setupAnimations() {
        if (!this.config.enableAnimations) return;
        
        // Stagger entry animations
        const entries = document.querySelectorAll('.leaderboard-entry');
        entries.forEach((entry, index) => {
            entry.style.animationDelay = `${index * 0.1}s`;
            entry.classList.add('fade-in');
        });
        
        // Add hover effects
        entries.forEach(entry => {
            entry.addEventListener('mouseenter', () => {
                if (this.config.enableAnimations) {
                    entry.style.transform = 'translateX(5px) scale(1.02)';
                }
            });
            
            entry.addEventListener('mouseleave', () => {
                entry.style.transform = '';
            });
        });
    }
    
    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Overlay error:', event.error);
        });
        
        // Handle network status
        window.addEventListener('online', () => {
            console.log('Connection restored');
            this.hideErrorIndicator();
            this.refreshData();
        });
        
        window.addEventListener('offline', () => {
            console.warn('Connection lost');
            this.showErrorIndicator();
        });
    }
    
    fadeOut(callback) {
        if (!this.config.enableAnimations) {
            callback();
            return;
        }
        
        const container = document.querySelector('.overlay-container');
        if (container) {
            container.style.transition = 'opacity 0.3s ease-out';
            container.style.opacity = '0';
            
            setTimeout(callback, 300);
        } else {
            callback();
        }
    }
    
    showErrorIndicator() {
        let indicator = document.querySelector('.error-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'error-indicator';
            indicator.innerHTML = '⚠️ Connection issue';
            indicator.style.cssText = `
                position: absolute;
                top: 5px;
                right: 5px;
                background: rgba(255, 0, 0, 0.8);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                z-index: 1000;
            `;
            
            document.body.appendChild(indicator);
        }
        
        indicator.style.display = 'block';
    }
    
    hideErrorIndicator() {
        const indicator = document.querySelector('.error-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    destroy() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get config from data attributes or global variables
    const config = {
        refreshInterval: parseInt(document.body.dataset.refreshInterval) || 15000,
        apiUrl: document.body.dataset.apiUrl || '',
        enableAnimations: document.body.dataset.enableAnimations !== 'false'
    };
    
    window.overlayManager = new OverlayManager(config);
});

// Expose for manual control if needed
window.OverlayManager = OverlayManager;