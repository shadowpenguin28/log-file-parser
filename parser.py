import re
import argparse
from datetime import datetime

#test 
class LogAnalyzer():
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
    
    

