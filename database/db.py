import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'healthcare.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        phone TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        address TEXT NOT NULL,
        emergency_contact TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        purpose TEXT NOT NULL,
        doctor_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Scheduled',
        created_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ambulance_requests (
        id TEXT PRIMARY KEY,
        patient_name TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        pickup_location TEXT NOT NULL,
        destination TEXT NOT NULL,
        emergency_level TEXT NOT NULL,
        requested_time TEXT NOT NULL,
        ambulance_provider TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blood_requirements (
        id TEXT PRIMARY KEY,
        blood_group TEXT NOT NULL,
        units_required INTEGER NOT NULL,
        hospital_name TEXT NOT NULL,
        location TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        required_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        created_at TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS healthcare_facilities (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        services TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    conn.commit()
    seed_demo_data(conn)
    conn.close()

def generate_id(table_name, prefix, conn):
    cursor = conn.cursor()
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0] + 1
    return f'{prefix}-{1000 + count}'

def seed_demo_data(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM patients')
    if cursor.fetchone()[0] > 0:
        return

    today_str = date.today().isoformat()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    patients_data = [
        ('PAT-1001', 'Rahul Sharma', 34, 'Male', '+91 98230 11223', 'B+', '402 Sunrise Heights, Kothrud, Pune', '+91 98230 44556 (Spouse)', now_str),
        ('PAT-1002', 'Priya Patel', 28, 'Female', '+91 97120 44556', 'O+', '12 Nilgiri Villa, Baner Road, Pune', '+91 97120 77889 (Brother)', now_str),
        ('PAT-1003', 'Amit Deshmukh', 52, 'Male', '+91 94220 77889', 'A+', 'Flat 5B Greenfield Apts, Shivaji Nagar, Pune', '+91 94220 99001 (Son)', now_str),
        ('PAT-1004', 'Sunita Rao', 45, 'Female', '+91 98901 22334', 'AB+', '88 Harmony Residency, Aundh, Pune', '+91 98901 55667 (Husband)', now_str),
        ('PAT-1005', 'Vikram Malhotra', 61, 'Male', '+91 97654 33221', 'O-', '21/A Clover Park, Viman Nagar, Pune', '+91 97654 88776 (Daughter)', now_str),
        ('PAT-1006', 'Ananya Sen', 24, 'Female', '+91 98112 33445', 'B-', '103 Oakwood Enclave, Hinjewadi, Pune', '+91 98112 66778 (Father)', now_str),
        ('PAT-1007', 'Rajesh Kulkarni', 39, 'Male', '+91 94033 66778', 'A-', '74 Prabhat Road, Deccan Gymkhana, Pune', '+91 94033 11223 (Sister)', now_str)
    ]
    cursor.executemany('''
        INSERT INTO patients (id, name, age, gender, phone, blood_group, address, emergency_contact, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients_data)

    appointments_data = [
        ('APT-2001', 'PAT-1001', 'Rahul Sharma', today_str, '10:00 AM', 'Routine Blood Pressure Checkup', 'Dr. Sneha Mehta (General Physician)', 'Scheduled', now_str),
        ('APT-2002', 'PAT-1002', 'Priya Patel', today_str, '11:30 AM', 'Post-surgery Wound Dressing & Review', 'Dr. Arjun Patil (Orthopedic Surgeon)', 'Scheduled', now_str),
        ('APT-2003', 'PAT-1003', 'Amit Deshmukh', today_str, '02:00 PM', 'Cardiology Follow-up & ECG Review', 'Dr. Rohan Verma (Cardiologist)', 'Completed', now_str),
        ('APT-2004', 'PAT-1004', 'Sunita Rao', today_str, '03:30 PM', 'Diabetes Management Consultation', 'Dr. Sneha Mehta (General Physician)', 'Scheduled', now_str),
        ('APT-2005', 'PAT-1005', 'Vikram Malhotra', '2026-09-28', '09:30 AM', 'Annual Geriatric Health Review', 'Dr. Rohan Verma (Cardiologist)', 'Scheduled', now_str),
        ('APT-2006', 'PAT-1006', 'Ananya Sen', '2026-09-29', '04:00 PM', 'Pediatric Vaccination & Nutrition Check', 'Dr. Kavita Nair (Pediatrician)', 'Scheduled', now_str),
        ('APT-2007', 'PAT-1007', 'Rajesh Kulkarni', '2026-09-26', '11:00 AM', 'Allergy & Bronchial Follow-up', 'Dr. Sneha Mehta (General Physician)', 'Cancelled', now_str)
    ]
    cursor.executemany('''
        INSERT INTO appointments (id, patient_id, patient_name, date, time, purpose, doctor_name, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', appointments_data)

    ambulance_data = [
        ('AMB-3001', 'Sunita Rao (Escort)', '+91 98901 55667', 'Harmony Residency, Aundh', 'Flora City General Hospital', 'Critical', '10:15 AM', 'Flora Rapid Response #108', 'En Route', now_str),
        ('AMB-3002', 'Mahesh Joshi', '+91 97650 11990', 'Bavdhan Flyover Junction', 'City Trauma Center', 'Urgent', '11:40 AM', 'City Trauma Ambulance Team A', 'Assigned', now_str),
        ('AMB-3003', 'Deepak Tambe', '+91 98221 44332', 'Wakad Highway Toll Plaza', 'Lifecare Multispecialty Clinic', 'Critical', '12:05 PM', 'Metro Lifeline Unit 3', 'Pending', now_str),
        ('AMB-3004', 'Gaurav Shinde', '+91 98450 77112', 'Viman Nagar Symbiosis Gate', 'Apollo Care Emergency Ward', 'Normal', '08:30 AM', 'Red Cross Transport Unit', 'Completed', now_str),
        ('AMB-3005', 'Kiran Shrestha', '+91 99234 55112', 'Khadki Railway Station East', 'Military Hospital Emergency', 'Normal', '09:10 AM', 'City Care Rapid #4', 'Cancelled', now_str)
    ]
    cursor.executemany('''
        INSERT INTO ambulance_requests (id, patient_name, contact_number, pickup_location, destination, emergency_level, requested_time, ambulance_provider, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ambulance_data)

    blood_data = [
        ('BLD-4001', 'O-', 3, 'Flora City General Hospital', 'Kothrud, Pune', '+91 20 2544 8800', today_str, 'Active', now_str),
        ('BLD-4002', 'B+', 4, 'City Trauma Center', 'Shivaji Nagar, Pune', '+91 20 2553 1200', today_str, 'Active', now_str),
        ('BLD-4003', 'AB-', 2, 'Apollo Emergency Wing', 'Senapati Bapat Road, Pune', '+91 20 6609 9999', '2026-09-28', 'Active', now_str),
        ('BLD-4004', 'A+', 5, 'Lifecare Multispecialty Hospital', 'Baner, Pune', '+91 20 2729 4400', '2026-09-27', 'Fulfilled', now_str),
        ('BLD-4005', 'O+', 6, 'Red Cross Blood Bank Core', 'Camp, Pune', '+91 20 2612 3344', '2026-09-29', 'Active', now_str),
        ('BLD-4006', 'B-', 2, 'Deccan Charitable Trust Hospital', 'Deccan, Pune', '+91 20 2567 1199', '2026-09-25', 'Cancelled', now_str)
    ]
    cursor.executemany('''
        INSERT INTO blood_requirements (id, blood_group, units_required, hospital_name, location, contact_number, required_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', blood_data)

    facilities_data = [
        ('FAC-5001', 'Flora City General Hospital', 'Hospital', 'Near Flora IT Park, Hinjewadi, Pune', '+91 20 4011 2200', '24x7 Emergency, ICU, Trauma Care, General Surgery, Radiology, Pharmacy', now_str),
        ('FAC-5002', 'Lifecare Community Clinic', 'Clinic', 'Sector 4, Baner Road, Pune', '+91 20 2729 4400', 'Outpatient OPD, General Medicine, Pediatrics, Minor Dressing, Routine Lab Tests', now_str),
        ('FAC-5003', 'Red Cross Regional Blood Bank', 'Blood Bank', 'MG Road, Camp, Pune', '+91 20 2612 3344', '24x7 Blood Component Separation, Platelet Apheresis, Emergency Cross-Matching', now_str),
        ('FAC-5004', 'Metro Lifeline Ambulance Dispatch', 'Ambulance Provider', 'JM Road, Deccan, Pune', '+91 20 2551 1080', 'Advanced Cardiac Life Support (ACLS), Basic Life Support (BLS), Patient Transport', now_str),
        ('FAC-5005', 'City Trauma & Emergency Center', 'Hospital', 'Shivaji Nagar, Pune', '+91 20 2553 1200', 'Emergency Resuscitation, Polytrauma Surgery, Burn Unit, ICU', now_str),
        ('FAC-5006', 'Apex Blood & Research Center', 'Blood Bank', 'Kothrud Industrial Area, Pune', '+91 20 2544 9911', 'Voluntary Donor Registry, Plasma Bank, Rare Blood Group Registry (Bombay Blood Group, Rh-null)', now_str),
        ('FAC-5007', 'City Care Rapid Ambulance Services', 'Ambulance Provider', 'Viman Nagar, Pune', '+91 20 2663 8822', 'GPS-Tracked Emergency Fleets, Neonatal Transport Units, Inter-facility Transfers', now_str)
    ]
    cursor.executemany('''
        INSERT INTO healthcare_facilities (id, name, type, location, contact_number, services, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', facilities_data)

    conn.commit()