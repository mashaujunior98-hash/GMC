from pymongo import MongoClient
from datetime import datetime

# =========================================================================
# DATABASE CONNECTION SETUP
# Replace this string with your actual Driver URI from MongoDB Atlas!
# =========================================================================
MONGO_URI = "mongodb+srv://mashaujunior98_db_user:5ozrMFQhK5dqcWCu@data.ccgekex.mongodb.net/?retryWrites=true&w=majority"

try:
    client = MongoClient(MONGO_URI)
    db = client['gmc_ministry_db']
    members_col = db['members']
    attendance_col = db['attendance_logs']
    
    # Clear out any old lingering records to start fresh
    members_col.delete_many({})
    attendance_col.delete_many({})
    print("🧹 Cleaned existing collection spaces successfully.")

    # 5 Mock profiles designed specifically to test all our UI features
    dummy_members = [
        {
            "full_name": "Eric Jones",
            "email": "eric.jones@gmail.com",
            "area": "Pretoria",
            "birthday": "2014-03-15", # Age 12 (Kid)
            "parent_phone": "+27123456789",
            "why_important": "To build a foundation in faith.",
            "goto_scripture": "Philippians 4:13",
            "skills": ["Music"],
            "age": "", "gender": "", "location": "", "baptism_date": "", "target_baptism": "",
            "status": "Existing",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "full_name": "Eric Smith",
            "email": "esmith@yahoo.com",
            "area": "Midrand",
            "birthday": "2017-08-22", # Age 8 (Kid) - Missing Parent Phone to trigger Warning!
            "parent_phone": "", 
            "why_important": "To learn and make good Christian friends.",
            "goto_scripture": "Psalm 23:1",
            "skills": ["Teaching"],
            "age": "", "gender": "", "location": "", "baptism_date": "", "target_baptism": "",
            "status": "Registered Today",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "full_name": "Sipho Modise",
            "email": "sipho@modise.co.za",
            "area": "Pretoria",
            "birthday": "2008-11-02", # Teenager
            "parent_phone": "+27829991122",
            "why_important": "Ministry helps guide youth choices.",
            "goto_scripture": "Proverbs 3:5-6",
            "skills": ["Media", "Music"],
            "age": "", "gender": "", "location": "", "baptism_date": "", "target_baptism": "",
            "status": "Existing",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "full_name": "Chantel Meyer",
            "email": "chantel.m@outlook.com",
            "area": "Centurion",
            "birthday": "1995-05-14", # Adult
            "parent_phone": "", # Adults don't need parent contacts
            "why_important": "I want to serve the community actively.",
            "goto_scripture": "Romans 8:28",
            "skills": ["Hospitality", "Teaching"],
            "age": "", "gender": "", "location": "", "baptism_date": "", "target_baptism": "",
            "status": "Existing",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "full_name": "Grace Ndlovu",
            "email": "grace.n@gmail.com",
            "area": "Midrand",
            "birthday": "2015-01-30", # Age 11 (Kid)
            "parent_phone": "+27715554433",
            "why_important": "To understand the scriptures deeply.",
            "goto_scripture": "John 3:16",
            "skills": ["Media"],
            "age": "", "gender": "", "location": "", "baptism_date": "", "target_baptism": "",
            "status": "Existing",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    # Insert the array into our members collection
    result = members_col.insert_many(dummy_members)
    print(f"✅ Successfully injected {len(result.inserted_ids)} dummy records into GMC Database!")
    
except Exception as e:
    print(f"❌ Error inserting dummy records: {e}")