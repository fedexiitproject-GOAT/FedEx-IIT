# Contributing to FedEx Data Repository

Thank you for your interest in contributing to **FedEx Data Repository**! We welcome bug reports, improvements, documentation updates, and feature contributions.

## Code of Conduct

Please maintain professional, respectful, and constructive communication at all times.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/fedex_repository.git
   cd fedex_repository
   ```
3. Create a branch for your feature or bug fix:
   ```bash
   git checkout -b feature/my-new-feature
   ```

## Development Guidelines

### Coding Standards
- **Python**: Follow PEP 8 and standard Odoo conventions (4 spaces indentation, clean docstrings, clear variable names).
- **XML**: Use 4 spaces indentation. Ensure all `<record>` elements have unique IDs prefixed with the module namespace or logical model view type.
- **JavaScript / OWL**: Follow modern ES6+ standards and Odoo 18 OWL component structures.
- **SCSS / CSS**: Maintain FedEx brand standards (`#4D148C` purple, `#FF6200` orange) and use CSS custom properties where appropriate.

### Pre-commit Hooks
We recommend installing `pre-commit` to automatically verify formatting and linting:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Running Tests
Run automated tests using `odoo-bin`:
```bash
./odoo-bin -c /path/to/odoo.conf -d <test_db> -i fedex_repository --test-enable --stop-after-init
```

## Submitting Pull Requests

1. Commit your changes with descriptive commit messages following the Conventional Commits style (e.g., `feat: add export button to analytics view`, `fix: handle empty xlsx rows in student import`).
2. Push your changes to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```
3. Open a Pull Request against the `18.0` branch of the upstream repository.
4. Fill in the Pull Request template completely and ensure CI checks pass.

## Reporting Issues

If you find a bug or have a suggestion:
- Check existing issues to see if it has already been reported.
- Open a new issue using our structured **Bug Report** or **Feature Request** template.
- Include reproduction steps, environment details (Odoo 18, PostgreSQL version, Python version), and relevant traceback logs.
