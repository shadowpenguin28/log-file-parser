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
analyzer = LogAnalyzer()
analyzer.parse_log_file('timetable.log')
print(analyzer.http_requests)
print(analyzer.router_logs)
print(analyzer.algorithm_logs)
print(analyzer.generation_logs)
print(analyzer.endpoints)
print(analyzer.response_times)
print(analyzer.users)
print(analyzer.users_by_year)
print(analyzer.algorithms_used)
print(analyzer.timetables_generated)
print(analyzer.total_requests)


