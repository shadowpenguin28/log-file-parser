import re
import argparse
from datetime import datetime

#test 
class LogAnalyzer():
    def __init__(self):
        # Data structures to store parsed information
        self.http_requests = []
        self.router_logs = []
        self.algorithm_logs = []
        self.generation_logs = []
        
        # Analysis results (using regular dicts instead of defaultdict)
        self.endpoints = {}
        self.response_times = {}  # endpoint -> list of times in microseconds
        self.users = set()
        self.users_by_year = {}
        self.algorithms_used = {}
        self.timetables_generated = []
        self.total_requests = 0
    def parse_response_time(self, time_str):
        """convert all response times to microseconds"""
        time_str = time_str.replace(' ', '')
        # find where the units start
        i = 0
        while i < len(time_str) and (time_str[i].isdigit() or time_str[i] == '.'):
            i += 1
        if i == 0:
            return 0
            
        value = float(time_str[:i])
        unit = time_str[i:]
        # convert to microseconds
        conversions = {
            'ns': 0.001,
            'µs': 1,
            'ms': 1000,
            's': 1000000
        }
        return value * conversions.get(unit, 1)

    def extract_year_from_id(self, user_id):
        """extract year from student ID => _2025_B7PS1194P"""
        if not user_id:
            return None
        match = re.match(r'(\d{4})', user_id)
        return match.group(1) if match else None

    def parse_log_file(self, filename):
        """Parse the log file and extract all relevant information"""
        print(f"Parsing log file: {filename}")
        
        try:
            with open(filename, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        self.parse_log_line(line)
                    except Exception as e:
                        print(f"Warning: Could not parse line {line_num}: {line}")
                        print(f"Error: {e}")
                        
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found!")
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
            
        print(f"Successfully parsed log file with {self.total_requests} total requests")
        return True
    
    def parse_log_line(self, line):
        """Parse individual log lines based on their format"""
        # regex was made by Claude AI (pls spare me 😭)
        # Pattern 1: HTTP Request logs
        # 2025/08/01 08:00:22 [47.15.69.30] POST /courses 200 473.604µs
        http_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] (GET|POST) ([^\s]+) (\d{3}) ([0-9.]+[µmns]+s?)'
        
        # Pattern 2: Router logs without user ID
        # 2025/08/01 08:00:22 [103.144.92.185] router: /courses
        router_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] router: ([^\s]+)$'
        
        # Pattern 3: Router logs with user ID
        # 2025/08/01 08:00:22 [103.144.92.185] router: /courses [2025B7PS1194P]
        
        router_with_id_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] router: ([^\s]+) \[([^\]]+)\]'
        
        # Pattern 4: Algorithm usage logs
        # 2025/08/01 08:00:29 [106.205.200.150] --- Using Heuristic Backtracking Strategy (for Sparse Spaces) ---
        algorithm_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] --- Using (.+) ---'
        
        # Pattern 5: Generation completion logs
        # 2025/08/01 08:00:29 [106.205.200.150] --- Generation Complete: Found 234 timetables in pool, returning 100. ---
        generation_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] --- Generation Complete: Found (\d+) timetables in pool, returning (\d+)\. ---'
        
        # Try to match each pattern
        if re.match(http_pattern, line):
            self.parse_http_request(line, http_pattern)
        elif re.match(router_with_id_pattern, line):
            self.parse_router_with_id(line, router_with_id_pattern)
        elif re.match(router_pattern, line):
            self.parse_router_log(line, router_pattern)
        elif re.match(algorithm_pattern, line):
            self.parse_algorithm_log(line, algorithm_pattern)
        elif re.match(generation_pattern, line):
            self.parse_generation_log(line, generation_pattern)

    def parse_http_request(self, line, pattern):
        """Parse HTTP request logs"""
        match = re.match(pattern, line)
        if match:
            timestamp, ip, method, endpoint, status_code, response_time = match.groups()
            
            request_data = {
                'timestamp': timestamp,
                'ip': ip,
                'method': method,
                'endpoint': endpoint,
                'status_code': int(status_code),
                'response_time': response_time,
                'response_time_us': self.parse_response_time(response_time)
            }
            self.http_requests.append(request_data)
            # Update endpoints count
            if endpoint in self.endpoints:
                self.endpoints[endpoint] += 1
            else:
                self.endpoints[endpoint] = 1
            
            # Update response times
            if endpoint not in self.response_times:
                self.response_times[endpoint] = []
            self.response_times[endpoint].append(request_data['response_time_us'])
            
            self.total_requests += 1
    
    def parse_router_log(self, line, pattern):
        """Parse router logs without user ID"""
        match = re.match(pattern, line)
        if match:
            timestamp, ip, endpoint = match.groups()
            self.router_logs.append({
                'timestamp': timestamp,
                'ip': ip,
                'endpoint': endpoint,
                'user_id': None
            })
    
    def parse_router_with_id(self, line, pattern):
        """Parse router logs with user ID"""
        match = re.match(pattern, line)
        if match:
            timestamp, ip, endpoint, user_id = match.groups()
            self.router_logs.append({
                'timestamp': timestamp,
                'ip': ip,
                'endpoint': endpoint,
                'user_id': user_id
            })
            
            # Track users
            self.users.add(user_id)
            year = self.extract_year_from_id(user_id)
            if year:
                if year in self.users_by_year:
                    self.users_by_year[year] += 1
                else:
                    self.users_by_year[year] = 1
    
    def parse_algorithm_log(self, line, pattern):
        """Parse algorithm usage logs"""
        match = re.match(pattern, line)
        if match:
            timestamp, ip, algorithm_info = match.groups()
            
            # Extract algorithm type
            algorithm_type = "Unknown"
            if "Backtracking" in algorithm_info:
                algorithm_type = "Heuristic Backtracking Strategy"
            elif "Iterative" in algorithm_info or "Random" in algorithm_info:
                algorithm_type = "Iterative Random Sampling"
            
            # Update algorithm count
            if algorithm_type in self.algorithms_used:
                self.algorithms_used[algorithm_type] += 1
            else:
                self.algorithms_used[algorithm_type] = 1
            self.algorithm_logs.append({
                'timestamp': timestamp,
                'ip': ip,
                'algorithm': algorithm_type,
                'details': algorithm_info
            })
    
    def parse_generation_log(self, line, pattern):
        """Parse timetable generation completion logs"""
        match = re.match(pattern, line)
        if match:
            timestamp, ip, found, returned = match.groups()
            generation_data = {
                'timestamp': timestamp,
                'ip': ip,
                'found': int(found),
                'returned': int(returned)
            }
            self.generation_logs.append(generation_data)
            self.timetables_generated.append(int(returned))
    
    def analyze_performance(self):
        """Calculate performance metrics for each endpoint"""
        performance = {}
        
        for endpoint in self.response_times:
            times = self.response_times[endpoint]
            if times:
                performance[endpoint] = {
                    'count': len(times),
                    'avg_response_time_us': sum(times) / len(times),
                    'max_response_time_us': max(times),
                    'min_response_time_us': min(times)
                }
        
        return performance

    def generate_report(self):
            """Generate comprehensive analysis report"""
            print("\n" + "="*60)
            print("         TIMETABLE GENERATOR LOG ANALYSIS REPORT")
            print("="*60)
            
            # Total API requests served
            print(f"\n📊 TOTAL API REQUESTS SERVED")
            print(f"   Total HTTP requests: {self.total_requests}")
            
            # Count methods and status codes manually
            method_counts = {}
            status_counts = {}
            
            for req in self.http_requests:
                method = req['method']
                status = req['status_code']
                
                # Count methods
                if method in method_counts:
                    method_counts[method] += 1
                else:
                    method_counts[method] = 1
                
                # Count status codes
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
            
            print(f"   GET requests: {method_counts.get('GET', 0)}")
            print(f"   POST requests: {method_counts.get('POST', 0)}")
            
            # Sort status codes for consistent output
            sorted_statuses = sorted(status_counts.items())
            for status, count in sorted_statuses:
                print(f"   Status {status}: {count} requests")
            
            # Endpoint Popularity
            print(f"\n🎯 ENDPOINT POPULARITY")
            sorted_endpoints = sorted(self.endpoints.items(), key=lambda x: x[1], reverse=True)
            for endpoint, count in sorted_endpoints:
                print(f"   {endpoint:<20} {count:>4} requests")
            
            # Performance Metrics
            print(f"\n⚡ PERFORMANCE METRICS")
            performance = self.analyze_performance()
            
            for endpoint in sorted(performance.keys()):
                metrics = performance[endpoint]
                avg_ms = metrics['avg_response_time_us'] / 1000
                max_ms = metrics['max_response_time_us'] / 1000
                print(f"   {endpoint:<20}")
                print(f"      Average: {avg_ms:>8.2f}ms")
                print(f"      Maximum: {max_ms:>8.2f}ms")
                print(f"      Requests: {metrics['count']:>7}")
            
            # User Analysis
            print(f"\n👥 USER ANALYSIS")
            print(f"   Total unique users: {len(self.users)}")
            
            if self.users_by_year:
                print(f"   Users by year:")
                for year in sorted(self.users_by_year.keys(), reverse=True):
                    print(f"      {year}: {self.users_by_year[year]} users")
            
            # Timetable Generation Insights
            print(f"\n📅 TIMETABLE GENERATION INSIGHTS")
            
            total_timetables = sum(self.timetables_generated)
            num_generations = len(self.timetables_generated)
            
            print(f"   Total timetables generated: {total_timetables}")
            
            if num_generations > 0:
                avg_timetables = total_timetables / num_generations
                print(f"   Average timetables per generation: {avg_timetables:.2f}")
                print(f"   Number of generation requests: {num_generations}")
            
            print(f"\n🔧 ALGORITHM USAGE")
            if self.algorithms_used:
                # Sort algorithms by usage count (descending)
                sorted_algorithms = sorted(self.algorithms_used.items(), key=lambda x: x[1], reverse=True)
                for algorithm, count in sorted_algorithms:
                    print(f"   {algorithm}: {count} times")
            else:
                print("   No algorithm usage found in logs")
            
            # Additional insights
            print(f"\n📈 ADDITIONAL INSIGHTS")
            
            if self.generation_logs:
                found_counts = [log['found'] for log in self.generation_logs]
                avg_found = sum(found_counts) / len(found_counts)
                print(f"   Average timetables found per generation: {avg_found:.2f}")
                print(f"   Maximum timetables found in single generation: {max(found_counts)}")
                print(f"   Minimum timetables found in single generation: {min(found_counts)}")
            
            print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description='Analyze timetable generator log files')
    parser.add_argument('logfile', help='Path to the log file')
    parser.add_argument('--endpoints', action='store_true', help='Show only endpoint popularity')
    parser.add_argument('--performance', action='store_true', help='Show only performance metrics')
    parser.add_argument('--users', action='store_true', help='Show only user statistics')
    parser.add_argument('--timetables', action='store_true', help='Show only timetable generation stats')
    parser.add_argument('--all', action='store_true', help='Show complete report (default)')
    
    args = parser.parse_args()
    
    # Create analyzer instance
    analyzer = LogAnalyzer()
    
    # Parse the log file
    if not analyzer.parse_log_file(args.logfile):
        return 1
    
    # Generate reports based on flags
    if args.endpoints:
        print("\n🎯 ENDPOINT POPULARITY")
        sorted_endpoints = sorted(analyzer.endpoints.items(), key=lambda x: x[1], reverse=True)
        for endpoint, count in sorted_endpoints:
            print(f"   {endpoint:<20} {count:>4} requests")
    
    elif args.performance:
        print("\n⚡ PERFORMANCE METRICS")
        performance = analyzer.analyze_performance()
        for endpoint in sorted(performance.keys()):
            metrics = performance[endpoint]
            avg_ms = metrics['avg_response_time_us'] / 1000
            max_ms = metrics['max_response_time_us'] / 1000
            print(f"   {endpoint:<20}")
            print(f"      Average: {avg_ms:>8.2f}ms")
            print(f"      Maximum: {max_ms:>8.2f}ms")
    
    elif args.users:
        print("\n👥 USER ANALYSIS")
        print(f"   Total unique users: {len(analyzer.users)}")
        if analyzer.users_by_year:
            print(f"   Users by year:")
            for year in sorted(analyzer.users_by_year.keys(), reverse=True):
                print(f"      {year}: {analyzer.users_by_year[year]} users")
    
    elif args.timetables:
        print("\n📅 TIMETABLE GENERATION INSIGHTS")
        total_timetables = sum(analyzer.timetables_generated)
        num_generations = len(analyzer.timetables_generated)
        print(f"   Total timetables generated: {total_timetables}")
        if num_generations > 0:
            avg_timetables = total_timetables / num_generations
            print(f"   Average timetables per generation: {avg_timetables:.2f}")
    
    else:
        # Show complete report by default
        analyzer.generate_report()

if __name__ == "__main__":
    exit(main())