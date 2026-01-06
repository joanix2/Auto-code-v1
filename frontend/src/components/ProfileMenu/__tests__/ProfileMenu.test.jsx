import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '../../../contexts/AuthContext';
import ProfileMenu from '../ProfileMenu';

const mockUser = {
  id: '1',
  name: 'Test User',
  email: 'test@example.com',
  avatar: null
};

const mockLogout = jest.fn();
const mockNavigate = jest.fn();
const mockOnClose = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

const renderProfileMenu = () => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={{ logout: mockLogout }}>
        <ProfileMenu user={mockUser} onClose={mockOnClose} />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('ProfileMenu', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user information', () => {
    renderProfileMenu();
    
    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  it('renders only Profile and Logout menu items', () => {
    renderProfileMenu();
    
    const menuItems = screen.getAllByRole('button');
    // Should have exactly 2 menu items (Profile and Logout)
    expect(menuItems).toHaveLength(2);
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('does not render Settings menu item', () => {
    renderProfileMenu();
    
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('navigates to profile page when Profile is clicked', () => {
    renderProfileMenu();
    
    const profileButton = screen.getByText('Profile');
    fireEvent.click(profileButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('logs out user when Logout is clicked', async () => {
    renderProfileMenu();
    
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/login');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('closes menu when clicking outside', () => {
    const { container } = renderProfileMenu();
    
    // Click outside the menu
    fireEvent.mouseDown(container);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('renders default avatar when user has no avatar', () => {
    renderProfileMenu();
    
    const avatar = screen.getByAltText(mockUser.name);
    expect(avatar.src).toContain('default-avatar.png');
  });
});