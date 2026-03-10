-- =============================================
-- Student Result Analyzer System - Oracle SQL Schema
-- =============================================

-- Drop existing tables if they exist (in reverse order of dependencies)
DROP TABLE RESULTS CASCADE CONSTRAINTS;
DROP TABLE TEACHERS CASCADE CONSTRAINTS;
DROP TABLE EXAMS CASCADE CONSTRAINTS;
DROP TABLE SUBJECTS CASCADE CONSTRAINTS;
DROP TABLE STUDENTS CASCADE CONSTRAINTS;

-- Drop sequences if they exist
DROP SEQUENCE student_seq;
DROP SEQUENCE subject_seq;
DROP SEQUENCE exam_seq;
DROP SEQUENCE result_seq;
DROP SEQUENCE teacher_seq;

-- =============================================
-- Create Sequences for Auto-increment IDs
-- =============================================

CREATE SEQUENCE student_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE subject_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE exam_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE result_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE teacher_seq START WITH 1 INCREMENT BY 1;

-- =============================================
-- Table 1: STUDENTS
-- =============================================

CREATE TABLE STUDENTS (
    student_id NUMBER PRIMARY KEY,
    first_name VARCHAR2(50) NOT NULL,
    last_name VARCHAR2(50) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR2(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    class VARCHAR2(20) NOT NULL,
    section VARCHAR2(5),
    email VARCHAR2(100) UNIQUE,
    phone VARCHAR2(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Table 2: SUBJECTS
-- =============================================

CREATE TABLE SUBJECTS (
    subject_id NUMBER PRIMARY KEY,
    subject_name VARCHAR2(100) NOT NULL UNIQUE,
    max_marks NUMBER NOT NULL CHECK (max_marks > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Table 3: EXAMS
-- =============================================

CREATE TABLE EXAMS (
    exam_id NUMBER PRIMARY KEY,
    exam_name VARCHAR2(100) NOT NULL,
    exam_date DATE NOT NULL,
    semester VARCHAR2(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Table 4: TEACHERS
-- =============================================

CREATE TABLE TEACHERS (
    teacher_id NUMBER PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    subject_id NUMBER,
    email VARCHAR2(100) UNIQUE,
    phone VARCHAR2(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES SUBJECTS(subject_id)
);

-- =============================================
-- Table 5: RESULTS
-- =============================================

CREATE TABLE RESULTS (
    result_id NUMBER PRIMARY KEY,
    student_id NUMBER NOT NULL,
    subject_id NUMBER NOT NULL,
    exam_id NUMBER NOT NULL,
    marks_obtained NUMBER NOT NULL,
    grade VARCHAR2(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES STUDENTS(student_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES SUBJECTS(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES EXAMS(exam_id) ON DELETE CASCADE,
    CONSTRAINT marks_check CHECK (marks_obtained >= 0),
    CONSTRAINT unique_result UNIQUE (student_id, subject_id, exam_id)
);

-- =============================================
-- Create Indexes for Performance
-- =============================================

CREATE INDEX idx_results_student ON RESULTS(student_id);
CREATE INDEX idx_results_subject ON RESULTS(subject_id);
CREATE INDEX idx_results_exam ON RESULTS(exam_id);
CREATE INDEX idx_students_class ON STUDENTS(class);
CREATE INDEX idx_teachers_subject ON TEACHERS(subject_id);

-- =============================================
-- Function: Calculate Grade Based on Percentage
-- =============================================

CREATE OR REPLACE FUNCTION calculate_grade(
    p_marks_obtained NUMBER,
    p_max_marks NUMBER
) RETURN VARCHAR2 IS
    v_percentage NUMBER;
BEGIN
    v_percentage := (p_marks_obtained / p_max_marks) * 100;
    
    IF v_percentage >= 90 THEN
        RETURN 'A+';
    ELSIF v_percentage >= 80 THEN
        RETURN 'A';
    ELSIF v_percentage >= 70 THEN
        RETURN 'B+';
    ELSIF v_percentage >= 60 THEN
        RETURN 'B';
    ELSIF v_percentage >= 50 THEN
        RETURN 'C';
    ELSIF v_percentage >= 40 THEN
        RETURN 'D';
    ELSE
        RETURN 'F';
    END IF;
END;
/

-- =============================================
-- Trigger: Auto-calculate Grade on Insert/Update
-- =============================================

CREATE OR REPLACE TRIGGER trg_calculate_grade
BEFORE INSERT OR UPDATE ON RESULTS
FOR EACH ROW
DECLARE
    v_max_marks NUMBER;
BEGIN
    SELECT max_marks INTO v_max_marks
    FROM SUBJECTS
    WHERE subject_id = :NEW.subject_id;
    
    :NEW.grade := calculate_grade(:NEW.marks_obtained, v_max_marks);
END;
/

-- =============================================
-- View: Student Performance Summary
-- =============================================

CREATE OR REPLACE VIEW vw_student_performance AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name AS student_name,
    s.class,
    s.section,
    e.exam_name,
    e.semester,
    COUNT(r.result_id) AS total_subjects,
    SUM(r.marks_obtained) AS total_marks,
    ROUND(AVG(r.marks_obtained), 2) AS average_marks,
    ROUND(AVG((r.marks_obtained / sub.max_marks) * 100), 2) AS average_percentage
FROM STUDENTS s
JOIN RESULTS r ON s.student_id = r.student_id
JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
JOIN EXAMS e ON r.exam_id = e.exam_id
GROUP BY s.student_id, s.first_name, s.last_name, s.class, s.section, e.exam_name, e.semester;

-- =============================================
-- View: Subject-wise Performance
-- =============================================

CREATE OR REPLACE VIEW vw_subject_performance AS
SELECT 
    sub.subject_name,
    e.exam_name,
    COUNT(r.result_id) AS total_students,
    ROUND(AVG(r.marks_obtained), 2) AS avg_marks,
    MAX(r.marks_obtained) AS highest_marks,
    MIN(r.marks_obtained) AS lowest_marks,
    sub.max_marks,
    ROUND(AVG((r.marks_obtained / sub.max_marks) * 100), 2) AS avg_percentage
FROM SUBJECTS sub
JOIN RESULTS r ON sub.subject_id = r.subject_id
JOIN EXAMS e ON r.exam_id = e.exam_id
GROUP BY sub.subject_name, e.exam_name, sub.max_marks;

-- =============================================
-- View: Top Performers
-- =============================================

CREATE OR REPLACE VIEW vw_top_performers AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name AS student_name,
    s.class,
    e.exam_id,
    e.exam_name,
    SUM(r.marks_obtained) AS total_marks,
    ROUND(AVG((r.marks_obtained / sub.max_marks) * 100), 2) AS percentage,
    RANK() OVER (PARTITION BY e.exam_id ORDER BY SUM(r.marks_obtained) DESC) AS rank_position
FROM STUDENTS s
JOIN RESULTS r ON s.student_id = r.student_id
JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
JOIN EXAMS e ON r.exam_id = e.exam_id
GROUP BY s.student_id, s.first_name, s.last_name, s.class, e.exam_id, e.exam_name;

-- =============================================
-- Stored Procedure: Get Student Report Card
-- =============================================

CREATE OR REPLACE PROCEDURE get_student_report(
    p_student_id IN NUMBER,
    p_exam_id IN NUMBER,
    p_cursor OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_cursor FOR
    SELECT 
        s.first_name || ' ' || s.last_name AS student_name,
        s.class,
        s.section,
        sub.subject_name,
        sub.max_marks,
        r.marks_obtained,
        r.grade,
        ROUND((r.marks_obtained / sub.max_marks) * 100, 2) AS percentage
    FROM STUDENTS s
    JOIN RESULTS r ON s.student_id = r.student_id
    JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
    WHERE s.student_id = p_student_id 
    AND r.exam_id = p_exam_id
    ORDER BY sub.subject_name;
END;
/

-- =============================================
-- INSERT SAMPLE DATA
-- =============================================

-- Insert Students
INSERT INTO STUDENTS VALUES (student_seq.NEXTVAL, 'John', 'Doe', TO_DATE('2005-03-15', 'YYYY-MM-DD'), 'Male', '10th', 'A', 'john.doe@school.com', '1234567890', CURRENT_TIMESTAMP);
INSERT INTO STUDENTS VALUES (student_seq.NEXTVAL, 'Jane', 'Smith', TO_DATE('2005-07-22', 'YYYY-MM-DD'), 'Female', '10th', 'A', 'jane.smith@school.com', '1234567891', CURRENT_TIMESTAMP);
INSERT INTO STUDENTS VALUES (student_seq.NEXTVAL, 'Mike', 'Johnson', TO_DATE('2005-01-10', 'YYYY-MM-DD'), 'Male', '10th', 'B', 'mike.j@school.com', '1234567892', CURRENT_TIMESTAMP);
INSERT INTO STUDENTS VALUES (student_seq.NEXTVAL, 'Emily', 'Davis', TO_DATE('2005-09-05', 'YYYY-MM-DD'), 'Female', '10th', 'A', 'emily.d@school.com', '1234567893', CURRENT_TIMESTAMP);
INSERT INTO STUDENTS VALUES (student_seq.NEXTVAL, 'Chris', 'Wilson', TO_DATE('2005-11-30', 'YYYY-MM-DD'), 'Male', '10th', 'B', 'chris.w@school.com', '1234567894', CURRENT_TIMESTAMP);

-- Insert Subjects
INSERT INTO SUBJECTS VALUES (subject_seq.NEXTVAL, 'Mathematics', 100, CURRENT_TIMESTAMP);
INSERT INTO SUBJECTS VALUES (subject_seq.NEXTVAL, 'Physics', 100, CURRENT_TIMESTAMP);
INSERT INTO SUBJECTS VALUES (subject_seq.NEXTVAL, 'Chemistry', 100, CURRENT_TIMESTAMP);
INSERT INTO SUBJECTS VALUES (subject_seq.NEXTVAL, 'English', 100, CURRENT_TIMESTAMP);
INSERT INTO SUBJECTS VALUES (subject_seq.NEXTVAL, 'Computer Science', 100, CURRENT_TIMESTAMP);

-- Insert Exams
INSERT INTO EXAMS VALUES (exam_seq.NEXTVAL, 'Midterm Exam', TO_DATE('2024-09-15', 'YYYY-MM-DD'), 'Fall 2024', CURRENT_TIMESTAMP);
INSERT INTO EXAMS VALUES (exam_seq.NEXTVAL, 'Final Exam', TO_DATE('2024-12-20', 'YYYY-MM-DD'), 'Fall 2024', CURRENT_TIMESTAMP);
INSERT INTO EXAMS VALUES (exam_seq.NEXTVAL, 'Unit Test 1', TO_DATE('2024-08-10', 'YYYY-MM-DD'), 'Fall 2024', CURRENT_TIMESTAMP);

-- Insert Teachers
INSERT INTO TEACHERS VALUES (teacher_seq.NEXTVAL, 'Dr. Robert Brown', 1, 'robert.b@school.com', '9876543210', CURRENT_TIMESTAMP);
INSERT INTO TEACHERS VALUES (teacher_seq.NEXTVAL, 'Prof. Sarah Miller', 2, 'sarah.m@school.com', '9876543211', CURRENT_TIMESTAMP);
INSERT INTO TEACHERS VALUES (teacher_seq.NEXTVAL, 'Dr. David Lee', 3, 'david.l@school.com', '9876543212', CURRENT_TIMESTAMP);

-- Insert Results (Midterm Exam - Student 1)
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 1, 1, 1, 85, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 1, 2, 1, 78, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 1, 3, 1, 82, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 1, 4, 1, 90, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 1, 5, 1, 88, NULL, CURRENT_TIMESTAMP);

-- Insert Results (Midterm Exam - Student 2)
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 2, 1, 1, 92, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 2, 2, 1, 88, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 2, 3, 1, 85, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 2, 4, 1, 94, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 2, 5, 1, 90, NULL, CURRENT_TIMESTAMP);

-- Insert Results (Midterm Exam - Student 3)
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 3, 1, 1, 75, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 3, 2, 1, 70, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 3, 3, 1, 68, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 3, 4, 1, 80, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 3, 5, 1, 72, NULL, CURRENT_TIMESTAMP);

-- Insert Results (Midterm Exam - Student 4)
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 4, 1, 1, 95, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 4, 2, 1, 91, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 4, 3, 1, 89, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 4, 4, 1, 96, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 4, 5, 1, 93, NULL, CURRENT_TIMESTAMP);

-- Insert Results (Midterm Exam - Student 5)
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 5, 1, 1, 65, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 5, 2, 1, 60, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 5, 3, 1, 58, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 5, 4, 1, 70, NULL, CURRENT_TIMESTAMP);
INSERT INTO RESULTS VALUES (result_seq.NEXTVAL, 5, 5, 1, 68, NULL, CURRENT_TIMESTAMP);

COMMIT;

-- =============================================
-- USEFUL QUERIES
-- =============================================

-- Query 1: Get all students with their results
-- SELECT * FROM vw_student_performance;
-- Query 2: Get subject-wise performance
-- SELECT * FROM vw_subject_performance;

-- Query 3: Get top 5 performers
-- SELECT * FROM vw_top_performers WHERE rank_position <= 5;

-- Query 4: Get student report card
-- DECLARE
--     v_cursor SYS_REFCURSOR;
-- BEGIN
--     get_student_report(1, 1, v_cursor);
-- END;
-- Query 5: Calculate class average
-- SELECT class, ROUND(AVG(average_marks), 2) AS class_average
-- FROM vw_student_performance
-- GROUP BY class;

-- Query 6: Grade distribution
-- SELECT grade, COUNT(*) AS count
-- FROM RESULTS
-- GROUP BY grade
-- ORDER BY grade;

-- Query 7: Pass/Fail analysis (assuming 40% is passing)
-- SELECT 
--     CASE WHEN (marks_obtained / sub.max_marks) * 100 >= 40 THEN 'Pass' ELSE 'Fail' END AS status,
--     COUNT(*) AS count
-- FROM RESULTS r
-- JOIN SUBJECTS sub ON r.subject_id = sub.subject_id
-- GROUP BY CASE WHEN (marks_obtained / sub.max_marks) * 100 >= 40 THEN 'Pass' ELSE 'Fail' END;

SELECT 'Schema created successfully!' AS status FROM DUAL;