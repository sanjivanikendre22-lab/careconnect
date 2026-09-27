import os
import unittest
import json
from app import app
from database import db

class CareConnectTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_dashboard(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CARECONNECT', response.data)
        self.assertIn(b'Coordination Dashboard', response.data)
        self.assertIn(b'Total Patients', response.data)
        print('  [PASS] test_01_dashboard')

    def test_02_patients_list(self):
        response = self.client.get('/patients')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rahul Sharma', response.data)
        self.assertIn(b'PAT-1001', response.data)
        print('  [PASS] test_02_patients_list')

    def test_03_patient_crud(self):
        # 1. Add Patient
        response = self.client.post('/patients/add', data={
            'name': 'Test Citizen',
            'age': '40',
            'gender': 'Male',
            'phone': '+91 99887 76655',
            'blood_group': 'AB+',
            'address': 'Plot 99 Tech Valley, Pune',
            'emergency_contact': '+91 99887 11223 (Wife)'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Citizen', response.data)

        conn = db.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM patients WHERE name = 'Test Citizen'")
        row = c.fetchone()
        self.assertIsNotNone(row)
        test_id = row['id']

        # 2. Edit Patient
        response = self.client.post(f'/patients/edit/{test_id}', data={
            'name': 'Test Citizen Updated',
            'age': '41',
            'gender': 'Male',
            'phone': '+91 99887 76655',
            'blood_group': 'AB+',
            'address': 'Plot 100 Tech Valley, Pune',
            'emergency_contact': '+91 99887 11223 (Wife)'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Citizen Updated', response.data)

        # 3. Delete Patient
        response = self.client.post(f'/patients/delete/{test_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        c.execute("SELECT id FROM patients WHERE id = ?", (test_id,))
        self.assertIsNone(c.fetchone())
        conn.close()
        print('  [PASS] test_03_patient_crud (Add, Edit, Delete)')

    def test_04_appointments(self):
        # View
        response = self.client.get('/appointments')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Clinic Appointments', response.data)

        # Book
        response = self.client.post('/appointments/book', data={
            'patient_id': 'PAT-1001',
            'patient_name': 'Rahul Sharma',
            'date': '2026-09-30',
            'time': '11:00 AM',
            'purpose': 'Blood pressure verification check',
            'doctor_name': 'Dr. Sneha Mehta (General Physician)'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        conn = db.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM appointments WHERE purpose = 'Blood pressure verification check'")
        row = c.fetchone()
        self.assertIsNotNone(row)
        appt_id = row['id']

        # Update Status
        response = self.client.post(f'/appointments/status/{appt_id}', data={'status': 'Completed'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        c.execute("SELECT status FROM appointments WHERE id = ?", (appt_id,))
        self.assertEqual(c.fetchone()['status'], 'Completed')
        conn.close()
        print('  [PASS] test_04_appointments (View, Book, Update Status)')

    def test_05_ambulance_requests(self):
        response = self.client.get('/ambulance')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ambulance Dispatch', response.data)

        # Submit request
        response = self.client.post('/ambulance/request', data={
            'patient_name': 'Deepak Verma',
            'contact_number': '+91 98220 99887',
            'pickup_location': 'Sector 10 Gate, Nigdi',
            'destination': 'Flora City General Hospital',
            'emergency_level': 'Critical',
            'requested_time': 'Immediate',
            'ambulance_provider': 'Flora Rapid Response #108'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        conn = db.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM ambulance_requests WHERE patient_name = 'Deepak Verma'")
        row = c.fetchone()
        self.assertIsNotNone(row)
        req_id = row['id']

        # Update status
        response = self.client.post(f'/ambulance/status/{req_id}', data={'status': 'En Route'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        c.execute("SELECT status FROM ambulance_requests WHERE id = ?", (req_id,))
        self.assertEqual(c.fetchone()['status'], 'En Route')
        conn.close()
        print('  [PASS] test_05_ambulance_requests (View, Submit, Status Transition)')

    def test_06_blood_requirements(self):
        response = self.client.get('/blood')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Blood Requirements Board', response.data)

        # Post requirement
        response = self.client.post('/blood/add', data={
            'blood_group': 'O-',
            'units_required': '2',
            'hospital_name': 'Test Emergency Hospital',
            'location': 'Camp, Pune',
            'contact_number': '+91 20 2611 0000',
            'required_date': '2026-09-30'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        conn = db.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM blood_requirements WHERE hospital_name = 'Test Emergency Hospital'")
        row = c.fetchone()
        self.assertIsNotNone(row)
        bld_id = row['id']

        # Update status
        response = self.client.post(f'/blood/status/{bld_id}', data={'status': 'Fulfilled'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        c.execute("SELECT status FROM blood_requirements WHERE id = ?", (bld_id,))
        self.assertEqual(c.fetchone()['status'], 'Fulfilled')
        conn.close()
        print('  [PASS] test_06_blood_requirements (View, Post, Fulfill)')

    def test_07_facilities_and_emergency(self):
        # Facilities
        response = self.client.get('/facilities')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Healthcare Facilities Directory', response.data)

        # Add facility
        response = self.client.post('/facilities/add', data={
            'name': 'Flora Health Hub',
            'type': 'Clinic',
            'location': 'Hinjewadi, Pune',
            'contact_number': '+91 20 4000 1111',
            'services': 'OPD, General Medicine, First Aid'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Emergency Cockpit
        response = self.client.get('/emergency')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Emergency Coordination Cockpit', response.data)
        self.assertIn(b'108', response.data)
        print('  [PASS] test_07_facilities_and_emergency (Directory & Emergency Cockpit)')

    def test_08_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('appointments', data)
        self.assertIn('blood_demand', data)
        self.assertIn('ambulance_levels', data)
        print('  [PASS] test_08_api_stats (JSON Metrics Feed)')

if __name__ == '__main__':
    print('Starting CareConnect Automated Verification Suite...\n')
    unittest.main()
