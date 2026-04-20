# Premium Django To-Do App

A modern, responsive, and highly dynamic To-Do list application built with Django. 

This project evolved from a traditional Server-Side Rendered (SSR) application into a robust API-driven application featuring a stunning Glassmorphism UI, asynchronous Javascript data-fetching, custom authentication, and automated PDF exports.

## ✨ Features

- **Modern Glassmorphism UI**: Beautiful, fully responsive dark-mode interface with vibrant gradients, custom typography, and micro-animations.
- **RESTful API Architecture**: Uses Django REST Framework and Javascript `fetch()` for seamless, asynchronous task management (Add, toggle, delete tasks without page reloads!).
- **PDF Export**: Generate and download beautifully formatted PDF reports of your task list instantly using the backend `reportlab` engine.
- **Secure Authentication**: Custom-built, independent registration and login workflows outside the standard Django admin.
- **Advanced Password Resets**: Custom email validation logic for password resets with fully configured Gmail SMTP integration.
- **Browser Autofill Mitigation**: Built-in logic to prevent aggressive browser auto-fill bugs on sensitive forms.

## 🛠️ Technology Stack
- **Backend:** Python, Django 5, Django REST Framework
- **Database:** MySQL
- **Frontend:** HTML5, Vanilla JavaScript, CSS3 (Custom Glassmorphism styling)
- **Utilities:** `reportlab` (PDF generation)

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- MySQL Server

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/todo_app.git
   cd todo_app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Settings:**
   Ensure your database credentials and Gmail App Passwords (for password resets) are correctly set inside `todo/settings.py`.

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   *Visit `http://127.0.0.1:8000/` in your browser to view the application.*

---
*Built as a showcase for integrating modern frontend aesthetics with powerful Django backend architectures.*
