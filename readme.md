╔══════════════════════════════════════════════════════════════════════════════╗
║                          🚀 TIMETABLE LOG ANALYZER                           ║ 
║                         Coding Club Recruitment Task                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 USAGE:
   python log_analyzer.py <logfile> [OPTIONS]

📄 REQUIRED ARGUMENTS:
   logfile                    Path to the log file you want to analyze

🔧 OPTIONAL FLAGS:
   --help                     Show this detailed help message
   --endpoints                Show only endpoint popularity statistics
   --performance              Show only performance metrics (response times)  
   --users                    Show only user statistics and year breakdown
   --timetables               Show only timetable generation statistics
   --all                      Show complete report (default behavior)

💡 EXAMPLES:

   Basic Usage:
   python log_analyzer.py server.log
   
   Show only endpoint statistics:
   python log_analyzer.py server.log --endpoints
   
   Show only performance data:
   python log_analyzer.py server.log --performance
   
   Show user statistics:
   python log_analyzer.py server.log --users
   
   Show everything explicitly:
   python log_analyzer.py server.log --all

⚠️  NOTES:
   • If no flags are specified, the complete report is shown by default
   • Only one report section flag can be used at a time
   • Make sure the log file path is correct and accessible
