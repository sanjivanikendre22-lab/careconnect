import os
import re
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'careconnect-fitfest-2026')

with app.app_context():
    db.init_db()

VALID_BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
VALID_EMERGENCY_LEVELS = ['Normal', 'Urgent', 'Critical']
VALID_APPT_STATUSES = ['Scheduled', 'Completed', 'Cancelled']
VALID_AMB_STATUSES = ['Pending', 'Assigned', 'En Route', 'Completed', 'Cancelled']
VALID_BLOOD_STATUSES = ['Active', 'Fulfilled', 'Cancelled']
VALID_FACILITY_TYPES = ['Hospital', 'Clinic', 'Blood Bank', 'Ambulance Provider']

def clean_str(val):
    return val.strip() if val else ''

def validate_phone(phone):
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return len(cleaned) >= 7 and cleaned.isdigit()

def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False

@app.context_processor
def inject_global_data():
    today_str = date.today().strftime('%A, %d %B %Y')
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ambulance_requests WHERE emergency_level = 'Critical' AND status IN ('Pending', 'Assigned', 'En Route')")
    critical_amb_count = c.fetchone()[0]
    conn.close()
    return {
        'today_display': today_str,
        'critical_amb_count': critical_amb_count,
        'current_date': date.today().isoformat()
    }

