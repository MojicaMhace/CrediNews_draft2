// CrediNews Dashboard JavaScript

// Theme Management
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupToggleButton();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
        
        // Update toggle button icon
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
            toggleBtn.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
        }
    }

    setupToggleButton() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
                this.applyTheme(newTheme);
            });
        }
    }

    toggle() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }
}

// News Analysis Manager
class NewsAnalysisManager {
    constructor() {
        this.isAnalyzing = false;
        this.init();
    }

    init() {
        this.setupAnalysisForm();
        this.setupFileUpload();
    }

    setupAnalysisForm() {
        const form = document.getElementById('analysis-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.analyzeNews();
            });
        }
    }

    setupFileUpload() {
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files[0]);
            });
        }
    }

    async analyzeNews() {
        if (this.isAnalyzing) return;

        const inputType = document.getElementById('input-type')?.value || 'text';
        const content = document.getElementById('news-content')?.value?.trim();
        const url = document.getElementById('news-url')?.value?.trim();

        if (!content && !url) {
            this.showAlert('Please enter news content or URL', 'error');
            return;
        }

        this.isAnalyzing = true;
        this.showLoading(true);
        this.clearResults();

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: inputType,
                    content: content || url
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data.analysis);
            } else {
                this.showAlert(data.error || 'Analysis failed', 'error');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showAlert('Network error. Please try again.', 'error');
        } finally {
            this.isAnalyzing = false;
            this.showLoading(false);
        }
    }

    async handleFileUpload(file) {
        if (!file) return;

        const allowedTypes = ['text/plain', 'application/pdf', 'text/csv'];
        if (!allowedTypes.includes(file.type)) {
            this.showAlert('Please upload a text, PDF, or CSV file', 'error');
            return;
        }

        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            this.showAlert('File size must be less than 5MB', 'error');
            return;
        }

        this.showLoading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data.analysis);
            } else {
                this.showAlert(data.error || 'File analysis failed', 'error');
            }
        } catch (error) {
            console.error('File upload error:', error);
            this.showAlert('File upload failed. Please try again.', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(analysis) {
        const resultsContainer = document.getElementById('analysis-results');
        if (!resultsContainer) return;

        const credibilityClass = this.getCredibilityClass(analysis.credibility_score);
        const confidenceClass = this.getConfidenceClass(analysis.confidence);

        resultsContainer.innerHTML = `
            <div class="result-card fade-in">
                <div class="result-header">
                    <h3>Analysis Results</h3>
                    <span class="badge badge-info">${new Date().toLocaleString()}</span>
                </div>
                
                <div class="grid grid-2">
                    <div class="credibility-score ${credibilityClass}">
                        <div class="stat-value">${analysis.credibility_score}%</div>
                        <div class="stat-label">Credibility Score</div>
                    </div>
                    
                    <div class="credibility-score ${confidenceClass}">
                        <div class="stat-value">${analysis.confidence}%</div>
                        <div class="stat-label">Confidence Level</div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4>Classification: <span class="badge ${analysis.is_fake ? 'badge-error' : 'badge-success'}">
                        ${analysis.is_fake ? 'Potentially Fake' : 'Likely Authentic'}
                    </span></h4>
                </div>
                
                ${this.renderModelResults(analysis.model_results)}
                ${this.renderFactChecks(analysis.fact_checks)}
                ${this.renderPoserDetection(analysis.poser_detection)}
                ${this.renderSourceAnalysis(analysis.source_analysis)}
            </div>
        `;

        resultsContainer.classList.remove('hidden');
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    renderModelResults(modelResults) {
        if (!modelResults) return '';

        return `
            <div class="mt-4">
                <h4>ML Model Results</h4>
                <div class="grid grid-3 mt-2">
                    ${Object.entries(modelResults).map(([model, result]) => `
                        <div class="card">
                            <div class="card-title">${this.formatModelName(model)}</div>
                            <div class="stat-value ${result.prediction === 'fake' ? 'error' : 'success'}">
                                ${(result.confidence * 100).toFixed(1)}%
                            </div>
                            <div class="stat-label">${result.prediction}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderFactChecks(factChecks) {
        if (!factChecks || factChecks.length === 0) return '';

        return `
            <div class="mt-4">
                <h4>Fact Check Results</h4>
                <div class="mt-2">
                    ${factChecks.map(check => `
                        <div class="card mb-2">
                            <div class="flex justify-between items-center">
                                <div>
                                    <div class="font-medium">${check.claim}</div>
                                    <div class="text-sm text-secondary">${check.claimant}</div>
                                </div>
                                <span class="badge ${this.getFactCheckClass(check.rating)}">
                                    ${check.rating}
                                </span>
                            </div>
                            <div class="mt-2">
                                <a href="${check.url}" target="_blank" class="text-primary text-sm">
                                    View full fact check →
                                </a>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderPoserDetection(poserDetection) {
        if (!poserDetection) return '';

        return `
            <div class="mt-4">
                <h4>Account Analysis</h4>
                <div class="card mt-2">
                    <div class="grid grid-2">
                        <div>
                            <div class="stat-label">Poser Risk</div>
                            <div class="stat-value ${poserDetection.is_poser ? 'error' : 'success'}">
                                ${poserDetection.risk_score}%
                            </div>
                        </div>
                        <div>
                            <div class="stat-label">Account Status</div>
                            <span class="badge ${poserDetection.is_poser ? 'badge-error' : 'badge-success'}">
                                ${poserDetection.is_poser ? 'Suspicious' : 'Verified'}
                            </span>
                        </div>
                    </div>
                    ${poserDetection.flags && poserDetection.flags.length > 0 ? `
                        <div class="mt-2">
                            <div class="stat-label">Risk Factors:</div>
                            <div class="flex gap-1 mt-1">
                                ${poserDetection.flags.map(flag => `
                                    <span class="badge badge-warning">${flag}</span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderSourceAnalysis(sourceAnalysis) {
        if (!sourceAnalysis) return '';

        return `
            <div class="mt-4">
                <h4>Source Analysis</h4>
                <div class="card mt-2">
                    <div class="grid grid-2">
                        <div>
                            <div class="stat-label">Domain</div>
                            <div class="font-medium">${sourceAnalysis.domain || 'N/A'}</div>
                        </div>
                        <div>
                            <div class="stat-label">Credibility</div>
                            <span class="badge ${this.getCredibilityBadgeClass(sourceAnalysis.credibility)}">
                                ${sourceAnalysis.credibility || 'Unknown'}
                            </span>
                        </div>
                    </div>
                    ${sourceAnalysis.reputation_score ? `
                        <div class="mt-2">
                            <div class="stat-label">Reputation Score</div>
                            <div class="stat-value info">${sourceAnalysis.reputation_score}/100</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    getCredibilityClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 60) return 'medium';
        return 'low';
    }

    getFactCheckClass(rating) {
        const lowerRating = rating.toLowerCase();
        if (lowerRating.includes('true') || lowerRating.includes('correct')) return 'badge-success';
        if (lowerRating.includes('false') || lowerRating.includes('incorrect')) return 'badge-error';
        return 'badge-warning';
    }

    getCredibilityBadgeClass(credibility) {
        if (!credibility) return 'badge-info';
        const lower = credibility.toLowerCase();
        if (lower.includes('high') || lower.includes('reliable')) return 'badge-success';
        if (lower.includes('low') || lower.includes('unreliable')) return 'badge-error';
        return 'badge-warning';
    }

    formatModelName(modelName) {
        const names = {
            'logistic_regression': 'Logistic Regression',
            'naive_bayes': 'Naive Bayes',
            'svm': 'Support Vector Machine',
            'ensemble': 'Ensemble Model'
        };
        return names[modelName] || modelName;
    }

    showLoading(show) {
        const loadingEl = document.getElementById('loading-overlay');
        const submitBtn = document.getElementById('analyze-btn');
        
        if (loadingEl) {
            loadingEl.classList.toggle('hidden', !show);
        }
        
        if (submitBtn) {
            submitBtn.disabled = show;
            submitBtn.innerHTML = show ? 
                '<span class="spinner"></span> Analyzing...' : 
                'Analyze News';
        }
    }

    clearResults() {
        const resultsContainer = document.getElementById('analysis-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
            resultsContainer.classList.add('hidden');
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || this.createAlertContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in`;
        alert.innerHTML = `
            <span>${message}</span>
            <button class="modal-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }

    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1001;
            max-width: 400px;
        `;
        document.body.appendChild(container);
        return container;
    }
}

// Trends Manager
class TrendsManager {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.loadTrendsData();
        this.setupTimeRangeSelector();
    }

    setupTimeRangeSelector() {
        const selector = document.getElementById('time-range-selector');
        if (selector) {
            selector.addEventListener('change', () => {
                this.loadTrendsData(selector.value);
            });
        }
    }

    async loadTrendsData(timeRange = '7') {
        try {
            const response = await fetch(`/api/trends?range=${timeRange}`);
            const data = await response.json();

            if (data.success) {
                this.updateMetrics(data.data);
                this.updateCharts(data.data);
            } else {
                console.error('Failed to load trends data:', data.error);
            }
        } catch (error) {
            console.error('Error loading trends data:', error);
        }
    }

    updateMetrics(data) {
        const metrics = {
            'total-news-verifications': data.total_news_verifications || 0,
            'fake-detected': data.fake_detected || 0,
            'accuracy-rate': data.accuracy_rate || 0,
            'posers-detected': data.posers_detected || 0
        };

        Object.entries(metrics).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateCounter(element, value);
            }
        });
    }

    animateCounter(element, targetValue) {
        const startValue = parseInt(element.textContent) || 0;
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = Math.floor(startValue + (targetValue - startValue) * progress);
            element.textContent = currentValue;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    updateCharts(data) {
        if (typeof Chart !== 'undefined') {
            this.updateDetectionRateChart(data.detection_rate_chart);
            this.updateCategoryChart(data.category_chart);
            this.updateSourceCredibilityChart(data.source_credibility_chart);
        }
    }

    updateDetectionRateChart(data) {
        const ctx = document.getElementById('detection-rate-chart');
        if (!ctx || !data) return;

        if (this.charts.detectionRate) {
            this.charts.detectionRate.destroy();
        }

        this.charts.detectionRate = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Detection Rate',
                    data: data.values || [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    updateCategoryChart(data) {
        const ctx = document.getElementById('category-chart');
        if (!ctx || !data) return;

        if (this.charts.category) {
            this.charts.category.destroy();
        }

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: [
                        '#EF4444',
                        '#F59E0B',
                        '#10B981',
                        '#3B82F6',
                        '#8B5CF6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    updateSourceCredibilityChart(data) {
        const ctx = document.getElementById('source-credibility-chart');
        if (!ctx || !data) return;

        if (this.charts.sourceCredibility) {
            this.charts.sourceCredibility.destroy();
        }

        this.charts.sourceCredibility = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Credibility Score',
                    data: data.values || [],
                    backgroundColor: 'rgba(13, 148, 136, 0.8)',
                    borderColor: 'rgb(13, 148, 136)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

// User Dashboard Manager
class UserDashboardManager {
    constructor() {
        this.init();
    }

    init() {
        this.loadUserData();
        this.setupAnalysisHistory();
        this.setupExportButton();
    }

    async loadUserData() {
        // Load user profile and stats
        this.updateUserStats();
    }

    setupAnalysisHistory() {
        const historyContainer = document.getElementById('analysis-history');
        if (historyContainer) {
            this.loadAnalysisHistory();
        }
    }

    async loadAnalysisHistory() {
        try {
            const response = await fetch('/api/user/news-verifications');
            const data = await response.json();

            if (data.success) {
                this.renderNewsVerificationHistory(data.news_verifications);
            }
        } catch (error) {
            console.error('Error loading analysis history:', error);
        }
    }

    renderNewsVerificationHistory(news_verifications) {
        const container = document.getElementById('analysis-history');
        if (!container) return;

        if (!news_verifications || news_verifications.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">No news verifications yet</p>';
            return;
        }

        container.innerHTML = news_verifications.map(verification => `
            <div class="card mb-2 cursor-pointer" onclick="userDashboard.viewNewsVerification('${verification.id}')">
                <div class="flex justify-between items-center">
                    <div>
                        <div class="font-medium">${analysis.title || 'News Analysis'}</div>
                        <div class="text-sm text-secondary">${new Date(analysis.created_at).toLocaleDateString()}</div>
                    </div>
                    <div class="text-right">
                        <span class="badge ${analysis.is_fake ? 'badge-error' : 'badge-success'}">
                            ${analysis.is_fake ? 'Fake' : 'Authentic'}
                        </span>
                        <div class="text-sm text-secondary">${analysis.credibility_score}% credible</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async viewAnalysis(analysisId) {
        try {
            const response = await fetch(`/api/analysis/${analysisId}`);
            const data = await response.json();

            if (data.success) {
                this.showAnalysisModal(data.analysis);
            }
        } catch (error) {
            console.error('Error loading analysis:', error);
        }
    }

    showAnalysisModal(analysis) {
        const modal = document.getElementById('analysis-modal');
        const modalContent = document.getElementById('modal-analysis-content');
        
        if (modal && modalContent) {
            modalContent.innerHTML = this.renderAnalysisDetails(analysis);
            modal.classList.remove('hidden');
        }
    }

    renderAnalysisDetails(analysis) {
        return `
            <h3>${analysis.title || 'News Analysis'}</h3>
            <p class="text-secondary mb-4">${new Date(analysis.created_at).toLocaleString()}</p>
            
            <div class="grid grid-2 mb-4">
                <div class="credibility-score ${this.getCredibilityClass(analysis.credibility_score)}">
                    <div class="stat-value">${analysis.credibility_score}%</div>
                    <div class="stat-label">Credibility</div>
                </div>
                <div class="credibility-score ${this.getConfidenceClass(analysis.confidence)}">
                    <div class="stat-value">${analysis.confidence}%</div>
                    <div class="stat-label">Confidence</div>
                </div>
            </div>
            
            <div class="mb-4">
                <h4>Classification</h4>
                <span class="badge ${analysis.is_fake ? 'badge-error' : 'badge-success'}">
                    ${analysis.is_fake ? 'Potentially Fake' : 'Likely Authentic'}
                </span>
            </div>
            
            ${analysis.content ? `
                <div class="mb-4">
                    <h4>Content</h4>
                    <div class="p-3 bg-gray-50 rounded">${analysis.content.substring(0, 200)}...</div>
                </div>
            ` : ''}
        `;
    }

    setupExportButton() {
        const exportBtn = document.getElementById('export-data-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportUserData());
        }
    }

    async exportUserData() {
        try {
            const response = await fetch('/api/user/export');
            const data = await response.json();

            if (data.success) {
                const blob = new Blob([JSON.stringify(data.data, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `credinews-data-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Error exporting data:', error);
        }
    }

    updateUserStats() {
        // Update user statistics on dashboard
        // This would be called with real data from the API
    }

    getCredibilityClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 60) return 'medium';
        return 'low';
    }
}

// Utility Functions
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success message
        const analysisManager = new NewsAnalysisManager();
        analysisManager.showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Initialize managers when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme manager
    window.themeManager = new ThemeManager();
    
    // Initialize appropriate manager based on page
    if (document.getElementById('analysis-form')) {
        window.analysisManager = new NewsAnalysisManager();
    }
    
    if (document.getElementById('detection-rate-chart')) {
        window.trendsManager = new TrendsManager();
    }
    
    if (document.getElementById('analysis-history')) {
        window.userDashboard = new UserDashboardManager();
    }
    
    // Setup modal close handlers
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.add('hidden');
        }
        
        if (e.target.classList.contains('modal-close')) {
            const modal = e.target.closest('.modal');
            if (modal) {
                modal.classList.add('hidden');
            }
        }
    });
    
    // Setup keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape key closes modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal:not(.hidden)');
            modals.forEach(modal => modal.classList.add('hidden'));
        }
        
        // Ctrl/Cmd + K for theme toggle
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (window.themeManager) {
                window.themeManager.toggle();
            }
        }
    });
});

// Export for global access
window.NewsAnalysisManager = NewsAnalysisManager;
window.TrendsManager = TrendsManager;
window.UserDashboardManager = UserDashboardManager;
window.ThemeManager = ThemeManager;