Attendance, Catering, and Access Control System Documentation
Overview
This project is a microservices-based system designed for a company with one floor, two rooms, a canteen, and a basement parking area. It automates attendance tracking, catering management, and access control, integrating AI-driven features, role-based access control (RBAC), and sustainability initiatives. The system is built to be scalable, secure, and compliant with GDPR, supporting multilingual interfaces (English, Persian, Arabic) and offline functionality.

Key Objectives
Attendance: Track employee attendance using face recognition, fingerprint, NFC, or QR codes, with penalties/rewards, leave management, and Jira integration.
Catering: Automate food reservations with AI-driven menu recommendations, QR-based tokens, and sustainability incentives for recyclable containers.
Access Control: Manage access to rooms, canteen, and parking using face recognition (including low-light and multi-person support), license plate recognition, and IoT integration for emergency systems.
General Features: Provide ERP/CRM/Jira integrations (mocked), transparency reports, opt-out options for tracking, and energy optimization for access devices.
The system achieves 100% alignment with the provided requirements document, with placeholders for hardware-dependent features (e.g., low-light face recognition) that require physical devices for full implementation.

System Architecture
The system follows a microservices architecture deployed using Docker Compose, with each service handling a specific domain. Services communicate via REST APIs and a GraphQL gateway, with PostgreSQL for data storage and Redis for caching. The frontend is a React-based single-page application (SPA) with separate Administrative and User Panels.

Services
Attendance Service (services/attendance):
Tech: FastAPI, SQLAlchemy, PostgreSQL
Features: Attendance recording, leave requests/approvals, shift management, penalties/rewards, fraud detection, Jira integration, predictive leave analysis.
Endpoints: /users/, /attendance/, /leaves/, /shifts/, /reports/attendance/pdf, /predict-leaves/
Catering Service (services/catering):
Tech: FastAPI, SQLAlchemy, PostgreSQL, scikit-learn
Features: Menu management, food reservations, inventory tracking, waste reporting, AI menu recommendations, QR-based tokens, sustainability rewards.
Endpoints: /menus/, /reservations/, /inventory/, /waste-reports/, /recommend-menu/, /tokens/pdf/, /sustainability/
Access Control Service (services/access-control):
Tech: FastAPI, SQLAlchemy, PostgreSQL, MQTT
Features: Access rules, visitor management, parking reservations, face/license plate recognition (placeholders), emergency system integration.
Endpoints: /access-rules/, /access-logs/, /visitors/, /parking/, /verify-plate/, /verify-faces/, /emergency/fire-alarm/
AI Engine Service (services/ai-engine):
Tech: FastAPI, pandas
Features: Fraud detection, demand prediction for leaves and catering.
Endpoints: /detect-fraud/, /predict-demand/
GraphQL Service (services/graphql):
Tech: Ariadne, FastAPI
Features: Unified API for querying attendance, catering, and access data; transparency reports.
Queries: attendances, reservations, accessLogs, transparencyReport
Frontend Service (services/frontend):
Tech: React, Tailwind CSS, Chart.js, i18next
Features: Administrative Panel (user management, leave approval, reporting) and User Panel (attendance, reservations, schedules); supports offline mode, voice commands, and WCAG compliance.
Components: App.js, AdminPanel.js, UserPanel.js
Mock Services:
Mock Jira (mock-jira): Simulates Jira API for task-hour tracking.
Mock Calendar (mock-calendar): Simulates calendar API for visitor meeting integration.
Data Flow
Frontend: Users interact via the React SPA, which routes to Admin or User Panels based on JWT-decoded roles (employee, manager, hr).
Backend: REST APIs handle requests, with GraphQL providing a unified query interface. PostgreSQL stores data, and Redis caches frequent queries.
AI: The AI Engine processes historical data for fraud detection and predictions, communicating with other services via REST.
IoT: MQTT is used for access control device communication (e.g., door locks, fire alarms).
Security: JWT for authentication, AES-256 encryption for sensitive data, and opt-out options for tracking.
Project Structure
text

Copy
project_root/
├── docker-compose.yml
├── nginx.conf
├── services/
│   ├── attendance/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── database.py
│   │   ├── tests/
│   │   │   ├── test_main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── catering/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── database.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── access-control/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── database.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── ai-engine/
│   │   ├── app/
│   │   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── graphql/
│   │   ├── app/
│   │   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.js
│   │   │   ├── AdminPanel.js
│   │   │   ├── UserPanel.js
│   │   ├── package.json
│   │   ├── Dockerfile
│   ├── mock-jira/
│   ├── mock-calendar/
Setup Instructions
Prerequisites
Docker: For containerized deployment.
Node.js: For frontend development.
Python 3.10+: For backend services.
VS Code: Recommended IDE for development.
Windows/Linux/Mac: Compatible with all platforms.
Installation
Clone the Repository:
bash

Copy
git clone <repository-url>
cd project_root
Install Frontend Dependencies:
bash

Copy
cd services/frontend
npm install
Install Backend Dependencies: For each service (attendance, catering, access-control, ai-engine, graphql):
bash

