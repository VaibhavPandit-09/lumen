# Contributing to Lumen

Thank you for your interest in contributing to **Lumen**! Lumen is an agent-friendly command launcher and command palette for KDE Plasma.

---

## 🧭 Guiding Principles

1. **Keep KDE Plasma Native**: Retain conventional KDE floating window behavior. Do not require external tiling managers or non-standard shell dependencies.
2. **Agent-Friendly & Malleable**: Configuration must remain human-readable JSONC with schema validation. Avoid binary state databases or opaque formats.
3. **Instant Performance**: Search indexing and keystroke processing must remain snappy and responsive (< 15ms per search frame).
4. **Permissive & Clean**: Keep dependencies minimal (Python standard library + PyQt6).

---

## 🛠️ Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/VaibhavPandit-09/lumen.git
cd lumen
```

### 2. Verify requirements
Make sure you have Python 3.10+ and PyQt6 installed:
```bash
# On Kubuntu / Debian / Ubuntu
sudo apt install python3 python3-pyqt6

# On Arch Linux
sudo pacman -S python python-pyqt6

# On Fedora
sudo dnf install python3 python3-qt6
```

### 3. Run the test suite
```bash
make test
# or
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py" -v
```

### 4. Run Lumen in development mode
```bash
python3 -m lumen
```

---

## 🧪 Testing Guidelines

* Write unit tests in `tests/` for any new matching algorithm, parser, provider, or UI feature.
* UI tests must run cleanly in headless mode using `QT_QPA_PLATFORM=offscreen`.
* Ensure all tests pass before submitting a pull request.

---

## 📝 Pull Request Workflow

1. Fork the repository on GitHub.
2. Create a descriptive feature branch (`git checkout -b feature/my-cool-provider`).
3. Make your changes with clear, focused commits.
4. Run the test suite and verify no regressions occur (`make test`).
5. Open a Pull Request on GitHub against the `main` branch.
