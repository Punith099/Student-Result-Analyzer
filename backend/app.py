"""
Student Result Analyzer - Flask Backend API
Python + Flask + oracledb (new Oracle driver)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import oracledb
import os
from datetime import datetime
from functools import wraps
import jwt

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
DB_USER = os.environ.get('DB_USER', 'student')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '2006')
DB_DSN = os.environ.get('DB_DSN', 'localhost:1521/XEPDB1')

# =============================================
# Database Connection
# =============================================

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN
        )
        return connection
    except oracledb.Error as error:
        print(f"Database connection error: {error}")
        raise

# =============================================
# Grade Calculation Function
# =============================================

def calculate_grade(marks_obtained, max_marks):
    """Calculate grade based on percentage"""
    percentage = (marks_obtained / max_marks) * 100
    
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B+'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 40:
        return 'D'
    else:
        return 'F'

# =============================================
# Authentication Decorator
# =============================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# =============================================
# AUTHENTICATION ROUTES
# =============================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple authentication (in production, verify against database)
    if username == 'admin' and password == 'admin123':
        token = jwt.encode({
            'username': username,
            'role': 'admin'
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': {'username': username, 'role': 'admin'}
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

# =============================================
# STUDENT ROUTES
# =============================================

@app.route('/api/students', methods=['GET'])
@token_required
def get_students():
    """Get all students with optional filters"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        class_filter = request.args.get('class')
        section_filter = request.args.get('section')
        
        query = "SELECT * FROM STUDENTS WHERE 1=1"
        params = []
        
        if class_filter:
            query += " AND class = :1"
            params.append(class_filter)
        
        if section_filter:
            query += " AND section = :2" if class_filter else " AND section = :1"
            params.append(section_filter)
        
        query += " ORDER BY student_id"
        
        cursor.execute(query, params)
        columns = [col[0].lower() for col in cursor.description]
        students = []
        
        for row in cursor:
            student = dict(zip(columns, row))
            # Convert date to string
            if student.get('dob'):
                student['dob'] = student['dob'].strftime('%Y-%m-%d')
            students.append(student)
        
        cursor.close()
        connection.close()
        
        return jsonify(students), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['GET'])
@token_required
def get_student(student_id):
    """Get a specific student by ID"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM STUDENTS WHERE student_id = :1", [student_id])
        columns = [col[0].lower() for col in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Student not found'}), 404
        
        student = dict(zip(columns, row))
        if student.get('dob'):
            student['dob'] = student['dob'].strftime('%Y-%m-%d')
        
        cursor.close()
        connection.close()
        
        return jsonify(student), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['POST'])
@token_required
def create_student():
    """Create a new student"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO STUDENTS 
            (student_id, first_name, last_name, dob, gender, class, section, email, phone)
            VALUES (student_seq.NEXTVAL, :1, :2, TO_DATE(:3, 'YYYY-MM-DD'), :4, :5, :6, :7, :8)
            RETURNING student_id INTO :9
        """
        
        # Changed from cx_Oracle.NUMBER to oracledb.NUMBER
        student_id_var = cursor.var(oracledb.NUMBER)
        
        cursor.execute(query, [
            data['first_name'],
            data['last_name'],
            data['dob'],
            data['gender'],
            data['class'],
            data.get('section', ''),
            data.get('email', ''),
            data.get('phone', ''),
            student_id_var
        ])
        
        connection.commit()
        new_student_id = student_id_var.getvalue()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'message': 'Student created successfully',
            'student_id': int(new_student_id)
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
@token_required
def update_student(student_id):
    """Update an existing student"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            UPDATE STUDENTS 
            SET first_name = :1, last_name = :2, dob = TO_DATE(:3, 'YYYY-MM-DD'),
                gender = :4, class = :5, section = :6, email = :7, phone = :8
            WHERE student_id = :9
        """
        
        cursor.execute(query, [
            data['first_name'],
            data['last_name'],
            data['dob'],
            data['gender'],
            data['class'],
            data.get('section', ''),
            data.get('email', ''),
            data.get('phone', ''),
            student_id
        ])
        
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Student not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Student updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@token_required
def delete_student(student_id):
    """Delete a student"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM STUDENTS WHERE student_id = :1", [student_id])
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Student not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Student deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# TEACHER ROUTES
# =============================================

