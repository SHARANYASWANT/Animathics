import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, Video, MessageSquare } from 'lucide-react';

const Layout = ({ children }) => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-indigo-600 flex items-center gap-2">
            <span>Animathics</span>
          </Link>

          <nav className="flex items-center gap-4">
            {user && (
              <>
                <Link 
                  to="/" 
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition ${location.pathname === '/' ? 'bg-indigo-50 text-indigo-600' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  <MessageSquare size={18} />
                  Chat Tutor
                </Link>
                <Link 
                  to="/generate" 
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition ${location.pathname === '/generate' ? 'bg-indigo-50 text-indigo-600' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  <Video size={18} />
                  Generate Video
                </Link>
                <div className="h-6 w-px bg-gray-200 mx-2"></div>
                <button 
                  onClick={handleLogout}
                  className="flex items-center gap-2 text-red-500 hover:text-red-700 font-medium"
                >
                  <LogOut size={18} />
                  Logout
                </button>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {children}
      </main>
    </div>
  );
};

export default Layout;