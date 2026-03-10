# Student Result Analyzer System

A full-stack web application for managing and analyzing student academic performance with Oracle SQL database, Flask/Node.js backend, and React frontend.

## 📋 Features

- **Student Management**: Add, edit, delete, and search students
- **Subject Management**: Manage subjects with customizable max marks
- **Exam Management**: Create and manage different exams and semesters
- **Result Entry**: Dynamic result entry with automatic grade calculation
- **Analytics Dashboard**: Visual charts showing performance metrics
- **Real-time CRUD**: All operations happen through UI forms
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Toggle between light and dark themes

## 🏗️ Architecture

```
student-result-analyzer/
├── database/
│   └── schema.sql              # Oracle SQL schema and sample data
├── backend/
│   ├── app.py                  # Flask backend (Python)
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # React application
│   │   └── index.jsx
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## 🔧 Prerequisites

- **Oracle Database** 19c or later (or Oracle XE)
- **Python** 3.8+ (for Flask backend)
- **Node.js** 16+ and npm (for React frontend)
- **Oracle Instant Client** (for cx_Oracle)

## 📦 Installation

### 1. Database Setup (Oracle SQL)

#### Install Oracle Database

```bash
# For Oracle XE (Express Edition) on Linux
wget https://download.oracle.com/otn-pub/otn_software/db-express/oracle-database-xe-21c-1.0-1.ol7.x86_64.rpm
sudo yum -y install oracle-database-xe-21c-1.0-1.ol7.x86_64.rpm
sudo /etc/init.d/oracle-xe-21c configure
```

#### Create Database Schema

```bash
# Connect to Oracle SQL*Plus
sqlplus sys/password@localhost:1521/XEPDB1 as sysdba

# Create user and grant privileges
CREATE USER student_analyzer IDENTIFIED BY yourpassword;
GRANT CONNECT, RESOURCE, DBA TO student_analyzer;
ALTER USER student_analyzer QUOTA UNLIMITED ON USERS;

# Connect as new user
CONNECT student_analyzer/yourpassword@localhost:1521/XEPDB1

# Run the schema script
@schema.sql
```

### 2. Backend Setup (Flask)

#### Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-cors cx_Oracle python-dotenv pyjwt
```

#### Configure Environment Variables

Create a `.env` file in the backend directory:

```env
DB_USER=student_analyzer
DB_PASSWORD=yourpassword
DB_DSN=localhost:1521/XEPDB1
SECRET_KEY=your-secret-key-change-this-in-production
```

#### Install Oracle Instant Client

```bash
# On Linux (Oracle Instant Client)
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-19.19.0.0.0dbru.zip
unzip instantclient-basic-linux.x64-19.19.0.0.0dbru.zip
sudo mv instantclient_19_19 /opt/oracle/
export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_19:$LD_LIBRARY_PATH

# On macOS
brew install instantclient-basic

# On Windows
# Download from Oracle website and add to PATH
```

#### Run Flask Server

```bash
python app.py
# Server will start on http://localhost:5000
```

### 3. Frontend Setup (React)

#### Install Dependencies

```bash
cd frontend

# Create React app with Vite
npm create vite@latest . -- --template react
npm install

# Install additional dependencies
npm install recharts lucide-react axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### Configure Tailwind CSS

Update `tailwind.config.js`:

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Update `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### Update API Base URL

In `src/App.jsx`, update the API_BASE constant to match your backend URL:

```javascript
const API_BASE = 'http://localhost:5000/api';
```

#### Run Development Server

```bash
npm run dev
# Server will start on http://localhost:5173
```

## 🚀 Usage

### Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

### Dashboard Features

1. **Dashboard**: View overall statistics and charts
2. **Students**: Manage student records (CRUD operations)
3. **Subjects**: Add and manage subjects
4. **Exams**: Create and schedule exams
5. **Results**: Enter and update student results

### API Endpoints

#### Authentication
- `POST /api/auth/login` - Login and get JWT token

