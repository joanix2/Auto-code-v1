import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import ProfileMenu from '../ProfileMenu/ProfileMenu';
import './AppBar.css';

const AppBar = () => {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleProfileClick = () => {
    setIsProfileMenuOpen(!isProfileMenuOpen);
  };

  const handleLogoClick = () => {
    navigate('/');
  };

  return (
    <header className="app-bar">
      <div className="app-bar-container">
        <div className="app-bar-left">
          <div className="app-bar-logo" onClick={handleLogoClick}>
            <img src="/logo.svg" alt="Logo" />
            <span>Auto-Code</span>
          </div>
        </div>
        
        <div className="app-bar-right">
          {user && (
            <div className="profile-zone">
              <button 
                className="profile-button"
                onClick={handleProfileClick}
                aria-label="Profile menu"
              >
                <img 
                  src={user.avatar || '/default-avatar.png'} 
                  alt={user.name}
                  className="profile-avatar"
                />
              </button>
              
              {isProfileMenuOpen && (
                <ProfileMenu 
                  user={user}
                  onClose={() => setIsProfileMenuOpen(false)}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default AppBar;