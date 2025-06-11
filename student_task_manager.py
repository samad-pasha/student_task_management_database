import sqlite3
import csv
from datetime import datetime, date
from abc import ABC, abstractmethod
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import re
import hashlib

# Abstract Base Class for Database Operations
class DatabaseHandler(ABC):
    @abstractmethod
    def save_to_db(self):
        pass
    
    @abstractmethod
    def load_from_db(self):
        pass

# Student Class implementing Encapsulation
class Student(DatabaseHandler):
    def __init__(self, name, roll_number):
        if not re.match(r'^[A-Za-z]+$', name):
            raise ValueError("Name can only contain alphabets")
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            raise ValueError("Roll number must contain only uppercase letters and digits, exactly 12 characters")
        self._roll_number = roll_number
        self._name = name
        self._grades = {}
        self._attendance = []
        
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not re.match(r'^[A-Za-z]+$', value):
            raise ValueError("Name can only contain alphabets")
        self._name = value
    
    @property
    def roll_number(self):
        return self._roll_number
    
    @roll_number.setter
    def roll_number(self, value):
        if not re.match(r'^[A-Z0-9]{12}$', value):
            raise ValueError("Roll number must contain only uppercase letters and digits, exactly 12 characters")
        self._roll_number = value
        
    def add_grade(self, subject, marks):
        self._grades[subject] = marks
        
    def remove_grade(self, subject):
        if subject in self._grades:
            del self._grades[subject]
        
    def calculate_average_grade(self):
        if not self._grades:
            return 0
        return sum(self._grades.values()) / len(self._grades)
    
    def mark_attendance(self, date, status):
        self._attendance.append((date, status))
        
    def remove_attendance(self, date):
        self._attendance = [(d, s) for d, s in self._attendance if d != date]
        
    def get_attendance_percentage(self):
        if not self._attendance:
            return 0
        present = sum(1 for _, status in self._attendance if status == 'Present')
        return (present / len(self._attendance)) * 100
    
    def save_to_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                        (roll_number TEXT PRIMARY KEY, name TEXT)''')
        cursor.execute('INSERT OR REPLACE INTO students VALUES (?, ?)', 
                      (self._roll_number, self._name))
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS grades 
                        (roll_number TEXT, subject TEXT, marks INTEGER)''')
        cursor.execute('DELETE FROM grades WHERE roll_number = ?', (self._roll_number,))
        for subject, marks in self._grades.items():
            cursor.execute('INSERT INTO grades VALUES (?, ?, ?)', 
                         (self._roll_number, subject, marks))
            
        cursor.execute('''CREATE TABLE IF NOT EXISTS attendance 
                        (roll_number TEXT, date TEXT, status TEXT)''')
        cursor.execute('DELETE FROM attendance WHERE roll_number = ?', (self._roll_number,))
        for date, status in self._attendance:
            cursor.execute('INSERT INTO attendance VALUES (?, ?, ?)', 
                         (self._roll_number, date, status))
        
        conn.commit()
        conn.close()
    
    def load_from_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM students WHERE roll_number = ?', (self._roll_number,))
        result = cursor.fetchone()
        if result:
            self._name = result[0]
        cursor.execute('SELECT subject, marks FROM grades WHERE roll_number = ?', (self._roll_number,))
        self._grades = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute('SELECT date, status FROM attendance WHERE roll_number = ?', (self._roll_number,))
        self._attendance = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()

