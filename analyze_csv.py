#!/usr/bin/env python3
import argparse
import pandas as pd
import json
import os
import datetime
import re
import matplotlib.pyplot as plt
from dateutil import parser as date_parser

class EvictionCSVAnalyzer:
    def __init__(self, csv_file, output_dir="eviction_analysis"):
        """Initialize the CSV analyzer.
        
        Args:
            csv_file: Path to the CSV file with eviction data
            output_dir: Directory to save analysis results
        """
        self.csv_file = csv_file
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Try to load the CSV file
        try:
            self.df = pd.read_csv(csv_file)
            print(f"Successfully loaded {len(self.df)} records from {csv_file}")
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            raise
    
    def clean_data(self):
        """Clean and prepare the data for analysis."""
        print("Cleaning and preparing data...")
        
        # Make column names consistent
        self.df.columns = [col.lower().replace(' ', '_') for col in self.df.columns]
        
        # Try to identify date columns and convert them
        date_columns = []
        
        # Common date column patterns
        date_patterns = [
            'date', 'filed', 'filing', 'hearing', 'judgment', 'decision', 'event'
        ]
        
        for col in self.df.columns:
            if any(pattern in col.lower() for pattern in date_patterns):
                try:
                    # Try to convert to datetime
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    date_columns.append(col)
                    print(f"Converted {col} to date format")
                except:
                    pass
        
        # If no date columns were found, try to detect date patterns in string columns
        if not date_columns:
            for col in self.df.columns:
                if self.df[col].dtype == 'object':  # String column
                    # Take a sample to check
                    sample = self.df[col].dropna().head(5)
                    
                    # Check if the values match common date patterns
                    date_like = True
                    for val in sample:
                        if not isinstance(val, str):
                            date_like = False
                            break
                            
                        # Check against common date patterns
                        date_patterns = [
                            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
                            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
                            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
                        ]
                        
                        if not any(re.match(pattern, val) for pattern in date_patterns):
                            date_like = False
                            break
                    
                    if date_like:
                        try:
                            # Try to convert to datetime
                            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                            date_columns.append(col)
                            print(f"Converted {col} to date format")
                        except:
                            pass
        
        # Alert if no date columns were found
        if not date_columns:
            print("Warning: No date columns were identified. Analysis may be limited.")
        else:
            self.date_columns = date_columns
        
        # Look for status column
        status_columns = [col for col in self.df.columns if 'status' in col.lower()]
        if status_columns:
            self.status_column = status_columns[0]
            print(f"Identified status column: {self.status_column}")
        else:
            self.status_column = None
            print("Warning: No status column identified.")
        
        # Look for case type column
        type_columns = [col for col in self.df.columns if 'type' in col.lower() or 'category' in col.lower()]
        if type_columns:
            self.type_column = type_columns[0]
            print(f"Identified case type column: {self.type_column}")
        else:
            self.type_column = None
            print("Warning: No case type column identified.")
        
        return date_columns
    
    def analyze_timelines(self):
        """Analyze timelines between different stages of eviction cases."""
        print("\nAnalyzing eviction timelines...")
        
        timeline_analysis = {
            "date_ranges": {},
            "time_between_events": {}
        }
        
        # First, get date ranges for each date column
        if hasattr(self, 'date_columns'):
            for col in self.date_columns:
                valid_dates = self.df[col].dropna()
                if not valid_dates.empty:
                    timeline_analysis["date_ranges"][col] = {
                        "min_date": valid_dates.min().strftime('%Y-%m-%d'),
                        "max_date": valid_dates.max().strftime('%Y-%m-%d'),
                        "count": len(valid_dates)
                    }
        
        # Next, calculate time between events if we have multiple date columns
        if hasattr(self, 'date_columns') and len(self.date_columns) > 1:
            for i, col1 in enumerate(self.date_columns):
                for col2 in self.date_columns[i+1:]:
                    # Calculate days between these two events
                    mask = self.df[col1].notna() & self.df[col2].notna()
                    if mask.sum() > 0:
                        days_diff = (self.df.loc[mask, col2] - self.df.loc[mask, col1]).dt.days
                        
                        # Only include positive differences (events in chronological order)
                        days_diff = days_diff[days_diff > 0]
                        
                        if not days_diff.empty:
                            timeline_analysis["time_between_events"][f"{col1}_to_{col2}"] = {
                                "mean_days": days_diff.mean(),
                                "median_days": days_diff.median(),
                                "min_days": days_diff.min(),
                                "max_days": days_diff.max(),
                                "count": len(days_diff)
                            }
        
        self.timeline_analysis = timeline_analysis
        return timeline_analysis
    
    def analyze_status_distribution(self):
        """Analyze the distribution of case statuses."""
        status_analysis = {}
        
        if hasattr(self, 'status_column') and self.status_column:
            status_counts = self.df[self.status_column].value_counts()
            status_analysis = status_counts.to_dict()
            
            print("\nCase Status Distribution:")
            for status, count in status_counts.items():
                print(f"  {status}: {count} cases ({count/len(self.df)*100:.1f}%)")
        
        self.status_analysis = status_analysis
        return status_analysis
    
    def analyze_recent_activity(self):
        """Analyze the most recent eviction activity."""
        recent_activity = {}
        
        if hasattr(self, 'date_columns'):
            # Find the most recent date across all date columns
            latest_dates = {}
            
            for col in self.date_columns:
                valid_dates = self.df[col].dropna()
                if not valid_dates.empty:
                    latest_dates[col] = valid_dates.max()
            
            if latest_dates:
                # Get the most recent date and its column
                most_recent_col = max(latest_dates.items(), key=lambda x: x[1])[0]
                most_recent_date = latest_dates[most_recent_col]
                
                # Find cases with this most recent activity
                recent_cases = self.df[self.df[most_recent_col] == most_recent_date]
                
                recent_activity = {
                    "most_recent_event": most_recent_col,
                    "most_recent_date": most_recent_date.strftime('%Y-%m-%d'),
                    "number_of_cases": len(recent_cases)
                }
                
                print(f"\nMost recent activity: {most_recent_col} on {most_recent_date.strftime('%Y-%m-%d')} ({len(recent_cases)} cases)")
        
        self.recent_activity = recent_activity
        return recent_activity
    
    def predict_future_evictions(self):
        """Predict future eviction timelines based on current patterns."""
        predictions = {}
        
        if hasattr(self, 'timeline_analysis') and self.timeline_analysis["time_between_events"]:
            # Get average time between key events
            time_between_events = self.timeline_analysis["time_between_events"]
            
            # Try to find key transition points
            filing_to_hearing = None
            hearing_to_judgment = None
            judgment_to_eviction = None
            
            # Look for these specific transitions
            for transition, stats in time_between_events.items():
                if 'fil' in transition.lower() and ('hear' in transition.lower() or 'court' in transition.lower()):
                    filing_to_hearing = stats["mean_days"]
                elif ('hear' in transition.lower() or 'court' in transition.lower()) and ('judg' in transition.lower() or 'decis' in transition.lower()):
                    hearing_to_judgment = stats["mean_days"]
                elif ('judg' in transition.lower() or 'decis' in transition.lower()) and ('evict' in transition.lower() or 'execut' in transition.lower() or 'writ' in transition.lower()):
                    judgment_to_eviction = stats["mean_days"]
            
            predictions["filing_to_hearing_days"] = filing_to_hearing
            predictions["hearing_to_judgment_days"] = hearing_to_judgment
            predictions["judgment_to_eviction_days"] = judgment_to_eviction
            
            # Calculate total timeline if we have all the transitions
            if filing_to_hearing and hearing_to_judgment and judgment_to_eviction:
                total_days = filing_to_hearing + hearing_to_judgment + judgment_to_eviction
                predictions["total_filing_to_eviction_days"] = total_days
                
                print(f"\nPredicted timeline from filing to eviction: {total_days:.1f} days")
                print(f"  Filing to hearing: {filing_to_hearing:.1f} days")
                print(f"  Hearing to judgment: {hearing_to_judgment:.1f} days")
                print(f"  Judgment to eviction: {judgment_to_eviction:.1f} days")
            else:
                # If we don't have all transitions, use what we have
                available_transitions = []
                if filing_to_hearing:
                    available_transitions.append(f"Filing to hearing: {filing_to_hearing:.1f} days")
                if hearing_to_judgment:
                    available_transitions.append(f"Hearing to judgment: {hearing_to_judgment:.1f} days")
                if judgment_to_eviction:
                    available_transitions.append(f"Judgment to eviction: {judgment_to_eviction:.1f} days")
                
                if available_transitions:
                    print("\nPartial timeline information available:")
                    for transition in available_transitions:
                        print(f"  {transition}")
                else:
                    print("\nInsufficient data to predict eviction timelines.")
        
        self.predictions = predictions
        return predictions
    
    def generate_visualizations(self):
        """Generate visualizations of the eviction data."""
        print("\nGenerating visualizations...")
        
        # Create a timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Status Distribution Pie Chart
        if hasattr(self, 'status_analysis') and self.status_analysis:
            plt.figure(figsize=(10, 6))
            plt.pie(
                self.status_analysis.values(), 
                labels=self.status_analysis.keys(),
                autopct='%1.1f%%',
                startangle=90
            )
            plt.axis('equal')
            plt.title('Eviction Case Status Distribution')
            
            chart_path = os.path.join(self.output_dir, f"status_distribution_{timestamp}.png")
            plt.savefig(chart_path)
            plt.close()
            print(f"Status distribution chart saved to {chart_path}")
        
        # 2. Timeline Visualization
        if hasattr(self, 'timeline_analysis') and self.timeline_analysis["time_between_events"]:
            events = list(self.timeline_analysis["time_between_events"].keys())
            days = [stats["mean_days"] for stats in self.timeline_analysis["time_between_events"].values()]
            
            plt.figure(figsize=(12, 6))
            plt.barh(events, days, color='skyblue')
            plt.xlabel('Average Days')
            plt.title('Average Time Between Eviction Events')
            plt.tight_layout()
            
            chart_path = os.path.join(self.output_dir, f"event_timelines_{timestamp}.png")
            plt.savefig(chart_path)
            plt.close()
            print(f"Timeline chart saved to {chart_path}")
        
        # 3. Cases Over Time (if filing date is available)
        if hasattr(self, 'date_columns'):
            filing_date_cols = [col for col in self.date_columns if 'fil' in col.lower()]
            if filing_date_cols:
                filing_col = filing_date_cols[0]
                
                # Group by month and count
                monthly_counts = self.df.set_index(filing_col).resample('M').size()
                
                plt.figure(figsize=(12, 6))
                monthly_counts.plot(kind='line', marker='o')
                plt.title('Eviction Cases Filed by Month')
                plt.xlabel('Month')
                plt.ylabel('Number of Cases')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                chart_path = os.path.join(self.output_dir, f"monthly_filings_{timestamp}.png")
                plt.savefig(chart_path)
                plt.close()
                print(f"Monthly filings chart saved to {chart_path}")
    
    def generate_report(self):
        """Generate a comprehensive report of the eviction data analysis."""
        print("\nGenerating report...")
        
        report = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Report header
        report.append("# Eviction Data Analysis Report")
        report.append(f"Generated on: {timestamp}")
        report.append(f"Data source: {self.csv_file}")
        report.append(f"Total records analyzed: {len(self.df)}")
        report.append("")
        
        # Status Distribution
        if hasattr(self, 'status_analysis') and self.status_analysis:
            report.append("## Case Status Distribution")
            
            for status, count in self.status_analysis.items():
                percentage = count / len(self.df) * 100
                report.append(f"- {status}: {count} cases ({percentage:.1f}%)")
            
            report.append("")
        
        # Timeline Analysis
        if hasattr(self, 'timeline_analysis'):
            # Date ranges
            if self.timeline_analysis["date_ranges"]:
                report.append("## Date Ranges")
                
                for column, stats in self.timeline_analysis["date_ranges"].items():
                    report.append(f"### {column.replace('_', ' ').title()}")
                    report.append(f"- Earliest: {stats['min_date']}")
                    report.append(f"- Latest: {stats['max_date']}")
                    report.append(f"- Count: {stats['count']} cases")
                    report.append("")
            
            # Time between events
            if self.timeline_analysis["time_between_events"]:
                report.append("## Timeline Analysis")
                
                for transition, stats in self.timeline_analysis["time_between_events"].items():
                    # Format the transition name for readability
                    transition_label = transition.replace('_', ' ').replace('to', 'to').title()
                    
                    report.append(f"### {transition_label}")
                    report.append(f"- Average: {stats['mean_days']:.1f} days")
                    report.append(f"- Median: {stats['median_days']:.1f} days")
                    report.append(f"- Minimum: {stats['min_days']} days")
                    report.append(f"- Maximum: {stats['max_days']} days")
                    report.append(f"- Sample size: {stats['count']} cases")
                    report.append("")
        
        # Recent Activity
        if hasattr(self, 'recent_activity') and self.recent_activity:
            report.append("## Most Recent Activity")
            report.append(f"- Event type: {self.recent_activity['most_recent_event'].replace('_', ' ').title()}")
            report.append(f"- Date: {self.recent_activity['most_recent_date']}")
            report.append(f"- Number of cases: {self.recent_activity['number_of_cases']}")
            report.append("")
        
        # Predictions
        if hasattr(self, 'predictions') and self.predictions:
            report.append("## Eviction Timeline Predictions")
            
            if 'total_filing_to_eviction_days' in self.predictions:
                report.append(f"- Total time from filing to eviction: **{self.predictions['total_filing_to_eviction_days']:.1f} days**")
                
            if 'filing_to_hearing_days' in self.predictions and self.predictions['filing_to_hearing_days']:
                report.append(f"- Filing to hearing: {self.predictions['filing_to_hearing_days']:.1f} days")
                
            if 'hearing_to_judgment_days' in self.predictions and self.predictions['hearing_to_judgment_days']:
                report.append(f"- Hearing to judgment: {self.predictions['hearing_to_judgment_days']:.1f} days")
                
            if 'judgment_to_eviction_days' in self.predictions and self.predictions['judgment_to_eviction_days']:
                report.append(f"- Judgment to eviction: {self.predictions['judgment_to_eviction_days']:.1f} days")
            
            report.append("")
            
            # Add specific marshal's office insights
            if 'judgment_to_eviction_days' in self.predictions and self.predictions['judgment_to_eviction_days']:
                marshal_time = self.predictions['judgment_to_eviction_days']
                report.append("## Marshal's Office Activity")
                report.append(f"Based on the data, the marshal's office is currently taking approximately **{marshal_time:.1f} days** to execute evictions after a judgment is entered.")
                
                # Add interpretation
                if marshal_time <= 7:
                    report.append("This indicates the marshal's office is processing evictions very quickly, usually within a week.")
                elif marshal_time <= 14:
                    report.append("The marshal's office is processing evictions at a moderate pace, typically within two weeks.")
                elif marshal_time <= 30:
                    report.append("The marshal's office has a significant backlog, taking up to a month to execute evictions.")
                else:
                    report.append("There is a substantial backlog at the marshal's office, with evictions taking over a month to execute after judgment.")
                
                report.append("")
        
        # Recommendations
        report.append("## Recommendations and Insights")
        
        # Add specific recommendations based on the analysis
        if hasattr(self, 'status_analysis') and self.status_analysis:
            # Find the most common status
            most_common_status = max(self.status_analysis.items(), key=lambda x: x[1])
            report.append(f"- The most common case status is '{most_common_status[0]}' ({most_common_status[1]} cases).")
        
        if hasattr(self, 'timeline_analysis') and self.timeline_analysis["time_between_events"]:
            # Find the longest transition
            longest_transition = max(self.timeline_analysis["time_between_events"].items(), 
                                     key=lambda x: x[1]['mean_days'])
            transition_name = longest_transition[0].replace('_', ' ').title()
            transition_days = longest_transition[1]['mean_days']
            
            report.append(f"- The longest delay in the eviction process is between {transition_name}: {transition_days:.1f} days on average.")
        
        if hasattr(self, 'recent_activity') and self.recent_activity:
            report.append(f"- The most recent eviction activity ({self.recent_activity['most_recent_event'].replace('_', ' ').title()}) occurred on {self.recent_activity['most_recent_date']}.")
        
        # Final insights
        report.append("- For tenants facing eviction, this data provides an approximation of how much time they have at each stage of the process.")
        report.append("- For landlords, this information can help set expectations about how long the eviction process will take.")
        report.append("- For housing advocates and policymakers, these timelines highlight potential bottlenecks in the eviction process.")
        
        # Save the report
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.output_dir, f"eviction_analysis_report_{timestamp}.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"Report saved to {report_path}")
        return report_path
    
    def save_analysis_json(self):
        """Save the complete analysis as a JSON file."""
        analysis = {
            "source_file": self.csv_file,
            "record_count": len(self.df),
            "analysis_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add the different analysis components
        if hasattr(self, 'timeline_analysis'):
            analysis["timeline_analysis"] = self.timeline_analysis
        
        if hasattr(self, 'status_analysis'):
            analysis["status_analysis"] = self.status_analysis
        
        if hasattr(self, 'recent_activity'):
            analysis["recent_activity"] = self.recent_activity
        
        if hasattr(self, 'predictions'):
            analysis["predictions"] = self.predictions
        
        # Save to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(self.output_dir, f"eviction_analysis_{timestamp}.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Analysis saved to {json_path}")
        return json_path
    
    def run_full_analysis(self):
        """Run all analysis steps and generate reports."""
        # Clean and prepare the data
        self.clean_data()
        
        # Run all analyses
        self.analyze_timelines()
        self.analyze_status_distribution()
        self.analyze_recent_activity()
        self.predict_future_evictions()
        
        # Generate outputs
        self.generate_visualizations()
        report_path = self.generate_report()
        json_path = self.save_analysis_json()
        
        print("\nAnalysis complete!")
        print(f"Report: {report_path}")
        print(f"JSON data: {json_path}")
        
        return {
            "report_path": report_path,
            "json_path": json_path
        }

def main():
    parser = argparse.ArgumentParser(description="Analyze eviction data from a CSV file")
    parser.add_argument("csv_file", help="Path to the CSV file containing eviction data")
    parser.add_argument("--output-dir", default="eviction_analysis", 
                        help="Output directory for analysis results")
    
    args = parser.parse_args()
    
    print("\nEviction Data CSV Analyzer")
    print("=========================")
    print(f"CSV file: {args.csv_file}")
    print(f"Output directory: {args.output_dir}")
    print("=========================\n")
    
    try:
        analyzer = EvictionCSVAnalyzer(args.csv_file, output_dir=args.output_dir)
        analyzer.run_full_analysis()
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 