# CareConnect – Clinic & Emergency Coordination System

> **FIT FEST 2026 / Flora Institute of Technology – Solo Hackathon MVP**  
> An administrative logistics and emergency coordination platform designed for small clinics, ambulance fleets, blood banks, and patients families.

---

## 1. Project Overview
Small healthcare clinics in urban and semi-urban communities face severe operational bottlenecks: appointments are routinely recorded in paper notebooks or fragmented WhatsApp chats, while emergency callers struggle to locate available ambulance units, nearby critical-care beds, or urgent blood donations.

**CareConnect** bridges this gap with an intuitive, unified administrative and emergency coordination hub that digitizes clinic appointments, streamlines ambulance dispatches, aggregates community blood requirements, and organizes local healthcare directories—all within a lightweight, ultra-reliable web application.

---

## 2. Problem Statement
- **Paper & Chat Fragmentation**: Small clinics lose track of appointments, follow-ups, and patient contact histories due to manual note-taking.
- **Critical Dispatch Delays**: Families and clinic staff waste vital minutes making uncoordinated phone calls to find available private or regional ambulance units.
- **Blood Availability Deficits**: Patients needing urgent blood units struggle to locate which nearby blood bank or hospital has active demand or stock.
- **Facility Discovery Bottlenecks**: Healthcare facilities, trauma centers, and diagnostic clinics lack a centralized community directory.

---

## 3. Proposed Solution
CareConnect delivers a unified, zero-bloat web platform that organizes:
1. **Patient Registry**: Secure administrative records (IDs, emergency contacts, blood group, address).
2. **Clinic Appointments**: Scheduling with date/time slots, assigned doctors, and lifecycle status tracking.
3. **Ambulance Coordination**: Emergency dispatch dashboard with urgency categorization (Critical, Urgent, Normal) and live status tracking (Pending -> Assigned -> En Route -> Completed).
4. **Blood Requirements Board**: Centralized demand reporting with blood group filters (A+, A-, B+, B-, AB+, AB-, O+, O-) and location search.
5. **Healthcare Directory**: Verified listing of hospitals, clinics, blood banks, and ambulance fleets with 1-click speed-dialing.
6. **Emergency Coordination Cockpit**: Central hub with national hotline speed-dials (108, 102, 112, 104, 100) and rapid 1-click dispatch.

---

