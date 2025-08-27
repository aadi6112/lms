// static/js/core/api.js - Centralized API Communication Layer
class APIService {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Enhanced API call with error handling and logging
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
            
            const response = await fetch(url, {
                credentials: 'include',
                headers: {
                    ...this.defaultHeaders,
                    ...options.headers
                },
                ...options
            });

            // Log response status
            console.log(`📡 API Response: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ 
                    detail: `HTTP ${response.status}: ${response.statusText}` 
                }));
                throw new Error(error.detail || error.message || 'Request failed');
            }

            const data = await response.json();
            console.log(`✅ API Success:`, data.success ? 'OK' : 'Failed');
            return data;

        } catch (error) {
            console.error(`❌ API Error: ${error.message}`);
            throw error;
        }
    }

    /**
     * GET request helper
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request helper
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request helper
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request helper
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * File upload helper
     */
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add any additional form data
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        return this.request(endpoint, {
            method: 'POST',
            headers: {}, // Don't set Content-Type for FormData
            body: formData
        });
    }

    /**
     * JSON text upload helper
     */
    async uploadJsonText(endpoint, jsonText) {
        const formData = new FormData();
        formData.append('json_text', jsonText);

        return this.request(endpoint, {
            method: 'POST',
            headers: {}, // Don't set Content-Type for FormData
            body: formData
        });
    }
}

// Specific API endpoint methods
class EndorsementAPI extends APIService {
    constructor() {
        super('/api');
    }

    // Authentication endpoints
    async login(username, password) {
        return this.post('/auth/login', { username, password });
    }

    async logout() {
        return this.post('/auth/logout');
    }

    async getCurrentUser() {
        return this.get('/auth/me');
    }

    // Endorsement endpoints
    async getEndorsements(filters = {}) {
        const params = {
            status: filters.status || '',
            endorsement_type: filters.endorsement_type || '',
            search_term: filters.search_term || '',
            sort_by: filters.sort_by || 'created_at',
            sort_order: filters.sort_order || 'DESC',
            grouped: filters.grouped !== undefined ? filters.grouped : true,
            limit: filters.limit || 100,
            offset: filters.offset || 0
        };

        // Remove empty parameters
        Object.keys(params).forEach(key => {
            if (params[key] === '' || params[key] === undefined) {
                delete params[key];
            }
        });

        return this.get('/endorsements', params);
    }

    async getEndorsementById(id) {
        return this.get(`/endorsements/${id}`);
    }

    async getEndorsementCombinations(policyNumber, endorsementType) {
        const encodedPolicy = encodeURIComponent(policyNumber);
        const encodedType = encodeURIComponent(endorsementType);
        return this.get(`/endorsements/${encodedPolicy}/${encodedType}/combinations`);
    }

    async createEndorsement(data) {
        return this.post('/endorsements', data);
    }

    async updateEndorsement(id, data) {
        return this.put(`/endorsements/${id}`, data);
    }

    async deleteEndorsement(id) {
        return this.delete(`/endorsements/${id}`);
    }

    async deleteEndorsementGroup(policyNumber, endorsementType) {
        const encodedPolicy = encodeURIComponent(policyNumber);
        const encodedType = encodeURIComponent(endorsementType);
        return this.delete(`/endorsements/${encodedPolicy}/${encodedType}/group`);
    }

    async bulkUpdateStatus(endorsementIds, status) {
        return this.put('/endorsements/bulk/status', {
            endorsement_ids: endorsementIds,
            status: status
        });
    }

    // File upload endpoints
    async uploadFile(file) {
        return super.uploadFile('/files/upload', file);
    }

    async uploadJsonData(jsonText) {
        return super.uploadJsonText('/files/upload-json', jsonText);
    }

    // Search and utility endpoints
    async getEndorsementTypes() {
        return this.get('/search/endorsement-types');
    }

    async getPolicyNumbers() {
        return this.get('/search/policy-numbers');
    }

    async getStatusOptions() {
        return this.get('/search/status-options');
    }

    async getStatistics() {
        return this.get('/statistics');
    }

    async getSystemTime() {
        return this.get('/system/time');
    }

    async searchEndorsements(searchTerm) {
        return this.get('/endorsements', { search_term: searchTerm });
    }
}

// Export for use in other modules
window.APIService = APIService;
window.EndorsementAPI = EndorsementAPI;

// Create global API instance
window.api = new EndorsementAPI();

console.log('🌐 API Service loaded successfully!');
