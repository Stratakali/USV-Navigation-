"""
Flask web application for USV mission planner.

This module provides a web interface for the USV mission planner,
allowing users to start the planner and monitor its progress.
"""

import os
import threading
import subprocess
import re
from flask import Flask, render_template, request, jsonify

# Import our risk assessment helper
import risk_assessment_helper

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development-key")

# Variable to store the process
planner_process = None
process_lock = threading.Lock()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/start-planner', methods=['POST'])
def start_planner():
    """Start the USV mission planner."""
    global planner_process
    
    # Get configuration from form
    display = request.form.get('display', 'false') == 'true'
    
    # Command to run the planner
    cmd = ['python', 'usv_mission_planner/main.py']
    if not display:
        cmd.append('--no-display')
    
    # Start the planner in a separate process
    with process_lock:
        if planner_process and planner_process.poll() is None:
            return jsonify({'status': 'error', 'message': 'Planner is already running'})
        
        planner_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
    
    return jsonify({'status': 'success', 'message': 'USV mission planner started'})

@app.route('/planner-status')
def planner_status():
    """Get the status of the running planner process."""
    global planner_process
    
    with process_lock:
        if not planner_process:
            return jsonify({'status': 'not_running', 'message': 'Planner is not running'})
        
        # Check if process is still running
        if planner_process.poll() is not None:
            return jsonify({
                'status': 'completed',
                'message': f'Planner has completed with return code {planner_process.returncode}'
            })
        
        # Process is running
        return jsonify({'status': 'running', 'message': 'Planner is running'})

@app.route('/planner-logs')
def planner_logs():
    """Get the latest logs from the planner."""
    try:
        with open('usv_mission_planner/usv_mission.log', 'r') as f:
            # Get the last 50 lines
            lines = f.readlines()[-50:]
            return jsonify({'status': 'success', 'logs': ''.join(lines)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop-planner', methods=['POST'])
def stop_planner():
    """Stop the running planner process."""
    global planner_process
    
    with process_lock:
        if not planner_process or planner_process.poll() is not None:
            return jsonify({'status': 'error', 'message': 'No planner process is running'})
        
        # Terminate the process
        planner_process.terminate()
        try:
            planner_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            planner_process.kill()
        
        return jsonify({'status': 'success', 'message': 'Planner process stopped'})

@app.route('/missions')
def missions():
    """Get the list of available missions."""
    missions = [
        {
            'type': 'waypoint',
            'description': 'Navigate through waypoints around New Zealand',
            'waypoints': [
                {'lat': -41.2865, 'lng': 174.7762, 'name': 'Wellington'},
                {'lat': -36.8485, 'lng': 174.7633, 'name': 'Auckland'},
                {'lat': -43.5321, 'lng': 172.6362, 'name': 'Christchurch'},
                {'lat': -45.0312, 'lng': 168.6626, 'name': 'Queenstown'},
                {'lat': -37.7833, 'lng': 175.2833, 'name': 'Hamilton'}
            ]
        },
        {
            'type': 'station_keeping',
            'description': 'Maintain station in Wellington Harbor',
            'location': {'lat': -41.2865, 'lng': 174.7762, 'name': 'Wellington Harbor'},
            'duration': 300
        },
        {
            'type': 'docking',
            'description': 'Dock at Auckland Marina',
            'location': {'lat': -36.8485, 'lng': 174.7633, 'name': 'Auckland Marina'},
            'heading': 270.0
        }
    ]
    
    return jsonify({'status': 'success', 'missions': missions})

@app.route('/usv-state')
def usv_state():
    """Get the current USV state including position and heading."""
    global planner_process
    
    # Default state (Wellington, New Zealand)
    state = {
        'position': {'lat': -41.2865, 'lng': 174.7762},
        'heading': 0.0,
        'speed': 0.0,
        'mission_type': None,
        'active': False,
        'mission_status': None
    }
    
    # Check if the planner is running
    with process_lock:
        if planner_process and planner_process.poll() is None:
            state['active'] = True
            
            # Try to read the latest logs to get the current position
            try:
                with open('usv_mission_planner/usv_mission.log', 'r') as f:
                    logs = f.readlines()
                    
                    # Look for position and heading updates in the log
                    for line in reversed(logs):
                        # Check for position update
                        if "Position:" in line:
                            position_match = re.search(r'Position: \(([0-9.-]+), ([0-9.-]+)\)', line)
                            if position_match:
                                lat = float(position_match.group(1))
                                lng = float(position_match.group(2))
                                state['position'] = {'lat': lat, 'lng': lng}
                        
                        # Check for heading update
                        if "Heading:" in line:
                            heading_match = re.search(r'Heading: ([0-9.-]+)', line)
                            if heading_match:
                                state['heading'] = float(heading_match.group(1))
                        
                        # Check for speed update
                        if "Speed:" in line:
                            speed_match = re.search(r'Speed: ([0-9.-]+)', line)
                            if speed_match:
                                state['speed'] = float(speed_match.group(1))
                        
                        # Check for mission type
                        if "Mission: " in line:
                            mission_match = re.search(r'Mission: ([a-zA-Z_]+)', line)
                            if mission_match:
                                state['mission_type'] = mission_match.group(1)
                        
                        # Check for mission status
                        if "Status: " in line:
                            status_match = re.search(r'Status: ([A-Z_]+)', line)
                            if status_match:
                                state['mission_status'] = status_match.group(1)
                        
                        # If we have all the data, break
                        if state['position'] and state['heading'] is not None and state['mission_type'] and state['mission_status']:
                            break
            except Exception as e:
                print(f"Error reading log file: {e}")
    
    return jsonify({'status': 'success', 'usv_state': state})

@app.route('/add-waypoint', methods=['POST'])
def add_waypoint():
    """Add a new waypoint to the mission planner."""
    # Get waypoint data from request
    data = request.json
    
    if not data or 'lat' not in data or 'lng' not in data or 'name' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing required waypoint data (lat, lng, name)'
        })
    
    # Add waypoint to log for future reference
    waypoint = {
        'lat': data['lat'],
        'lng': data['lng'],
        'name': data['name']
    }
    
    try:
        with open('usv_mission_planner/custom_waypoints.log', 'a') as f:
            f.write(f"Custom Waypoint: {waypoint['name']} ({waypoint['lat']}, {waypoint['lng']})\n")
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to save waypoint: {str(e)}'
        })
    
    return jsonify({
        'status': 'success',
        'message': f'Waypoint {waypoint["name"]} added successfully',
        'waypoint': waypoint
    })