@app.route('/')
def dashboard():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    today_iso = date.today().isoformat()

    cursor.execute('SELECT COUNT(*) FROM patients')
    total_patients = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM appointments WHERE date = ?', (today_iso,))
    today_appointments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Scheduled'")
    pending_appointments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Completed'")
    completed_appointments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ambulance_requests WHERE status IN ('Pending', 'Assigned', 'En Route')")
    pending_ambulance = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM blood_requirements WHERE status = 'Active'")
    active_blood = cursor.fetchone()[0]

    cursor.execute('SELECT * FROM appointments ORDER BY date ASC, time ASC LIMIT 5')
    recent_appointments = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM ambulance_requests 
        WHERE status IN ('Pending', 'Assigned', 'En Route')
        ORDER BY CASE emergency_level WHEN 'Critical' THEN 1 WHEN 'Urgent' THEN 2 ELSE 3 END, created_at DESC 
        LIMIT 5
    ''')
    active_ambulance = cursor.fetchall()

    cursor.execute("SELECT * FROM blood_requirements WHERE status = 'Active' ORDER BY required_date ASC LIMIT 5")
    active_blood_reqs = cursor.fetchall()
    conn.close()

    stats = {
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,
        'pending_ambulance': pending_ambulance,
        'active_blood': active_blood
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_appointments=recent_appointments,
        active_ambulance=active_ambulance,
        active_blood_reqs=active_blood_reqs
    )

@app.route('/patients')
def patients():
    search_query = clean_str(request.args.get('q', ''))
    conn = db.get_db_connection()
    cursor = conn.cursor()

    if search_query:
        param = f'%{search_query}%'
        cursor.execute('''
            SELECT * FROM patients 
            WHERE name LIKE ? OR phone LIKE ? OR id LIKE ? OR blood_group LIKE ? OR address LIKE ?
            ORDER BY created_at DESC
        ''', (param, param, param, param, param))
    else:
        cursor.execute('SELECT * FROM patients ORDER BY created_at DESC')

    patients_list = cursor.fetchall()
    conn.close()
    return render_template('patients.html', patients=patients_list, search_query=search_query)

@app.route('/patients/add', methods=['POST'])
def add_patient():
    name = clean_str(request.form.get('name'))
    age_str = clean_str(request.form.get('age'))
    gender = clean_str(request.form.get('gender'))
    phone = clean_str(request.form.get('phone'))
    blood_group = clean_str(request.form.get('blood_group'))
    address = clean_str(request.form.get('address'))
    emergency_contact = clean_str(request.form.get('emergency_contact'))

    if not (name and age_str and gender and phone and blood_group and address and emergency_contact):
        flash('All fields are required. Please fill in all patient details.', 'danger')
        return redirect(url_for('patients'))

    try:
        age = int(age_str)
        if age < 0 or age > 130:
            raise ValueError()
    except ValueError:
        flash('Invalid age. Please enter a valid number between 0 and 130.', 'danger')
        return redirect(url_for('patients'))

    if blood_group not in VALID_BLOOD_GROUPS:
        flash(f'Invalid blood group selected. Must be one of {", ".join(VALID_BLOOD_GROUPS)}.', 'danger')
        return redirect(url_for('patients'))

    if not validate_phone(phone):
        flash('Invalid phone number format. Please provide at least 7 digits.', 'danger')
        return redirect(url_for('patients'))

    conn = db.get_db_connection()
    new_id = db.generate_id('patients', 'PAT', conn)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patients (id, name, age, gender, phone, blood_group, address, emergency_contact, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (new_id, name, age, gender, phone, blood_group, address, emergency_contact, now_str))
    conn.commit()
    conn.close()

    flash(f'Patient {name} ({new_id}) successfully registered!', 'success')
    return redirect(url_for('patients'))

@app.route('/patients/edit/<patient_id>', methods=['POST'])
def edit_patient(patient_id):
    name = clean_str(request.form.get('name'))
    age_str = clean_str(request.form.get('age'))
    gender = clean_str(request.form.get('gender'))
    phone = clean_str(request.form.get('phone'))
    blood_group = clean_str(request.form.get('blood_group'))
    address = clean_str(request.form.get('address'))
    emergency_contact = clean_str(request.form.get('emergency_contact'))

    if not (name and age_str and gender and phone and blood_group and address and emergency_contact):
        flash('All fields are required for updating patient details.', 'danger')
        return redirect(url_for('patients'))

    try:
        age = int(age_str)
        if age < 0 or age > 130:
            raise ValueError()
    except ValueError:
        flash('Invalid age. Must be between 0 and 130.', 'danger')
        return redirect(url_for('patients'))

    if blood_group not in VALID_BLOOD_GROUPS:
        flash('Invalid blood group.', 'danger')
        return redirect(url_for('patients'))

    if not validate_phone(phone):
        flash('Invalid phone number format.', 'danger')
        return redirect(url_for('patients'))

    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE patients 
        SET name = ?, age = ?, gender = ?, phone = ?, blood_group = ?, address = ?, emergency_contact = ?
        WHERE id = ?
    ''', (name, age, gender, phone, blood_group, address, emergency_contact, patient_id))

    cursor.execute('UPDATE appointments SET patient_name = ? WHERE patient_id = ?', (name, patient_id))
    conn.commit()
    conn.close()

    flash(f'Patient {patient_id} updated successfully!', 'success')
    return redirect(url_for('patients'))

@app.route('/patients/delete/<patient_id>', methods=['POST'])
def delete_patient(patient_id):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments WHERE patient_id = ?', (patient_id,))
    cursor.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
    conn.commit()
    conn.close()

    flash(f'Patient {patient_id} and associated records removed successfully.', 'success')
    return redirect(url_for('patients'))

@app.route('/appointments')
def appointments():
    filter_status = clean_str(request.args.get('filter', 'all')).lower()
    search_query = clean_str(request.args.get('q', ''))
    today_iso = date.today().isoformat()

    conn = db.get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM appointments WHERE 1=1'
    params = []

    if filter_status == 'today':
        query += ' AND date = ?'
        params.append(today_iso)
    elif filter_status == 'upcoming':
        query += ' AND date >= ? AND status = ?'
        params.extend([today_iso, 'Scheduled'])
    elif filter_status == 'completed':
        query += ' AND status = ?'
        params.append('Completed')
    elif filter_status == 'cancelled':
        query += ' AND status = ?'
        params.append('Cancelled')

    if search_query:
        query += ' AND (patient_name LIKE ? OR doctor_name LIKE ? OR purpose LIKE ? OR id LIKE ?)'
        p = f'%{search_query}%'
        params.extend([p, p, p, p])

    query += ' ORDER BY date ASC, time ASC'
    cursor.execute(query, params)
    appointments_list = cursor.fetchall()

    cursor.execute('SELECT id, name, phone FROM patients ORDER BY name ASC')
    all_patients = cursor.fetchall()

    conn.close()
    return render_template(
        'appointments.html',
        appointments=appointments_list,
        all_patients=all_patients,
        filter_status=filter_status,
        search_query=search_query
    )

