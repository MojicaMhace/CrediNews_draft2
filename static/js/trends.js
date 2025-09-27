// CrediNews Trends Page JavaScript

// Trends Page Manager
class TrendsPageManager {
    constructor() {
        this.charts = {};
        this.currentTimeRange = '7';
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupTimeRangeSelector();
        this.setupExportButtons();
        this.loadInitialData();
        this.setupAutoRefresh();
    }

    setupTimeRangeSelector() {
        const buttons = document.querySelectorAll('.time-range-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Update active state
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update time range and reload data
                this.currentTimeRange = btn.dataset.range;
                this.loadTrendsData();
            });
        });
    }

    setupExportButtons() {
        const exportButtons = document.querySelectorAll('.export-btn');
        exportButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const format = btn.dataset.format;
                this.exportData(format);
            });
        });
    }

    setupAutoRefresh() {
        // Auto-refresh every 5 minutes
        setInterval(() => {
            if (!this.isLoading) {
                this.loadTrendsData(false); // Silent refresh
            }
        }, 5 * 60 * 1000);
    }

    async loadInitialData() {
        this.showLoading(true);
        await this.loadTrendsData();
        this.showLoading(false);
    }

    async loadTrendsData(showLoading = true) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        if (showLoading) {
            this.showChartsLoading();
        }

        try {
            const response = await fetch(`/api/trends?range=${this.currentTimeRange}`);
            const data = await response.json();

            if (data.success) {
                this.updateMetrics(data.data);
                this.updateCharts(data.data);
                this.updateTrendingTopics(data.data);
                this.updateAnalytics(data.data);
                this.hideChartsLoading();
            } else {
                this.showError('Failed to load trends data: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading trends data:', error);
            this.showError('Network error. Please check your connection.');
        } finally {
            this.isLoading = false;
        }
    }

    updateMetrics(data) {
        const metrics = {
            'total-news-verifications': {
                value: data.total_news_verifications || 0,
                change: data.total_news_verifications_change || 0
            },
            'fake-detected': {
                value: data.fake_detected || 0,
                change: data.fake_detected_change || 0
            },
            'accuracy-rate': {
                value: data.accuracy_rate || 0,
                change: data.accuracy_rate_change || 0,
                suffix: '%'
            },
            'posers-detected': {
                value: data.posers_detected || 0,
                change: data.posers_detected_change || 0
            }
        };

        Object.entries(metrics).forEach(([id, metric]) => {
            const valueElement = document.getElementById(id);
            const changeElement = document.getElementById(id + '-change');
            
            if (valueElement) {
                this.animateCounter(valueElement, metric.value, metric.suffix);
            }
            
            if (changeElement && metric.change !== undefined) {
                this.updateChangeIndicator(changeElement, metric.change);
            }
        });
    }

    animateCounter(element, targetValue, suffix = '') {
        const startValue = parseInt(element.textContent.replace(/[^0-9]/g, '')) || 0;
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            
            const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuart);
            element.textContent = this.formatNumber(currentValue) + suffix;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    updateChangeIndicator(element, change) {
        const isPositive = change > 0;
        const isNegative = change < 0;
        
        element.className = 'metric-change ' + 
            (isPositive ? 'positive' : isNegative ? 'negative' : 'neutral');
        
        const arrow = isPositive ? '↗' : isNegative ? '↘' : '→';
        const sign = isPositive ? '+' : '';
        
        element.innerHTML = `${arrow} ${sign}${change}%`;
    }

    updateCharts(data) {
        if (typeof Chart !== 'undefined') {
            this.updateDetectionRateChart(data.detection_rate_chart);
            this.updateCategoryChart(data.category_chart);
            this.updateSourceCredibilityChart(data.source_credibility_chart);
        } else {
            console.warn('Chart.js not loaded');
        }
    }

    updateDetectionRateChart(chartData) {
        const ctx = document.getElementById('detection-rate-chart');
        if (!ctx || !chartData) return;

        if (this.charts.detectionRate) {
            this.charts.detectionRate.destroy();
        }

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#D1D5DB' : '#374151';
        const gridColor = isDark ? '#374151' : '#E5E7EB';

        this.charts.detectionRate = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Detection Rate (%)',
                    data: chartData.values || [],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3B82F6',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: isDark ? '#1F2937' : '#ffffff',
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: isDark ? '#374151' : '#E5E7EB',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: gridColor,
                            drawBorder: false
                        },
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: gridColor,
                            drawBorder: false
                        },
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    updateCategoryChart(chartData) {
        const ctx = document.getElementById('category-chart');
        if (!ctx || !chartData) return;

        if (this.charts.category) {
            this.charts.category.destroy();
        }

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#D1D5DB' : '#374151';

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    data: chartData.values || [],
                    backgroundColor: [
                        '#EF4444', // Red
                        '#F59E0B', // Amber
                        '#10B981', // Emerald
                        '#3B82F6', // Blue
                        '#8B5CF6', // Violet
                        '#EC4899', // Pink
                        '#14B8A6', // Teal
                        '#F97316'  // Orange
                    ],
                    borderWidth: 2,
                    borderColor: isDark ? '#1F2937' : '#ffffff',
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            font: {
                                size: 12
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: isDark ? '#1F2937' : '#ffffff',
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: isDark ? '#374151' : '#E5E7EB',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    updateSourceCredibilityChart(chartData) {
        const ctx = document.getElementById('source-credibility-chart');
        if (!ctx || !chartData) return;

        if (this.charts.sourceCredibility) {
            this.charts.sourceCredibility.destroy();
        }

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#D1D5DB' : '#374151';
        const gridColor = isDark ? '#374151' : '#E5E7EB';

        this.charts.sourceCredibility = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Credibility Score',
                    data: chartData.values || [],
                    backgroundColor: 'rgba(13, 148, 136, 0.8)',
                    borderColor: '#0D9488',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: isDark ? '#1F2937' : '#ffffff',
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: isDark ? '#374151' : '#E5E7EB',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `Credibility: ${context.parsed.y}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: textColor,
                            font: {
                                size: 11
                            },
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: gridColor,
                            drawBorder: false
                        },
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    updateTrendingTopics(data) {
        this.updateTrendingKeywords(data.trending_keywords);
        this.updateFakeNewsPatterns(data.fake_news_patterns);
        this.updateHighRiskSources(data.high_risk_sources);
    }

    updateTrendingKeywords(keywords) {
        const container = document.getElementById('trending-keywords');
        if (!container || !keywords) return;

        if (keywords.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">No trending keywords found</p>';
            return;
        }

        const keywordsHtml = keywords.map((keyword, index) => {
            const frequency = keyword.frequency || 0;
            const frequencyClass = frequency > 50 ? 'high-frequency' : 
                                 frequency > 20 ? 'medium-frequency' : 'low-frequency';
            
            return `
                <span class="keyword-tag ${frequencyClass}" 
                      data-frequency="${frequency}"
                      title="Mentioned ${frequency} times">
                    ${keyword.word || keyword}
                </span>
            `;
        }).join('');

        container.innerHTML = `<div class="keywords-cloud">${keywordsHtml}</div>`;
    }

    updateFakeNewsPatterns(patterns) {
        const container = document.getElementById('fake-news-patterns');
        if (!container || !patterns) return;

        if (patterns.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">No patterns detected</p>';
            return;
        }

        const patternsHtml = patterns.map(pattern => `
            <div class="trending-item">
                <div class="trending-item-content">
                    <div class="trending-item-title">${pattern.pattern || pattern.title}</div>
                    <div class="trending-item-meta">${pattern.description || 'Recent pattern'}</div>
                </div>
                <div class="trending-item-value">${pattern.count || pattern.frequency || 0}</div>
            </div>
        `).join('');

        container.innerHTML = patternsHtml;
    }

    updateHighRiskSources(sources) {
        const container = document.getElementById('high-risk-sources');
        if (!container || !sources) return;

        if (sources.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">No high-risk sources detected</p>';
            return;
        }

        const sourcesHtml = sources.map(source => `
            <div class="trending-item">
                <div class="trending-item-content">
                    <div class="trending-item-title">${source.domain || source.name}</div>
                    <div class="trending-item-meta">Risk Score: ${source.risk_score || 0}%</div>
                </div>
                <span class="badge badge-error">${source.fake_count || 0} fake</span>
            </div>
        `).join('');

        container.innerHTML = sourcesHtml;
    }

    updateAnalytics(data) {
        this.updateMLModelPerformance(data.ml_performance);
        this.updateFactCheckCoverage(data.fact_check_coverage);
        this.updateGeographicDistribution(data.geographic_distribution);
    }

    updateMLModelPerformance(performance) {
        const container = document.getElementById('ml-performance');
        if (!container || !performance) return;

        const metricsHtml = `
            <div class="model-metric">
                <div class="model-metric-value">${(performance.accuracy * 100).toFixed(1)}%</div>
                <div class="model-metric-label">Accuracy</div>
            </div>
            <div class="model-metric">
                <div class="model-metric-value">${(performance.precision * 100).toFixed(1)}%</div>
                <div class="model-metric-label">Precision</div>
            </div>
            <div class="model-metric">
                <div class="model-metric-value">${(performance.recall * 100).toFixed(1)}%</div>
                <div class="model-metric-label">Recall</div>
            </div>
            <div class="model-metric">
                <div class="model-metric-value">${(performance.f1_score * 100).toFixed(1)}%</div>
                <div class="model-metric-label">F1 Score</div>
            </div>
        `;

        container.innerHTML = metricsHtml;
    }

    updateFactCheckCoverage(coverage) {
        const container = document.getElementById('fact-check-coverage');
        if (!container || !coverage) return;

        const coverageHtml = `
            <div class="stat-value info">${coverage.total_checks || 0}</div>
            <div class="stat-label">Total Fact Checks</div>
            <div class="mt-2">
                <div class="text-sm text-secondary">Coverage Rate: ${(coverage.coverage_rate * 100).toFixed(1)}%</div>
                <div class="text-sm text-secondary">Avg Response Time: ${coverage.avg_response_time || 'N/A'}</div>
            </div>
        `;

        container.innerHTML = coverageHtml;
    }

    updateGeographicDistribution(geoData) {
        const container = document.getElementById('geographic-distribution');
        if (!container || !geoData) return;

        if (!geoData.countries || geoData.countries.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">No geographic data available</p>';
            return;
        }

        const maxCount = Math.max(...geoData.countries.map(c => c.count));
        
        const geoHtml = geoData.countries.map(country => {
            const percentage = (country.count / maxCount) * 100;
            return `
                <div class="geo-item">
                    <div class="geo-country">${country.name}</div>
                    <div class="geo-bar">
                        <div class="geo-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="geo-count">${country.count}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = geoHtml;
    }

    async exportData(format) {
        try {
            const response = await fetch(`/api/trends/export?format=${format}&range=${this.currentTimeRange}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `credinews-trends-${this.currentTimeRange}days.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showSuccess(`Data exported as ${format.toUpperCase()}`);
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showError('Failed to export data. Please try again.');
        }
    }

    showChartsLoading() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.innerHTML = `
                <div class="chart-loading">
                    <div class="spinner"></div>
                    <span>Loading chart data...</span>
                </div>
            `;
        });
    }

    hideChartsLoading() {
        // Charts will be rendered, replacing loading state
    }

    showLoading(show) {
        const loadingOverlay = document.getElementById('trends-loading');
        if (loadingOverlay) {
            loadingOverlay.classList.toggle('hidden', !show);
        }
    }

    showError(message) {
        this.showAlert(message, 'error');
        
        // Show error state in charts
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.innerHTML = `
                <div class="chart-error">
                    <div class="chart-error-icon">⚠️</div>
                    <div class="chart-error-message">${message}</div>
                    <button class="chart-retry-btn" onclick="trendsManager.loadTrendsData()">Retry</button>
                </div>
            `;
        });
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
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

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Update charts when theme changes
    onThemeChange() {
        // Recreate charts with new theme colors
        if (this.charts.detectionRate) {
            this.updateDetectionRateChart(this.charts.detectionRate.data);
        }
        if (this.charts.category) {
            this.updateCategoryChart(this.charts.category.data);
        }
        if (this.charts.sourceCredibility) {
            this.updateSourceCredibilityChart(this.charts.sourceCredibility.data);
        }
    }
}

// Initialize trends manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.trendsManager = new TrendsPageManager();
    
    // Listen for theme changes
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                if (window.trendsManager) {
                    setTimeout(() => window.trendsManager.onThemeChange(), 100);
                }
            }
        });
    });
    
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
    
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (window.trendsManager) {
                Object.values(window.trendsManager.charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }
        }, 250);
    });
});

// Export for global access
window.TrendsPageManager = TrendsPageManager;