@app.route('/api/teachers', methods=['GET'])
@token_required
def get_teachers():
    """Get all teachers with their subject information"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT t.*, s.subject_name
            FROM TEACHERS t
            LEFT JOIN SUBJECTS s ON t.subject_id = s.subject_id
            ORDER BY t.name
        """
        
        cursor.execute(query)
        columns = [col[0].lower() for col in cursor.description]
        teachers = [dict(zip(columns, row)) for row in cursor]
        
        cursor.close()
        connection.close()
        
        return jsonify(teachers), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<int:teacher_id>', methods=['GET'])
@token_required
def get_teacher(teacher_id):
    """Get a specific teacher by ID"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT t.*, s.subject_name
            FROM TEACHERS t
            LEFT JOIN SUBJECTS s ON t.subject_id = s.subject_id
            WHERE t.teacher_id = :1
        """
        
        cursor.execute(query, [teacher_id])
        columns = [col[0].lower() for col in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Teacher not found'}), 404
        
        teacher = dict(zip(columns, row))
        
        cursor.close()
        connection.close()
        
        return jsonify(teacher), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers', methods=['POST'])
@token_required
def create_teacher():
    """Create a new teacher"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO TEACHERS (teacher_id, name, subject_id, email, phone)
            VALUES (teacher_seq.NEXTVAL, :1, :2, :3, :4)
            RETURNING teacher_id INTO :5
        """
        
        teacher_id_var = cursor.var(oracledb.NUMBER)
        
        # Handle optional subject_id
        subject_id = data.get('subject_id')
        if subject_id == '' or subject_id is None:
            subject_id = None
        
        cursor.execute(query, [
            data['name'],
            subject_id,
            data.get('email', ''),
            data.get('phone', ''),
            teacher_id_var
        ])
        
        connection.commit()
        new_teacher_id = teacher_id_var.getvalue()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'message': 'Teacher created successfully',
            'teacher_id': int(new_teacher_id)
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<int:teacher_id>', methods=['PUT'])
@token_required
def update_teacher(teacher_id):
    """Update an existing teacher"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Handle optional subject_id
        subject_id = data.get('subject_id')
        if subject_id == '' or subject_id is None:
            subject_id = None
        
        query = """
            UPDATE TEACHERS 
            SET name = :1, subject_id = :2, email = :3, phone = :4
            WHERE teacher_id = :5
        """
        
        cursor.execute(query, [
            data['name'],
            subject_id,
            data.get('email', ''),
            data.get('phone', ''),
            teacher_id
        ])
        
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Teacher not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Teacher updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<int:teacher_id>', methods=['DELETE'])
@token_required
def delete_teacher(teacher_id):
    """Delete a teacher"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM TEACHERS WHERE teacher_id = :1", [teacher_id])
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Teacher not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Teacher deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# SUBJECT ROUTES
# =============================================

@app.route('/api/subjects', methods=['GET'])
@token_required
def get_subjects():
    """Get all subjects"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM SUBJECTS ORDER BY subject_name")
        columns = [col[0].lower() for col in cursor.description]
        subjects = [dict(zip(columns, row)) for row in cursor]
        
        cursor.close()
        connection.close()
        
        return jsonify(subjects), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects', methods=['POST'])
@token_required
def create_subject():
    """Create a new subject"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO SUBJECTS (subject_id, subject_name, max_marks)
            VALUES (subject_seq.NEXTVAL, :1, :2)
            RETURNING subject_id INTO :3
        """
        
        subject_id_var = cursor.var(oracledb.NUMBER)
        
        cursor.execute(query, [
            data['subject_name'],
            data['max_marks'],
            subject_id_var
        ])
        
        connection.commit()
        new_subject_id = subject_id_var.getvalue()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'message': 'Subject created successfully',
            'subject_id': int(new_subject_id)
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['PUT'])
@token_required
def update_subject(subject_id):
    """Update a subject"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "UPDATE SUBJECTS SET subject_name = :1, max_marks = :2 WHERE subject_id = :3"
        cursor.execute(query, [data['subject_name'], data['max_marks'], subject_id])
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Subject not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Subject updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
@token_required
def delete_subject(subject_id):
    """Delete a subject"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM SUBJECTS WHERE subject_id = :1", [subject_id])
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Subject not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Subject deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# EXAM ROUTES
# =============================================

@app.route('/api/exams', methods=['GET'])
@token_required
def get_exams():
    """Get all exams"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM EXAMS ORDER BY exam_date DESC")
        columns = [col[0].lower() for col in cursor.description]
        exams = []
        
        for row in cursor:
            exam = dict(zip(columns, row))
            if exam.get('exam_date'):
                exam['exam_date'] = exam['exam_date'].strftime('%Y-%m-%d')
            exams.append(exam)
        
        cursor.close()
        connection.close()
        
        return jsonify(exams), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/exams', methods=['POST'])
