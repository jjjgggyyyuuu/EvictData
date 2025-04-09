#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import os
import json
import re
import argparse

class MarshalEvictionAnalyzer:
    def __init__(self, csv_file, output_dir="marshal_eviction_analysis"):
        """Initialize the Marshal Eviction Analyzer.
        
        Args:
            csv_file: Path to the CSV file with eviction data
            output_dir: Directory to save analysis results
        """
        self.csv_file = csv_file
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Load and process the CSV file
        try:
            self.df = pd.read_csv(csv_file)
            print(f"Successfully loaded {len(self.df)} records from {csv_file}")
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            raise
    
    def clean_and_identify_key_fields(self):
        """Clean data and identify key fields for marshal execution analysis."""
        print("\nCleaning data and identifying key fields for eviction analysis...")
        
        # Standardize column names
        self.df.columns = [col.lower().replace(' ', '_') for col in self.df.columns]
        
        # Search for key columns using common patterns
        self.filing_date_col = self._find_column(['file', 'fil', 'filed', 'filing_date', 'date_filed'])
        self.judgment_date_col = self._find_column(['judgment', 'judg', 'judgment_date', 'date_of_judgment'])
        self.eviction_date_col = self._find_column(['evict', 'marshal', 'execution', 'served', 'removal', 'lockout'])
        self.status_col = self._find_column(['status', 'case_status', 'disposition'])
        self.case_number_col = self._find_column(['case', 'number', 'case_number', 'docket', 'id'])
        
        # Convert date columns
        date_cols = [col for col in [self.filing_date_col, self.judgment_date_col, self.eviction_date_col] if col]
        for col in date_cols:
            try:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                print(f"Converted {col} to date format")
            except:
                print(f"Warning: Could not convert {col} to date format")
        
        # Identify completed evictions
        if self.eviction_date_col:
            self.completed_evictions = self.df[self.df[self.eviction_date_col].notna()]
            print(f"Found {len(self.completed_evictions)} completed evictions with marshal execution dates")
        elif self.status_col:
            # Look for status values indicating completed evictions
            eviction_status_patterns = ['executed', 'complete', 'evicted', 'removed', 'lockout', 'closed']
            mask = self.df[self.status_col].astype(str).str.lower().apply(
                lambda x: any(pattern in x for pattern in eviction_status_patterns)
            )
            self.completed_evictions = self.df[mask]
            print(f"Found {len(self.completed_evictions)} completed evictions based on status")
        else:
            print("Warning: Could not identify completed evictions. Analysis will be limited.")
            self.completed_evictions = self.df
        
        if len(self.completed_evictions) == 0:
            print("No completed evictions found in the data.")
        
        return self.completed_evictions
    
    def _find_column(self, patterns):
        """Find a column that matches one of the patterns."""
        for pattern in patterns:
            matches = [col for col in self.df.columns if pattern in col.lower()]
            if matches:
                print(f"Found {matches[0]} matching pattern '{pattern}'")
                return matches[0]
        print(f"Warning: No column found matching patterns {patterns}")
        return None
    
    def analyze_marshal_timelines(self):
        """Analyze timelines for marshal-executed evictions."""
        print("\nAnalyzing marshal execution timelines...")
        
        timeline_stats = {}
        
        # Check if we have the necessary date columns
        if not self.filing_date_col or (not self.judgment_date_col and not self.eviction_date_col):
            print("Warning: Insufficient date columns for timeline analysis")
            return timeline_stats
        
        # Filing to eviction (total process time)
        if self.filing_date_col and self.eviction_date_col:
            mask = (
                self.completed_evictions[self.filing_date_col].notna() & 
                self.completed_evictions[self.eviction_date_col].notna()
            )
            
            if mask.sum() > 0:
                days_diff = (
                    self.completed_evictions.loc[mask, self.eviction_date_col] - 
                    self.completed_evictions.loc[mask, self.filing_date_col]
                ).dt.days
                
                # Only include positive differences
                days_diff = days_diff[days_diff > 0]
                
                if not days_diff.empty:
                    timeline_stats["filing_to_eviction"] = {
                        "mean_days": days_diff.mean(),
                        "median_days": days_diff.median(),
                        "min_days": days_diff.min(),
                        "max_days": days_diff.max(),
                        "count": len(days_diff)
                    }
                    
                    print(f"Filing to eviction (total process): {days_diff.mean():.1f} days on average (median: {days_diff.median():.1f})")
        
        # Judgment to eviction (marshal-specific time)
        if self.judgment_date_col and self.eviction_date_col:
            mask = (
                self.completed_evictions[self.judgment_date_col].notna() & 
                self.completed_evictions[self.eviction_date_col].notna()
            )
            
            if mask.sum() > 0:
                days_diff = (
                    self.completed_evictions.loc[mask, self.eviction_date_col] - 
                    self.completed_evictions.loc[mask, self.judgment_date_col]
                ).dt.days
                
                # Only include positive differences
                days_diff = days_diff[days_diff > 0]
                
                if not days_diff.empty:
                    timeline_stats["judgment_to_eviction"] = {
                        "mean_days": days_diff.mean(),
                        "median_days": days_diff.median(),
                        "min_days": days_diff.min(),
                        "max_days": days_diff.max(),
                        "count": len(days_diff)
                    }
                    
                    print(f"Judgment to eviction (marshal execution time): {days_diff.mean():.1f} days on average (median: {days_diff.median():.1f})")
        
        # Filing to judgment (court process time)
        if self.filing_date_col and self.judgment_date_col:
            mask = (
                self.completed_evictions[self.filing_date_col].notna() & 
                self.completed_evictions[self.judgment_date_col].notna()
            )
            
            if mask.sum() > 0:
                days_diff = (
                    self.completed_evictions.loc[mask, self.judgment_date_col] - 
                    self.completed_evictions.loc[mask, self.filing_date_col]
                ).dt.days
                
                # Only include positive differences
                days_diff = days_diff[days_diff > 0]
                
                if not days_diff.empty:
                    timeline_stats["filing_to_judgment"] = {
                        "mean_days": days_diff.mean(),
                        "median_days": days_diff.median(),
                        "min_days": days_diff.min(),
                        "max_days": days_diff.max(),
                        "count": len(days_diff)
                    }
                    
                    print(f"Filing to judgment (court process): {days_diff.mean():.1f} days on average (median: {days_diff.median():.1f})")
        
        self.timeline_stats = timeline_stats
        return timeline_stats
    
    def analyze_marshal_trends(self):
        """Analyze trends in marshal eviction execution over time."""
        print("\nAnalyzing trends in marshal eviction execution...")
        
        trends = {}
        
        # Check if we have the necessary eviction date column
        if not self.eviction_date_col:
            print("Warning: No eviction date column found for trend analysis")
            return trends
        
        # Ensure we have datetime format
        if pd.api.types.is_datetime64_any_dtype(self.completed_evictions[self.eviction_date_col]):
            # Group by month and count
            evictions_by_month = self.completed_evictions.set_index(self.eviction_date_col).resample('M').size()
            
            if not evictions_by_month.empty:
                # Calculate monthly statistics
                trends["monthly_counts"] = evictions_by_month.to_dict()
                
                # Get the latest 3 months with data
                latest_months = evictions_by_month.tail(3)
                trends["recent_months"] = latest_months.to_dict()
                
                # Calculate moving averages
                if len(evictions_by_month) >= 3:
                    trends["three_month_moving_avg"] = evictions_by_month.rolling(3).mean().dropna().to_dict()
                
                print(f"Analyzed monthly eviction trends from {evictions_by_month.index.min().strftime('%Y-%m')} to {evictions_by_month.index.max().strftime('%Y-%m')}")
                
                # Calculate and display the most recent month's data
                most_recent_month = evictions_by_month.index.max()
                most_recent_count = evictions_by_month.loc[most_recent_month]
                print(f"Most recent month ({most_recent_month.strftime('%Y-%m')}): {most_recent_count} evictions")
                
                # Compare to previous month
                if len(evictions_by_month) > 1:
                    previous_month = evictions_by_month.index[-2]
                    previous_count = evictions_by_month.loc[previous_month]
                    change = ((most_recent_count - previous_count) / previous_count) * 100
                    print(f"Change from previous month: {change:.1f}% ({previous_count} to {most_recent_count})")
        else:
            print(f"Warning: {self.eviction_date_col} is not in date format. Trend analysis skipped.")
        
        self.trends = trends
        return trends
    
    def analyze_processing_time_distribution(self):
        """Analyze the distribution of processing times for marshal executions."""
        print("\nAnalyzing distribution of marshal execution times...")
        
        distribution = {}
        
        # Check if we have judgment to eviction stats
        if not hasattr(self, 'timeline_stats') or 'judgment_to_eviction' not in self.timeline_stats:
            if self.judgment_date_col and self.eviction_date_col:
                self.analyze_marshal_timelines()  # Try to calculate timelines first
            else:
                print("Warning: Cannot analyze processing time distribution without judgment and eviction dates")
                return distribution
        
        if hasattr(self, 'timeline_stats') and 'judgment_to_eviction' in self.timeline_stats:
            # Create time buckets for analysis
            mask = (
                self.completed_evictions[self.judgment_date_col].notna() & 
                self.completed_evictions[self.eviction_date_col].notna()
            )
            
            if mask.sum() > 0:
                days_diff = (
                    self.completed_evictions.loc[mask, self.eviction_date_col] - 
                    self.completed_evictions.loc[mask, self.judgment_date_col]
                ).dt.days
                
                # Only include positive differences
                days_diff = days_diff[days_diff > 0]
                
                if not days_diff.empty:
                    # Create time buckets
                    buckets = [
                        (0, 7, "0-7 days (very fast)"),
                        (8, 14, "8-14 days (fast)"),
                        (15, 30, "15-30 days (moderate)"),
                        (31, 60, "31-60 days (slow)"),
                        (61, float('inf'), "61+ days (very slow)")
                    ]
                    
                    bucket_counts = {}
                    for start, end, label in buckets:
                        count = ((days_diff >= start) & (days_diff <= end)).sum()
                        bucket_counts[label] = {
                            "count": int(count),
                            "percentage": (count / len(days_diff)) * 100
                        }
                    
                    distribution["execution_time_buckets"] = bucket_counts
                    
                    # Print the distribution
                    print("Distribution of marshal execution times:")
                    for label, stats in bucket_counts.items():
                        print(f"  {label}: {stats['count']} evictions ({stats['percentage']:.1f}%)")
        
        self.distribution = distribution
        return distribution
    
    def generate_marshal_report(self):
        """Generate a report focused on marshal execution of evictions."""
        print("\nGenerating marshal execution report...")
        
        report = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Report header
        report.append("# Marshal Eviction Execution Analysis")
        report.append(f"Generated on: {timestamp}")
        report.append(f"Data source: {self.csv_file}")
        report.append(f"Total records analyzed: {len(self.df)}")
        if hasattr(self, 'completed_evictions'):
            report.append(f"Completed evictions identified: {len(self.completed_evictions)}")
        report.append("")
        
        # Timeline statistics
        if hasattr(self, 'timeline_stats') and self.timeline_stats:
            report.append("## Eviction Timeline Analysis")
            
            if 'filing_to_eviction' in self.timeline_stats:
                stats = self.timeline_stats['filing_to_eviction']
                report.append("### Filing to Eviction (Total Process)")
                report.append(f"- Average: **{stats['mean_days']:.1f} days**")
                report.append(f"- Median: {stats['median_days']:.1f} days")
                report.append(f"- Range: {stats['min_days']} to {stats['max_days']} days")
                report.append(f"- Sample size: {stats['count']} completed evictions")
                report.append("")
            
            if 'judgment_to_eviction' in self.timeline_stats:
                stats = self.timeline_stats['judgment_to_eviction']
                report.append("### Judgment to Eviction (Marshal Execution Time)")
                report.append(f"- Average: **{stats['mean_days']:.1f} days**")
                report.append(f"- Median: {stats['median_days']:.1f} days")
                report.append(f"- Range: {stats['min_days']} to {stats['max_days']} days")
                report.append(f"- Sample size: {stats['count']} completed evictions")
                report.append("")
            
            if 'filing_to_judgment' in self.timeline_stats:
                stats = self.timeline_stats['filing_to_judgment']
                report.append("### Filing to Judgment (Court Process)")
                report.append(f"- Average: {stats['mean_days']:.1f} days")
                report.append(f"- Median: {stats['median_days']:.1f} days")
                report.append(f"- Range: {stats['min_days']} to {stats['max_days']} days")
                report.append(f"- Sample size: {stats['count']} cases")
                report.append("")
        
        # Marshal execution time distribution
        if hasattr(self, 'distribution') and 'execution_time_buckets' in self.distribution:
            report.append("## Marshal Execution Time Distribution")
            
            for label, stats in self.distribution['execution_time_buckets'].items():
                report.append(f"- **{label}**: {stats['count']} evictions ({stats['percentage']:.1f}%)")
            
            report.append("")
        
        # Recent trends
        if hasattr(self, 'trends') and 'recent_months' in self.trends:
            report.append("## Recent Marshal Activity")
            
            recent_months = self.trends['recent_months']
            if recent_months:
                report.append("### Most Recent Months")
                for date, count in sorted(recent_months.items(), reverse=True):
                    month_str = pd.to_datetime(date).strftime('%Y-%m')
                    report.append(f"- **{month_str}**: {count} evictions executed")
                
                # Get the most recent month and previous month data
                dates = sorted(list(recent_months.keys()))
                if len(dates) >= 2:
                    most_recent = dates[-1]
                    previous = dates[-2]
                    
                    most_recent_count = recent_months[most_recent]
                    previous_count = recent_months[previous]
                    
                    change = ((most_recent_count - previous_count) / previous_count) * 100
                    report.append("")
                    report.append(f"### Month-to-Month Change")
                    report.append(f"- {pd.to_datetime(previous).strftime('%Y-%m')}: {previous_count} evictions")
                    report.append(f"- {pd.to_datetime(most_recent).strftime('%Y-%m')}: {most_recent_count} evictions")
                    report.append(f"- Percentage change: **{change:.1f}%**")
                
                report.append("")
        
        # Marshal insights and recommendations
        report.append("## Marshal's Office Insights")
        
        # Add specific marshal's office insights based on the data
        if hasattr(self, 'timeline_stats') and 'judgment_to_eviction' in self.timeline_stats:
            marshal_time = self.timeline_stats['judgment_to_eviction']['mean_days']
            
            report.append(f"Based on the data, the **marshal's office is currently taking approximately {marshal_time:.1f} days on average** to execute evictions after a judgment is entered.")
            
            # Add interpretation
            if marshal_time <= 7:
                report.append("This indicates the marshal's office is processing evictions very quickly, usually within a week.")
                report.append("For tenants with a judgment against them, there is very little time before eviction is executed.")
            elif marshal_time <= 14:
                report.append("The marshal's office is processing evictions at a moderate pace, typically within two weeks.")
                report.append("Tenants with judgments should prepare to relocate within approximately two weeks.")
            elif marshal_time <= 30:
                report.append("The marshal's office has a significant backlog, taking up to a month to execute evictions.")
                report.append("This provides tenants with more time to find alternative housing after a judgment.")
            else:
                report.append("There is a substantial backlog at the marshal's office, with evictions taking over a month to execute after judgment.")
                report.append("The lengthy delay between judgment and execution suggests possible resource constraints at the marshal's office.")
            
            report.append("")
        
        # Add trends insights if available
        if hasattr(self, 'trends') and 'recent_months' in self.trends:
            recent_months = self.trends['recent_months']
            dates = sorted(list(recent_months.keys()))
            if len(dates) >= 2:
                most_recent = dates[-1]
                previous = dates[-2]
                
                most_recent_count = recent_months[most_recent]
                previous_count = recent_months[previous]
                
                change = ((most_recent_count - previous_count) / previous_count) * 100
                
                report.append("### Current Trend Analysis")
                
                if change > 20:
                    report.append(f"Marshal eviction activity has **increased dramatically** by {change:.1f}% in the most recent month.")
                    report.append("This suggests the marshal's office is clearing backlogs or prioritizing eviction executions.")
                elif change > 5:
                    report.append(f"Marshal eviction activity has **increased moderately** by {change:.1f}% in the most recent month.")
                    report.append("This suggests a slight acceleration in processing evictions.")
                elif change > -5:
                    report.append(f"Marshal eviction activity has remained **relatively stable** ({change:.1f}% change) in the most recent month.")
                    report.append("This suggests consistent processing capacity at the marshal's office.")
                elif change > -20:
                    report.append(f"Marshal eviction activity has **decreased moderately** by {-change:.1f}% in the most recent month.")
                    report.append("This may indicate growing backlogs or reduced capacity at the marshal's office.")
                else:
                    report.append(f"Marshal eviction activity has **decreased significantly** by {-change:.1f}% in the most recent month.")
                    report.append("This substantial decrease may indicate policy changes, resource constraints, or seasonal factors affecting the marshal's office.")
                
                report.append("")
        
        # Final recommendations
        report.append("## Practical Recommendations")
        
        if hasattr(self, 'timeline_stats'):
            if 'judgment_to_eviction' in self.timeline_stats:
                marshal_time = self.timeline_stats['judgment_to_eviction']['mean_days']
                report.append(f"- **For tenants**: After a judgment is entered, expect the marshal to execute the eviction in approximately **{marshal_time:.1f} days** on average.")
            
            if 'filing_to_eviction' in self.timeline_stats:
                total_time = self.timeline_stats['filing_to_eviction']['mean_days']
                report.append(f"- **For landlords**: The complete eviction process from filing to execution currently takes approximately **{total_time:.1f} days** on average.")
        
        report.append("- **For advocates**: Use this data to help tenants understand how much time they realistically have to find new housing after an eviction judgment.")
        report.append("- **For policymakers**: This analysis highlights the actual pace of evictions and can inform decisions about eviction prevention and housing assistance programs.")
        
        # Save the report
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.output_dir, f"marshal_eviction_report_{timestamp}.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"Marshal execution report saved to {report_path}")
        return report_path
    
    def generate_visualizations(self):
        """Generate visualizations focused on marshal execution timelines."""
        print("\nGenerating marshal execution visualizations...")
        
        # Create a timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Marshal Execution Time Distribution
        if hasattr(self, 'distribution') and 'execution_time_buckets' in self.distribution:
            labels = []
            counts = []
            
            for label, stats in self.distribution['execution_time_buckets'].items():
                labels.append(label)
                counts.append(stats['count'])
            
            plt.figure(figsize=(12, 6))
            bars = plt.bar(labels, counts, color='darkblue')
            
            # Add data labels on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f"{height:.0f}",
                        ha='center', va='bottom')
                
            plt.title('Distribution of Marshal Execution Times', fontsize=16)
            plt.ylabel('Number of Evictions', fontsize=12)
            plt.xticks(rotation=30, ha='right')
            plt.tight_layout()
            
            chart_path = os.path.join(self.output_dir, f"marshal_execution_distribution_{timestamp}.png")
            plt.savefig(chart_path)
            plt.close()
            print(f"Marshal execution distribution chart saved to {chart_path}")
        
        # 2. Monthly Eviction Executions Trend
        if hasattr(self, 'trends') and 'monthly_counts' in self.trends:
            monthly_data = self.trends['monthly_counts']
            
            # Convert to Series for easier plotting
            monthly_series = pd.Series(monthly_data)
            monthly_series.index = pd.to_datetime(monthly_series.index)
            
            plt.figure(figsize=(14, 6))
            
            # Plot the monthly counts
            plt.plot(monthly_series.index, monthly_series.values, 'b-o', linewidth=2, markersize=8)
            
            # Add 3-month moving average if available
            if 'three_month_moving_avg' in self.trends:
                moving_avg = pd.Series(self.trends['three_month_moving_avg'])
                moving_avg.index = pd.to_datetime(moving_avg.index)
                plt.plot(moving_avg.index, moving_avg.values, 'r--', linewidth=2, 
                         label='3-Month Moving Average')
                plt.legend()
            
            plt.title('Marshal Eviction Executions by Month', fontsize=16)
            plt.xlabel('Month', fontsize=12)
            plt.ylabel('Number of Evictions Executed', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Format x-axis to show months
            plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            chart_path = os.path.join(self.output_dir, f"monthly_eviction_trend_{timestamp}.png")
            plt.savefig(chart_path)
            plt.close()
            print(f"Monthly eviction trend chart saved to {chart_path}")
        
        # 3. Timeline Comparison (Filing to Judgment vs. Judgment to Eviction)
        if hasattr(self, 'timeline_stats'):
            timeline_data = {}
            
            if 'filing_to_judgment' in self.timeline_stats:
                timeline_data['Court Process\n(Filing to Judgment)'] = self.timeline_stats['filing_to_judgment']['mean_days']
            
            if 'judgment_to_eviction' in self.timeline_stats:
                timeline_data['Marshal Process\n(Judgment to Eviction)'] = self.timeline_stats['judgment_to_eviction']['mean_days']
            
            if 'filing_to_eviction' in self.timeline_stats:
                timeline_data['Total Process\n(Filing to Eviction)'] = self.timeline_stats['filing_to_eviction']['mean_days']
            
            if timeline_data:
                plt.figure(figsize=(10, 6))
                
                # Create horizontal bar chart
                bars = plt.barh(list(timeline_data.keys()), list(timeline_data.values()), 
                               color=['lightblue', 'darkblue', 'navy'])
                
                # Add data labels
                for bar in bars:
                    width = bar.get_width()
                    plt.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                            f"{width:.1f} days",
                            ha='left', va='center')
                
                plt.title('Average Days in Eviction Process', fontsize=16)
                plt.xlabel('Days', fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.7, axis='x')
                
                plt.tight_layout()
                
                chart_path = os.path.join(self.output_dir, f"eviction_timeline_comparison_{timestamp}.png")
                plt.savefig(chart_path)
                plt.close()
                print(f"Eviction timeline comparison chart saved to {chart_path}")
    
    def run_full_analysis(self):
        """Run all marshal execution analysis steps."""
        # Clean and identify key fields
        self.clean_and_identify_key_fields()
        
        # Run analyses
        self.analyze_marshal_timelines()
        self.analyze_marshal_trends()
        self.analyze_processing_time_distribution()
        
        # Generate outputs
        self.generate_visualizations()
        report_path = self.generate_marshal_report()
        
        print("\nMarshal eviction analysis complete!")
        print(f"Report saved to: {report_path}")
        
        return report_path

def main():
    parser = argparse.ArgumentParser(description="Analyze marshal-executed evictions from CSV data")
    parser.add_argument("csv_file", help="Path to the CSV file containing eviction data")
    parser.add_argument("--output-dir", default="marshal_eviction_analysis", 
                        help="Output directory for analysis results")
    
    args = parser.parse_args()
    
    print("\nMarshal Eviction Timeline Analyzer")
    print("=================================")
    print(f"CSV file: {args.csv_file}")
    print(f"Output directory: {args.output_dir}")
    print("=================================\n")
    
    try:
        analyzer = MarshalEvictionAnalyzer(args.csv_file, output_dir=args.output_dir)
        analyzer.run_full_analysis()
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 