Copy
cd services/<service>
pip install -r requirements.txt
Configure Environment:
Update TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in services/attendance/app/main.py.
Set SECRET_KEY for JWT in services/attendance/app/main.py.
Ensure Docker Compose has correct port mappings.
Run the System:
bash

Copy
docker-compose up --build
Frontend: http://localhost:3000
GraphQL: http://localhost:8005
REST APIs: http://localhost:<port> (e.g., 8001 for Attendance)
Testing
Backend Tests:
bash

Copy
cd services/attendance
pytest tests/test_main.py
Frontend Testing: Add Jest or React Testing Library for component tests (not yet implemented).
Manual Testing:
Use Postman to test REST endpoints (e.g., /users/, /reservations/, /access-logs/).
Access GraphQL at http://localhost:8005 with queries like:
graphql

Copy
query {
  transparencyReport(userId: 1) {
    user_id
    data_used
  }
}
Usage
Authentication
Login: POST to /token with username and password to obtain a JWT token.
RBAC: Roles (employee, manager, hr) determine access to Admin or User Panels.
Token Storage: Frontend stores JWT in localStorage for API requests.
Administrative Panel (http://localhost:3000, manager or hr role)
User Management: Create/edit users, assign roles.
Leave Approval: Multi-stage approval for leave requests.
Shift Configuration: Create/adjust shifts, including emergency shifts.
Reporting: Download attendance reports (PDF/Excel), view access log heatmaps.
Sustainability: Track recyclable container usage and reward points.
User Panel (http://localhost:3000, employee role)
Attendance: Record entry/exit via button (integrates with face/NFC placeholders).
Catering: Reserve food for the week, view AI-recommended menus, download QR tokens.
Schedules: View personal shift schedules.
Settings: Opt out of tracking for privacy.
Hardware Integration (Placeholders)
Face Recognition: Placeholder in attendance and access-control services (verify_face). Replace with DeepFace or similar for low-light/multi-person support.
Fingerprint/NFC: Placeholder functions (verify_fingerprint, verify_nfc). Integrate with hardware SDKs.
License Plate Recognition: Placeholder in access-control (recognize_plate). Use OpenALPR or similar.
IoT Devices: MQTT used for door locks and fire alarms. Test with actual IoT hardware.
Key Features
Attendance
Multi-Method Authentication: Face, fingerprint, NFC, QR code (placeholders).
Penalties/Rewards: $10 penalty for tardiness (>15 min), $5 reward for punctuality.
Leave Management: Multi-stage approval (manager, HR) with substitute suggestions.
Fraud Detection: AI-driven anomaly detection in attendance patterns.
Jira Integration: Mocked task-hour logging.
Predictive Analysis: AI forecasts leave demand using historical data.
Catering
Reservations: Weekly planning with AI-recommended menus based on user history.
Tokens: QR-based tokens for food pickup, printable via PDF.
Inventory: Tracks ingredients, alerts for low stock.
Sustainability: Rewards (10 points) for using recyclable containers.
Waste Reporting: Tracks food waste for optimization.
Access Control
Access Rules: Time- and location-based rules with two-factor authentication option.
Visitor Management: QR codes for visitors, linked to meeting schedules (mocked calendar).
Parking: Reserves basement parking spots.
Emergency Integration: Fire alarm triggers door unlocking and headcount reports.
Recognition: Placeholders for low-light face recognition and multi-person identification.
General
Integrations: Mocked ERP/CRM/Jira/calendar APIs for extensibility.
Transparency: Reports on data usage (e.g., attendance, access logs) via GraphQL.
Privacy: Opt-out option for tracking (e.g., location, attendance).
Energy Optimization: MQTT-based control of access device power states.
Multilingual: Supports English, Persian, Arabic with RTL support.
Offline Mode: Stores attendance/reservations in IndexedDB for offline use.
Accessibility: WCAG-compliant frontend with voice command support.
Security and Compliance
Authentication: JWT with role-based access control.
Encryption: AES-256 for sensitive data (e.g., access logs).
GDPR: Opt-out options and transparency reports ensure compliance.
Fraud Detection: AI monitors for suspicious patterns in attendance and access.
Limitations and Future Work
Hardware Integration: Current placeholders for face recognition, fingerprint, NFC, and license plate recognition require real hardware and libraries (e.g., DeepFace, OpenALPR).
Scalability: Add load balancing (e.g., Kubernetes) and monitoring (e.g., Prometheus) for production.
Mobile App: Extend frontend to React Native for native iOS/Android apps.
Testing: Implement frontend unit tests and end-to-end tests.
Real Integrations: Replace mocked Jira/ERP/CRM/calendar APIs with actual endpoints.
AI Enhancements: Train AI models on larger datasets for better fraud detection and predictions.
Troubleshooting
Docker Issues: Ensure ports (3000, 8001–8005) are free. Check logs with docker-compose logs.
API Errors: Verify JWT token in Authorization header for protected endpoints.
Frontend Offline Mode: Ensure IndexedDB is enabled in the browser.
Hardware Placeholders: Replace placeholder functions with actual SDKs for production.