@app.route('/appointments/book', methods=['POST'])
def book_appointment():
    patient_id = clean_str(request.form.get('patient_id'))
    patient_name = clean_str(request.form.get('patient_name'))
    appt_date = clean_str(request.form.get('date'))
    appt_time = clean_str(request.form.get('time'))
    purpose = clean_str(request.form.get('purpose'))
    doctor_name = clean_str(request.form.get('doctor_name'))

    if not (appt_date and appt_time and purpose and doctor_name):
        flash('All appointment fields are required.', 'danger')
        return redirect(url_for('appointments'))

    if not validate_date(appt_date):
        flash('Invalid appointment date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('appointments'))

    conn = db.get_db_connection()
    cursor = conn.cursor()

    if patient_id and not patient_name:
        cursor.execute('SELECT name FROM patients WHERE id = ?', (patient_id,))
        row = cursor.fetchone()
        if row:
            patient_name = row['name']
    elif not patient_id:
        patient_id = 'WALK-IN'
        if not patient_name:
            patient_name = 'Walk-in Patient'

    new_id = db.generate_id('appointments', 'APT', conn)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO appointments (id, patient_id, patient_name, date, time, purpose, doctor_name, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?)
    ''', (new_id, patient_id, patient_name, appt_date, appt_time, purpose, doctor_name, now_str))
    conn.commit()
    conn.close()

    flash(f'Appointment {new_id} booked for {patient_name} with {doctor_name} on {appt_date} at {appt_time}!', 'success')
    return redirect(url_for('appointments'))

@app.route('/appointments/status/<appt_id>', methods=['POST'])
def update_appointment_status(appt_id):
    new_status = clean_str(request.form.get('status'))
    if new_status not in VALID_APPT_STATUSES:
        flash('Invalid appointment status.', 'danger')
        return redirect(url_for('appointments'))

    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE appointments SET status = ? WHERE id = ?', (new_status, appt_id))
    conn.commit()
    conn.close()

    flash(f'Appointment {appt_id} status updated to {new_status}.', 'success')
    return redirect(url_for('appointments'))

@app.route('/ambulance')
def ambulance():
    status_filter = clean_str(request.args.get('status', 'all')).capitalize()
    level_filter = clean_str(request.args.get('level', 'all')).capitalize()
    search_query = clean_str(request.args.get('q', ''))

    conn = db.get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM ambulance_requests WHERE 1=1'
    params = []

    if status_filter != 'All' and status_filter in VALID_AMB_STATUSES:
        query += ' AND status = ?'
        params.append(status_filter)

    if level_filter != 'All' and level_filter in VALID_EMERGENCY_LEVELS:
        query += ' AND emergency_level = ?'
        params.append(level_filter)

    if search_query:
        query += ' AND (patient_name LIKE ? OR pickup_location LIKE ? OR destination LIKE ? OR ambulance_provider LIKE ? OR id LIKE ?)'
        p = f'%{search_query}%'
        params.extend([p, p, p, p, p])

    query += ''' ORDER BY 
        CASE status 
            WHEN 'Pending' THEN 1 
            WHEN 'Assigned' THEN 2 
            WHEN 'En Route' THEN 3 
            WHEN 'Completed' THEN 4 
            ELSE 5 END,
        CASE emergency_level 
            WHEN 'Critical' THEN 1 
            WHEN 'Urgent' THEN 2 
            ELSE 3 END,
        created_at DESC'''

    cursor.execute(query, params)
    requests_list = cursor.fetchall()

    cursor.execute("SELECT name FROM healthcare_facilities WHERE type = 'Ambulance Provider'")
    providers = [row['name'] for row in cursor.fetchall()]

    conn.close()
    return render_template(
        'ambulance.html',
        ambulance_requests=requests_list,
        providers=providers,
        status_filter=status_filter,
        level_filter=level_filter,
        search_query=search_query
    )

@app.route('/ambulance/request', methods=['POST'])
def create_ambulance_request():
    patient_name = clean_str(request.form.get('patient_name'))
    contact_number = clean_str(request.form.get('contact_number'))
    pickup_location = clean_str(request.form.get('pickup_location'))
    destination = clean_str(request.form.get('destination'))
    emergency_level = clean_str(request.form.get('emergency_level'))
    ambulance_provider = clean_str(request.form.get('ambulance_provider')) or 'Unassigned'
    requested_time = clean_str(request.form.get('requested_time')) or datetime.now().strftime('%I:%M %p')

    if not (patient_name and contact_number and pickup_location and destination and emergency_level):
        flash('All required fields must be filled to dispatch ambulance request.', 'danger')
        return redirect(url_for('ambulance'))

    if emergency_level not in VALID_EMERGENCY_LEVELS:
        flash('Invalid emergency level selected.', 'danger')
        return redirect(url_for('ambulance'))

    if not validate_phone(contact_number):
        flash('Invalid contact phone number format.', 'danger')
        return redirect(url_for('ambulance'))

    conn = db.get_db_connection()
    new_id = db.generate_id('ambulance_requests', 'AMB', conn)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    initial_status = 'Assigned' if ambulance_provider != 'Unassigned' else 'Pending'

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ambulance_requests (id, patient_name, contact_number, pickup_location, destination, emergency_level, requested_time, ambulance_provider, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (new_id, patient_name, contact_number, pickup_location, destination, emergency_level, requested_time, ambulance_provider, initial_status, now_str))
    conn.commit()
    conn.close()

    flash(f'Ambulance Request {new_id} ({emergency_level}) submitted! Status: {initial_status}', 'success')
    return redirect(url_for('ambulance'))

@app.route('/ambulance/status/<req_id>', methods=['POST'])
def update_ambulance_status(req_id):
    new_status = clean_str(request.form.get('status'))
    provider = clean_str(request.form.get('ambulance_provider'))

    if new_status and new_status not in VALID_AMB_STATUSES:
        flash('Invalid ambulance status.', 'danger')
        return redirect(url_for('ambulance'))

    conn = db.get_db_connection()
    cursor = conn.cursor()

    if provider and new_status:
        cursor.execute('UPDATE ambulance_requests SET status = ?, ambulance_provider = ? WHERE id = ?', (new_status, provider, req_id))
    elif new_status:
        cursor.execute('UPDATE ambulance_requests SET status = ? WHERE id = ?', (new_status, req_id))
    elif provider:
        cursor.execute('UPDATE ambulance_requests SET ambulance_provider = ? WHERE id = ?', (provider, req_id))

    conn.commit()
    conn.close()

    flash(f'Ambulance Request {req_id} updated successfully.', 'success')
    return redirect(url_for('ambulance'))

@app.route('/blood')
def blood():
    blood_group_filter = clean_str(request.args.get('group', 'all')).upper()
    location_filter = clean_str(request.args.get('location', ''))
    status_filter = clean_str(request.args.get('status', 'all')).capitalize()
    search_query = clean_str(request.args.get('q', ''))

    conn = db.get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM blood_requirements WHERE 1=1'
    params = []

    if blood_group_filter != 'ALL' and blood_group_filter in VALID_BLOOD_GROUPS:
        query += ' AND blood_group = ?'
        params.append(blood_group_filter)

    if status_filter != 'All' and status_filter in VALID_BLOOD_STATUSES:
        query += ' AND status = ?'
        params.append(status_filter)

    if location_filter:
        query += ' AND location LIKE ?'
        params.append(f'%{location_filter}%')

    if search_query:
        query += ' AND (hospital_name LIKE ? OR location LIKE ? OR blood_group LIKE ? OR id LIKE ?)'
        p = f'%{search_query}%'
        params.extend([p, p, p, p])

    query += ''' ORDER BY 
        CASE status 
            WHEN 'Active' THEN 1 
            WHEN 'Fulfilled' THEN 2 
            ELSE 3 END,
        required_date ASC'''

    cursor.execute(query, params)
    requirements_list = cursor.fetchall()
    conn.close()

    return render_template(
        'blood.html',
        requirements=requirements_list,
        blood_groups=VALID_BLOOD_GROUPS,
        blood_group_filter=blood_group_filter,
        location_filter=location_filter,
        status_filter=status_filter,
        search_query=search_query
    )

@app.route('/blood/add', methods=['POST'])
def add_blood_requirement():
    blood_group = clean_str(request.form.get('blood_group'))
    units_str = clean_str(request.form.get('units_required'))
    hospital_name = clean_str(request.form.get('hospital_name'))
    location = clean_str(request.form.get('location'))
    contact_number = clean_str(request.form.get('contact_number'))
    required_date = clean_str(request.form.get('required_date'))

    if not (blood_group and units_str and hospital_name and location and contact_number and required_date):
        flash('All fields are required to post a blood requirement.', 'danger')
        return redirect(url_for('blood'))

    if blood_group not in VALID_BLOOD_GROUPS:
        flash('Invalid blood group selected.', 'danger')
        return redirect(url_for('blood'))

    try:
        units = int(units_str)
        if units <= 0 or units > 100:
            raise ValueError()
    except ValueError:
        flash('Units required must be a valid number between 1 and 100.', 'danger')
        return redirect(url_for('blood'))

    if not validate_phone(contact_number):
        flash('Invalid contact phone number format.', 'danger')
        return redirect(url_for('blood'))

    if not validate_date(required_date):
        flash('Invalid required date format.', 'danger')
        return redirect(url_for('blood'))

    conn = db.get_db_connection()
    new_id = db.generate_id('blood_requirements', 'BLD', conn)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO blood_requirements (id, blood_group, units_required, hospital_name, location, contact_number, required_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', ?)
    ''', (new_id, blood_group, units, hospital_name, location, contact_number, required_date, now_str))
    conn.commit()
    conn.close()

    flash(f'Blood Requirement {new_id} for {units} unit(s) of {blood_group} posted successfully!', 'success')
    return redirect(url_for('blood'))