#### Students
- `GET /api/students` - Get all students (with filters)
- `POST /api/students` - Create new student
- `GET /api/students/:id` - Get student by ID
- `PUT /api/students/:id` - Update student
- `DELETE /api/students/:id` - Delete student

#### Subjects
- `GET /api/subjects` - Get all subjects
- `POST /api/subjects` - Create new subject
- `PUT /api/subjects/:id` - Update subject
- `DELETE /api/subjects/:id` - Delete subject

#### Exams
- `GET /api/exams` - Get all exams
- `POST /api/exams` - Create new exam

#### Results
- `GET /api/results` - Get all results (with filters)
- `POST /api/results` - Add new result (grade auto-calculated)
- `PUT /api/results/:id` - Update result
- `DELETE /api/results/:id` - Delete result

#### Analytics
- `GET /api/analytics/dashboard` - Get dashboard statistics
- `GET /api/students/:id/summary` - Get student performance summary
- `GET /api/analytics/top-performers` - Get top performing students

## 📊 Database Schema

### Tables

1. **STUDENTS**: Student information
2. **SUBJECTS**: Subject details with max marks
3. **EXAMS**: Exam information
4. **RESULTS**: Student results linking all entities
5. **TEACHERS**: Teacher information (optional)

### Automatic Features

- **Auto-increment IDs**: Using Oracle sequences
- **Grade Calculation**: Automatic grade computation based on percentage
- **Triggers**: Auto-calculate grade on insert/update
- **Views**: Pre-built views for analytics
- **Stored Procedures**: For complex queries

## 🎨 Frontend Components

- **StatCard**: Dashboard statistics cards
- **Modal Forms**: Dynamic forms for CRUD operations
- **Data Tables**: Sortable and searchable tables
- **Charts**: Bar, Line, and Pie charts using Recharts
- **Dark Mode**: Toggle between themes

## 🔒 Security Features

- JWT-based authentication
- Protected API routes
- SQL injection prevention (parameterized queries)
- CORS enabled for frontend-backend communication

## 🧪 Testing

### Backend API Testing

```bash
# Using curl
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Using Postman or Thunder Client
# Import the API endpoints and test each route
```

### Frontend Testing

```bash
# In frontend directory
npm run build
npm run preview
```

## 📝 Common Issues & Solutions

### Issue: Oracle Connection Error

**Solution**: 
- Verify Oracle database is running: `lsnrctl status`
- Check connection string in `.env` file
- Ensure Oracle Instant Client is installed and in PATH

### Issue: CORS Error

**Solution**:
- Enable CORS in Flask: `CORS(app)`
- Check frontend API_BASE URL matches backend

### Issue: Module Not Found (cx_Oracle)

**Solution**:
```bash
pip install cx_Oracle
# Ensure Oracle Instant Client is installed
```

### Issue: Port Already in Use

**Solution**:
```bash
# For Flask (port 5000)
lsof -ti:5000 | xargs kill -9

# For React (port 5173)
lsof -ti:5173 | xargs kill -9
```

## 🚀 Deployment

### Backend Deployment (Heroku/Render)

```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Install gunicorn
pip install gunicorn

# Deploy to Render/Heroku
git push heroku main
```

### Frontend Deployment (Netlify/Vercel)

```bash
# Build for production
npm run build

# Deploy dist folder to Netlify/Vercel
netlify deploy --prod --dir=dist
```

### Database (Oracle Cloud)

- Use Oracle Autonomous Database
- Update connection string in `.env`
- Ensure wallet files are configured

## 📚 Additional Resources

- [Oracle SQL Documentation](https://docs.oracle.com/en/database/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Recharts Documentation](https://recharts.org/)
- [Tailwind CSS](https://tailwindcss.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Student Result Analyzer Team

## 🙏 Acknowledgments

- Oracle Database for robust data management
- Flask community for excellent documentation
- React and Recharts for beautiful UI components
- Tailwind CSS for rapid styling

---

