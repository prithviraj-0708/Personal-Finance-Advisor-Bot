// Financial Charts Handler using Chart.js

const CHART_COLORS = {
    emerald: '#10b981',
    emeraldSoft: 'rgba(16, 185, 129, 0.2)',
    rose: '#f43f5e',
    roseSoft: 'rgba(244, 63, 94, 0.2)',
    blue: '#3b82f6',
    blueSoft: 'rgba(59, 130, 246, 0.2)',
    purple: '#8b5cf6',
    amber: '#f59e0b',
    teal: '#14b8a6',
    slate: '#64748b',
    palette: [
        '#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6',
        '#06b6d4', '#f43f5e', '#84cc16', '#6366f1', '#14b8a6',
        '#d946ef', '#64748b'
    ]
};

function renderIncomeExpenseChart(canvasId, labels, incomeData, expenseData, currency = '₹') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: CHART_COLORS.emerald,
                    borderRadius: 6,
                    maxBarThickness: 32
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: CHART_COLORS.rose,
                    borderRadius: 6,
                    maxBarThickness: 32
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        font: { family: "'Inter', sans-serif", size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${context.dataset.label}: ${currency}${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: function (value) {
                            return `${currency}${value >= 1000 ? (value / 1000) + 'k' : value}`;
                        },
                        font: { family: "'Inter', sans-serif", size: 11 }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
                }
            }
        }
    });
}

function renderCategoryDoughnut(canvasId, labels, data, currency = '₹') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (!data || data.length === 0 || data.every(v => v === 0)) {
        ctx.parentNode.innerHTML = '<div class="text-center py-5 text-muted"><i class="bi bi-pie-chart fs-1 d-block mb-2"></i>No expense records to display yet</div>';
        return;
    }

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: CHART_COLORS.palette.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 14,
                        font: { family: "'Inter', sans-serif", size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = context.parsed;
                            return ` ${context.label}: ${currency}${val.toLocaleString()}`;
                        }
                    }
                }
            }
        }
    });
}

function renderSavingsLineChart(canvasId, labels, savingsData, currency = '₹') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Net Monthly Savings',
                data: savingsData,
                borderColor: CHART_COLORS.emerald,
                backgroundColor: CHART_COLORS.emeraldSoft,
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointBackgroundColor: CHART_COLORS.emerald
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` Net Savings: ${currency}${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: function (value) {
                            return `${currency}${value >= 1000 ? (value / 1000) + 'k' : value}`;
                        },
                        font: { family: "'Inter', sans-serif", size: 11 }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
                }
            }
        }
    });
}

function renderBudgetUtilizationChart(canvasId, categories, spentData, limitData, currency = '₹') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Actual Spent',
                    data: spentData,
                    backgroundColor: CHART_COLORS.rose,
                    borderRadius: 4
                },
                {
                    label: 'Budget Limit',
                    data: limitData,
                    backgroundColor: CHART_COLORS.blue,
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return ` ${ctx.dataset.label}: ${currency}${ctx.parsed.x.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: function (val) {
                            return `${currency}${val}`;
                        }
                    }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}
