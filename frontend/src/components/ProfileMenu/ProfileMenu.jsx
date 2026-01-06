import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './ProfileMenu.css';

const ProfileMenu = ({ user, onClose }) => {
  const menuRef = useRef(null);
  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  const handleProfileClick = () => {
    navigate('/profile');
    onClose();
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
    onClose();
  };

  const menuItems = [
    {
      label: 'Profile',
      icon: 'person',
      onClick: handleProfileClick
    },
    {
      label: 'Logout',
      icon: 'logout',
      onClick: handleLogout
    }
  ];

  return (
    <div className="profile-menu" ref={menuRef}>
      <div className="profile-menu-header">
        <img 
          src={user.avatar || '/default-avatar.png'} 
          alt={user.name}
          className="profile-menu-avatar"
        />
        <div className="profile-menu-info">
          <div className="profile-menu-name">{user.name}</div>
          <div className="profile-menu-email">{user.email}</div>
        </div>
      </div>
      
      <div className="profile-menu-divider" />
      
      <ul className="profile-menu-items">
        {menuItems.map((item, index) => (
          <li key={index}>
            <button 
              className="profile-menu-item"
              onClick={item.onClick}
            >
              <span className="material-icons">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ProfileMenu;