API Documentation
REST APIs
Attendance Service

POST /users/: Create a new user.
POST /attendance/: Record attendance.
POST /leaves/: Request a leave.
GET /attendances/: Get all attendances.
GET /reports/attendance/pdf: Generate PDF report.
GET /reports/attendance/excel: Generate Excel report.

Catering Service

POST /menus/: Create a menu.
POST /reservations/: Create a reservation with QR token.
POST /inventory/: Update inventory.
GET /reservations/: Get all reservations.
GET /recommend-menu/{user_id}: Get recommended menu.

Access Control Service

POST /access-rules/: Create an access rule.
POST /access-logs/: Log access.
POST /visitors/: Create a visitor with QR code.
POST /parking/: Reserve a parking spot.
GET /access-logs/: Get all access logs.

GraphQL API

Endpoint: /graphql
Queries:
attendances: Fetch all attendances.
reservations: Fetch all reservations.
accessLogs: Fetch all access logs.



