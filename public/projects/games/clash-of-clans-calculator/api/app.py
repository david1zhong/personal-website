from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import re
import os
import sys

sys.path.append(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)

def parse_time_string(time_str):
    time_str = time_str.strip()
    
    if 'd' in time_str and 'h' in time_str:
        match = re.match(r'^(\d+)d(\d+)h$', time_str)
        if match:
            days, hours = match.groups()
            return int(days) * 24 + int(hours)
    elif 'd' in time_str:
        match = re.match(r'^(\d+)d$', time_str)
        if match:
            days = match.groups()[0]
            return int(days) * 24
    elif 'h' in time_str:
        match = re.match(r'^(\d+)h$', time_str)
        if match:
            hours = match.groups()[0]
            return int(hours)
    
    return -1

def calculate_completion_time(current_hour, current_minute, upgrade_time_str, builder_potions):
    upgrade_hours = parse_time_string(upgrade_time_str)
    potion_reduction = builder_potions * 9
    actual_upgrade_hours = max(0, upgrade_hours - potion_reduction)
    
    now = datetime.now().replace(hour=current_hour, minute=current_minute, second=0, microsecond=0)
    completion_time = now + timedelta(hours=actual_upgrade_hours)
    
    return completion_time

def format_completion_time(completion_time):
    now = datetime.now().replace(second=0, microsecond=0)
    time_diff = completion_time - now
    
    if time_diff.total_seconds() <= 0:
        return "Done"
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    day_name = completion_time.strftime('%A')
    time_str = completion_time.strftime('%I:%M %p')
    
    if days > 0:
        if minutes > 0:
            return f"{days}d {hours}h {minutes}m ({day_name} {time_str})"
        else:
            return f"{days}d {hours}h ({day_name} {time_str})"
    else:
        if minutes > 0:
            return f"{hours}h {minutes}m ({day_name} {time_str})"
        else:
            return f"{hours}h ({day_name} {time_str})"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        current_hour = int(data['current_hour'])
        current_minute = int(data['current_minute'])
        builder_potions = int(data['builder_potions'])
        upgrade_times = data['upgrade_times']
        
        for i, upgrade_time in enumerate(upgrade_times):
            if upgrade_time.strip():
                upgrade_hours = parse_time_string(upgrade_time)
                
                if upgrade_hours == -1:
                    return jsonify({
                        'success': False, 
                        'error': f"Wrong format in field {i + 1}: '{upgrade_time}'. Use Xd, Xh, or XdYh"
                    })
                
                if upgrade_hours > 720:
                    return jsonify({
                        'success': False,
                        'error': f"Field {i + 1} too long - max 30 days. You entered {upgrade_hours} hours"
                    })
        
        results = []
        
        for i, upgrade_time in enumerate(upgrade_times):
            if upgrade_time.strip():
                completion_time = calculate_completion_time(current_hour, current_minute, upgrade_time, builder_potions)
                formatted_time = format_completion_time(completion_time)
                
                results.append({
                    'index': i + 1,
                    'original_time': upgrade_time,
                    'completion': formatted_time,
                    'completion_datetime': completion_time.strftime('%m/%d/%Y at %I:%M %p')
                })
        
        return jsonify({'success': True, 'results': results})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(port=8080)