# Faculty Class implementing Encapsulation
class Faculty(DatabaseHandler):
    def __init__(self, name, user_id, course):
        if not re.match(r'^[A-Za-z]+$', name):
            raise ValueError("Name can only contain alphabets")
        if not re.match(r'^[A-Za-z0-9]{4,}$', user_id):
            raise ValueError("User ID must be alphanumeric and at least 4 characters long")
        if not course.strip():
            raise ValueError("Course name cannot be empty")
        self._name = name
        self._user_id = user_id
        self._course = course
        self._email = f"{name.lower()}.{user_id.lower()}@university.in"
    
    @property
    def name(self):
        return self._name
    
    @property
    def user_id(self):
        return self._user_id
    
    @property
    def course(self):
        return self._course
    
    @property
    def email(self):
        return self._email
    
    def save_to_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS faculty 
                        (user_id TEXT PRIMARY KEY, name TEXT, course TEXT, email TEXT)''')
        cursor.execute('INSERT OR REPLACE INTO faculty VALUES (?, ?, ?, ?)', 
                      (self._user_id, self._name, self._course, self._email))
        conn.commit()
        conn.close()
    
    def load_from_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, course, email FROM faculty WHERE user_id = ?', (self._user_id,))
        result = cursor.fetchone()
        if result:
            self._name, self._course, self._email = result
        conn.close()

# Task Class implementing Inheritance
class Task(DatabaseHandler):
    def __init__(self, title, deadline, priority='low', category='work'):
        self.title = title
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', deadline):
            raise ValueError("Deadline must be in YYYY-MM-DD format")
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
            current_date = datetime.now().date()
            if deadline_date < current_date:
                raise ValueError("Deadline cannot be in the past")
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Invalid date format. Use YYYY-MM-DD with a valid date")
            raise
        self.deadline = deadline
        self.priority = priority
        self.category = category
        self.completed = False
        self.subtasks = []
        self.assigned_to = None
        
    def add_subtask(self, subtask_title):
        self.subtasks.append(SubTask(subtask_title))
        
    def assign_to(self, user):
        self.assigned_to = user
        
    def mark_complete(self):
        self.completed = True
        
    def save_to_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
                        (title TEXT, deadline TEXT, priority TEXT, 
                        category TEXT, completed INTEGER, assigned_to TEXT)''')
        cursor.execute('INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?)', 
                      (self.title, self.deadline, self.priority, 
                       self.category, int(self.completed), self.assigned_to))
        print(f"DEBUG: Saved task {self.title} with assigned_to={self.assigned_to}")
        cursor.execute('''CREATE TABLE IF NOT EXISTS subtasks 
                        (task_title TEXT, subtask_title TEXT)''')
        cursor.execute('DELETE FROM subtasks WHERE task_title = ?', (self.title,))
        for subtask in self.subtasks:
            cursor.execute('INSERT OR REPLACE INTO subtasks VALUES (?, ?)', 
                         (self.title, subtask.title))
        conn.commit()
        conn.close()
    
    def load_from_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('SELECT title, deadline, priority, category, completed, assigned_to FROM tasks WHERE title = ?', (self.title,))
        result = cursor.fetchone()
        if result:
            print(f"DEBUG: Loaded task {self.title} raw row={result}")
            self.deadline = result[1]
            self.priority = result[2]
            self.category = result[3]
            self.completed = bool(result[4])
            self.assigned_to = result[5]
            print(f"DEBUG: Loaded task {self.title} with assigned_to={self.assigned_to}")
        else:
            print(f"DEBUG: No task found in database for title {self.title}")
        cursor.execute('SELECT subtask_title FROM subtasks WHERE task_title = ?', (self.title,))
        self.subtasks = [SubTask(row[0]) for row in cursor.fetchall()]
        conn.close()

# SubTask Class inheriting from Task
class SubTask(Task):
    def __init__(self, title):
        super().__init__(title, None)
        
    def save_to_db(self):
        pass  # Handled by parent task
    
    def load_from_db(self):
        pass  # Handled by parent task

