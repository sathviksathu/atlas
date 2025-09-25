"""
Fraud Transaction Monitor Home Page
"""

fraud_monitoring_home_page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fraud Transaction Monitor</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                box-sizing: border-box;
            }
            button {
                background-color: #007bff;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-right: 10px;
            }
            button:hover {
                background-color: #0056b3;
            }
            .loading {
                display: none;
                text-align: center;
                color: #666;
                margin: 20px 0;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
            .loading-message {
                font-size: 16px;
                margin: 10px 0;
                min-height: 24px;
                transition: opacity 0.3s ease-in-out;
            }
            .loading-spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .results {
                margin-top: 30px;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .error {
                color: #dc3545;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .success {
                color: #155724;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .fraud-highlight {
                background-color: #ffebee;
            }
            .pagination {
                margin: 20px 0;
                text-align: center;
            }
            .pagination button {
                margin: 0 5px;
                padding: 8px 16px;
            }
            .pagination button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .fraud-code {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.9em;
                margin: 2px;
                display: inline-block;
            }
            .explanations {
                background-color: #e8f4fd;
                border: 1px solid #bee5eb;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .explanations h4 {
                margin-top: 0;
                color: #0c5460;
            }
            .explanation-item {
                margin: 8px 0;
            }
            .explanation-code {
                font-weight: bold;
                color: #0c5460;
            }
            select {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Fraud Transaction Monitor</h1>
            
            <div class="form-group">
                <label for="filePath">CSV File Path:</label>
                <input type="text" id="filePath" placeholder="Enter the full path to your CSV file" />
            </div>
            
            <div class="form-group">
                <label for="pageSize">Transactions per page:</label>
                <select id="pageSize">
                    <option value="15" selected>15</option>
                    <option value="25">25</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                </select>
            </div>
            
            <button onclick="analyzeTransactions()">Analyze Transactions</button>
            <button onclick="clearResults()">Clear Results</button>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <div class="loading-message" id="loadingMessage">🔄 Analyzing transactions for fraud patterns...</div>
            </div>
            
            <div id="results"></div>
        </div>

        <script>
            let currentPage = 1;
            let currentFilePath = '';
            let loadingInterval = null;
            
            // Array of engaging loading messages
            const loadingMessages = [
                "🔄 Analyzing transactions for fraud patterns...",
                "📊 Loading CSV transaction data...",
                "🔍 Scanning for high-value transactions...",
                "⏰ Checking for unusual transaction times...",
                "👥 Analyzing user behavior patterns...",
                "🏪 Examining merchant relationships...",
                "💸 Detecting suspicious frequency patterns...",
                "🔎 Looking for duplicate transactions...",
                "📈 Calculating transaction velocity...",
                "🛡️ Applying fraud detection rules...",
                "🎯 Identifying potential fraud cases...",
                "📋 Compiling fraud analysis results...",
                "✨ Almost done, finalizing report..."
            ];
            
            function startLoadingAnimation() {
                let messageIndex = 0;
                const loadingMessageEl = document.getElementById('loadingMessage');
                
                loadingInterval = setInterval(() => {
                    loadingMessageEl.style.opacity = '0';
                    setTimeout(() => {
                        loadingMessageEl.textContent = loadingMessages[messageIndex];
                        loadingMessageEl.style.opacity = '1';
                        messageIndex = (messageIndex + 1) % loadingMessages.length;
                    }, 150);
                }, 2000);
            }
            
            function stopLoadingAnimation() {
                if (loadingInterval) {
                    clearInterval(loadingInterval);
                    loadingInterval = null;
                }
            }
            
            async function analyzeTransactions(page = 1) {
                const filePath = document.getElementById('filePath').value.trim();
                const pageSize = parseInt(document.getElementById('pageSize').value);
                
                if (!filePath) {
                    showError('Please enter a file path');
                    return;
                }

                currentFilePath = filePath;
                currentPage = page;

                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                
                loading.style.display = 'block';
                startLoadingAnimation();
                if (page === 1) {
                    results.innerHTML = '';
                }

                try {
                    const response = await fetch('/analyze-fraud', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            file_path: filePath,
                            page: page,
                            page_size: pageSize
                        })
                    });

                    const data = await response.json();
                    
                    if (response.ok) {
                        displayResults(data);
                    } else {
                        showError(data.detail || 'An error occurred');
                    }
                } catch (error) {
                    showError('Network error: ' + error.message);
                } finally {
                    stopLoadingAnimation();
                    loading.style.display = 'none';
                }
            }
            
            function nextPage() {
                analyzeTransactions(currentPage + 1);
            }
            
            function previousPage() {
                analyzeTransactions(currentPage - 1);
            }

            function displayResults(data) {
                const results = document.getElementById('results');
                const fraudPercentage = (data.fraud_percentage * 100).toFixed(2);
                
                let html = `
                    <div class="results">
                        <h2>📊 Analysis Results</h2>
                        <div class="success">
                            <strong>Analysis Complete!</strong><br>
                            Total Transactions: ${data.total_transactions.toLocaleString()}<br>
                            Fraudulent Transactions: ${data.fraudulent_transactions.toLocaleString()}<br>
                            Fraud Percentage: ${fraudPercentage}%
                        </div>
                        
                        <h3>🔧 Rules Applied:</h3>
                        <ul>
                            ${data.rules_applied.map(rule => `<li>${rule}</li>`).join('')}
                        </ul>
                        
                        <div class="explanations">
                            <h4>📋 Fraud Code Explanations:</h4>
                            ${Object.entries(data.fraud_code_explanations).map(([code, explanation]) => `
                                <div class="explanation-item">
                                    <span class="explanation-code">${code}:</span> ${explanation}
                                </div>
                            `).join('')}
                        </div>
                `;

                if (data.fraud_data && data.fraud_data.length > 0) {
                    html += `
                        <h3>🚨 Fraudulent Transactions (Page ${data.pagination.current_page} of ${data.pagination.total_pages}):</h3>
                        <table>
                            <thead>
                                <tr>
                                    ${Object.keys(data.fraud_data[0]).map(key => `<th>${key}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${data.fraud_data.map(row => `
                                    <tr class="fraud-highlight">
                                        ${Object.entries(row).map(([key, value]) => {
                                            if (key === 'fraud_code') {
                                                const codes = value.split(',').filter(code => code.trim());
                                                return `<td>${codes.map(code => `<span class="fraud-code">${code.trim()}</span>`).join('')}</td>`;
                                            }
                                            return `<td>${value}</td>`;
                                        }).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        
                        <div class="pagination">
                            <button onclick="previousPage()" ${!data.pagination.has_previous ? 'disabled' : ''}>
                                ← Previous
                            </button>
                            <span>Page ${data.pagination.current_page} of ${data.pagination.total_pages}</span>
                            <button onclick="nextPage()" ${!data.pagination.has_next ? 'disabled' : ''}>
                                Next →
                            </button>
                        </div>
                    `;
                } else {
                    html += '<p>✅ No fraudulent transactions detected!</p>';
                }

                html += '</div>';
                results.innerHTML = html;
            }

            function showError(message) {
                const results = document.getElementById('results');
                results.innerHTML = `<div class="error">❌ ${message}</div>`;
            }

            function clearResults() {
                stopLoadingAnimation();
                document.getElementById('results').innerHTML = '';
                document.getElementById('filePath').value = '';
                currentPage = 1;
                currentFilePath = '';
            }
        </script>
    </body>
    </html>
    """