#!/usr/bin/env python
"""Generate HTML dashboard for GitHub Pages from metrics results."""

import json
from pathlib import Path

import pandas as pd


def generate_html_dashboard(
    summary_csv: Path,
    regional_csv: Path | None = None,
    output_path: Path | None = None
) -> str:
    """Generate HTML dashboard with embedded data and charts."""
    
    # Load data
    summary_df = pd.read_csv(summary_csv)
    regional_df = pd.read_csv(regional_csv) if regional_csv and regional_csv.exists() else None
    
    # Convert to JSON for JavaScript
    summary_json = summary_df.to_json(orient='records')
    regional_json = regional_df.to_json(orient='records') if regional_df is not None else "[]"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Biosample Enrichment Metrics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .metric-card {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; }}
        .chart-container {{ 
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        h1 {{ margin: 30px 0; }}
        .table {{ margin-top: 20px; }}
        .high-coverage {{ background-color: #d4edda; }}
        .medium-coverage {{ background-color: #fff3cd; }}
        .low-coverage {{ background-color: #f8d7da; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center">🔬 Biosample Enrichment Performance Dashboard</h1>
        
        <div class="row" id="summary-cards">
            <!-- Summary cards will be inserted here -->
        </div>
        
        <div class="chart-container">
            <h3>Coverage by Source and Data Type</h3>
            <div id="coverage-chart"></div>
        </div>
        
        <div class="chart-container">
            <h3>Enrichment Improvement</h3>
            <div id="improvement-chart"></div>
        </div>
        
        <div class="chart-container">
            <h3>Detailed Metrics Table</h3>
            <table class="table table-striped" id="metrics-table">
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Data Type</th>
                        <th>Samples</th>
                        <th>Before (%)</th>
                        <th>After (%)</th>
                        <th>Improvement (%)</th>
                    </tr>
                </thead>
                <tbody id="table-body">
                    <!-- Table rows will be inserted here -->
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Data from Python
        const summaryData = {summary_json};
        const regionalData = {regional_json};
        
        // Generate summary cards
        function generateSummaryCards() {{
            const container = document.getElementById('summary-cards');
            
            // Calculate statistics by source
            const sources = [...new Set(summaryData.map(d => d.source))];
            
            sources.forEach(source => {{
                const sourceData = summaryData.filter(d => d.source === source);
                const avgBefore = sourceData.reduce((sum, d) => sum + d.before, 0) / sourceData.length;
                const avgAfter = sourceData.reduce((sum, d) => sum + d.after, 0) / sourceData.length;
                const avgImprovement = avgAfter - avgBefore;
                
                const card = `
                    <div class="col-md-6">
                        <div class="metric-card">
                            <h4>${{source}} Enrichment</h4>
                            <div class="row">
                                <div class="col-4 text-center">
                                    <div class="metric-value">${{avgBefore.toFixed(1)}}%</div>
                                    <div>Original</div>
                                </div>
                                <div class="col-4 text-center">
                                    <div class="metric-value">${{avgAfter.toFixed(1)}}%</div>
                                    <div>Enriched</div>
                                </div>
                                <div class="col-4 text-center">
                                    <div class="metric-value">+${{avgImprovement.toFixed(1)}}%</div>
                                    <div>Gain</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                container.innerHTML += card;
            }});
        }}
        
        // Generate coverage chart
        function generateCoverageChart() {{
            const dataTypes = [...new Set(summaryData.map(d => d.data_type))];
            const sources = [...new Set(summaryData.map(d => d.source))];
            
            const traces = [];
            sources.forEach(source => {{
                const sourceData = summaryData.filter(d => d.source === source);
                
                // Before bars
                traces.push({{
                    x: dataTypes,
                    y: dataTypes.map(dt => {{
                        const item = sourceData.find(d => d.data_type === dt);
                        return item ? item.before : 0;
                    }}),
                    name: `${{source}} Before`,
                    type: 'bar',
                    marker: {{ opacity: 0.5 }}
                }});
                
                // After bars
                traces.push({{
                    x: dataTypes,
                    y: dataTypes.map(dt => {{
                        const item = sourceData.find(d => d.data_type === dt);
                        return item ? item.after : 0;
                    }}),
                    name: `${{source}} After`,
                    type: 'bar'
                }});
            }});
            
            const layout = {{
                barmode: 'group',
                yaxis: {{ title: 'Coverage (%)' }},
                xaxis: {{ title: 'Data Type' }},
                height: 400
            }};
            
            Plotly.newPlot('coverage-chart', traces, layout);
        }}
        
        // Generate improvement chart
        function generateImprovementChart() {{
            const traces = [];
            const sources = [...new Set(summaryData.map(d => d.source))];
            
            sources.forEach(source => {{
                const sourceData = summaryData.filter(d => d.source === source);
                traces.push({{
                    x: sourceData.map(d => d.data_type),
                    y: sourceData.map(d => d.improvement),
                    name: source,
                    type: 'bar'
                }});
            }});
            
            const layout = {{
                barmode: 'group',
                yaxis: {{ title: 'Improvement (%)' }},
                xaxis: {{ title: 'Data Type' }},
                height: 400
            }};
            
            Plotly.newPlot('improvement-chart', traces, layout);
        }}
        
        // Generate table
        function generateTable() {{
            const tbody = document.getElementById('table-body');
            
            summaryData.forEach(row => {{
                const coverageClass = row.after >= 80 ? 'high-coverage' : 
                                    row.after >= 50 ? 'medium-coverage' : 'low-coverage';
                
                const tr = `
                    <tr class="${{coverageClass}}">
                        <td>${{row.source}}</td>
                        <td>${{row.data_type}}</td>
                        <td>${{row.samples}}</td>
                        <td>${{row.before.toFixed(1)}}</td>
                        <td>${{row.after.toFixed(1)}}</td>
                        <td>${{row.improvement > 0 ? '+' : ''}}${{row.improvement.toFixed(1)}}</td>
                    </tr>
                `;
                tbody.innerHTML += tr;
            }});
        }}
        
        // Initialize dashboard
        generateSummaryCards();
        generateCoverageChart();
        generateImprovementChart();
        generateTable();
    </script>
</body>
</html>"""
    
    if output_path:
        output_path.write_text(html)
        print(f"Dashboard saved to {output_path}")
    
    return html


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: generate_metrics_dashboard.py <summary.csv> [regional.csv] [output.html]")
        sys.exit(1)
    
    summary_csv = Path(sys.argv[1])
    regional_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("metrics_dashboard.html")
    
    generate_html_dashboard(summary_csv, regional_csv, output_path)