import os
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__, static_folder='images', static_url_path='/images')

# =========================================================================
# DATABASE CONNECTION SETUP
# Replace this string with the actual Driver URI from your Atlas modal screen!
# =========================================================================
client = MongoClient( os.getenv("MONGO_URI")
try:
    client = MongoClient(MONGO_URI)
    db = client['gmc_ministry_db']
    members_col = db['members']
    attendance_col = db['attendance_logs']
    print("Successfully connected to GMC MongoDB Atlas database Cluster!")
except Exception as e:
    print(f"Database connection breakdown error: {e}")

# Helper function to compute age accurately from birthday string
def calculate_age(born_str):
    if not born_str:
        return "N/A"
    try:
        born = datetime.strptime(born_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except Exception:
        return "N/A"

# Route to serve the main frontend web page layout template
@app.route('/')
def index():
    return render_template('index.html')

# =========================================================================
# TAB 1: SUBMIT NEW MEMBER ONBOARDING PROFILES
# =========================================================================
@app.route('/api/register', methods=['POST'])
def register_member():
    try:
        # Pull values out of the incoming form submittal data
        data = request.form
        
        # Build structure document mapping parameters safely
        new_profile = {
            "full_name": data.get("full_name", "").strip(),
            "email": data.get("email", "").strip(),
            "area": data.get("area", "").strip(),
            "birthday": data.get("birthday", ""),
            "parent_phone": data.get("parent_phone", "").strip(),
            "why_important": data.get("why_important", "").strip(),
            "goto_scripture": data.get("goto_scripture", "").strip(),
            "skills": request.form.getlist("skills"),  # Parses array list from checkboxes
            "age": "", # Placeholder to match structure updates
            "gender": "",
            "location": "",
            "baptism_date": "",
            "target_baptism": "",
            "status": "Registered Today",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Prevent completely blank data injections if name is missing entirely
        if not new_profile["full_name"]:
            return jsonify({"status": "error", "message": "Full Name parameter required to open a tracking account"}), 400
            
        result = members_col.insert_one(new_profile)
        return jsonify({"status": "success", "message": "GMC Profile saved successfully!", "id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================================
# TAB 2A: LIVE ASYNC BACKGROUND AUTO-SEARCH ALGORITHM 
# =========================================================================
@app.route('/api/search', methods=['GET'])
def search_members():
    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify([])
        
    try:
        # Dynamic case-insensitive regex search matches query starting characters
        regex_query = {"full_name": {"$regex": f"^{query_text}", "$options": "i"}}
        records = members_col.find(regex_query).limit(10) # Safe mobile resource optimization cap
        
        output_results = []
        for record in records:
            # Handle age calculations on the fly dynamically
            age_val = record.get("age") or calculate_age(record.get("birthday"))
            
            output_results.append({
                "id": str(record["_id"]),
                "name": record.get("full_name", "Unknown"),
                "status": record.get("status", "Existing Member"),
                "area": record.get("location") or record.get("area") or "Unknown Region",
                "age": age_val
            })
        return jsonify(output_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================================
# TAB 2B: ATTENDANCE CHECK-IN LOGGER WITH TIMESTAMPS
# =========================================================================
@app.route('/api/checkin', methods=['POST'])
def execute_checkin():
    try:
        req_data = request.get_json() or {}
        member_name = req_data.get("name")
        
        # Find member by name to get parent info
        member = members_col.find_one({"full_name": member_name})
        parent_name = member.get("full_name", "") if member else "N/A"
        parent_phone = member.get("parent_phone", "") if member else ""
        
        now = datetime.now()
        checkout_time = now + timedelta(hours=4)
        
        log_entry = {
            "name": member_name,
            "checkin_date": now.strftime("%Y-%m-%d"),
            "checkin_time": now.strftime("%H:%M:%S"),
            "checkin_datetime": now,
            "checkout_time": checkout_time,
            "checked_out": False,
            "parent_name": parent_name,
            "parent_phone": parent_phone
        }
        result = attendance_col.insert_one(log_entry)
        return jsonify({
            "status": "success", 
            "message": f"Welcome logged for {member_name}",
            "checkout_time": checkout_time.strftime("%H:%M:%S")
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================================
# GET CURRENT CHECKED-IN MEMBERS
# =========================================================================
@app.route('/api/current-checkins', methods=['GET'])
def get_current_checkins():
    try:
        now = datetime.now()
        # Get all members checked in but not checked out
        current_checkins = list(attendance_col.find({"checked_out": False}))
        
        result = []
        for checkin in current_checkins:
            checkout_dt = checkin.get("checkout_time")
            is_expired = now > checkout_dt if checkout_dt else False
            
            result.append({
                "id": str(checkin["_id"]),
                "name": checkin.get("name", ""),
                "parent_name": checkin.get("parent_name", "N/A"),
                "parent_phone": checkin.get("parent_phone", ""),
                "checkin_time": checkin.get("checkin_time", ""),
                "checkout_time": checkout_dt.strftime("%H:%M:%S") if checkout_dt else "N/A",
                "is_expired": is_expired
            })
        
        # Auto-checkout expired members
        attendance_col.update_many(
            {"checked_out": False, "checkout_time": {"$lt": now}},
            {"$set": {"checked_out": True, "actual_checkout_time": now}}
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================================
# MANUAL CHECKOUT ENDPOINT
# =========================================================================
@app.route('/api/checkout', methods=['POST'])
def execute_checkout():
    try:
        req_data = request.get_json() or {}
        checkin_id = req_data.get("id")
        
        if not checkin_id:
            return jsonify({"status": "error", "message": "Invalid check-in ID"}), 400
        
        now = datetime.now()
        attendance_col.update_one(
            {"_id": ObjectId(checkin_id)},
            {"$set": {"checked_out": True, "actual_checkout_time": now}}
        )
        
        return jsonify({"status": "success", "message": "Member checked out"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================================
# TAB 2C: ON-THE-FLY PROFILE ACCOUNT UPDATE PARAMETERS
# =========================================================================
@app.route('/api/update', methods=['POST'])
def update_profile():
    try:
        data = request.form
        m_id = data.get("member_id")
        
        if not m_id:
            return jsonify({"status": "error", "message": "Invalid Reference Target Profile Id"}), 400
            
        updated_fields = {
            "age": data.get("age", "").strip(),
            "gender": data.get("gender", ""),
            "location": data.get("location", "").strip(),
            "baptism_date": data.get("baptism_date", ""),
            "target_baptism": data.get("target_baptism", ""),
            "status": "Existing" # Upgrades status tier cleanly once updated
        }
        
        members_col.update_one({"_id": ObjectId(m_id)}, {"$set": updated_fields})
        return jsonify({"status": "success", "message": "GMC Profile record adjustments completed successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================================
# TAB 3: SECURE LIVE ROSTER RETRIEVAL (KIDS / EMERGENCY ACCESS)
# =========================================================================
@app.route('/api/roster', methods=['GET'])
def get_emergency_roster():
    try:
        # FIX: Only look up active check-ins instead of pulling all members
        active_checkins = attendance_col.find({"checked_out": False})
        roster_output = []
        
        for log in active_checkins:
            # Look up the member profile dynamically to grab area/age details securely
            record = members_col.find_one({"full_name": log.get("name")})
            if not record:
                continue
                
            age_raw = record.get("age")
            calculated_age_val = calculate_age(record.get("birthday")) if not age_raw else age_raw
            
            roster_output.append({
                "name": log.get("name", "Unknown Profile"),
                "area": record.get("location") or record.get("area") or "Unknown Area",
                "age": calculated_age_val,
                "parent_phone": log.get("parent_phone", "").strip()
            })
        return jsonify(roster_output)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    # Starts app local listening service network layer 
    app.run(debug=True, host='0.0.0.0', port=5000)