## 4. Key Features
- **Real-Time Operational Dashboard**: Key metrics (Registered Patients, Today's Visits, Pending Consultations, Active Ambulances, Blood Demands) and interactive Chart.js analytics.
- **Patient Directory**: Add, search, edit, and safely delete patient records with automatic `PAT-XXXX` identification.
- **Appointment Lifecycle**: Filter visits by Today, Upcoming, Completed, and Cancelled. Instant status transitions.
- **Ambulance Dispatch Control**: Triage dispatches by urgency level with visual alerts and provider allocation.
- **Blood Demand Matcher**: Clear sample data notices, units tracking, and coordinator contact links.
- **Emergency Speed-Dial & Hotlines**: Pre-configured emergency lines for immediate dialing on mobile devices.
- **Responsive Healthcare UI**: Modern teal/navy clinical theme, accessible high contrast, modal workflows, and zero-reload notifications.

---

## 5. Technology Stack
- **Backend**: Python 3.13 / Flask 3.1.0 (RESTful routing, server-side validation, clean modular design)
- **Database**: SQLite 3 (Auto-initializing schema, parameterized queries, pre-seeded realistic demo data)
- **Frontend**: HTML5, Semantic CSS3, Vanilla JavaScript (ES6), FontAwesome 6, Chart.js CDN
- **Server / Container**: Gunicorn WSGI, Docker (Multi-stage Python slim base), Google Cloud Run ready

---

## 6. System Architecture
```
                         +-----------------------------------+
                         |         Web Browser Client        |
                         |   (Responsive HTML5 / CSS3 / JS)  |
                         +-----------------+-----------------+
                                           | HTTP / REST
                                           v
                         +-----------------------------------+
                         |           Flask Server            |
                         |             (app.py)              |
                         +--------+--------+--------+--------+
                                  |        |        |
         +------------------------+        |        +------------------------+
         v                                 v                                 v
+-----------------+              +-------------------+              +-----------------+
| Patient & Appt  |              | Emergency Dispatch|              |  Blood & Health |
| Service Manager |              | & Fleet Allocator |              | Directory Board |
+--------+--------+              +---------+---------+              +--------+--------+
         |                                 |                                 |
         +------------------------+--------+---------------------------------+
                                  |
                                  v
                      +-------------------------+
                      |   SQLite Database       |
                      | (database/healthcare.db)|
                      +-------------------------+
```

---

## 7. Database Structure

### Schema Overview:
- `patients`: `id (PK, TEXT)`, `name`, `age`, `gender`, `phone`, `blood_group`, `address`, `emergency_contact`, `created_at`
- `appointments`: `id (PK, TEXT)`, `patient_id (FK)`, `patient_name`, `date`, `time`, `purpose`, `doctor_name`, `status`, `created_at`
- `ambulance_requests`: `id (PK, TEXT)`, `patient_name`, `contact_number`, `pickup_location`, `destination`, `emergency_level`, `requested_time`, `ambulance_provider`, `status`, `created_at`
- `blood_requirements`: `id (PK, TEXT)`, `blood_group`, `units_required`, `hospital_name`, `location`, `contact_number`, `required_date`, `status`, `created_at`
- `healthcare_facilities`: `id (PK, TEXT)`, `name`, `type`, `location`, `contact_number`, `services`, `created_at`

*Note: Database tables and realistic demonstration records are generated automatically on the very first startup.*

---

## 8. Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- `pip` package manager

### Steps
1. Navigate to the project directory:
   ```bash
   cd careconnect
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 9. How to Run Locally

Run the Flask application:
```bash
python app.py
```

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```
*(or `http://localhost:5000`)*

The system will automatically initialize `database/healthcare.db` and populate realistic demonstration data (patients, appointments, ambulance dispatches, blood records, and facilities).

---

## 10. Application Screenshots (UI Previews)
*(Screenshots captured during live demonstration)*
- **Dashboard**: Metric cards, Chart.js visualizations, active ambulance radar, today's clinic schedule.
- **Patients Registry**: Searchable table, add patient modal with blood group and emergency contact validation.
- **Appointments Manager**: Status filter tabs (Today, Upcoming, Completed, Cancelled) and booking modal.
- **Ambulance Dispatch Hub**: Urgency level badges (Normal, Urgent, Critical) and live provider status dropdowns.
- **Blood Demand Board**: Quick blood group pills (A+, O-, etc.) and fulfillment toggles.
- **Facilities Directory**: Searchable directory with 1-click calling links.
- **Emergency Cockpit**: High-contrast speed dials (108, 102, 112, 104, 100) and rapid SOS dispatch.

---

## 11. Deployment (Docker)

Build the Docker container:
```bash
docker build -t careconnect:latest .
```

Run the container locally:
```bash
docker run -p 8080:8080 -e PORT=8080 careconnect:latest
```
Visit `http://localhost:8080`.

---

## 12. Google Cloud Run Deployment

CareConnect is designed specifically for containerized deployment on **Google Cloud Run**:
- Binds to `0.0.0.0`
- Dynamically respects the `$PORT` environment variable (default: `8080`)
- Employs production-grade Gunicorn WSGI server with multithreaded workers

### One-Command Deployment using Google Cloud SDK:
```bash
# 1. Authenticate with Google Cloud
gcloud auth login

# 2. Set your Google Cloud Project
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy directly from source to Cloud Run
gcloud run deploy careconnect \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080
```

Google Cloud Run will automatically build the container, provision an HTTPS URL, and scale the service to zero when idle to minimize costs.

---

## 13. Future Scope
The following capabilities represent natural extensions for production rollout beyond the MVP:
- **Live GPS Fleet Tracking**: WebSocket / WebRTC map integration for real-time ambulance vehicle coordinates.
- **Government Blood Bank API (e-RaktKosh)**: Live verified blood stock queries and donor appointment reservations.
- **Automated SMS & WhatsApp Alerts**: Twilio or Firebase Cloud Messaging triggers for appointment confirmations and ambulance driver arrival notices.
- **Role-Based Authentication (RBAC)**: Distinct permissions for Clinic Doctors, Ambulance Drivers, Blood Bank Admins, and Receptionists.
- **Cloud Database Synchronization**: Migration from SQLite to Google Cloud SQL (PostgreSQL) for distributed multi-clinic deployments.

---

## 14. Important Safety & Scope Disclaimer
> **MANDATORY HEALTHCARE DISCLAIMER:**  
> **CareConnect is strictly an administrative and emergency logistics coordination platform.**  
> It **DOES NOT** provide medical diagnosis, medical advice, clinical treatment recommendations, prescription generation, medical decision-making, or disease prediction.  
> In any life-threatening medical emergency, users must immediately contact certified emergency medical services (such as dialing **108** or **112**) or visit the nearest hospital emergency department.