@token_required
def create_exam():
    """Create a new exam"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO EXAMS (exam_id, exam_name, exam_date, semester)
            VALUES (exam_seq.NEXTVAL, :1, TO_DATE(:2, 'YYYY-MM-DD'), :3)
            RETURNING exam_id INTO :4
        """
        
        exam_id_var = cursor.var(oracledb.NUMBER)
        
        cursor.execute(query, [
            data['exam_name'],
            data['exam_date'],
            data['semester'],
            exam_id_var
        ])
        
        connection.commit()
        new_exam_id = exam_id_var.getvalue()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'message': 'Exam created successfully',
            'exam_id': int(new_exam_id)
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# RESULT ROUTES
# =============================================

@app.route('/api/results', methods=['GET'])
@token_required
def get_results():
    """Get all results with filters"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        student_id = request.args.get('student_id')
        exam_id = request.args.get('exam_id')
        subject_id = request.args.get('subject_id')
        
        query = """
            SELECT r.*, 
                   s.first_name || ' ' || s.last_name as student_name,
                   sub.subject_name,
                   sub.max_marks,
                   e.exam_name
            FROM RESULTS r
            JOIN STUDENTS s ON r.student_id = s.student_id
            JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
            JOIN EXAMS e ON r.exam_id = e.exam_id
            WHERE 1=1
        """
        params = []
        
        if student_id:
            query += " AND r.student_id = :1"
            params.append(int(student_id))
        
        if exam_id:
            param_num = len(params) + 1
            query += f" AND r.exam_id = :{param_num}"
            params.append(int(exam_id))
        
        if subject_id:
            param_num = len(params) + 1
            query += f" AND r.subject_id = :{param_num}"
            params.append(int(subject_id))
        
        query += " ORDER BY r.result_id"
        
        cursor.execute(query, params)
        columns = [col[0].lower() for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor]
        
        cursor.close()
        connection.close()
        
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['POST'])
@token_required
def create_result():
    """Create a new result with automatic grade calculation"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get max marks for the subject
        cursor.execute("SELECT max_marks FROM SUBJECTS WHERE subject_id = :1", [data['subject_id']])
        max_marks_row = cursor.fetchone()
        
        if not max_marks_row:
            return jsonify({'error': 'Subject not found'}), 404
        
        max_marks = max_marks_row[0]
        grade = calculate_grade(data['marks_obtained'], max_marks)
        
        query = """
            INSERT INTO RESULTS (result_id, student_id, subject_id, exam_id, marks_obtained, grade)
            VALUES (result_seq.NEXTVAL, :1, :2, :3, :4, :5)
            RETURNING result_id INTO :6
        """
        
        result_id_var = cursor.var(oracledb.NUMBER)
        
        cursor.execute(query, [
            data['student_id'],
            data['subject_id'],
            data['exam_id'],
            data['marks_obtained'],
            grade,
            result_id_var
        ])
        
        connection.commit()
        new_result_id = result_id_var.getvalue()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'message': 'Result added successfully',
            'result_id': int(new_result_id),
            'grade': grade
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<int:result_id>', methods=['PUT'])
@token_required
def update_result(result_id):
    """Update result marks and recalculate grade"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get subject_id and max_marks
        cursor.execute("""
            SELECT r.subject_id, s.max_marks 
            FROM RESULTS r 
            JOIN SUBJECTS s ON r.subject_id = s.subject_id 
            WHERE r.result_id = :1
        """, [result_id])
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Result not found'}), 404
        
        max_marks = row[1]
        grade = calculate_grade(data['marks_obtained'], max_marks)
        
        query = "UPDATE RESULTS SET marks_obtained = :1, grade = :2 WHERE result_id = :3"
        cursor.execute(query, [data['marks_obtained'], grade, result_id])
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'message': 'Result updated successfully',
            'grade': grade
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<int:result_id>', methods=['DELETE'])
@token_required
def delete_result(result_id):
    """Delete a result"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM RESULTS WHERE result_id = :1", [result_id])
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Result not found'}), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({'message': 'Result deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# ANALYTICS ROUTES
# =============================================