# Report Generator implementing Polymorphism
class ReportGenerator:
    @staticmethod
    def generate_student_report(student, format_type):
        print(f"Generating report for student: {student.name}, format: {format_type}")
        if format_type == 'pdf':
            return ReportGenerator._generate_pdf(student)
        elif format_type == 'csv':
            return ReportGenerator._generate_csv(student)
        else:
            print(f"Invalid format: {format_type}")
            return None
    
    @staticmethod
    def _generate_pdf(student):
        filename = os.path.join(r"C:\Users\PC\Downloads\StudentTaskManager", f"student_report_{student._roll_number}.pdf")
        print(f"Attempting to generate PDF: {filename}")
        try:
            c = canvas.Canvas(filename, pagesize=letter)
            c.drawString(100, 750, f"Student Report: {student.name}")
            c.drawString(100, 730, f"Roll Number: {student._roll_number}")
            c.drawString(100, 710, "Grades:")
            y = 690
            for subject, marks in student._grades.items():
                c.drawString(120, y, f"{subject}: {marks}")
                y -= 20
            c.drawString(100, y-20, f"Average Grade: {student.calculate_average_grade():.2f}")
            c.drawString(100, y-40, f"Attendance: {student.get_attendance_percentage():.2f}%")
            c.save()
            print(f"PDF generated successfully: {filename}")
            return filename
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
    
    @staticmethod
    def _generate_csv(student):
        filename = os.path.join(r"C:\Users\PC\Downloads\StudentTaskManager", f"student_report_{student._roll_number}.csv")
        print(f"Attempting to generate CSV: {filename}")
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Name', 'Roll Number', 'Subject', 'Marks', 'Attendance %'])
                for subject, marks in student._grades.items():
                    writer.writerow([student.name, student._roll_number, subject, 
                                   marks, student.get_attendance_percentage()])
            print(f"CSV generated successfully: {filename}")
            return filename
        except Exception as e:
            print(f"Error generating CSV: {e}")
            return None
    
    @staticmethod
    def generate_all_students_report(students, format_type):
        print(f"Generating report for all students, format: {format_type}")
        if not students:
            print("No students found in the database.")
            return None
        if format_type == 'pdf':
            return ReportGenerator._generate_all_students_pdf(students)
        elif format_type == 'csv':
            return ReportGenerator._generate_all_students_csv(students)
        else:
            print(f"Invalid format: {format_type}")
            return None
    
    @staticmethod
    def _generate_all_students_pdf(students):
        filename = os.path.join(r"C:\Users\PC\Downloads\StudentTaskManager", "all_students_report.pdf")
        print(f"Attempting to generate PDF: {filename}")
        try:
            c = canvas.Canvas(filename, pagesize=letter)
            y = 750
            c.drawString(100, y, "All Students Report")
            y -= 30
            for student in students.values():
                if y < 100:
                    c.showPage()
                    y = 750
                c.drawString(100, y, f"Student: {student.name}")
                c.drawString(100, y-20, f"Roll Number: {student._roll_number}")
                c.drawString(100, y-40, "Grades:")
                y -= 60
                for subject, marks in student._grades.items():
                    c.drawString(120, y, f"{subject}: {marks}")
                    y -= 20
                c.drawString(100, y, f"Average Grade: {student.calculate_average_grade():.2f}")
                c.drawString(100, y-20, f"Attendance: {student.get_attendance_percentage():.2f}%")
                y -= 50
                c.drawString(100, y, "-" * 50)
                y -= 30
            c.save()
            print(f"PDF generated successfully: {filename}")
            return filename
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
    
    @staticmethod
    def _generate_all_students_csv(students):
        filename = os.path.join(r"C:\Users\PC\Downloads\StudentTaskManager", "all_students_report.csv")
        print(f"Attempting to generate CSV: {filename}")
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Name', 'Roll Number', 'Subject', 'Marks', 'Average Grade', 'Attendance %'])
                for student in students.values():
                    for subject, marks in student._grades.items():
                        writer.writerow([
                            student.name, 
                            student._roll_number, 
                            subject, 
                            marks, 
                            student.calculate_average_grade(), 
                            student.get_attendance_percentage()
                        ])
                    if not student._grades:
                        writer.writerow([
                            student.name, 
                            student._roll_number, 
                            '', 
                            '', 
                            student.calculate_average_grade(), 
                            student.get_attendance_percentage()
                        ])
            print(f"CSV generated successfully: {filename}")
            return filename
        except Exception as e:
            print(f"Error generating CSV: {e}")
            return None