@app.route('/blood/status/<req_id>', methods=['POST'])
def update_blood_status(req_id):
    new_status = clean_str(request.form.get('status'))
    if new_status not in VALID_BLOOD_STATUSES:
        flash('Invalid blood requirement status.', 'danger')
        return redirect(url_for('blood'))

    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE blood_requirements SET status = ? WHERE id = ?', (new_status, req_id))
    conn.commit()
    conn.close()

    flash(f'Blood Requirement {req_id} marked as {new_status}.', 'success')
    return redirect(url_for('blood'))

@app.route('/facilities')
def facilities():
    type_filter = clean_str(request.args.get('type', 'all'))
    location_filter = clean_str(request.args.get('location', ''))
    search_query = clean_str(request.args.get('q', ''))

    conn = db.get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM healthcare_facilities WHERE 1=1'
    params = []

    if type_filter != 'all' and type_filter in VALID_FACILITY_TYPES:
        query += ' AND type = ?'
        params.append(type_filter)

    if location_filter:
        query += ' AND location LIKE ?'
        params.append(f'%{location_filter}%')

    if search_query:
        query += ' AND (name LIKE ? OR location LIKE ? OR services LIKE ? OR contact_number LIKE ?)'
        p = f'%{search_query}%'
        params.extend([p, p, p, p])

    query += ' ORDER BY type ASC, name ASC'
    cursor.execute(query, params)
    facilities_list = cursor.fetchall()
    conn.close()

    return render_template(
        'facilities.html',
        facilities=facilities_list,
        facility_types=VALID_FACILITY_TYPES,
        type_filter=type_filter,
        location_filter=location_filter,
        search_query=search_query
    )

