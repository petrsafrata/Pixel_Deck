# 🤝 Contributing to Pixel Deck

Thank you for your interest in contributing!

Contributions are welcome — whether it's a bug fix, performance improvement, new scene, documentation enhancement, or general refactoring.

---

## 📌 How to Contribute

1. Fork the repository  
2. Create a feature branch  
3. Make your changes  
4. Submit a Pull Request  

Please describe clearly:
- What you changed
- Why it was needed
- Any configuration impact

---

## 🧭 Contribution Rules

### Code Quality

- Follow the existing project structure
- Keep code modular and readable
- Use clear naming conventions
- Write comments in English
- Avoid unnecessary complexity

### Scenes

- Always inherit from `BaseScene`
- Follow the standardized scene lifecycle
- Keep rendering logic separate from data-fetching logic
- Do not hardcode values that belong in `config.yml`

### Logging

- Use the built-in `logging` module
- Do NOT use `print()` in production code
- Log meaningful warnings and errors only

### Configuration

- Keep configuration backward compatible
- Document new configuration fields if introduced
- Avoid breaking existing scenes

### Dependencies

- Avoid adding new dependencies unless necessary
- If added, update `requirements.txt`
- Keep Raspberry Pi compatibility in mind

---

## 🐳 Raspberry Pi Compatibility

Pixel Deck runs on Raspberry Pi (via Docker).  
Please ensure your changes do not break hardware compatibility.

---

## 🧪 Before Submitting a PR

- Test the application locally
- Verify that scene rotation works
- Ensure no crashes occur on startup
- Check logging output for warnings or errors

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for helping improve Pixel Deck 🚀
