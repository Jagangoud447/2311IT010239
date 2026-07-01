import requests
from datetime import datetime

# Priority Weights: Placement (3) > Result (2) > Event (1)
PRIORITY_WEIGHTS = {
    "Placement": 3,
    "Result": 2,
    "Event": 1
}

def fetch_notifications(api_url):
    """
    Attempts to fetch live notifications from the evaluation server.
    Falls back to mock data if hit with a 401 Unauthorized to keep the pipeline functional.
    """
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("[INFO] Successfully fetched real-time notifications from the live server!")
            return response.json()
        
        elif response.status_code == 401:
            print("[WARN] Server responded with 401 Unauthorized (Session/Token missing).")
            print("[INFO] Activating mock fallback dataset to evaluate sorting logic...")
            return get_fallback_mock_data()
            
        else:
            print(f"[ERROR] Unexpected server response: {response.status_code}")
            return get_fallback_mock_data()
            
    except Exception as e:
        print(f"[CONNECTION ERROR] Could not connect to host: {e}")
        return get_fallback_mock_data()

def get_fallback_mock_data():
    """Generates an un-ordered stream of notifications mimicking the production server."""
    return [
        {"id": 1, "title": "Tech Talk", "notificationType": "Event", "createdAt": "2026-07-01T10:00:00Z"},
        {"id": 2, "title": "Google Placement Drive", "notificationType": "Placement", "createdAt": "2026-07-01T09:30:00Z"},
        {"id": 3, "title": "Midterm Exam Results", "notificationType": "Result", "createdAt": "2026-07-01T11:00:00Z"},
        {"id": 4, "title": "Hackathon Registration", "notificationType": "Event", "createdAt": "2026-07-01T12:00:00Z"},
        {"id": 5, "title": "Microsoft Placement Offer", "notificationType": "Placement", "createdAt": "2026-07-01T08:00:00Z"},
        {"id": 6, "title": "Amazon Shortlist", "notificationType": "Placement", "createdAt": "2026-07-01T12:15:00Z"},
        {"id": 7, "title": "Coding Club Meetup", "notificationType": "Event", "createdAt": "2026-06-30T15:00:00Z"},
        {"id": 8, "title": "DBMS Assignment Grades", "notificationType": "Result", "createdAt": "2026-07-01T06:00:00Z"},
        {"id": 9, "title": "Capgemini Interview Schedule", "notificationType": "Placement", "createdAt": "2026-07-01T11:45:00Z"},
        {"id": 10, "title": "Cultural Fest Update", "notificationType": "Event", "createdAt": "2026-07-01T05:00:00Z"},
        {"id": 11, "title": "Python Test Marks", "notificationType": "Result", "createdAt": "2026-07-01T12:20:00Z"}
    ]

def sort_priority_notifications(notifications, top_n=10):
    """Sorts data using compound rules: Weight (DESC) then Recency (DESC)"""
    def calculation_key(item):
        notif_type = item.get("notificationType")
        weight = PRIORITY_WEIGHTS.get(notif_type, 0)
        
        created_at_str = item.get("createdAt")
        try:
            dt = datetime.strptime(created_at_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            dt = datetime.strptime(created_at_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            
        # Negative signs ensure descending order (highest weight and newest timestamps first)
        return (-weight, -dt.timestamp())

    # Sort array inline using our compound keys
    notifications.sort(key=calculation_key)
    return notifications[:top_n]

if __name__ == "__main__":
    TARGET_API = "http://4.224.186.213/evaluation-service/notifications"
    
    print("==================================================")
    print("   STARTING PRIORITY INBOX PROCESSING PIPELINE   ")
    print("==================================================")
    
    # Run pipeline
    raw_data = fetch_notifications(TARGET_API)
    sorted_top_10 = sort_priority_notifications(raw_data, top_n=10)
    
    print("\n--- TOP 10 PRIORITY INBOX NOTIFICATIONS ---")
    for rank, item in enumerate(sorted_top_10, start=1):
        print(f"Rank {rank:02d} | Type: [{item.get('notificationType'):<9}] | Date: {item.get('createdAt')} | Title: {item.get('title')}")
    print("==================================================")