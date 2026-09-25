import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '@/pages/Dashboard';

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Redirect base URL directly to the dashboard for now */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* The main dashboard page */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* 
          FUTURE AUTHENTICATION ROUTES:
          Once you build the login UI, you will uncomment these.
        */}
        {/* <Route path="/login" element={<Login />} /> */}
        {/* <Route path="/register" element={<Register />} /> */}

        {/* Catch-all: If user types a random URL, send them to the dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}