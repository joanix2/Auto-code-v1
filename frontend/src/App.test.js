import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Auto-Code Platform heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/Auto-Code Platform/i);
  expect(headingElement).toBeInTheDocument();
});
