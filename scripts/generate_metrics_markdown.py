#!/usr/bin/env python
"""Generate markdown report from metrics CSV for GitHub display."""

import sys
from pathlib import Path

import pandas as pd


def generate_markdown_table(df: pd.DataFrame) -> str:
    """Convert DataFrame to GitHub-flavored markdown table."""
    lines = []
    
    # Header
    lines.append("| " + " | ".join(df.columns) + " |")
    lines.append("|" + "|".join(["---"] * len(df.columns)) + "|")
    
    # Rows
    for _, row in df.iterrows():
        values = []
        for col in df.columns:
            val = row[col]
            # Format percentages nicely
            if isinstance(val, (int, float)) and col != "samples":
                values.append(f"{val:.1f}%")
            else:
                values.append(str(val))
        lines.append("| " + " | ".join(values) + " |")
    
    return "\n".join(lines)


def generate_metrics_report(csv_path: Path) -> str:
    """Generate enrichment performance report showing what data types are enriched."""
    df = pd.read_csv(csv_path)
    
    report = []
    
    # Header
    report.append("## 🔬 Enrichment Performance Analysis")
    report.append("")
    report.append("This report shows **what data types are being enriched** and **the degree of enrichment** for each input source.")
    report.append("")
    
    # NMDC Performance
    nmdc_data = df[df["source"] == "NMDC"]
    if not nmdc_data.empty:
        report.append("### 📊 NMDC Biosample Enrichment")
        report.append("")
        
        # What's being enriched
        enriched_types = nmdc_data[nmdc_data["after"] > nmdc_data["before"]]
        report.append(f"**Enriched Data Types:** {len(enriched_types)}/{len(nmdc_data)}")
        report.append("")
        
        # Performance by data type
        report.append("| Data Type | Original Coverage | Enriched Coverage | Enrichment Gain |")
        report.append("|-----------|------------------|-------------------|-----------------|")
        
        for _, row in nmdc_data.iterrows():
            original = f"{row['before']:.1f}%"
            enriched = f"{row['after']:.1f}%"
            gain = f"+{row['improvement']:.1f}%" if row['improvement'] > 0 else f"{row['improvement']:.1f}%"
            
            # Highlight high-performing enrichments
            if row['improvement'] > 50:
                gain = f"**{gain}** 🎯"
            elif row['improvement'] > 20:
                gain = f"**{gain}**"
                
            report.append(f"| {row['data_type']} | {original} | {enriched} | {gain} |")
        
        report.append("")
        
        # Summary stats
        avg_after = nmdc_data["after"].mean()
        fully_enriched = len(nmdc_data[nmdc_data["after"] >= 90])
        poorly_covered = len(nmdc_data[nmdc_data["after"] < 50])
        
        report.append("**Summary:**")
        report.append(f"- Average enriched coverage: **{avg_after:.1f}%**")
        report.append(f"- Fully enriched (≥90%): **{fully_enriched}** data types")
        report.append(f"- Need improvement (<50%): **{poorly_covered}** data types")
        report.append("")
    
    # GOLD Performance
    gold_data = df[df["source"] == "GOLD"]
    if not gold_data.empty:
        report.append("### 🏆 GOLD Biosample Enrichment")
        report.append("")
        
        # What's being enriched
        enriched_types = gold_data[gold_data["after"] > gold_data["before"]]
        report.append(f"**Enriched Data Types:** {len(enriched_types)}/{len(gold_data)}")
        report.append("")
        
        # Performance by data type
        report.append("| Data Type | Original Coverage | Enriched Coverage | Enrichment Gain |")
        report.append("|-----------|------------------|-------------------|-----------------|")
        
        for _, row in gold_data.iterrows():
            original = f"{row['before']:.1f}%"
            enriched = f"{row['after']:.1f}%"
            gain = f"+{row['improvement']:.1f}%" if row['improvement'] > 0 else f"{row['improvement']:.1f}%"
            
            # Highlight high-performing enrichments
            if row['improvement'] > 50:
                gain = f"**{gain}** 🎯"
            elif row['improvement'] > 20:
                gain = f"**{gain}**"
                
            report.append(f"| {row['data_type']} | {original} | {enriched} | {gain} |")
        
        report.append("")
        
        # Summary stats
        avg_after = gold_data["after"].mean()
        fully_enriched = len(gold_data[gold_data["after"] >= 90])
        poorly_covered = len(gold_data[gold_data["after"] < 50])
        
        report.append("**Summary:**")
        report.append(f"- Average enriched coverage: **{avg_after:.1f}%**")
        report.append(f"- Fully enriched (≥90%): **{fully_enriched}** data types")
        report.append(f"- Need improvement (<50%): **{poorly_covered}** data types")
        report.append("")
    
    # Overall Assessment
    report.append("### 🎯 Overall Enrichment Performance")
    report.append("")
    
    # Identify what's working well
    high_performers = df[df["after"] >= 90]
    if not high_performers.empty:
        report.append("**High-Performance Enrichments (≥90% coverage):**")
        for _, row in high_performers.iterrows():
            report.append(f"- {row['source']} {row['data_type']}: {row['after']:.1f}%")
        report.append("")
    
    # Identify what needs work
    low_performers = df[df["after"] < 50]
    if not low_performers.empty:
        report.append("**Needs Improvement (<50% coverage):**")
        for _, row in low_performers.iterrows():
            report.append(f"- {row['source']} {row['data_type']}: {row['after']:.1f}%")
        report.append("")
    
    # Data type comparison
    report.append("### 📈 Data Type Analysis")
    report.append("")
    
    # Group by data type to compare sources
    data_types = df["data_type"].unique()
    for dt in data_types:
        dt_data = df[df["data_type"] == dt]
        report.append(f"**{dt}:**")
        for _, row in dt_data.iterrows():
            status = "✅" if row["after"] >= 75 else "⚠️" if row["after"] >= 50 else "❌"
            report.append(f"- {row['source']}: {row['before']:.1f}% → {row['after']:.1f}% {status}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: generate_metrics_markdown.py <metrics_summary.csv>")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)
    
    report = generate_metrics_report(csv_path)
    print(report)