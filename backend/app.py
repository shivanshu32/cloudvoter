"""
Flask Backend for CloudVoter - Web-Based Voting Automation Control Panel
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from threading import Thread
import traceback

from voter_engine import MultiInstanceVoter, VoterInstance
from config import TARGET_URL, TARGET_URLS, BRIGHT_DATA_USERNAME, BRIGHT_DATA_PASSWORD, SESSION_SCAN_INTERVAL
from vote_logger import VoteLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloudvoter.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress Flask HTTP access logs (GET /api/instances, GET /api/statistics, etc.)
# These logs clutter the UI without providing useful information
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Only show errors, not INFO level HTTP requests

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cloudvoter-secret-key-change-in-production')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
voter_system = None
monitoring_active = False
monitoring_task = None
event_loop = None
loop_thread = None
login_browsers = {}  # Store active login browsers

# Vote logger - use absolute path to match VoterInstance
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vote_logger_path = os.path.join(project_root, "voting_logs.csv")
vote_logger = VoteLogger(log_file=vote_logger_path)
logger.info(f"📊 Vote logger initialized: {vote_logger_path}")

class WebSocketLogHandler(logging.Handler):
    """Custom log handler to send logs to WebSocket clients"""
    
    def emit(self, record):
        try:
            log_entry = self.format(record)
            socketio.emit('log_update', {
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'message': log_entry
            })
        except Exception:
            pass

# Add WebSocket handler to logger
ws_handler = WebSocketLogHandler()
ws_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(ws_handler)

def start_event_loop():
    """Start asyncio event loop in separate thread"""
    global event_loop
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()

def init_event_loop():
    """Initialize event loop thread"""
    global loop_thread
    if loop_thread is None or not loop_thread.is_alive():
        loop_thread = Thread(target=start_event_loop, daemon=True)
        loop_thread.start()
        logger.info("✅ Event loop thread started")

# Initialize event loop on startup
init_event_loop()

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'monitoring_active': monitoring_active
    })

@app.route('/api/config', methods=['GET', 'POST'])
def config_endpoint():
    """Get or update configuration"""
    if request.method == 'GET':
        # Return config values with fallback to config.py defaults
        return jsonify({
            'voting_url': TARGET_URL,
            'voting_urls': TARGET_URLS,
            'bright_data_username': os.environ.get('BRIGHT_DATA_USERNAME', BRIGHT_DATA_USERNAME),
            'bright_data_password': os.environ.get('BRIGHT_DATA_PASSWORD', BRIGHT_DATA_PASSWORD)
        })
    
    elif request.method == 'POST':
        data = request.json
        # Update environment variables (in production, use proper config management)
        if 'bright_data_username' in data:
            os.environ['BRIGHT_DATA_USERNAME'] = data['bright_data_username']
        if 'bright_data_password' in data:
            os.environ['BRIGHT_DATA_PASSWORD'] = data['bright_data_password']
        
        return jsonify({'status': 'success', 'message': 'Configuration updated'})

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start ultra monitoring"""
    global voter_system, monitoring_active, monitoring_task
    
    try:
        # Get JSON data or use empty dict if no body
        data = request.get_json(silent=True) or {}
        
        # Use credentials from request or environment variables
        username = data.get('username') or BRIGHT_DATA_USERNAME
        password = data.get('password') or BRIGHT_DATA_PASSWORD
        voting_url = data.get('voting_url') or TARGET_URL
        
        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': 'Bright Data credentials required (set in config.py or provide in request)'
            }), 400
        
        if monitoring_active:
            return jsonify({
                'status': 'error',
                'message': 'Monitoring already active'
            }), 400
        
        # Initialize voter system
        if not voter_system:
            voter_system = MultiInstanceVoter(
                username=username,
                password=password,
                target_url=voting_url
            )
            logger.info("✅ Voter system initialized")
        
        # Start monitoring in event loop
        monitoring_active = True
        
        async def monitoring_loop():
            """Main monitoring loop"""
            try:
                logger.info("🚀 Starting ultra monitoring loop...")
                
                # Start browser monitoring service
                if hasattr(voter_system, 'start_browser_monitoring_service'):
                    await voter_system.start_browser_monitoring_service()
                
                loop_count = 0
                last_scan_time = 0  # Track last session scan time
                while monitoring_active:
                    loop_count += 1
                    
                    # Emit status update
                    socketio.emit('status_update', {
                        'monitoring_active': True,
                        'loop_count': loop_count,
                        'active_instances': len(voter_system.active_instances) if voter_system else 0
                    })
                    
                    # Emit statistics update
                    try:
                        stats = vote_logger.get_statistics()
                        stats['active_instances'] = len(voter_system.active_instances) if voter_system else 0
                        socketio.emit('statistics_update', stats)
                    except Exception as e:
                        logger.error(f"Error emitting statistics: {e}")
                    
                    # Emit instance updates
                    try:
                        if voter_system:
                            instances = []
                            for ip, instance in voter_system.active_instances.items():
                                time_info = instance.get_time_until_next_vote()
                                instances.append({
                                    'instance_id': getattr(instance, 'instance_id', None),
                                    'ip': ip,
                                    'status': getattr(instance, 'status', 'Unknown'),
                                    'is_paused': getattr(instance, 'is_paused', False),
                                    'waiting_for_login': getattr(instance, 'waiting_for_login', False),
                                    'vote_count': getattr(instance, 'vote_count', 0),
                                    'seconds_remaining': time_info['seconds_remaining'],
                                    'next_vote_time': time_info['next_vote_time'],
                                    'last_vote_time': getattr(instance, 'last_vote_time', None).isoformat() if getattr(instance, 'last_vote_time', None) else None,
                                    'last_successful_vote': getattr(instance, 'last_successful_vote', None).isoformat() if getattr(instance, 'last_successful_vote', None) else None,
                                    'last_attempted_vote': getattr(instance, 'last_attempted_vote', None).isoformat() if getattr(instance, 'last_attempted_vote', None) else None,
                                    'last_failure_reason': getattr(instance, 'last_failure_reason', None),
                                    'last_failure_type': getattr(instance, 'last_failure_type', None)
                                })
                            socketio.emit('instances_update', {'instances': instances})
                    except Exception as e:
                        logger.error(f"Error emitting instances update: {e}")
                    
                    # Check for ready instances (with reduced frequency)
                    current_time = time.time()
                    if current_time - last_scan_time >= SESSION_SCAN_INTERVAL:
                        last_scan_time = current_time
                        
                        try:
                            # CRITICAL: Check if global hourly limit is active before launching
                            if voter_system and voter_system.global_hourly_limit:
                                logger.debug(f"⏰ Global hourly limit active - skipping instance launch")
                            else:
                                ready_instances = await check_ready_instances()
                                
                                if ready_instances:
                                    logger.info(f"🔍 Found {len(ready_instances)} ready instances")
                                    
                                    # Try to launch first ready instance that's not already running
                                    launched = False
                                    for instance_info in ready_instances:
                                        success = await launch_instance_from_session(instance_info)
                                        if success:
                                            launched = True
                                            break
                                    
                                    # Wait a bit after launching to let it stabilize
                                    if launched:
                                        await asyncio.sleep(5)
                            
                        except Exception as e:
                            logger.error(f"❌ Error in monitoring loop: {e}")
                    
                    # Wait before next check
                    await asyncio.sleep(10)  # Check every 10 seconds
                
                logger.info("⏹ Monitoring loop stopped")
                
            except Exception as e:
                logger.error(f"❌ Critical error in monitoring loop: {e}")
                logger.error(traceback.format_exc())
            finally:
                # Stop browser monitoring
                if voter_system and hasattr(voter_system, 'stop_browser_monitoring_service'):
                    await voter_system.stop_browser_monitoring_service()
        
        # Schedule monitoring task
        monitoring_task = asyncio.run_coroutine_threadsafe(monitoring_loop(), event_loop)
        
        logger.info("✅ Ultra monitoring started")
        
        return jsonify({
            'status': 'success',
            'message': 'Ultra monitoring started'
        })
        
    except Exception as e:
        logger.error(f"❌ Error starting monitoring: {e}")
        logger.error(traceback.format_exc())
        monitoring_active = False
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    """Stop ultra monitoring"""
    global monitoring_active, monitoring_task
    
    try:
        monitoring_active = False
        
        if monitoring_task:
            monitoring_task.cancel()
        
        logger.info("⏹ Ultra monitoring stopped")
        
        socketio.emit('status_update', {
            'monitoring_active': False
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Ultra monitoring stopped'
        })
        
    except Exception as e:
        logger.error(f"❌ Error stopping monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        active_instances = []
        
        if voter_system and hasattr(voter_system, 'active_instances'):
            for ip, instance in voter_system.active_instances.items():
                active_instances.append({
                    'instance_id': getattr(instance, 'instance_id', 'Unknown'),
                    'ip': ip,
                    'status': getattr(instance, 'status', 'Unknown'),
                    'is_paused': getattr(instance, 'is_paused', False),
                    'waiting_for_login': getattr(instance, 'waiting_for_login', False)
                })
        
        return jsonify({
            'monitoring_active': monitoring_active,
            'active_instances': active_instances,
            'total_instances': len(active_instances)
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/instances', methods=['GET'])
def get_instances():
    """Get all instances"""
    try:
        instances = []
        
        if voter_system and hasattr(voter_system, 'active_instances'):
            # Note: active_instances is keyed by IP address, not instance_id
            for ip, instance in voter_system.active_instances.items():
                instance_id = getattr(instance, 'instance_id', None)
                
                # Debug logging
                if instance_id is None:
                    logger.error(f"[API] Instance at IP {ip} has no instance_id! Type: {type(instance)}, Attrs: {dir(instance)}")
                
                # Get time until next vote
                time_info = instance.get_time_until_next_vote() if hasattr(instance, 'get_time_until_next_vote') else {
                    'seconds_remaining': 0,
                    'next_vote_time': None,
                    'status': 'unknown'
                }
                
                instances.append({
                    'instance_id': instance_id if instance_id is not None else 'Unknown',
                    'ip': ip,
                    'status': getattr(instance, 'status', 'Unknown'),
                    'is_paused': getattr(instance, 'is_paused', False),
                    'waiting_for_login': getattr(instance, 'waiting_for_login', False),
                    'session_id': getattr(instance, 'session_id', None),
                    'vote_count': getattr(instance, 'vote_count', 0),
                    'seconds_remaining': time_info['seconds_remaining'],
                    'next_vote_time': time_info['next_vote_time'],
                    'last_vote_time': getattr(instance, 'last_vote_time', None).isoformat() if getattr(instance, 'last_vote_time', None) else None,
                    'last_successful_vote': getattr(instance, 'last_successful_vote', None).isoformat() if getattr(instance, 'last_successful_vote', None) else None,
                    'last_attempted_vote': getattr(instance, 'last_attempted_vote', None).isoformat() if getattr(instance, 'last_attempted_vote', None) else None,
                    'last_failure_reason': getattr(instance, 'last_failure_reason', None),
                    'last_failure_type': getattr(instance, 'last_failure_type', None)
                })
        
        return jsonify({
            'instances': instances,
            'total': len(instances)
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting instances: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/launch-instance', methods=['POST'])
def launch_instance():
    """Launch a new instance"""
    global voter_system
    
    try:
        if not voter_system:
            return jsonify({
                'status': 'error',
                'message': 'Voter system not initialized'
            }), 400
        
        async def launch():
            success = await voter_system.launch_new_instance()
            return success
        
        future = asyncio.run_coroutine_threadsafe(launch(), event_loop)
        success = future.result(timeout=30)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Instance launched successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to launch instance'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error launching instance: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/vote-history', methods=['GET'])
def get_vote_history():
    """Get voting history"""
    try:
        history = vote_logger.get_recent_votes(limit=100)
        return jsonify({
            'history': history,
            'total': len(history)
        })
    except Exception as e:
        logger.error(f"❌ Error getting vote history: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get voting statistics"""
    global voter_system
    try:
        stats = vote_logger.get_statistics()
        
        # Get real-time active instances count from voter_system
        if voter_system and hasattr(voter_system, 'active_instances'):
            stats['active_instances'] = len(voter_system.active_instances)
        else:
            stats['active_instances'] = 0
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_saved_sessions():
    """Get all saved sessions"""
    try:
        sessions = []
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        session_dir = os.path.join(project_root, "brightdata_session_data")
        
        if os.path.exists(session_dir):
            for dir_name in os.listdir(session_dir):
                if dir_name.startswith('instance_'):
                    try:
                        instance_id = int(dir_name.replace('instance_', ''))
                        session_path = os.path.join(session_dir, dir_name)
                        
                        # Load session info
                        info_file = os.path.join(session_path, 'session_info.json')
                        if os.path.exists(info_file):
                            with open(info_file, 'r') as f:
                                session_info = json.load(f)
                            
                            # Get last vote time and count from CSV logs (most accurate)
                            last_successful_vote = 'Never'
                            last_attempted_vote = 'Never'
                            vote_count = 0
                            
                            try:
                                # Read from CSV to get most recent vote
                                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                csv_file = os.path.join(project_root, 'voting_logs.csv')
                                
                                if os.path.exists(csv_file):
                                    import csv
                                    with open(csv_file, 'r', encoding='utf-8') as f:
                                        reader = csv.DictReader(f)
                                        instance_votes = [row for row in reader if row.get('instance_id') == str(instance_id)]
                                        
                                        if instance_votes:
                                            # Get most recent attempt (last entry)
                                            last_attempt = instance_votes[-1]
                                            last_attempted_vote = last_attempt.get('time_of_click', 'Never')
                                            
                                            # Get most recent successful vote
                                            successful_votes = [v for v in instance_votes if v.get('status') == 'success']
                                            if successful_votes:
                                                last_success = successful_votes[-1]
                                                last_successful_vote = last_success.get('time_of_click', 'Never')
                                            
                                            # Count successful votes
                                            vote_count = len(successful_votes)
                            except Exception as e:
                                logger.warning(f"[SESSIONS] Error reading CSV for instance #{instance_id}: {e}")
                                # Fallback to session file
                                last_successful_vote = session_info.get('last_vote_time', 'Never')
                                last_attempted_vote = session_info.get('last_vote_time', 'Never')
                                vote_count = session_info.get('vote_count', 0)
                            
                            # Check if cookies exist
                            cookies_file = os.path.join(session_path, 'cookies.json')
                            has_cookies = os.path.exists(cookies_file)
                            
                            sessions.append({
                                'instance_id': instance_id,
                                'ip': session_info.get('proxy_ip', 'N/A'),
                                'last_successful_vote': last_successful_vote,
                                'last_attempted_vote': last_attempted_vote,
                                'vote_count': vote_count,
                                'status': 'saved' if has_cookies else 'needs_login',
                                'session_path': session_path
                            })
                    except (ValueError, json.JSONDecodeError) as e:
                        logger.warning(f"Error loading session {dir_name}: {e}")
                        continue
        
        return jsonify({
            'status': 'success',
            'sessions': sorted(sessions, key=lambda x: x['instance_id']),
            'total': len(sessions)
        })
    
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/save-login/<int:instance_id>', methods=['POST'])
def save_google_login(instance_id):
    """Open browser for manual Google login and save session"""
    global voter_system
    
    try:
        data = request.get_json(silent=True) or {}
        username = data.get('username') or BRIGHT_DATA_USERNAME
        password = data.get('password') or BRIGHT_DATA_PASSWORD
        
        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': 'BrightData credentials required'
            }), 400
        
        # Initialize voter system if not exists
        if not voter_system:
            voter_system = MultiInstanceVoter(username, password, TARGET_URL)
        
        async def open_login_browser():
            try:
                from playwright.async_api import async_playwright
                
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                session_dir = os.path.join(project_root, "brightdata_session_data", f"instance_{instance_id}")
                os.makedirs(session_dir, exist_ok=True)
                
                # Get proxy IP
                proxy_ip = await voter_system.proxy_api.get_proxy_ip(instance_id)
                session_id = proxy_ip.replace('.', '_')
                
                # Proxy configuration
                proxy_config = {
                    'server': f'http://{voter_system.proxy_api.proxy_host}:{voter_system.proxy_api.proxy_port}',
                    'username': f"brd-customer-{username}-zone-{voter_system.proxy_api.zone}-country-in-session-{session_id}",
                    'password': password
                }
                
                # Launch headed browser
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(
                    headless=False,  # Headed mode for manual login
                    proxy=proxy_config,
                    args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                # Navigate to voting page
                await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=60000)
                
                # Store browser info for later saving
                login_browsers[instance_id] = {
                    'playwright': playwright,
                    'browser': browser,
                    'context': context,
                    'page': page,
                    'session_dir': session_dir,
                    'proxy_ip': proxy_ip,
                    'session_id': session_id
                }
                
                logger.info(f"[SAVE_LOGIN] Browser opened for Instance #{instance_id} - Please complete Google login")
                return {'status': 'browser_opened', 'instance_id': instance_id}
                
            except Exception as e:
                logger.error(f"[SAVE_LOGIN] Error opening browser for Instance #{instance_id}: {e}")
                return {'status': 'error', 'message': str(e)}
        
        if event_loop:
            future = asyncio.run_coroutine_threadsafe(open_login_browser(), event_loop)
            result = future.result(timeout=60)
            return jsonify(result)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Event loop not initialized'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in save_google_login: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/save-login/<int:instance_id>/complete', methods=['POST'])
def complete_google_login(instance_id):
    """Complete Google login and save session"""
    try:
        if instance_id not in login_browsers:
            return jsonify({
                'status': 'error',
                'message': f'No active login browser for Instance #{instance_id}'
            }), 400
        
        async def save_session():
            try:
                browser_info = login_browsers[instance_id]
                context = browser_info['context']
                session_dir = browser_info['session_dir']
                proxy_ip = browser_info['proxy_ip']
                session_id = browser_info['session_id']
                
                # Save storage state (cookies + localStorage)
                storage_state_path = os.path.join(session_dir, 'storage_state.json')
                await context.storage_state(path=storage_state_path)
                
                # Save cookies separately
                cookies = await context.cookies()
                cookies_path = os.path.join(session_dir, 'cookies.json')
                with open(cookies_path, 'w') as f:
                    json.dump(cookies, f, indent=2)
                
                # Save session info
                session_info = {
                    'instance_id': instance_id,
                    'proxy_ip': proxy_ip,
                    'session_id': session_id,
                    'last_vote_time': None,
                    'vote_count': 0,
                    'created_at': datetime.now().isoformat()
                }
                
                info_path = os.path.join(session_dir, 'session_info.json')
                with open(info_path, 'w') as f:
                    json.dump(session_info, f, indent=2)
                
                # Close browser
                await browser_info['browser'].close()
                await browser_info['playwright'].stop()
                
                # Remove from active browsers
                del login_browsers[instance_id]
                
                logger.info(f"[SAVE_LOGIN] Session saved successfully for Instance #{instance_id}")
                logger.info(f"[SAVE_LOGIN] Saved {len(cookies)} cookies")
                
                return {'status': 'success', 'message': f'Session saved successfully for Instance #{instance_id}'}
                
            except Exception as e:
                logger.error(f"[SAVE_LOGIN] Error saving session for Instance #{instance_id}: {e}")
                return {'status': 'error', 'message': str(e)}
        
        if event_loop:
            future = asyncio.run_coroutine_threadsafe(save_session(), event_loop)
            result = future.result(timeout=30)
            return jsonify(result)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Event loop not initialized'
            }), 500
    
    except Exception as e:
        logger.error(f"Error completing login: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/check-login/<int:instance_id>', methods=['POST'])
def check_google_login(instance_id):
    """Check if saved session is still logged in"""
    global voter_system
    
    try:
        if not voter_system:
            return jsonify({
                'status': 'error',
                'message': 'Voter system not initialized. Start monitoring first.'
            }), 400
        
        async def check_login():
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                session_dir = os.path.join(project_root, "brightdata_session_data", f"instance_{instance_id}")
                
                if not os.path.exists(session_dir):
                    return {'status': 'error', 'message': f'No saved session found for Instance #{instance_id}'}
                
                # Load session info
                info_file = os.path.join(session_dir, 'session_info.json')
                if not os.path.exists(info_file):
                    return {'status': 'error', 'message': f'Session info not found for Instance #{instance_id}'}
                
                with open(info_file, 'r') as f:
                    session_info = json.load(f)
                
                proxy_ip = session_info.get('proxy_ip')
                session_id = session_info.get('session_id', proxy_ip.replace('.', '_') if proxy_ip else None)
                
                # Create temporary instance
                instance = VoterInstance(
                    instance_id=instance_id,
                    proxy_ip=proxy_ip,
                    session_id=session_id,
                    target_url=voter_system.target_url,
                    vote_logger=vote_logger,
                    voter_manager=voter_system
                )
                
                # Initialize with saved session
                success = await instance.initialize(use_session=True)
                if not success:
                    await instance.close_browser()
                    return {'status': 'error', 'message': 'Failed to initialize browser'}
                
                # Navigate to voting page
                await instance.page.goto(voter_system.target_url, wait_until='domcontentloaded', timeout=45000)
                await asyncio.sleep(2)
                
                # Check if login required
                login_required = await instance.check_login_required()
                
                # Close browser
                await instance.close_browser()
                
                if login_required:
                    logger.info(f"[CHECK_LOGIN] Instance #{instance_id} requires login")
                    return {
                        'status': 'success',
                        'logged_in': False,
                        'message': 'Session requires re-login'
                    }
                else:
                    logger.info(f"[CHECK_LOGIN] Instance #{instance_id} is logged in")
                    return {
                        'status': 'success',
                        'logged_in': True,
                        'message': 'Session is valid and logged in'
                    }
                
            except Exception as e:
                logger.error(f"[CHECK_LOGIN] Error checking login for Instance #{instance_id}: {e}")
                return {'status': 'error', 'message': str(e)}
        
        if event_loop:
            future = asyncio.run_coroutine_threadsafe(check_login(), event_loop)
            result = future.result(timeout=60)
            return jsonify(result)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Event loop not initialized'
            }), 500
    
    except Exception as e:
        logger.error(f"Error checking login: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/launch-instance/<int:instance_id>', methods=['POST'])
def launch_specific_instance(instance_id):
    """Launch a specific saved instance"""
    global voter_system
    
    try:
        if not voter_system:
            return jsonify({
                'status': 'error',
                'message': 'Voter system not initialized. Start monitoring first.'
            }), 400
        
        # Check if instance already running
        if instance_id in voter_system.active_instances:
            return jsonify({
                'status': 'error',
                'message': f'Instance #{instance_id} is already running'
            }), 400
        
        # Launch instance in background
        async def launch():
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            session_dir = os.path.join(project_root, "brightdata_session_data", f"instance_{instance_id}")
            
            if not os.path.exists(session_dir):
                return {'status': 'error', 'message': f'No saved session found for instance #{instance_id}'}
            
            # Load session info
            info_file = os.path.join(session_dir, 'session_info.json')
            if os.path.exists(info_file):
                with open(info_file, 'r') as f:
                    session_info = json.load(f)
                
                proxy_ip = session_info.get('proxy_ip')
                session_id = session_info.get('session_id', proxy_ip.replace('.', '_') if proxy_ip else None)
                
                # Create instance
                instance = VoterInstance(
                    instance_id=instance_id,
                    proxy_ip=proxy_ip,
                    session_id=session_id,
                    target_url=voter_system.target_url,
                    vote_logger=vote_logger,
                    voter_manager=voter_system
                )
                
                # Initialize and start
                success = await instance.initialize(use_session=True)
                if success:
                    voter_system.active_instances[instance_id] = instance
                    instance.voting_task = asyncio.create_task(instance.run_voting_cycle())
                    return {'status': 'success', 'message': f'Instance #{instance_id} launched successfully'}
                else:
                    return {'status': 'error', 'message': f'Failed to initialize instance #{instance_id}'}
            else:
                return {'status': 'error', 'message': f'Session info not found for instance #{instance_id}'}
        
        # Run in event loop
        if event_loop:
            future = asyncio.run_coroutine_threadsafe(launch(), event_loop)
            result = future.result(timeout=30)
            return jsonify(result)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Event loop not initialized'
            }), 500
    
    except Exception as e:
        logger.error(f"Error launching instance #{instance_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("🔌 Client connected")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("🔌 Client disconnected")

# Helper functions
async def check_ready_instances():
    """Check for ready instances from saved sessions"""
    ready_instances = []
    
    try:
        import csv
        
        # Use absolute path relative to project root (one level up from backend)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        session_dir = os.path.join(project_root, "brightdata_session_data")
        log_file = os.path.join(project_root, "voting_logs.csv")
        
        if not os.path.exists(session_dir):
            logger.info(f"📁 No session data folder found at: {session_dir}")
            return ready_instances
        
        # Get list of saved sessions
        session_folders = [f for f in os.listdir(session_dir) 
                          if os.path.isdir(os.path.join(session_dir, f)) and f.startswith('instance_')]
        
        if not session_folders:
            logger.info("📋 No saved sessions found")
            return ready_instances
        
        logger.debug(f"🔍 Scanning {len(session_folders)} saved sessions...")
        
        # Get active instance IDs to filter them out
        active_instance_ids = set()
        if voter_system and hasattr(voter_system, 'active_instances'):
            active_instance_ids = set(
                getattr(instance, 'instance_id', None) 
                for instance in voter_system.active_instances.values() 
                if hasattr(instance, 'instance_id')
            )
        
        # Read last vote times from voting_logs.csv
        instance_last_vote = {}
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            instance_id = int(row.get('instance_id', 0))
                            # Use time_of_click (actual vote time) instead of timestamp (log time)
                            time_of_click_str = row.get('time_of_click', '')
                            status = row.get('status', '')
                            
                            if instance_id and time_of_click_str and status == 'success':
                                vote_time = datetime.fromisoformat(time_of_click_str)
                                # Server is IST, timestamps are IST, no conversion needed
                                # Keep only the most recent vote time for each instance
                                if instance_id not in instance_last_vote or vote_time > instance_last_vote[instance_id]:
                                    instance_last_vote[instance_id] = vote_time
                        except Exception:
                            continue
            except Exception as e:
                logger.error(f"❌ Error reading voting logs: {e}")
        
        # Check each session for cooldown status
        # Server is in IST timezone, datetime.now() returns IST
        current_time = datetime.now()
        ready_count = 0
        cooldown_count = 0
        
        for folder in session_folders:
            try:
                # Extract instance ID from folder name (e.g., "instance_1" -> 1)
                instance_id = int(folder.split('_')[1])
                instance_path = os.path.join(session_dir, folder)
                
                # Skip if instance is already active
                if instance_id in active_instance_ids:
                    logger.debug(f"⏭️ Instance #{instance_id}: Already active, skipping")
                    continue
                
                # Check if session files exist
                session_info_path = os.path.join(instance_path, "session_info.json")
                storage_state_path = os.path.join(instance_path, "storage_state.json")
                
                if not os.path.exists(storage_state_path):
                    continue
                
                # Check cooldown from voting logs
                if instance_id in instance_last_vote:
                    last_vote_time = instance_last_vote[instance_id]
                    time_since_vote = (current_time - last_vote_time).total_seconds() / 60
                    
                    if time_since_vote >= 31:  # 31 minute cooldown
                        ready_instances.append({
                            'instance_id': instance_id,
                            'session_path': instance_path,
                            'last_vote_time': last_vote_time.isoformat(),
                            'minutes_since_vote': int(time_since_vote)
                        })
                        ready_count += 1
                        logger.info(f"✅ Instance #{instance_id}: Ready to launch ({int(time_since_vote)} min since last vote)")
                    else:
                        remaining = 31 - time_since_vote
                        cooldown_count += 1
                        logger.debug(f"⏰ Instance #{instance_id}: {int(remaining)} minutes remaining in cooldown")
                else:
                    # No voting history, ready to launch
                    ready_instances.append({
                        'instance_id': instance_id,
                        'session_path': instance_path,
                        'last_vote_time': None,
                        'minutes_since_vote': None
                    })
                    ready_count += 1
                    logger.info(f"✅ Instance #{instance_id}: Ready to launch (no voting history)")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {folder}: {e}")
                continue
        
        logger.info(f"📊 Scan complete: {ready_count} ready, {cooldown_count} in cooldown")
        
        return ready_instances
        
    except Exception as e:
        logger.error(f"❌ Error checking ready instances: {e}")
        logger.error(traceback.format_exc())
        return ready_instances

async def launch_instance_from_session(instance_info):
    """Launch instance from saved session"""
    global voter_system
    
    try:
        instance_id = instance_info['instance_id']
        session_path = instance_info['session_path']
        
        logger.info(f"🚀 Launching instance #{instance_id} from saved session")
        
        if not voter_system:
            logger.error("❌ Voter system not initialized")
            return False
        
        # Check if instance is already running by checking all active instances
        for ip, instance in voter_system.active_instances.items():
            if instance.instance_id == instance_id:
                logger.info(f"⚠️ Instance #{instance_id} already running with IP {ip}, skipping")
                return False
        
        # Launch the instance with voter_engine
        try:
            # Create a new voter instance
            voter_instance = await voter_system.launch_instance_from_saved_session(
                instance_id=instance_id,
                session_path=session_path
            )
            
            if voter_instance:
                logger.info(f"✅ Instance #{instance_id} launched successfully")
                
                # Emit status update via WebSocket
                socketio.emit('instance_update', {
                    'instance_id': instance_id,
                    'status': 'launched',
                    'message': f'Instance #{instance_id} launched from saved session'
                })
                
                return True
            else:
                logger.error(f"❌ Failed to launch instance #{instance_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error launching instance #{instance_id}: {e}")
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        logger.error(f"❌ Error in launch_instance_from_session: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    logger.info("🚀 Starting CloudVoter Backend Server...")
    logger.info(f"📍 Server will be available at http://localhost:5000")
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
