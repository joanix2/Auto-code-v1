import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '../../../contexts/AuthContext';
import AppBar from '../AppBar';

const mockUser = {
  id: '1',
  name: 'Test User',
  email: 'test@example.com',
  avatar: null
};

const renderWithAuth = (user = null) => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={{ user }}>
        <AppBar />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('AppBar', () => {
  it('renders logo and title', () => {
    renderWithAuth();
    expect(screen.getByText('Auto-Code')).toBeInTheDocument();
    expect(screen.getByAltText('Logo')).toBeInTheDocument();
  });

  it('shows profile button when user is authenticated', () => {
    renderWithAuth(mockUser);
    expect(screen.getByLabelText('Profile menu')).toBeInTheDocument();
  });

  it('does not show profile button when user is not authenticated', () => {
    renderWithAuth(null);
    expect(screen.queryByLabelText('Profile menu')).not.toBeInTheDocument();
  });

  it('opens profile menu when profile button is clicked', () => {
    renderWithAuth(mockUser);
    const profileButton = screen.getByLabelText('Profile menu');
    
    fireEvent.click(profileButton);
    
    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  it('does not render settings button in profile zone', () => {
    renderWithAuth(mockUser);
    
    // Settings button should not exist
    expect(screen.queryByLabelText('Settings')).not.toBeInTheDocument();
    expect(screen.queryByTestId('settings-button')).not.toBeInTheDocument();
  });

  it('navigates to home when logo is clicked', () => {
    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));
    
    renderWithAuth(mockUser);
    const logo = screen.getByText('Auto-Code').parentElement;
    
    fireEvent.click(logo);
    
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});