import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { User, BookOpen, FileText, TrendingUp, Plus, Edit2, Trash2, Search, LogOut, Home, Users, Book, Calendar, Award, X } from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(false);
  
  const [students, setStudents] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [exams, setExams] = useState([]);
  const [results, setResults] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      setIsLoggedIn(true);
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn && token) {
      fetchData();
    }
  }, [isLoggedIn, token, currentPage]);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const apiCall = async (endpoint, method = 'GET', body = null) => {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json();
    
    if (!response.ok) throw new Error(data.error || 'API call failed');
    return data;
  };

  const fetchData = async () => {
    try {
      if (currentPage === 'dashboard') {
        const data = await apiCall('/analytics/dashboard');
        setAnalytics(data);
      } else if (currentPage === 'students') {
        const data = await apiCall('/students');
        setStudents(data);
      } else if (currentPage === 'teachers') {
        const data = await apiCall('/teachers');
        setTeachers(data);
      } else if (currentPage === 'subjects') {
        const data = await apiCall('/subjects');
        setSubjects(data);
      } else if (currentPage === 'exams') {
        const data = await apiCall('/exams');
        setExams(data);
      } else if (currentPage === 'results') {
        const [studentsData, subjectsData, examsData, resultsData] = await Promise.all([
          apiCall('/students'),
          apiCall('/subjects'),
          apiCall('/exams'),
          apiCall('/results')
        ]);
        setStudents(studentsData);
        setSubjects(subjectsData);
        setExams(examsData);
        setResults(resultsData);
      }
    } catch (error) {
      showNotification(error.message, 'error');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: formData.username, password: formData.password })
      });
      const data = await response.json();
      
      if (response.ok) {
        setToken(data.token);
        localStorage.setItem('token', data.token);
        setIsLoggedIn(true);
        showNotification('Login successful!');
      } else {
        showNotification(data.error, 'error');
      }
    } catch (error) {
      showNotification('Login failed', 'error');
    }
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setCurrentPage('dashboard');
  };

  const openModal = (type, item = null) => {
    setModalType(type);
    setEditingItem(item);
    setFormData(item || {});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setModalType('');
    setEditingItem(null);
    setFormData({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      let endpoint = '';
      let method = editingItem ? 'PUT' : 'POST';
      
      if (modalType === 'student') {
        endpoint = editingItem ? `/students/${editingItem.student_id}` : '/students';
      } else if (modalType === 'teacher') {
        endpoint = editingItem ? `/teachers/${editingItem.teacher_id}` : '/teachers';
      } else if (modalType === 'subject') {
        endpoint = editingItem ? `/subjects/${editingItem.subject_id}` : '/subjects';
      } else if (modalType === 'exam') {
        endpoint = editingItem ? `/exams/${editingItem.exam_id}` : '/exams';
      } else if (modalType === 'result') {
        endpoint = editingItem ? `/results/${editingItem.result_id}` : '/results';
      }

      await apiCall(endpoint, method, formData);
      showNotification(`${modalType} ${editingItem ? 'updated' : 'created'} successfully!`);
      closeModal();
      fetchData();
    } catch (error) {
      showNotification(error.message, 'error');
    }
  };

  const handleDelete = async (type, id) => {
    if (!confirm(`Are you sure you want to delete this ${type}?`)) return;
    
    try {
      let endpoint = '';
      if (type === 'student') endpoint = `/students/${id}`;
      else if (type === 'teacher') endpoint = `/teachers/${id}`;
      else if (type === 'subject') endpoint = `/subjects/${id}`;
      else if (type === 'exam') endpoint = `/exams/${id}`;
      else if (type === 'result') endpoint = `/results/${id}`;

      await apiCall(endpoint, 'DELETE');
      showNotification(`${type} deleted successfully!`);
      fetchData();
    } catch (error) {
      showNotification(error.message, 'error');
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <User className="text-white" size={32} />
            </div>
            <h1 className="text-3xl font-bold text-gray-800">Student Result Analyzer</h1>
            <p className="text-gray-600 mt-2">Login to access dashboard</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input
                type="text"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter username"
                value={formData.username || ''}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
                value={formData.password || ''}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Login
            </button>
          </form>
          <p className="text-sm text-gray-500 text-center mt-4">Default: admin / admin123</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
          notification.type === 'error' ? 'bg-red-500' : 'bg-green-500'
        } text-white`}>
          {notification.message}
        </div>
      )}

      <div className="flex">
        <aside className={`w-64 min-h-screen ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
          <div className="p-6">
            <h2 className="text-2xl font-bold text-blue-600">Result Analyzer</h2>
          </div>
          <nav className="mt-6">
            {[
              { id: 'dashboard', icon: Home, label: 'Dashboard' },
              { id: 'students', icon: Users, label: 'Students' },
              { id: 'teachers', icon: User, label: 'Teachers' },
              { id: 'subjects', icon: Book, label: 'Subjects' },
              { id: 'exams', icon: Calendar, label: 'Exams' },
              { id: 'results', icon: Award, label: 'Results' }
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                className={`w-full flex items-center px-6 py-3 ${
                  currentPage === item.id
                    ? 'bg-blue-600 text-white'
                    : darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <item.icon size={20} className="mr-3" />
                {item.label}
              </button>
            ))}
          </nav>
          <div className="absolute bottom-0 w-64 p-6">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              <LogOut size={20} className="mr-2" />
              Logout
            </button>
          </div>
        </aside>

        <main className="flex-1 p-8">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold capitalize">{currentPage}</h1>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-700"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>

          {currentPage === 'dashboard' && analytics && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard icon={Users} title="Total Students" value={analytics.total_students} color="blue" darkMode={darkMode} />
                <StatCard icon={Book} title="Total Subjects" value={analytics.total_subjects} color="green" darkMode={darkMode} />
                <StatCard icon={Calendar} title="Total Exams" value={analytics.total_exams} color="yellow" darkMode={darkMode} />
                <StatCard icon={TrendingUp} title="Pass Rate" value={`${analytics.pass_rate}%`} color="red" darkMode={darkMode} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg p-6`}>
                  <h3 className="text-xl font-bold mb-4">Subject-wise Performance</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={analytics.subject_averages} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="subject" 
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        interval={0}
                        fontSize={12}
                      />
                      <YAxis />
                      <Tooltip 
                        formatter={(value, name, props) => {
                          if (props.payload.has_results) {
                            return [`${value} marks`, 'Average Marks'];
                          } else {
                            return ['No results yet', 'Status'];
                          }
                        }}
                      />
                      <Bar dataKey="average">
                        {analytics.subject_averages.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.has_results ? "#3b82f6" : "#e5e7eb"} 
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-sm text-gray-500 mt-2">
                    Gray bars indicate subjects with no results yet
                  </p>
                </div>

                <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg p-6`}>
                  <h3 className="text-xl font-bold mb-4">Grade Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={analytics.grade_distribution}
                        dataKey="count"
                        nameKey="grade"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label
                      >
                        {analytics.grade_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {currentPage === 'students' && (
            <div>
              <div className="flex justify-between mb-6">
                <input
                  type="text"
                  placeholder="Search students..."
                  className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-300'} w-64`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button
                  onClick={() => openModal('student')}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus size={20} className="mr-2" />
                  Add Student
                </button>
              </div>

              <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg overflow-hidden`}>
                <table className="w-full">
                  <thead className={`${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Class</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {students.filter(s => 
                      `${s.first_name} ${s.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
                    ).map((student) => (
                      <tr key={student.student_id}>
                        <td className="px-6 py-4 whitespace-nowrap">{student.student_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{student.first_name} {student.last_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{student.class} - {student.section}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{student.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => openModal('student', student)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete('student', student.student_id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {currentPage === 'teachers' && (
            <div>
              <div className="flex justify-between mb-6">
                <input
                  type="text"
                  placeholder="Search teachers..."
                  className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-300'} w-64`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button
                  onClick={() => openModal('teacher')}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus size={20} className="mr-2" />
                  Add Teacher
                </button>
              </div>

              <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg overflow-hidden`}>
                <table className="w-full">
                  <thead className={`${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Subject</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Phone</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {teachers.filter(t => 
                      t.name.toLowerCase().includes(searchTerm.toLowerCase())
                    ).map((teacher) => (
                      <tr key={teacher.teacher_id}>
                        <td className="px-6 py-4 whitespace-nowrap">{teacher.teacher_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{teacher.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{teacher.subject_name || 'N/A'}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{teacher.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{teacher.phone}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => openModal('teacher', teacher)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete('teacher', teacher.teacher_id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {currentPage === 'subjects' && (
            <div>
              <div className="flex justify-end mb-6">
                <button
                  onClick={() => openModal('subject')}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus size={20} className="mr-2" />
                  Add Subject
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {subjects.map((subject) => (
                  <div key={subject.subject_id} className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg p-6`}>
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold">{subject.subject_name}</h3>
                        <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mt-1`}>Max Marks: {subject.max_marks}</p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openModal('subject', subject)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete('subject', subject.subject_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentPage === 'exams' && (
            <div>
              <div className="flex justify-end mb-6">
                <button
                  onClick={() => openModal('exam')}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus size={20} className="mr-2" />
                  Add Exam
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {exams.map((exam) => (
                  <div key={exam.exam_id} className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg p-6`}>
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold">{exam.exam_name}</h3>
                        <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mt-1`}>Date: {exam.exam_date}</p>
                        <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Semester: {exam.semester}</p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openModal('exam', exam)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete('exam', exam.exam_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentPage === 'results' && (
            <div>
              <div className="flex justify-end mb-6">
                <button
                  onClick={() => openModal('result')}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus size={20} className="mr-2" />
                  Add Result
                </button>
              </div>

              <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg overflow-hidden`}>
                <table className="w-full">
                  <thead className={`${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Student</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Subject</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Exam</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Marks</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Grade</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {results.map((result) => (
                      <tr key={result.result_id}>
                        <td className="px-6 py-4 whitespace-nowrap">{result.student_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{result.subject_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{result.exam_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{result.marks_obtained}/{result.max_marks}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            result.grade === 'A+' || result.grade === 'A' ? 'bg-green-100 text-green-800' :
                            result.grade === 'B+' || result.grade === 'B' ? 'bg-blue-100 text-blue-800' :
                            result.grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {result.grade}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => openModal('result', result)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete('result', result.result_id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-2xl p-6 w-full max-w-md`}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">{editingItem ? 'Edit' : 'Add'} {modalType}</h2>
              <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {modalType === 'student' && (
                <>
                  <input
                    type="text"
                    placeholder="First Name"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.first_name || ''}
                    onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Last Name"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.last_name || ''}
                    onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                    required
                  />
                  <input
                    type="date"
                    placeholder="Date of Birth"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.dob || ''}
                    onChange={(e) => setFormData({...formData, dob: e.target.value})}
                    required
                  />
                  <select
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.gender || ''}
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                    required
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                  <input
                    type="text"
                    placeholder="Class (e.g., 10th)"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.class || ''}
                    onChange={(e) => setFormData({...formData, class: e.target.value})}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Section"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.section || ''}
                    onChange={(e) => setFormData({...formData, section: e.target.value})}
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.email || ''}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                  <input
                    type="tel"
                    placeholder="Phone"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.phone || ''}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  />
                </>
              )}

              {modalType === 'teacher' && (
                <>
                  <input
                    type="text"
                    placeholder="Teacher Name"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.name || ''}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                  <select
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.subject_id || ''}
                    onChange={(e) => setFormData({...formData, subject_id: e.target.value})}
                  >
                    <option value="">Select Subject (Optional)</option>
                    {subjects.map(s => (
                      <option key={s.subject_id} value={s.subject_id}>
                        {s.subject_name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="email"
                    placeholder="Email"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.email || ''}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                  <input
                    type="tel"
                    placeholder="Phone"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.phone || ''}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  />
                </>
              )}

              {modalType === 'subject' && (
                <>
                  <input
                    type="text"
                    placeholder="Subject Name"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.subject_name || ''}
                    onChange={(e) => setFormData({...formData, subject_name: e.target.value})}
                    required
                  />
                  <input
                    type="number"
                    placeholder="Maximum Marks"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.max_marks || ''}
                    onChange={(e) => setFormData({...formData, max_marks: e.target.value})}
                    required
                  />
                </>
              )}

              {modalType === 'exam' && (
                <>
                  <input
                    type="text"
                    placeholder="Exam Name"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.exam_name || ''}
                    onChange={(e) => setFormData({...formData, exam_name: e.target.value})}
                    required
                  />
                  <input
                    type="date"
                    placeholder="Exam Date"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.exam_date || ''}
                    onChange={(e) => setFormData({...formData, exam_date: e.target.value})}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Semester"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.semester || ''}
                    onChange={(e) => setFormData({...formData, semester: e.target.value})}
                    required
                  />
                </>
              )}

              {modalType === 'result' && (
                <>
                  <select
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.student_id || ''}
                    onChange={(e) => setFormData({...formData, student_id: e.target.value})}
                    required
                    disabled={editingItem}
                  >
                    <option value="">Select Student</option>
                    {students.map(s => (
                      <option key={s.student_id} value={s.student_id}>
                        {s.first_name} {s.last_name} - {s.class}
                      </option>
                    ))}
                  </select>
                  <select
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.subject_id || ''}
                    onChange={(e) => setFormData({...formData, subject_id: e.target.value})}
                    required
                    disabled={editingItem}
                  >
                    <option value="">Select Subject</option>
                    {subjects.map(s => (
                      <option key={s.subject_id} value={s.subject_id}>
                        {s.subject_name}
                      </option>
                    ))}
                  </select>
                  <select
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.exam_id || ''}
                    onChange={(e) => setFormData({...formData, exam_id: e.target.value})}
                    required
                    disabled={editingItem}
                  >
                    <option value="">Select Exam</option>
                    {exams.map(e => (
                      <option key={e.exam_id} value={e.exam_id}>
                        {e.exam_name} - {e.semester}
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    placeholder="Marks Obtained"
                    className={`w-full px-4 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                    value={formData.marks_obtained || ''}
                    onChange={(e) => setFormData({...formData, marks_obtained: e.target.value})}
                    required
                  />
                </>
              )}

              <div className="flex space-x-4 mt-6">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
                >
                  {editingItem ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, title, value, color, darkMode }) {
  const colors = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };

  return (
    <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg p-6`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-1`}>{title}</p>
          <p className="text-3xl font-bold">{value}</p>
        </div>
        <div className={`${colors[color]} w-12 h-12 rounded-full flex items-center justify-center`}>
          <Icon className="text-white" size={24} />
        </div>
      </div>
    </div>
  );
}

export default App;