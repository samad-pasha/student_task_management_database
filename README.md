School Management System
A Python-based application for managing students, faculty, and tasks in an educational institution. Built with object-oriented principles, it uses SQLite for data persistence and ReportLab for PDF report generation. Supports role-based access for admins, faculty, and students.
License: MIT
Features

Student Management: Add/edit students, record grades, mark attendance, and generate PDF/CSV reports.
Faculty Management: Register faculty, assign tasks, and manage student grades/attendance.
Task Management: Create tasks/subtasks, assign to students, and filter by category.
Security: SHA-256 hashed passwords with role-based authentication.
Reporting: Generate individual or all-students reports in PDF/CSV formats.

Prerequisites

Python 3.6+
Required packages: reportlab

Installation

Clone the repository:git clone https://github.com/samad-pasha/school-management-system.git
cd school-management-system


Install dependencies:pip install reportlab


Run the application:python main.py



Usage

Run the Program:Launch the CLI with python main.py and select a user role (Admin, Faculty, or Student).
Default Credentials:
Admin: ID admin, Password admin@123
Faculty/Students: Set via admin interface (defaults: teacher@123/student@123).


Example Commands:
Admin: Add a student (Student Menu > Register New Student).
Faculty: Assign a task (Task Menu > Create New Task).
Student: View details (View Personal Information and Tasks).



Project Structure

main.py: Core application with all classes and CLI interface.
school.db: SQLite database (generated on first run).
StudentTaskManager/: Directory for generated PDF/CSV reports.

Contributing
Contributions are welcome! Please:

Fork the repository.
Create a feature branch (git checkout -b feature/your-feature).
Commit changes (git commit -m 'Add your feature').
Push to the branch (git push origin feature/your-feature).
Open a pull request.

Issues
Report bugs or suggest features via GitHub Issues.
License
This project is licensed under the MIT License. See the LICENSE file for details.
