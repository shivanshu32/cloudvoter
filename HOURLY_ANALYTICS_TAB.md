# Hourly Analytics Tab - Feature Documentation

## Overview

Added a new "Hourly Analytics" tab that displays voting statistics grouped by hour, showing how many votes were cast each hour and when hourly limits were reached.

## Features

### 1. **Hourly Breakdown**
- Groups all votes by hour
- Shows total attempts, successful votes, and failed votes per hour
- Displays success rate percentage
- Highlights hours when hourly limit was reached

### 2. **Filters**

**Date Filter:**
- Today
- Yesterday
- Last 7 Days
- Last 30 Days
- All Time

**Show Filter:**
- All Hours
- Hours with Limit (only hours where hourly limit was reached)
- Hours without Limit (only hours with no limits)

### 3. **Sorting**

- Hour (Newest First) - Default
- Hour (Oldest First)
- Votes (High to Low)
- Votes (Low to High)

### 4. **Data Display**

Each hour shows:
- **Hour**: Date and time (e.g., "Oct 22, 12:00 AM")
- **Total Attempts**: All voting attempts in that hour
- **Successful Votes**: Votes that succeeded
- **Failed Votes**: Votes that failed
- **Hourly Limits**: Number of hourly limit detections
- **Success Rate**: Percentage of successful votes
- **Status**: Badge showing:
  - 🟢 "No Limit" (green) - Hour completed without hitting limit
  - 🔴 "Limit Reached (X votes)" (red) - Hourly limit hit after X successful votes

### 5. **Visual Indicators**

- Rows with hourly limits are highlighted in light red background
- Hourly limit count shown in red when limit was reached
- Successful votes shown in green
- Failed votes shown in red

## Implementation

### Frontend (index.html)

**Tab Navigation** (lines 138-145):
- Added "Hourly Analytics" tab button with bar chart icon

**Tab Content** (lines 360-418):
- Filter controls (Date, Sort, Show)
- Refresh button
- Analytics content area with placeholder

**JavaScript Functions** (lines 1490-1651):
- `loadHourlyAnalytics()`: Fetches data from API
- `renderHourlyAnalytics(analytics)`: Renders table with filters and sorting
- Auto-refresh every 30 seconds when tab is active

### Backend (app.py)

**API Endpoint** (lines 736-752):
```python
@app.route('/api/hourly-analytics', methods=['GET'])
def get_hourly_analytics():
    """Get hourly voting analytics from CSV logs"""
    analytics = vote_logger.get_hourly_analytics()
    return jsonify({
        'status': 'success',
        'analytics': analytics
    })
```

### Vote Logger (vote_logger.py)

**Analytics Method** (lines 316-389):
```python
def get_hourly_analytics(self) -> List[Dict]:
    """Get hourly voting analytics from CSV file"""
    # Groups votes by hour
    # Counts attempts, successes, failures
    # Detects hourly limits
    # Returns sorted list
```

**Data Structure:**
```python
{
    'hour': '2025-10-22T12:00:00',  # ISO format
    'total_attempts': 45,
    'successful_votes': 38,
    'failed_votes': 7,
    'hourly_limit_count': 2,
    'votes_before_limit': 38  # How many votes before limit hit
}
```

## How It Works

1. **Data Collection**:
   - Reads all entries from `voting_logs.csv`
   - Groups by hour (rounds timestamp to nearest hour)
   - Counts votes and detects hourly limits

2. **Hourly Limit Detection**:
   - Checks `failure_type` for "hourly" or "limit"
   - Checks `cooldown_message` for "hourly" or "limit"
   - Records number of successful votes before first limit

3. **Filtering**:
   - Client-side filtering by date range
   - Filter by limit status (with/without)
   - Sorting by hour or vote count

4. **Display**:
   - Table format with color-coded data
   - Status badges for quick identification
   - Auto-refresh when tab is active

## Use Cases

### 1. **Track Voting Patterns**
- See which hours have the most voting activity
- Identify peak voting times
- Monitor success rates throughout the day

### 2. **Hourly Limit Analysis**
- Quickly see when hourly limits are being hit
- Determine how many votes before limit is reached
- Identify if limits are consistent or varying

### 3. **Performance Monitoring**
- Compare success rates across different hours
- Identify hours with high failure rates
- Spot trends in voting behavior

### 4. **Troubleshooting**
- Filter to hours with limits to investigate issues
- Check if limits are happening at specific times
- Verify if vote counts are increasing as expected

## Example Output

```
Hour                  | Total | Success | Failed | Limits | Rate  | Status
Oct 22, 12:00 AM     | 45    | 38      | 7      | 2      | 84.4% | Limit Reached (38 votes)
Oct 22, 11:00 PM     | 52    | 52      | 0      | 0      | 100%  | No Limit
Oct 22, 10:00 PM     | 41    | 35      | 6      | 1      | 85.4% | Limit Reached (35 votes)
Oct 22, 09:00 PM     | 48    | 48      | 0      | 0      | 100%  | No Limit
```

## Benefits

1. ✅ **Historical Analysis**: See voting patterns over time
2. ✅ **Limit Tracking**: Know exactly when and after how many votes limits are hit
3. ✅ **Performance Insights**: Identify hours with best/worst success rates
4. ✅ **Data-Driven Decisions**: Use analytics to optimize voting strategy
5. ✅ **Easy Filtering**: Quickly find specific time periods or limit events
6. ✅ **Auto-Refresh**: Stay updated with latest data

## Notes

- Data is read from `voting_logs.csv` (all-time history)
- Hourly limits are detected from failure_type and cooldown_message fields
- "Votes before limit" shows successful votes count when first limit was detected in that hour
- Auto-refresh runs every 30 seconds when tab is active
- All times are in local timezone
- Sorting and filtering happen client-side for instant response
