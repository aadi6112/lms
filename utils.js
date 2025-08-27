// static/js/core/utils.js - Utility Functions Module
class UIUtils {
    /**
     * Show success or error message
     */
    static showMessage(message, isError = false, duration = 5000) {
        const successEl = document.getElementById('successMessage');
        const errorEl = document.getElementById('errorMessage');
        
        if (!successEl || !errorEl) {
            console.warn('Message elements not found');
            return;
        }

        const messageEl = isError ? errorEl : successEl;
        const otherEl = isError ? successEl : errorEl;

        // Hide other message
        otherEl.style.display = 'none';
        
        // Show current message
        messageEl.querySelector('span').textContent = message;
        messageEl.style.display = 'flex';

        // Auto-hide after duration
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, duration);

        // Log to console
        console.log(isError ? '❌' : '✅', message);
    }

    /**
     * Show loading state
     */
    static showLoading(element, show = true) {
        if (!element) return;
        
        if (show) {
            element.style.display = 'flex';
        } else {
            element.style.display = 'none';
        }
    }

    /**
     * Toggle element visibility
     */
    static toggleVisibility(element, show) {
        if (!element) return;
        element.style.display = show ? 'block' : 'none';
    }

    /**
     * Add CSS class conditionally
     */
    static toggleClass(element, className, condition) {
        if (!element) return;
        
        if (condition) {
            element.classList.add(className);
        } else {
            element.classList.remove(className);
        }
    }

    /**
     * Animate counter from current value to target
     */
    static animateCounter(element, target, duration = 1000) {
        if (!element) return;
        
        const current = parseInt(element.textContent) || 0;
        const increment = target > current ? 1 : -1;
        const stepTime = Math.abs(duration / (target - current));
        
        const timer = setInterval(() => {
            const value = parseInt(element.textContent) || 0;
            if (value === target) {
                clearInterval(timer);
            } else {
                element.textContent = value + increment;
            }
        }, stepTime);
    }

    /**
     * Debounce function calls
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function calls
     */
    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }

    /**
     * Smooth scroll to element
     */
    static scrollToElement(element, behavior = 'smooth') {
        if (!element) return;
        element.scrollIntoView({ behavior, block: 'nearest' });
    }

    /**
     * Copy text to clipboard
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showMessage('Copied to clipboard!');
            return true;
        } catch (error) {
            console.error('Copy failed:', error);
            this.showMessage('Failed to copy to clipboard', true);
            return false;
        }
    }

    /**
     * Format file size for display
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Validate file type
     */
    static isValidFileType(file, allowedTypes) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        return allowedTypes.includes(`.${fileExtension}`);
    }
}

class DateUtils {
    /**
     * Format date for display
     */
    static formatDate(dateString) {
        if (!dateString) return 'N/A';

        try {
            let date;
            // Handle different date formats
            if (dateString.includes('T')) {
                // ISO format (2025-08-18T19:36:37Z)
                date = new Date(dateString);
            } else if (dateString.includes('-') && dateString.includes(':')) {
                // Local SQLite format (2025-08-18 19:36:37)
                date = new Date(dateString.replace(' ', 'T'));
            } else {
                date = new Date(dateString);
            }

            // Format in local time with readable format
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
        } catch (error) {
            console.error('Date formatting error:', error, 'Input:', dateString);
            return dateString; // Return original if parsing fails
        }
    }

    /**
     * Format date for API calls
     */
    static formatDateForAPI(date) {
        if (!date) return null;
        return date.toISOString();
    }

    /**
     * Get current timestamp
     */
    static getCurrentTimestamp() {
        return new Date().toISOString();
    }

    /**
     * Get relative time (e.g., "2 hours ago")
     */
    static getRelativeTime(dateString) {
        if (!dateString) return 'Unknown';

        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
        
        return this.formatDate(dateString);
    }

    /**
     * Update live time display
     */
    static updateCurrentTimeDisplay() {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });

        const timeElement = document.getElementById('currentTime');
        if (timeElement) {
            timeElement.textContent = timeString;
        }

        // Update page title with current time
        document.title = `Policy Management - ${timeString}`;
    }
}

