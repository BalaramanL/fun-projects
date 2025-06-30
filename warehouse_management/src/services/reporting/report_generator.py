"""
Base report generator module for the warehouse management system.

This module provides the foundation for generating reports with various formats.
"""
import logging
import datetime
import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import csv
import jinja2

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Base class for generating reports in various formats."""
    
    def __init__(self, report_dir: Optional[str] = None):
        """
        Initialize the report generator.
        
        Args:
            report_dir: Directory to save reports (defaults to reports/ in current directory)
        """
        self.report_dir = report_dir or os.path.join(os.getcwd(), 'reports')
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Set up Jinja2 environment for HTML templates
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
            ),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    def generate_report(self, 
                       data: Dict[str, Any], 
                       report_type: str, 
                       output_format: str = 'json',
                       filename: Optional[str] = None) -> str:
        """
        Generate a report in the specified format.
        
        Args:
            data: Report data
            report_type: Type of report (e.g., 'inventory', 'orders')
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename (without extension)
            
        Returns:
            Path to the generated report file
        """
        # Generate default filename if not provided
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_{timestamp}"
        
        # Ensure filename has no extension
        filename = os.path.splitext(filename)[0]
        
        # Generate report based on format
        if output_format == 'json':
            return self._generate_json_report(data, filename)
        elif output_format == 'csv':
            return self._generate_csv_report(data, filename)
        elif output_format == 'html':
            return self._generate_html_report(data, report_type, filename)
        elif output_format == 'pdf':
            return self._generate_pdf_report(data, report_type, filename)
        else:
            logger.error(f"Unsupported output format: {output_format}")
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_json_report(self, data: Dict[str, Any], filename: str) -> str:
        """
        Generate a JSON report.
        
        Args:
            data: Report data
            filename: Filename without extension
            
        Returns:
            Path to the generated report file
        """
        filepath = os.path.join(self.report_dir, f"{filename}.json")
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Generated JSON report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            raise
    
    def _generate_csv_report(self, data: Dict[str, Any], filename: str) -> str:
        """
        Generate a CSV report.
        
        Args:
            data: Report data
            filename: Filename without extension
            
        Returns:
            Path to the generated report file
        """
        filepath = os.path.join(self.report_dir, f"{filename}.csv")
        
        try:
            # Convert data to DataFrame
            if 'items' in data and isinstance(data['items'], list):
                df = pd.DataFrame(data['items'])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                # Flatten nested dictionaries
                flattened_data = self._flatten_dict(data)
                df = pd.DataFrame([flattened_data])
            
            # Write to CSV
            df.to_csv(filepath, index=False)
            
            logger.info(f"Generated CSV report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error generating CSV report: {str(e)}")
            raise
    
    def _generate_html_report(self, data: Dict[str, Any], report_type: str, filename: str) -> str:
        """
        Generate an HTML report.
        
        Args:
            data: Report data
            report_type: Type of report
            filename: Filename without extension
            
        Returns:
            Path to the generated report file
        """
        filepath = os.path.join(self.report_dir, f"{filename}.html")
        
        try:
            # Load template
            template_name = f"{report_type}_report.html"
            try:
                template = self.jinja_env.get_template(template_name)
            except jinja2.exceptions.TemplateNotFound:
                # Fall back to generic template
                template = self.jinja_env.get_template("generic_report.html")
            
            # Generate charts if needed
            charts = {}
            if 'generate_charts' in data and data['generate_charts']:
                charts = self._generate_charts(data, filename)
            
            # Render template
            html_content = template.render(
                report_title=data.get('title', f"{report_type.title()} Report"),
                report_data=data,
                charts=charts,
                generated_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Write to file
            with open(filepath, 'w') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            raise
    
    def _generate_pdf_report(self, data: Dict[str, Any], report_type: str, filename: str) -> str:
        """
        Generate a PDF report.
        
        Args:
            data: Report data
            report_type: Type of report
            filename: Filename without extension
            
        Returns:
            Path to the generated report file
        """
        # First generate HTML
        html_path = self._generate_html_report(data, report_type, filename)
        pdf_path = os.path.join(self.report_dir, f"{filename}.pdf")
        
        try:
            # Convert HTML to PDF using weasyprint if available
            try:
                from weasyprint import HTML
                HTML(html_path).write_pdf(pdf_path)
                logger.info(f"Generated PDF report: {pdf_path}")
                return pdf_path
            except ImportError:
                logger.warning("weasyprint not installed. Unable to generate PDF.")
                return html_path
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _generate_charts(self, data: Dict[str, Any], filename: str) -> Dict[str, str]:
        """
        Generate charts for the report.
        
        Args:
            data: Report data
            filename: Base filename
            
        Returns:
            Dictionary mapping chart names to file paths
        """
        charts = {}
        charts_dir = os.path.join(self.report_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        
        # Generate charts based on data type
        try:
            if 'time_series_data' in data:
                # Time series chart
                plt.figure(figsize=(10, 6))
                time_data = data['time_series_data']
                
                if isinstance(time_data, dict):
                    for key, values in time_data.items():
                        if isinstance(values, dict):
                            x = list(values.keys())
                            y = list(values.values())
                            plt.plot(x, y, marker='o', label=key)
                        elif isinstance(values, list) and 'x' in time_data and len(time_data['x']) == len(values):
                            plt.plot(time_data['x'], values, marker='o', label=key)
                
                plt.title(data.get('chart_title', 'Time Series Data'))
                plt.xlabel(data.get('x_label', 'Time'))
                plt.ylabel(data.get('y_label', 'Value'))
                plt.legend()
                plt.tight_layout()
                
                chart_path = os.path.join(charts_dir, f"{filename}_timeseries.png")
                plt.savefig(chart_path)
                plt.close()
                
                charts['time_series'] = os.path.relpath(chart_path, self.report_dir)
            
            if 'distribution_data' in data:
                # Distribution chart
                plt.figure(figsize=(10, 6))
                dist_data = data['distribution_data']
                
                if isinstance(dist_data, list):
                    sns.histplot(dist_data, kde=True)
                elif isinstance(dist_data, dict):
                    for key, values in dist_data.items():
                        if isinstance(values, list):
                            sns.histplot(values, kde=True, label=key)
                
                plt.title(data.get('dist_title', 'Distribution'))
                plt.xlabel(data.get('dist_x_label', 'Value'))
                plt.ylabel(data.get('dist_y_label', 'Frequency'))
                plt.legend()
                plt.tight_layout()
                
                chart_path = os.path.join(charts_dir, f"{filename}_distribution.png")
                plt.savefig(chart_path)
                plt.close()
                
                charts['distribution'] = os.path.relpath(chart_path, self.report_dir)
            
            if 'pie_data' in data:
                # Pie chart
                plt.figure(figsize=(8, 8))
                pie_data = data['pie_data']
                
                if isinstance(pie_data, dict):
                    plt.pie(
                        list(pie_data.values()),
                        labels=list(pie_data.keys()),
                        autopct='%1.1f%%',
                        startangle=90
                    )
                
                plt.title(data.get('pie_title', 'Distribution'))
                plt.axis('equal')
                plt.tight_layout()
                
                chart_path = os.path.join(charts_dir, f"{filename}_pie.png")
                plt.savefig(chart_path)
                plt.close()
                
                charts['pie'] = os.path.relpath(chart_path, self.report_dir)
        
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
        
        return charts
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """
        Flatten nested dictionaries for CSV export.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested items
            sep: Separator for keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                # Convert list to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
                
        return dict(items)
