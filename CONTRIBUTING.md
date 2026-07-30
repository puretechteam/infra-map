# Contributing to Infra Map

## How to Contribute

We welcome contributions from the community. Here are some ways you can help:

- Report bugs by opening an issue
- Suggest new features or improvements
- Submit pull requests with bug fixes or enhancements
- Improve documentation

## Development Setup

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/<your-username>/infra-map.git
   ```
3. Navigate to the project directory:
   ```
   cd infra-map
   ```
4. Create a virtual environment:
   ```
   python -m venv venv
   ```
5. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
6. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```
7. Run the development server:
   ```
   python app.py
   ```

## Submitting Changes

1. Create a new branch for your feature or bug fix:
   ```
   git checkout -b my-feature
   ```
2. Make your changes and commit them with a clear, descriptive commit message.
3. Push your branch to your fork:
   ```
   git push origin my-feature
   ```
4. Open a pull request against the `main` branch of the repository.
5. Ensure all checks pass and your PR description clearly explains the changes.

## Code Style Guidelines

- Follow PEP 8 for Python code.
- Use 4 spaces for indentation (no tabs).
- Keep lines to a maximum of 88 characters (Black default).
- Use descriptive variable and function names.
- Add docstrings to public functions and classes.
- Run `black` to format code before committing.
- Run `flake8` or `ruff` to check for linting errors before committing.
- Keep JavaScript files consistent with the existing style in `static/js/`.