@app.route('/api/analytics/dashboard', methods=['GET'])
@token_required
def get_dashboard_analytics():
    """Get dashboard statistics"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Total students
        cursor.execute("SELECT COUNT(*) FROM STUDENTS")
        total_students = cursor.fetchone()[0]
        
        # Total subjects
        cursor.execute("SELECT COUNT(*) FROM SUBJECTS")
        total_subjects = cursor.fetchone()[0]
        
        # Total exams
        cursor.execute("SELECT COUNT(*) FROM EXAMS")
        total_exams = cursor.fetchone()[0]
        
        # Average percentage
        cursor.execute("""
            SELECT ROUND(AVG((r.marks_obtained / s.max_marks) * 100), 2)
            FROM RESULTS r
            JOIN SUBJECTS s ON r.subject_id = s.subject_id
        """)
        avg_percentage = cursor.fetchone()[0] or 0
        
        # Pass rate (assuming 40% is passing)
        cursor.execute("""
            SELECT 
                ROUND((SUM(CASE WHEN (r.marks_obtained / s.max_marks) * 100 >= 40 THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2)
            FROM RESULTS r
            JOIN SUBJECTS s ON r.subject_id = s.subject_id
        """)
        pass_rate = cursor.fetchone()[0] or 0
        
        # Grade distribution (with default grades if no results exist)
        cursor.execute("""
            SELECT grade, COUNT(*) as count
            FROM RESULTS
            GROUP BY grade
            ORDER BY grade
        """)
        grade_distribution = [{'grade': row[0], 'count': row[1]} for row in cursor]
        
        # If no results exist, show empty grade distribution
        if not grade_distribution:
            grade_distribution = [
                {'grade': 'A+', 'count': 0},
                {'grade': 'A', 'count': 0},
                {'grade': 'B+', 'count': 0},
                {'grade': 'B', 'count': 0},
                {'grade': 'C', 'count': 0},
                {'grade': 'D', 'count': 0},
                {'grade': 'F', 'count': 0}
            ]
        
        # Subject-wise average (show all subjects, even those without results)
        cursor.execute("""
            SELECT s.subject_name, 
                   CASE 
                       WHEN COUNT(r.result_id) > 0 THEN ROUND(AVG(r.marks_obtained), 2)
                       ELSE 0
                   END as avg_marks,
                   COUNT(r.result_id) as result_count
            FROM SUBJECTS s
            LEFT JOIN RESULTS r ON s.subject_id = r.subject_id
            GROUP BY s.subject_name, s.subject_id
            ORDER BY avg_marks DESC
        """)
        subject_averages = [{'subject': row[0], 'average': float(row[1]), 'has_results': row[2] > 0} for row in cursor]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'total_students': total_students,
            'total_subjects': total_subjects,
            'total_exams': total_exams,
            'average_percentage': float(avg_percentage),
            'pass_rate': float(pass_rate),
            'grade_distribution': grade_distribution,
            'subject_averages': subject_averages
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>/summary', methods=['GET'])
@token_required
def get_student_summary(student_id):
    """Get comprehensive summary for a student"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        exam_id = request.args.get('exam_id')
        
        # Student basic info
        cursor.execute("""
            SELECT first_name || ' ' || last_name as name, class, section
            FROM STUDENTS WHERE student_id = :1
        """, [student_id])
        
        student_row = cursor.fetchone()
        if not student_row:
            return jsonify({'error': 'Student not found'}), 404
        
        student_info = {
            'name': student_row[0],
            'class': student_row[1],
            'section': student_row[2]
        }
        
        # Results for specific exam or all exams
        if exam_id:
            query = """
                SELECT s.subject_name, s.max_marks, r.marks_obtained, r.grade,
                       ROUND((r.marks_obtained / s.max_marks) * 100, 2) as percentage
                FROM RESULTS r
                JOIN SUBJECTS s ON r.subject_id = s.subject_id
                WHERE r.student_id = :1 AND r.exam_id = :2
                ORDER BY s.subject_name
            """
            cursor.execute(query, [student_id, int(exam_id)])
        else:
            query = """
                SELECT e.exam_name, s.subject_name, s.max_marks, r.marks_obtained, r.grade,
                       ROUND((r.marks_obtained / s.max_marks) * 100, 2) as percentage
                FROM RESULTS r
                JOIN SUBJECTS s ON r.subject_id = s.subject_id
                JOIN EXAMS e ON r.exam_id = e.exam_id
                WHERE r.student_id = :1
                ORDER BY e.exam_name, s.subject_name
            """
            cursor.execute(query, [student_id])
        
        columns = [col[0].lower() for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor]
        
        # Calculate totals
        if results:
            total_marks = sum(r['marks_obtained'] for r in results)
            total_max = sum(r['max_marks'] for r in results)
            average_percentage = round((total_marks / total_max) * 100, 2) if total_max > 0 else 0
        else:
            total_marks = 0
            total_max = 0
            average_percentage = 0
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'student': student_info,
            'results': results,
            'total_marks': total_marks,
            'total_max_marks': total_max,
            'average_percentage': average_percentage
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top-performers', methods=['GET'])
@token_required
def get_top_performers():
    """Get top performing students"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        exam_id = request.args.get('exam_id')
        limit = int(request.args.get('limit', 10))
        
        if exam_id:
            query = """
                SELECT s.student_id, s.first_name || ' ' || s.last_name as student_name,
                       SUM(r.marks_obtained) as total_marks,
                       ROUND(AVG((r.marks_obtained / sub.max_marks) * 100), 2) as percentage
                FROM STUDENTS s
                JOIN RESULTS r ON s.student_id = r.student_id
                JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
                WHERE r.exam_id = :1
                GROUP BY s.student_id, s.first_name, s.last_name
                ORDER BY percentage DESC
                FETCH FIRST :2 ROWS ONLY
            """
            cursor.execute(query, [int(exam_id), limit])
        else:
            query = """
                SELECT s.student_id, s.first_name || ' ' || s.last_name as student_name,
                       ROUND(AVG((r.marks_obtained / sub.max_marks) * 100), 2) as avg_percentage
                FROM STUDENTS s
                JOIN RESULTS r ON s.student_id = r.student_id
                JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
                GROUP BY s.student_id, s.first_name, s.last_name
                ORDER BY avg_percentage DESC
                FETCH FIRST :1 ROWS ONLY
            """
            cursor.execute(query, [limit])
        
        columns = [col[0].lower() for col in cursor.description]
        top_performers = [dict(zip(columns, row)) for row in cursor]
        
        cursor.close()
        connection.close()
        
        return jsonify(top_performers), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# HEALTH CHECK
# =============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'message': 'Server is running'}), 200

# =============================================
# RUN APPLICATION
# =============================================
@app.route('/')
def home():
    return jsonify({
        "message": "Student Result Analyzer API",
        "version": "1.0.0",
        "database": "Oracle (oracledb driver)",
        "available_routes": [
            "/api/health",
            "/api/auth/login",
            "/api/students",
            "/api/teachers",
            "/api/subjects",
            "/api/exams",
            "/api/results",
            "/api/analytics/dashboard"
        ]
    })

if __name__ == '__main__':
    print("=" * 60)
    print("✅ Student Result Analyzer - Backend Server")
    print("=" * 60)
    print(f"📊 Database User: {DB_USER}")
    print(f"🌐 Database DSN: {DB_DSN}")
    print(f"🔌 Server: http://localhost:5000")
    print(f"🔑 Login: admin / admin123")
    print("=" * 60)
    try:
        # Test database connection on startup
        test_conn = get_db_connection()
        test_conn.close()
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️  Server will start but database operations will fail.")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)