# Main Application Class
class SchoolManagementSystem:
    def __init__(self, user_type, authenticated_id=None):
        self.user_type = user_type
        self.authenticated_id = authenticated_id
        self.students = {}
        self.faculty = {}
        self.tasks = {}
        self.load_students_from_db()
        self.load_faculty_from_db()
        self.load_tasks_from_db()
    
    def load_students_from_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                        (roll_number TEXT PRIMARY KEY, name TEXT)''')
        cursor.execute('SELECT roll_number, name FROM students')
        for roll_number, name in cursor.fetchall():
            try:
                student = Student(name, roll_number)
                student.load_from_db()
                self.students[roll_number] = student
            except ValueError as e:
                print(f"Skipping invalid student record (roll_number: {roll_number}, name: {name}): {e}")
        conn.close()
    
    def load_faculty_from_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS faculty 
                        (user_id TEXT PRIMARY KEY, name TEXT, course TEXT, email TEXT)''')
        cursor.execute('SELECT user_id, name, course, email FROM faculty')
        for user_id, name, course, email in cursor.fetchall():
            try:
                faculty = Faculty(name, user_id, course)
                faculty.load_from_db()
                self.faculty[user_id] = faculty
            except ValueError as e:
                print(f"Skipping invalid faculty record (user_id: {user_id}, name: {name}): {e}")
        conn.close()
    
    def load_tasks_from_db(self):
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
                        (title TEXT, deadline TEXT, priority TEXT, 
                        category TEXT, completed INTEGER, assigned_to TEXT)''')
        cursor.execute('SELECT title, deadline, priority, category, completed, assigned_to FROM tasks')
        for title, deadline, priority, category, completed, assigned_to in cursor.fetchall():
            try:
                task = Task(title, deadline, priority, category)
                task.completed = bool(completed)
                task.assigned_to = assigned_to
                task.load_from_db()
                self.tasks[title] = task
            except ValueError as e:
                print(f"Skipping invalid task {title}: {e}")
        conn.close()
        
    def add_student(self, name, roll_number):
        if self.user_type != 'admin':
            print("Error: Only admins can add students.")
            return
        for existing_roll in self.students:
            if existing_roll.upper() == roll_number.upper():
                print("Error: Student with this roll number already exists.")
                return
        try:
            student = Student(name, roll_number)
            self.students[student.roll_number] = student
            student.save_to_db()
            self.set_student_password(student.roll_number, "student@123")
            print(f"Student {name} added successfully with roll number {student.roll_number} and default password 'student@123'.")
        except ValueError as e:
            print(f"Error: {e}. Student not added.")
    
    def add_faculty(self, name, user_id, course):
        if self.user_type != 'admin':
            print("Error: Only admins can add faculty.")
            return
        for existing_id in self.faculty:
            if existing_id.lower() == user_id.lower():
                print("Error: Faculty with this user ID already exists.")
                return
        try:
            faculty = Faculty(name, user_id, course)
            for existing_faculty in self.faculty.values():
                if existing_faculty.email.lower() == faculty.email.lower():
                    print(f"Error: Email {faculty.email} already exists for another faculty.")
                    return
            self.faculty[user_id] = faculty
            faculty.save_to_db()
            self.set_faculty_password(user_id, "teacher@123")
            print(f"Faculty {name} added successfully with user ID {user_id}, course {course}, email {faculty.email}, and default password 'teacher@123'.")
        except ValueError as e:
            print(f"Error: {e}. Faculty not added.")
        
    def set_student_password(self, roll_number, password="student@123"):
        if self.user_type != 'admin':
            print("Error: Only admins can set passwords.")
            return
        if roll_number not in self.students:
            print(f"Error: Student with roll_number {roll_number} not found.")
            return
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        # Create table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                        (roll_number TEXT PRIMARY KEY, password TEXT, user_type TEXT)''')
        # Check if user_type column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'user_type' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN user_type TEXT')
            # Update existing records to have user_type='student'
            cursor.execute('UPDATE users SET user_type = ? WHERE user_type IS NULL', ('student',))
        cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)', 
                      (roll_number, hashed_password, 'student'))
        conn.commit()
        conn.close()
        print(f"Password set for student {roll_number}.")
    
    def set_faculty_password(self, user_id, password="teacher@123"):
        if self.user_type != 'admin':
            print("Error: Only admins can set passwords.")
            return
        if user_id not in self.faculty:
            print(f"Error: Faculty with user ID {user_id} not found.")
            return
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        email = self.faculty[user_id].email
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        # Create table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                        (roll_number TEXT PRIMARY KEY, password TEXT, user_type TEXT)''')
        # Check if user_type column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'user_type' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN user_type TEXT')
            # Update existing records to have user_type='student'
            cursor.execute('UPDATE users SET user_type = ? WHERE user_type IS NULL', ('student',))
        cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)', 
                      (email, hashed_password, 'faculty'))
        conn.commit()
        conn.close()
        print(f"Password set for faculty {user_id} with email {email}.")
        
    def verify_student_login(self, roll_number, password):
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return False
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE roll_number = ? AND user_type = ?', 
                      (roll_number, 'student'))
        result = cursor.fetchone()
        conn.close()
        if result:
            stored_hash = result[0]
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            return stored_hash == input_hash
        return False
    
    def verify_faculty_login(self, email, password):
        # Basic email validation
        if not re.match(r'^[a-z]+\.[a-z0-9]+@university\.in$', email.lower()):
            print("Error: Invalid email format. Must be name.userid@university.in")
            return False
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        # Check if email exists in faculty table
        cursor.execute('SELECT user_id FROM faculty WHERE email = ?', (email.lower(),))
        if not cursor.fetchone():
            print("Error: Faculty with this email not found.")
            conn.close()
            return False
        # Verify credentials in users table
        cursor.execute('SELECT password FROM users WHERE roll_number = ? AND user_type = ?', 
                      (email.lower(), 'faculty'))
        result = cursor.fetchone()
        conn.close()
        if result:
            stored_hash = result[0]
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            return stored_hash == input_hash
        print("Error: Invalid email or password.")
        return False
    
    def add_grade(self, roll_number, subject, marks):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can add grades.")
            return
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return
        student = self.search_student(roll_number)
        if student:
            try:
                marks = float(marks)
                rounded_marks = round(marks)
                if not 0 <= rounded_marks <= 100:
                    print("Error: Marks must be between 0 and 100.")
                    return
                student.add_grade(subject, rounded_marks)
                student.save_to_db()
                print(f"Grade added for {student.name} in {subject}: {rounded_marks}")
            except ValueError:
                print("Error: Marks must be a valid number.")
        else:
            print(f"Student with roll_number {roll_number} not found.")
    
    def mark_attendance(self, roll_number, date, status):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can mark attendance.")
            return
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return
        student = self.search_student(roll_number)
        if student:
            if status not in ['Present', 'Absent']:
                print("Error: Status must be 'Present' or 'Absent'.")
                return
            student.mark_attendance(date, status)
            student.save_to_db()
            print(f"Attendance marked for {student.name} on {date}.")
        else:
            print(f"Student with roll_number {roll_number} not found.")
    
    def add_task(self, title, deadline, priority, category):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can add tasks.")
            return
        try:
            task = Task(title, deadline, priority, category)
            self.tasks[title] = task
            task.save_to_db()
            print(f"Task {title} added successfully.")
        except ValueError as e:
            print(f"Error: {e}. Task not added.")
        
    def add_subtask(self, task_title, subtask_title):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can add subtasks.")
            return
        if task_title in self.tasks:
            self.tasks[task_title].add_subtask(subtask_title)
            self.tasks[task_title].save_to_db()
            print(f"Subtask {subtask_title} added to {task_title}.")
        else:
            print(f"Task {task_title} not found.")
            
    def assign_task(self, task_title, user):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can assign tasks.")
            return
        if not re.match(r'^[A-Z0-9]{12}$', user):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return
        if task_title not in self.tasks:
            print(f"Task {task_title} not found.")
            return
        if user not in self.students:
            print(f"Error: Student with roll number {user} not found.")
            return
        task = self.tasks[task_title]
        task.assign_to(user)
        task.save_to_db()
        task.load_from_db()
        self.tasks[task_title] = task
        print(f"DEBUG: Assigned task {task_title} to {user}, in-memory assigned_to={task.assigned_to}")
        print(f"Task {task_title} assigned to {user}.")
    
    def generate_report(self, roll_number, format_type):
        if self.user_type == 'student' and roll_number != self.authenticated_id:
            print("Error: Students can only generate reports for themselves.")
            return
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return
        student = self.search_student(roll_number)
        if student:
            filename = ReportGenerator.generate_student_report(student, format_type)
            if filename:
                print(f"Report generated: {filename}")
            else:
                print("Failed to generate report. Check the format or try again.")
        else:
            print(f"Student with roll_number {roll_number} not found.")
    
    def generate_all_students_report(self, format_type):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can generate all students report.")
            return
        filename = ReportGenerator.generate_all_students_report(self.students, format_type)
        if filename:
            print(f"All students report generated: {filename}")
        else:
            print("Failed to generate all students report. Check the format or try again.")
    
    def view_student_details(self, roll_number):
        if self.user_type == 'student' and roll_number != self.authenticated_id:
            print("Error: Students can only view their own details.")
            return
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return
        student = self.search_student(roll_number)
        if student:
            student.load_from_db()
            print(f"\nStudent Details for {student.name} ({roll_number}):")
            print(f"Name: {student.name}")
            print(f"Roll Number: {student._roll_number}")
            print(f"Average Grade: {student.calculate_average_grade():.2f}")
            print(f"Attendance: {student.get_attendance_percentage():.2f}%")
            print("Grades:")
            for subject, marks in student._grades.items():
                print(f"  {subject}: {marks}")
            print("Attendance Records:")
            for date, status in student._attendance:
                print(f"  {date}: {status}")
            if self.user_type != 'student':
                print("Tasks Assigned:")
                for task in self.tasks.values():
                    if task.assigned_to == roll_number:
                        print(f"  {task.title} (Deadline: {task.deadline}, Priority: {task.priority}, Category: {task.category})")
            else:
                print(f"Assigned Tasks:")
                assigned_tasks = [task for task in self.tasks.values() if task.assigned_to == roll_number]
                if not assigned_tasks:
                    print("  No tasks assigned.")
                else:
                    for task in assigned_tasks:
                        print(f"  Title: {task.title}")
                        print(f"    Deadline: {task.deadline}")
                        print(f"    Priority: {task.priority}")
                        print(f"    Category: {task.category}")
                        print(f"    Completed: {'Yes' if task.completed else 'No'}")
                        if task.subtasks:
                            print("    Subtasks:")
                            for subtask in task.subtasks:
                                print(f"      - {subtask.title}")
        else:
            print(f"Student with roll_number {roll_number} not found.")
    
    def search_student(self, roll_number):
        return self.students.get(roll_number)
    
    def filter_tasks_by_category(self, category):
        if self.user_type not in ['admin', 'faculty']:
            print("Error: Only admins and faculty can filter tasks.")
            return []
        tasks = [task for task in self.tasks.values() if task.category.lower() == category.lower()]
        return tasks
    
    def edit_student_details(self, roll_number):
        if self.user_type != 'admin':
            print("Error: Only admins can edit student details.")
            return
        if not re.match(r'^[A-Z0-9]{12}$', roll_number):
            print("Error: Roll number must contain only uppercase letters and digits, exactly 12 characters.")
            return
        student = self.search_student(roll_number)
        if not student:
            print(f"Error: Student with roll_number {roll_number} not found.")
            return
        while True:
            print(f"\nEditing Student: {student.name} ({roll_number})")
            print("1. Edit Name")
            print("2. Edit Roll Number")
            print("3. Edit Password")
            print("4. Edit Grades")
            print("5. Edit Attendance")
            print("6. Done")
            choice = input("Enter choice (1-6): ")
            if choice == '1':
                try:
                    new_name = input("Enter new name: ")
                    student.name = new_name
                    student.save_to_db()
                    print(f"Name updated to {new_name}.")
                except ValueError as e:
                    print(f"Error: {e}")
            elif choice == '2':
                try:
                    new_roll = input("Enter new roll number: ")
                    for existing_roll in self.students:
                        if existing_roll.upper() == new_roll.upper() and existing_roll != roll_number:
                            print("Error: Roll number already exists.")
                            break
                    else:
                        conn = sqlite3.connect('school.db')
                        cursor = conn.cursor()
                        cursor.execute('UPDATE students SET roll_number = ? WHERE roll_number = ?', 
                                     (new_roll, roll_number))
                        cursor.execute('UPDATE grades SET roll_number = ? WHERE roll_number = ?', 
                                     (new_roll, roll_number))
                        cursor.execute('UPDATE attendance SET roll_number = ? WHERE roll_number = ?', 
                                     (new_roll, roll_number))
                        cursor.execute('UPDATE users SET roll_number = ? WHERE roll_number = ?', 
                                     (new_roll, roll_number))
                        cursor.execute('UPDATE tasks SET assigned_to = ? WHERE assigned_to = ?', 
                                     (new_roll, roll_number))
                        conn.commit()
                        conn.close()
                        student.roll_number = new_roll
                        self.students[new_roll] = student
                        del self.students[roll_number]
                        for task in self.tasks.values():
                            if task.assigned_to == roll_number:
                                task.assigned_to = new_roll
                                task.save_to_db()
                        roll_number = new_roll
                        print(f"Roll number updated to {new_roll}.")
                except ValueError as e:
                    print(f"Error: {e}")
            elif choice == '3':
                new_password = input("Enter new password: ")
                self.set_student_password(roll_number, new_password)
            elif choice == '4':
                print("Grades:")
                for subject, marks in student._grades.items():
                    print(f"  {subject}: {marks}")
                print("1. Add Grade")
                print("2. Modify Grade")
                print("3. Delete Grade")
                print("4. Back")
                grade_choice = input("Enter choice (1-4): ")
                if grade_choice == '1':
                    subject = input("Enter subject: ")
                    marks = input("Enter marks (0 to 100): ")
                    try:
                        marks = float(marks)
                        rounded_marks = round(marks)
                        if not 0 <= rounded_marks <= 100:
                            print("Error: Marks must be between 0 and 100.")
                            continue
                        student.add_grade(subject, rounded_marks)
                        student.save_to_db()
                        print(f"Grade added for {subject}: {rounded_marks}")
                    except ValueError:
                        print("Error: Marks must be a valid number.")
                elif grade_choice == '2':
                    subject = input("Enter subject to modify: ")
                    if subject in student._grades:
                        marks = input("Enter marks (0 to 100): ")
                        try:
                            marks = float(marks)
                            rounded_marks = round(marks)
                            if not 0 <= rounded_marks <= 100:
                                print("Error: Marks must be between 0 and 100.")
                                continue
                            student.add_grade(subject, rounded_marks)
                            student.save_to_db()
                            print(f"Grade updated for {subject}: {rounded_marks}")
                        except ValueError:
                            print("Error: Marks must be a valid number.")
                    else:
                        print(f"Subject {subject} not found.")
                elif grade_choice == '3':
                    subject = input("Enter subject to delete: ")
                    if subject in student._grades:
                        student.remove_grade(subject)
                        student.save_to_db()
                        print(f"Grade for {subject} deleted.")
                    else:
                        print(f"Subject {subject} not found.")
            elif choice == '5':
                print("Attendance Records:")
                for date, status in student._attendance:
                    print(f"  {date}: {status}")
                print("1. Add Attendance")
                print("2. Modify Attendance")
                print("3. Delete Attendance")
                print("4. Back")
                att_choice = input("Enter choice (1-4): ")
                if att_choice == '1':
                    date = input("Enter date (YYYY-MM-DD): ")
                    status = input("Enter status (Present/Absent): ")
                    if status not in ['Present', 'Absent']:
                        print("Error: Status must be 'Present' or 'Absent'.")
                        continue
                    student.mark_attendance(date, status)
                    student.save_to_db()
                    print(f"Attendance added for {date}.")
                elif att_choice == '2':
                    date = input("Enter date to modify (YYYY-MM-DD): ")
                    if any(d == date for d, _ in student._attendance):
                        status = input("Enter new status (Present/Absent): ")
                        if status not in ['Present', 'Absent']:
                            print("Error: Status must be 'Present' or 'Absent'.")
                            continue
                        student.remove_attendance(date)
                        student.mark_attendance(date, status)
                        student.save_to_db()
                        print(f"Attendance updated for {date}.")
                    else:
                        print(f"No attendance record for {date}.")
                elif att_choice == '3':
                    date = input("Enter date to delete (YYYY-MM-DD): ")
                    if any(d == date for d, _ in student._attendance):
                        student.remove_attendance(date)
                        student.save_to_db()
                        print(f"Attendance record for {date} deleted.")
                    else:
                        print(f"No attendance record for {date}.")
            elif choice == '6':
                break
            else:
                print("Invalid choice.")

