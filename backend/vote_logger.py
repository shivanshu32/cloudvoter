"""
Vote Logger for CloudVoter
Tracks voting history and statistics
Enhanced to match googleloginautomate's comprehensive logging
"""

import csv
import json
import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional

class VoteLogger:
    """Logger for voting attempts and results"""
    
    def __init__(self, log_file='voting_logs.csv'):
        self.log_file = log_file
        
        # CRITICAL: Use same directory as main log file for hourly limit log
        log_dir = os.path.dirname(os.path.abspath(log_file))
        self.hourly_limit_log_file = os.path.join(log_dir, 'hourly_limit_logs.csv')
        
        self._file_lock = threading.Lock()  # Thread-safe file access
        self._hourly_limit_lock = threading.Lock()  # Thread-safe hourly limit logging
        self.fieldnames = [
            'timestamp',
            'instance_id', 
            'instance_name',
            'time_of_click',
            'status',
            'voting_url',
            'cooldown_message',
            'failure_type',
            'failure_reason',
            'initial_vote_count',
            'final_vote_count',
            'vote_count_change',
            'proxy_ip',
            'session_id',
            'click_attempts',
            'error_message',
            'browser_closed'
        ]
        
        # Hourly limit log fieldnames
        self.hourly_limit_fieldnames = [
            'timestamp',
            'detection_time',
            'instance_id',
            'instance_name',
            'vote_count',
            'proxy_ip',
            'session_id',
            'cooldown_message',
            'failure_type'
        ]
        
        # Session-based counters (reset when script starts)
        self.session_total_attempts = 0
        self.session_successful_votes = 0
        self.session_failed_votes = 0
        self.session_hourly_limits = 0
        self._counter_lock = threading.Lock()  # Thread-safe counter access
        
        self._ensure_log_file()
        self._ensure_hourly_limit_log_file()
    
    def _ensure_log_file(self):
        """Ensure log file exists with headers"""
        with self._file_lock:  # Thread-safe file creation
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                    writer.writeheader()
    
    def _ensure_hourly_limit_log_file(self):
        """Ensure hourly limit log file exists with headers"""
        with self._hourly_limit_lock:  # Thread-safe file creation
            if not os.path.exists(self.hourly_limit_log_file):
                with open(self.hourly_limit_log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.hourly_limit_fieldnames)
                    writer.writeheader()
    
    def log_hourly_limit(self,
                        instance_id: int,
                        instance_name: str,
                        vote_count: int,
                        proxy_ip: str = "",
                        session_id: str = "",
                        cooldown_message: str = "",
                        failure_type: str = "") -> None:
        """
        Log hourly limit detection to separate CSV
        
        Args:
            instance_id: Instance identifier
            instance_name: Human readable instance name
            vote_count: Total votes when limit was detected
            proxy_ip: IP address used
            session_id: BrightData session ID
            cooldown_message: Cooldown message detected
            failure_type: Type of failure
        """
        try:
            detection_time = datetime.now()
            
            log_entry = {
                'timestamp': detection_time.isoformat(),
                'detection_time': detection_time.strftime('%Y-%m-%d %H:%M:%S'),
                'instance_id': instance_id,
                'instance_name': instance_name,
                'vote_count': vote_count,
                'proxy_ip': proxy_ip,
                'session_id': session_id,
                'cooldown_message': cooldown_message,
                'failure_type': failure_type
            }
            
            # Thread-safe CSV writing
            with self._hourly_limit_lock:
                with open(self.hourly_limit_log_file, 'a', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.hourly_limit_fieldnames)
                    writer.writerow(log_entry)
                    file.flush()
            
            print(f"[HOURLY_LIMIT_LOG] Instance #{instance_id} - Vote count: {vote_count}")
            
        except Exception as e:
            print(f"Error logging hourly limit: {e}")
            import traceback
            traceback.print_exc()
    
    def get_hourly_limit_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get recent hourly limit logs
        
        Args:
            limit: Maximum number of logs to return (default 100)
            
        Returns:
            List of hourly limit log entries (newest first)
        """
        try:
            if not os.path.exists(self.hourly_limit_log_file):
                return []
            
            logs = []
            with self._hourly_limit_lock:
                with open(self.hourly_limit_log_file, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        logs.append(row)
            
            # Sort by timestamp (newest first) and limit
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return logs[:limit]
            
        except Exception as e:
            print(f"Error reading hourly limit logs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def log_vote_attempt(self, 
                        instance_id: int,
                        instance_name: str,
                        time_of_click: datetime,
                        status: str,
                        voting_url: str = "",
                        cooldown_message: str = "",
                        failure_type: str = "",
                        failure_reason: str = "",
                        initial_vote_count: Optional[int] = None,
                        final_vote_count: Optional[int] = None,
                        proxy_ip: str = "",
                        session_id: str = "",
                        click_attempts: int = 1,
                        error_message: str = "",
                        browser_closed: bool = False) -> None:
        """
        Log a voting attempt to CSV
        
        Args:
            instance_id: Instance identifier
            instance_name: Human readable instance name
            time_of_click: When the vote button was clicked
            status: 'success' or 'failed'
            voting_url: URL that was voted on
            cooldown_message: Any cooldown message detected
            failure_type: Type of failure (cooldown, authentication, technical, etc.)
            failure_reason: Detailed failure reason message
            initial_vote_count: Vote count before clicking
            final_vote_count: Vote count after clicking
            proxy_ip: IP address used for voting
            session_id: BrightData session ID
            click_attempts: Number of click attempts made
            error_message: Any error encountered
            browser_closed: Whether browser was closed after attempt
        """
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                vote_count_change = None
                if initial_vote_count is not None and final_vote_count is not None:
                    vote_count_change = final_vote_count - initial_vote_count
                
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'instance_id': instance_id,
                    'instance_name': instance_name,
                    'time_of_click': time_of_click.isoformat(),
                    'status': status,
                    'voting_url': voting_url,
                    'cooldown_message': cooldown_message,
                    'failure_type': failure_type,
                    'failure_reason': failure_reason,
                    'initial_vote_count': initial_vote_count,
                    'final_vote_count': final_vote_count,
                    'vote_count_change': vote_count_change,
                    'proxy_ip': proxy_ip,
                    'session_id': session_id,
                    'click_attempts': click_attempts,
                    'error_message': error_message,
                    'browser_closed': browser_closed
                }
                
                # CRITICAL: Thread-safe CSV writing with retry mechanism
                with self._file_lock:
                    with open(self.log_file, 'a', newline='', encoding='utf-8') as file:
                        writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                        writer.writerow(log_entry)
                        file.flush()  # Ensure data is written immediately
                
                # Update session counters (thread-safe)
                with self._counter_lock:
                    self.session_total_attempts += 1
                    
                    status_lower = status.lower()
                    if 'success' in status_lower:
                        self.session_successful_votes += 1
                    elif 'fail' in status_lower or 'error' in status_lower:
                        self.session_failed_votes += 1
                    
                    # Check for hourly limit/cooldown
                    if failure_type and ('cooldown' in failure_type.lower() or 'hourly' in failure_type.lower()):
                        self.session_hourly_limits += 1
                    elif cooldown_message:
                        self.session_hourly_limits += 1
                
                # Success - break retry loop
                break
                
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    print(f"CSV write attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"CRITICAL: Failed to log vote attempt after {max_retries} attempts: {e}")
            except Exception as e:
                print(f"Error logging vote attempt: {e}")
                break
    
    # Keep old method for backward compatibility
    def log_vote(self, instance_id: int, ip: str, status: str, message: str = '', vote_count: int = 0):
        """Legacy method - redirects to log_vote_attempt"""
        self.log_vote_attempt(
            instance_id=instance_id,
            instance_name=f"Instance_{instance_id}",
            time_of_click=datetime.now(),
            status=status,
            failure_reason=message,
            proxy_ip=ip,
            browser_closed=False
        )
    
    def get_recent_votes(self, limit: int = 100) -> List[Dict]:
        """Get recent voting history"""
        votes = []
        
        try:
            if not os.path.exists(self.log_file):
                return votes
            
            with open(self.log_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                all_votes = list(reader)
                
                # Get last N votes
                recent_votes = all_votes[-limit:] if len(all_votes) > limit else all_votes
                
                for row in reversed(recent_votes):
                    votes.append({
                        'timestamp': row.get('timestamp', ''),
                        'instance_id': row.get('instance_id', ''),
                        'ip': row.get('ip', ''),
                        'status': row.get('status', ''),
                        'message': row.get('message', ''),
                        'vote_count': row.get('vote_count', '0')
                    })
            
            return votes
            
        except Exception as e:
            print(f"Error getting recent votes: {e}")
            return votes
    
    def get_success_rate(self, instance_id: Optional[int] = None) -> Dict:
        """
        Calculate success rate from logged data
        
        Args:
            instance_id: Optional instance ID to filter by
            
        Returns:
            Dictionary with success statistics
        """
        try:
            if not os.path.exists(self.log_file):
                return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}
            
            total = 0
            successful = 0
            failed = 0
            
            with open(self.log_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if instance_id is None or int(row.get('instance_id', 0)) == instance_id:
                        total += 1
                        if row.get('status') == 'success':
                            successful += 1
                        else:
                            failed += 1
            
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            return {
                "total": total,
                "successful": successful, 
                "failed": failed,
                "success_rate": success_rate
            }
            
        except Exception as e:
            print(f"Error calculating success rate: {e}")
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}
    
    def get_session_statistics(self) -> Dict:
        """Get voting statistics for current session only (since script started)"""
        with self._counter_lock:
            stats = {
                'total_attempts': self.session_total_attempts,
                'successful_votes': self.session_successful_votes,
                'failed_votes': self.session_failed_votes,
                'hourly_limits': self.session_hourly_limits,
                'success_rate': 0.0,
                'active_instances': 0  # Will be set by caller
            }
            
            # Calculate success rate
            if stats['total_attempts'] > 0:
                stats['success_rate'] = (stats['successful_votes'] / stats['total_attempts']) * 100
            
            return stats
    
    def get_statistics(self) -> Dict:
        """Get voting statistics (returns session stats, not CSV file stats)"""
        # Return session-based statistics instead of reading from CSV
        return self.get_session_statistics()
    
    def get_statistics_from_csv(self) -> Dict:
        """Get voting statistics from CSV file (all-time history)"""
        stats = {
            'total_attempts': 0,
            'successful_votes': 0,
            'failed_votes': 0,
            'hourly_limits': 0,
            'success_rate': 0.0,
            'active_instances': 0
        }
        
        try:
            if not os.path.exists(self.log_file):
                return stats
            
            with open(self.log_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                instance_ids = set()
                
                for row in reader:
                    stats['total_attempts'] += 1
                    
                    status = row.get('status', '').lower()
                    
                    if 'success' in status:
                        stats['successful_votes'] += 1
                    elif 'fail' in status or 'error' in status:
                        stats['failed_votes'] += 1
                    elif 'hourly' in status or 'limit' in status or 'cooldown' in status:
                        stats['hourly_limits'] += 1
                    
                    instance_id = row.get('instance_id', '')
                    if instance_id:
                        instance_ids.add(instance_id)
                
                stats['active_instances'] = len(instance_ids)
                
                # Calculate success rate
                if stats['total_attempts'] > 0:
                    stats['success_rate'] = (stats['successful_votes'] / stats['total_attempts']) * 100
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return stats
    
    def get_hourly_analytics(self) -> List[Dict]:
        """Get hourly voting analytics from CSV file with hourly limit data"""
        analytics = {}
        
        try:
            # Step 1: Read voting logs to get vote counts per hour
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        try:
                            # Parse timestamp
                            timestamp_str = row.get('timestamp', '')
                            if not timestamp_str:
                                continue
                            
                            # Parse datetime and round to hour
                            dt = datetime.fromisoformat(timestamp_str)
                            hour_key = dt.replace(minute=0, second=0, microsecond=0).isoformat()
                            
                            # Initialize hour data if not exists
                            if hour_key not in analytics:
                                analytics[hour_key] = {
                                    'hour': hour_key,
                                    'total_attempts': 0,
                                    'successful_votes': 0,
                                    'failed_votes': 0,
                                    'hourly_limit_count': 0,
                                    'votes_before_limit': None  # Will be set from hourly_limit_logs.csv
                                }
                            
                            # Count this attempt
                            analytics[hour_key]['total_attempts'] += 1
                            
                            # Check status
                            status = row.get('status', '').lower()
                            
                            if 'success' in status:
                                analytics[hour_key]['successful_votes'] += 1
                            elif 'fail' in status or 'error' in status:
                                analytics[hour_key]['failed_votes'] += 1
                        
                        except Exception as e:
                            # Skip malformed rows
                            continue
            
            # Step 2: Read hourly_limit_logs.csv to get actual hourly limit detections
            if os.path.exists(self.hourly_limit_log_file):
                with open(self.hourly_limit_log_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        try:
                            # Parse timestamp
                            timestamp_str = row.get('timestamp', '')
                            if not timestamp_str:
                                continue
                            
                            # Parse datetime and round to hour
                            dt = datetime.fromisoformat(timestamp_str)
                            hour_key = dt.replace(minute=0, second=0, microsecond=0).isoformat()
                            
                            # Initialize hour data if not exists (in case no votes in that hour)
                            if hour_key not in analytics:
                                analytics[hour_key] = {
                                    'hour': hour_key,
                                    'total_attempts': 0,
                                    'successful_votes': 0,
                                    'failed_votes': 0,
                                    'hourly_limit_count': 0,
                                    'votes_before_limit': None
                                }
                            
                            # Count hourly limit detection
                            analytics[hour_key]['hourly_limit_count'] += 1
                            
                            # Get vote count from hourly limit log
                            vote_count_str = row.get('vote_count', '0')
                            try:
                                vote_count = int(vote_count_str)
                                # Use the FIRST hourly limit's vote count (earliest detection)
                                if analytics[hour_key]['votes_before_limit'] is None:
                                    analytics[hour_key]['votes_before_limit'] = vote_count
                            except (ValueError, TypeError):
                                pass
                        
                        except Exception as e:
                            # Skip malformed rows
                            continue
            
            # Step 3: Set votes_before_limit to 0 for hours with no limit
            for hour_key in analytics:
                if analytics[hour_key]['votes_before_limit'] is None:
                    analytics[hour_key]['votes_before_limit'] = 0
            
            # Convert to list and sort by hour (newest first)
            result = list(analytics.values())
            result.sort(key=lambda x: x['hour'], reverse=True)
            
            return result
            
        except Exception as e:
            print(f"Error getting hourly analytics: {e}")
            import traceback
            traceback.print_exc()
            return []
