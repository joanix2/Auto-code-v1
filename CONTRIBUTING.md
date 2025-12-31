# Contributing to Auto-Code Platform

Thank you for your interest in contributing to the Auto-Code Platform! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Node version)
   - Screenshots if applicable

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create a new issue with:
   - Clear description of the enhancement
   - Use cases and benefits
   - Possible implementation approach

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/Auto-code-v1.git
   cd Auto-code-v1
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Backend tests
   cd backend
   python -m pytest tests/
   
   # Frontend tests
   cd frontend
   npm test
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description
   - Reference related issues
   - Include screenshots for UI changes

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/joanix2/Auto-code-v1.git
   cd Auto-code-v1
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Option A: Using Docker**
   ```bash
   docker-compose up --build
   ```

4. **Option B: Manual setup**
   
   Backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```
   
   Frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for functions and classes
- Use meaningful variable names

Example:
```python
def create_issue(title: str, body: str, labels: Optional[list] = None) -> Optional[Dict[str, Any]]:
    """
    Create a new issue in the repository
    
    Args:
        title: Issue title
        body: Issue description
        labels: Optional list of label names
        
    Returns:
        Dictionary with issue information or None if failed
    """
    # Implementation
```

### JavaScript/React (Frontend)

- Use ES6+ features
- Use functional components and hooks
- Use meaningful component and variable names
- Add PropTypes or TypeScript types
- Keep components focused and single-purpose

Example:
```javascript
const TicketForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: ''
  });
  
  // Component implementation
};
```

### Git Commit Messages

Follow these conventions:

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests

Examples:
```
Add user authentication feature
Fix issue with RabbitMQ connection timeout
Update README with deployment instructions
Refactor GitHub client for better error handling
```

## Testing Guidelines

### Backend Tests

Create tests in `backend/tests/`:

```python
import pytest
from github_client import GitHubClient

def test_create_issue():
    client = GitHubClient()
    result = client.create_issue("Test Issue", "Test body")
    assert result is not None
    assert "issue_number" in result
```

### Frontend Tests

Create tests alongside components:

```javascript
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders create task button', () => {
  render(<App />);
  const buttonElement = screen.getByText(/Create Task/i);
  expect(buttonElement).toBeInTheDocument();
});
```

## Documentation

- Update README.md for major changes
- Update API.md for API changes
- Add inline comments for complex logic
- Update DEPLOYMENT.md for deployment changes

## Project Structure

```
Auto-code-v1/
├── backend/          # Python FastAPI backend
├── frontend/         # React PWA frontend
├── docs/            # Additional documentation
├── tests/           # Integration tests
└── scripts/         # Utility scripts
```

## Areas for Contribution

### High Priority

- [ ] Enhanced Claude API integration for actual code generation
- [ ] Real-time WebSocket updates for task progress
- [ ] Authentication and authorization system
- [ ] More comprehensive testing suite

### Medium Priority

- [ ] Multi-agent collaboration features
- [ ] Code review automation
- [ ] Performance monitoring dashboard
- [ ] Mobile native apps

### Low Priority

- [ ] Advanced analytics
- [ ] Custom agent configurations
- [ ] Plugin system
- [ ] Theme customization

## Getting Help

- Create an issue for bugs or questions
- Check existing documentation
- Review closed issues and PRs
- Join community discussions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project website (when available)

Thank you for contributing to Auto-Code Platform! 🚀