# Command-line Interface
def main():
    print("Welcome to the School Management System")
    print("Please select your user role:")
    print("1. Administrator")
    print("2. Faculty Member")
    print("3. Student")
    user_choice = input("Enter choice (1-3): ")
    
    sms = None
    if user_choice == '1':
        user_id = input("Enter Administrator ID: ")
        password = input("Enter Password: ")
        if user_id != "admin" or password != "admin@123":
            print("Error: Invalid administrator credentials.")
            return
        user_type = 'admin'
        sms = SchoolManagementSystem(user_type)
    elif user_choice == '2':
        email = input("Enter Faculty Email (name.userid@university.in): ")
        password = input("Enter Password: ")
        sms = SchoolManagementSystem('faculty', email)
        if not sms.verify_faculty_login(email, password):
            return
        user_type = 'faculty'
    elif user_choice == '3':
        user_type = 'student'
        roll_number = input("Enter Roll Number: ")
        # Check if roll number exists in students table
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute('SELECT roll_number FROM students WHERE roll_number = ?', (roll_number,))
        if not cursor.fetchone():
            print(f"Error: Student with roll number {roll_number} is not registered.")
            conn.close()
            return
        conn.close()
        password = input("Enter Password: ")
        sms = SchoolManagementSystem(user_type, roll_number)
        if not sms.verify_student_login(roll_number, password):
            print("Error: Invalid roll number or password.")
            return
    else:
        print("Invalid user role selected.")
        return
    
    while True:
        if user_type == 'admin':
            print("\nAdministrator Menu:")
            print("1. Student Menu")
            print("2. Register New Faculty")
            print("3. Generate report")
            print("4. Task")
            print("5. Log Out")
            choice = input("Enter top-level choice (1-5): ")
            
            if choice == '1':
                print("\nStudent Menu:")
                print("1.1. Register New Student")
                print("1.2. Set Student Password")
                print("1.3. Record Student Grade")
                print("1.4. Mark Student Attendance")
                print("1.5. Edit Student Information")
                print("1.6. View Student Details")
                sub_choice = input("Enter Student Menu choice (1.1-1.6): ")
                if sub_choice == '1.1':
                    name = input("Enter student name: ")
                    roll_number = input("Enter roll number: ")
                    sms.add_student(name, roll_number)
                elif sub_choice == '1.2':
                    roll_number = input("Enter roll number: ")
                    password = input("Enter new password: ")
                    sms.set_student_password(roll_number, password)
                elif sub_choice == '1.3':
                    roll_number = input("Enter roll number: ")
                    subject = input("Enter subject: ")
                    marks = input("Enter marks (0 to 100): ")
                    sms.add_grade(roll_number, subject, marks)
                elif sub_choice == '1.4':
                    roll_number = input("Enter roll number: ")
                    date = input("Enter date (YYYY-MM-DD): ")
                    status = input("Enter status (Present/Absent): ")
                    sms.mark_attendance(roll_number, date, status)
                elif sub_choice == '1.5':
                    roll_number = input("Enter roll number: ")
                    sms.edit_student_details(roll_number)
                elif sub_choice == '1.6':
                    roll_number = input("Enter roll number: ")
                    sms.view_student_details(roll_number)
                else:
                    print("Invalid choice. Please enter a valid option (1.1-1.6).")
            elif choice == '2':
                name = input("Enter faculty name: ")
                user_id = input("Enter user ID: ")
                course = input("Enter course name: ")
                sms.add_faculty(name, user_id, course)
            elif choice == '3':
                print("\nGenerate report:")
                print("3.1. Generate Student Report")
                print("3.2. Generate All Students Report")
                sub_choice = input("Enter Generate report choice (3.1-3.2): ")
                if sub_choice == '3.1':
                    roll_number = input("Enter roll number: ")
                    format_type = input("Enter format (pdf/csv): ").lower()
                    sms.generate_report(roll_number, format_type)
                elif sub_choice == '3.2':
                    format_type = input("Enter format (pdf/csv): ").lower()
                    sms.generate_all_students_report(format_type)
                else:
                    print("Invalid choice. Please enter a valid option (3.1-3.2).")
            elif choice == '4':
                print("\nTask Menu:")
                print("4.1. Create New Task")
                print("4.2. Add Subtask to Task")
                print("4.3. Assign Task to Student")
                print("4.4. Filter Tasks by Category")
                sub_choice = input("Enter Task Menu choice (4.1-4.4): ")
                if sub_choice == '4.1':
                    title = input("Enter task title: ")
                    deadline = input("Enter deadline (YYYY-MM-DD): ")
                    priority = input("Enter priority (low/medium/high): ")
                    category = input("Enter category (work/personal/urgent): ")
                    sms.add_task(title, deadline, priority, category)
                elif sub_choice == '4.2':
                    task_title = input("Enter task title: ")
                    subtask_title = input("Enter subtask title: ")
                    sms.add_subtask(task_title, subtask_title)
                elif sub_choice == '4.3':
                    task_title = input("Enter task title: ")
                    user = input("Enter assigned user (roll number): ")
                    sms.assign_task(task_title, user)
                elif sub_choice == '4.4':
                    category = input("Enter category to filter: ")
                    tasks = sms.filter_tasks_by_category(category)
                    for task in tasks:
                        print(f"Task: {task.title}, Deadline: {task.deadline}, Priority: {task.priority}")
                else:
                    print("Invalid choice. Please enter a valid option (4.1-4.4).")
            elif choice == '5':
                print("Logging out. Thank you for using the School Management System.")
                break
            else:
                print("Invalid choice. Please enter a valid option (1-5).")
        
        elif user_type == 'faculty':
            print("\nFaculty Menu:")
            print("1. Record Student Grade")
            print("2. Mark Student Attendance")
            print("3. Generate report")
            print("4. Task")
            print("5. View Student Details")
            print("6. Log Out")
            choice = input("Enter top-level choice (1-6): ")
            
            if choice == '1':
                roll_number = input("Enter roll number: ")
                subject = input("Enter subject: ")
                marks = input("Enter marks (0 to 100): ")
                sms.add_grade(roll_number, subject, marks)
            elif choice == '2':
                roll_number = input("Enter roll number: ")
                date = input("Enter date (YYYY-MM-DD): ")
                status = input("Enter status (Present/Absent): ")
                sms.mark_attendance(roll_number, date, status)
            elif choice == '3':
                print("\nGenerate report:")
                print("3.1. Generate individual Student Report")
                print("3.2. Generate All Students Report")
                sub_choice = input("Enter Generate report choice (3.1-3.2): ")
                if sub_choice == '3.1':
                    roll_number = input("Enter roll number: ")
                    format_type = input("Enter format (pdf/csv): ").lower()
                    sms.generate_report(roll_number, format_type)
                elif sub_choice == '3.2':
                    format_type = input("Enter format (pdf/csv): ").lower()
                    sms.generate_all_students_report(format_type)
                else:
                    print("Invalid choice. Please enter a valid option (3.1-3.2).")
            elif choice == '4':
                print("\nTask Menu:")
                print("4.1. Create New Task")
                print("4.2. Add Subtask to Task")
                print("4.3. Assign Task to Student")
                print("4.4. Filter Tasks by Category")
                sub_choice = input("Enter Task Menu choice (4.1-4.4): ")
                if sub_choice == '4.1':
                    title = input("Enter task title: ")
                    deadline = input("Enter deadline (YYYY-MM-DD): ")
                    priority = input("Enter priority (low/medium/high): ")
                    category = input("Enter category (work/personal/urgent): ")
                    sms.add_task(title, deadline, priority, category)
                elif sub_choice == '4.2':
                    task_title = input("Enter task title: ")
                    subtask_title = input("Enter subtask title: ")
                    sms.add_subtask(task_title, subtask_title)
                elif sub_choice == '4.3':
                    task_title = input("Enter task title: ")
                    user = input("Enter assigned user (roll number): ")
                    sms.assign_task(task_title, user)
                elif sub_choice == '4.4':
                    category = input("Enter category to filter: ")
                    tasks = sms.filter_tasks_by_category(category)
                    for task in tasks:
                        print(f"Task: {task.title}, Deadline: {task.deadline}, Priority: {task.priority}")
                else:
                    print("Invalid choice. Please enter a valid option (4.1-4.4).")
            elif choice == '5':
                roll_number = input("Enter roll number: ")
                sms.view_student_details(roll_number)
            elif choice == '6':
                print("Logging out. Thank you for using the School Management System.")
                break
            else:
                print("Invalid choice. Please enter a valid option (1-6).")
        
        elif user_type == 'student':
            print("\nStudent Menu:")
            print("1. View Personal Information and Tasks")
            print("2. Generate Academic Report")
            print("3. Submit a Concern")
            print("4. Log Out")
            choice = input("Enter choice (1-4): ")
            if choice == '1':
                sms.view_student_details(sms.authenticated_id)
            elif choice == '2':
                format_type = input("Enter format (pdf/csv): ").lower()
                sms.generate_report(sms.authenticated_id, format_type)
            elif choice == '3':
                print("To submit a concern, please contact yogeetha_support@school.edu.")
            elif choice == '4':
                print("Logging out. Thank you for using the School Management System.")
                break
            else:
                print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()