@app.route('/assess-mission-risks', methods=['POST'])
def assess_mission_risks():
    """
    Assess the risks for a mission under specified environmental conditions.
    
    Expects JSON with:
    - mission_index: Index of the mission to assess
    - env_condition: Environmental condition (good, moderate, poor)
    """
    # Define available missions (same as in missions())
    missions_data = [
        {
            'type': 'waypoint',
            'description': 'Navigate through waypoints around New Zealand',
            'waypoints': [
                {'lat': -41.2865, 'lng': 174.7762, 'name': 'Wellington'},
                {'lat': -36.8485, 'lng': 174.7633, 'name': 'Auckland'},
                {'lat': -43.5321, 'lng': 172.6362, 'name': 'Christchurch'},
                {'lat': -45.0312, 'lng': 168.6626, 'name': 'Queenstown'},
                {'lat': -37.7833, 'lng': 175.2833, 'name': 'Hamilton'}
            ]
        },
        {
            'type': 'station_keeping',
            'description': 'Maintain station in Wellington Harbor',
            'location': {'lat': -41.2865, 'lng': 174.7762, 'name': 'Wellington Harbor'},
            'duration': 300
        },
        {
            'type': 'docking',
            'description': 'Dock at Auckland Marina',
            'location': {'lat': -36.8485, 'lng': 174.7633, 'name': 'Auckland Marina'},
            'heading': 270.0
        }
    ]
    
    # Get request data
    data = request.json
    mission_index = data.get('mission_index', 0)
    env_condition = data.get('env_condition', 'good')
    
    # Validate mission index
    if mission_index < 0 or mission_index >= len(missions_data):
        return jsonify({
            'status': 'error',
            'message': f'Invalid mission index: {mission_index}'
        })
    
    # Get mission data
    mission_data = missions_data[mission_index]
    mission_type = mission_data['type']
    
    try:
        # Assess risks
        risk_assessment = risk_assessment_helper.assess_mission_risks(
            mission_type, 
            mission_data, 
            env_condition
        )
        
        return jsonify({
            'status': 'success',
            'risk_assessment': risk_assessment
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error assessing risks: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)