@app.route('/facilities/add', methods=['POST'])
def add_facility():
    name = clean_str(request.form.get('name'))
    fac_type = clean_str(request.form.get('type'))
    location = clean_str(request.form.get('location'))
    contact_number = clean_str(request.form.get('contact_number'))
    services = clean_str(request.form.get('services'))

    if not (name and fac_type and location and contact_number and services):
        flash('All fields are required to register a healthcare facility.', 'danger')
        return redirect(url_for('facilities'))

    if fac_type not in VALID_FACILITY_TYPES:
        flash('Invalid facility type selected.', 'danger')
        return redirect(url_for('facilities'))

    if not validate_phone(contact_number):
        flash('Invalid contact phone number format.', 'danger')
        return redirect(url_for('facilities'))

    conn = db.get_db_connection()
    new_id = db.generate_id('healthcare_facilities', 'FAC', conn)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO healthcare_facilities (id, name, type, location, contact_number, services, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (new_id, name, fac_type, location, contact_number, services, now_str))
    conn.commit()
    conn.close()

    flash(f'Facility "{name}" ({new_id}) successfully added to directory!', 'success')
    return redirect(url_for('facilities'))

@app.route('/emergency')
def emergency():
    conn = db.get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM ambulance_requests 
        WHERE status IN ('Pending', 'Assigned', 'En Route') 
        ORDER BY CASE emergency_level WHEN 'Critical' THEN 1 WHEN 'Urgent' THEN 2 ELSE 3 END, created_at DESC
    ''')
    active_ambulances = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM blood_requirements 
        WHERE status = 'Active' 
        ORDER BY units_required DESC, required_date ASC
    ''')
    urgent_blood = cursor.fetchall()

    cursor.execute("SELECT * FROM healthcare_facilities WHERE type IN ('Hospital', 'Ambulance Provider') ORDER BY type ASC, name ASC")
    emergency_facilities = cursor.fetchall()

    conn.close()

    return render_template(
        'emergency.html',
        active_ambulances=active_ambulances,
        urgent_blood=urgent_blood,
        emergency_facilities=emergency_facilities
    )