class DataUtils {
    /**
     * Get status CSS class
     */
    static getStatusClass(status) {
        switch (status?.toLowerCase()) {
            case 'approved': return 'approved';
            case 'rejected': return 'rejected';
            default: return 'review';
        }
    }

    /**
     * Get status icon
     */
    static getStatusIcon(status) {
        switch (status?.toLowerCase()) {
            case 'approved': return 'fa-check-circle';
            case 'rejected': return 'fa-times-circle';
            default: return 'fa-clock';
        }
    }

    /**
     * Extract core fields from JSON data
     */
    static extractCoreFields(jsonData) {
        const coreFieldMappings = {
            'número de póliza': 'policy_number',
            'numero de poliza': 'policy_number',
            'policy_number': 'policy_number',
            'poliza': 'policy_number',
            'póliza': 'policy_number',
            
            'nombre del endoso': 'endorsement_type',
            'tipo de endoso': 'endorsement_type',
            'endorsement_type': 'endorsement_type',
            'endoso': 'endorsement_type',
            
            'versión del endoso inicial': 'endorsement_version',
            'version del endoso inicial': 'endorsement_version',
            'versión del endoso': 'endorsement_version',
            'version del endoso': 'endorsement_version',
            'endorsement_version': 'endorsement_version',
            'version': 'endorsement_version',
            'versión': 'endorsement_version'
        };
        
        const coreFields = {};
        
        for (const [spanishField, englishField] of Object.entries(coreFieldMappings)) {
            for (const [fieldName, fieldValue] of Object.entries(jsonData)) {
                if (spanishField.toLowerCase() === fieldName.toLowerCase().trim()) {
                    if (englishField === 'policy_number') {
                        // Extract policy number
                        if (fieldValue && String(fieldValue).trim()) {
                            const cleanedValue = String(fieldValue).trim();
                            const numbers = cleanedValue.match(/\d+/);
                            if (numbers) {
                                coreFields[englishField] = numbers[0];
                            } else {
                                coreFields[englishField] = cleanedValue;
                            }
                        }
                    } else {
                        coreFields[englishField] = String(fieldValue).trim() || null;
                    }
                    break;
                }
            }
        }
        
        return coreFields;
    }

    /**
     * Validate JSON string
     */
    static validateJSON(jsonString) {
        try {
            JSON.parse(jsonString);
            return { valid: true };
        } catch (error) {
            return { 
                valid: false, 
                message: `Invalid JSON: ${error.message}` 
            };
        }
    }

    /**
     * Safe JSON parse
     */
    static safeJSONParse(jsonString, fallback = {}) {
        try {
            return JSON.parse(jsonString);
        } catch (error) {
            console.warn('JSON parse failed:', error);
            return fallback;
        }
    }

    /**
     * Deep clone object
     */
    static deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    /**
     * Check if object is empty
     */
    static isEmpty(obj) {
        return obj && Object.keys(obj).length === 0;
    }

    /**
     * Generate unique ID
     */
    static generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

class ValidationUtils {
    /**
     * Validate email format
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate policy number format
     */
    static isValidPolicyNumber(policyNumber) {
        if (!policyNumber) return false;
        // Allow alphanumeric and hyphens
        const policyRegex = /^[A-Za-z0-9-]+$/;
        return policyRegex.test(policyNumber);
    }

    /**
     * Sanitize string for HTML display
     */
    static sanitizeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Validate required fields
     */
    static validateRequired(value, fieldName) {
        if (!value || String(value).trim().length === 0) {
            return { 
                valid: false, 
                message: `${fieldName} is required` 
            };
        }
        return { valid: true };
    }
}

// Export all utility classes
window.UIUtils = UIUtils;
window.DateUtils = DateUtils;
window.DataUtils = DataUtils;
window.ValidationUtils = ValidationUtils;

console.log('🛠️ Utility modules loaded successfully!');