@app.route('/api/stats')
def api_stats():
    conn = db.get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT status, COUNT(*) FROM appointments GROUP BY status')
    appt_status_counts = dict(cursor.fetchall())

    cursor.execute("SELECT blood_group, SUM(units_required) FROM blood_requirements WHERE status = 'Active' GROUP BY blood_group")
    blood_group_demand = dict(cursor.fetchall())

    cursor.execute('SELECT emergency_level, COUNT(*) FROM ambulance_requests GROUP BY emergency_level')
    ambulance_levels = dict(cursor.fetchall())

    conn.close()

    return jsonify({
        'appointments': {
            'Scheduled': appt_status_counts.get('Scheduled', 0),
            'Completed': appt_status_counts.get('Completed', 0),
            'Cancelled': appt_status_counts.get('Cancelled', 0)
        },
        'blood_demand': {group: (blood_group_demand.get(group, 0) or 0) for group in VALID_BLOOD_GROUPS},
        'ambulance_levels': {
            'Normal': ambulance_levels.get('Normal', 0),
            'Urgent': ambulance_levels.get('Urgent', 0),
            'Critical': ambulance_levels.get('Critical', 0)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'Starting CareConnect on http://0.0.0.0:{port} ...')
    app.run(host='0.0.0.0', port=port, debug=True)
