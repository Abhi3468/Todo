const taskList = document.getElementById('taskList');
const addTaskForm = document.getElementById('addTaskForm');
const taskTitleInput = document.getElementById('taskTitle');
const taskSearch = document.getElementById('taskSearch');
const taskSummary = document.getElementById('taskSummary');
const taskError = document.getElementById('taskError');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

let tasks = [];
let activeFilter = 'all';

function showError(message) {
    taskError.textContent = message;
    taskError.hidden = !message;
}

function filteredTasks() {
    const query = taskSearch.value.trim().toLowerCase();
    return tasks.filter((task) => {
        const matchesFilter = activeFilter === 'all'
            || (activeFilter === 'active' && !task.completed)
            || (activeFilter === 'completed' && task.completed);
        return matchesFilter && task.title.toLowerCase().includes(query);
    });
}

function updateSummary() {
    const completed = tasks.filter((task) => task.completed).length;
    const remaining = tasks.length - completed;
    taskSummary.textContent = tasks.length
        ? `${remaining} task${remaining === 1 ? '' : 's'} remaining · ${completed} completed`
        : 'Start small—add your first task.';
}

function createButton(className, label, handler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `task-action ${className}`;
    button.setAttribute('aria-label', label);
    button.title = label;
    button.addEventListener('click', handler);
    return button;
}

function renderTasks() {
    const visibleTasks = filteredTasks();
    taskList.replaceChildren();
    updateSummary();

    if (!visibleTasks.length) {
        const emptyState = document.createElement('li');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = '<div class="empty-icon" aria-hidden="true">✨</div><p>No matching tasks found.</p>';
        taskList.appendChild(emptyState);
        return;
    }

    visibleTasks.forEach((task) => {
        const item = document.createElement('li');
        item.className = `task-item ${task.completed ? 'completed' : ''}`;

        const toggle = createButton('task-toggle', task.completed ? `Mark ${task.title} as active` : `Mark ${task.title} as complete`, () => toggleTask(task.id));
        const checkbox = document.createElement('span');
        checkbox.className = `checkbox ${task.completed ? 'checked' : ''}`;
        checkbox.setAttribute('aria-hidden', 'true');
        toggle.appendChild(checkbox);

        const title = document.createElement('span');
        title.className = 'task-title';
        title.textContent = task.title;

        const remove = createButton('task-delete', `Delete ${task.title}`, () => deleteTask(task.id));
        remove.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1 2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>';

        item.append(toggle, title, remove);
        taskList.appendChild(item);
    });
}

async function fetchTasks() {
    try {
        const response = await fetch('/api/tasks/');
        if (!response.ok) throw new Error('Unable to load tasks. Refresh and try again.');
        tasks = await response.json();
        showError('');
        renderTasks();
    } catch (error) {
        showError(error.message);
    }
}

addTaskForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const title = taskTitleInput.value.trim();
    if (!title) return;

    try {
        const response = await fetch('/api/tasks/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ title })
        });
        if (!response.ok) throw new Error('Unable to add the task. Please try again.');
        taskTitleInput.value = '';
        await fetchTasks();
    } catch (error) {
        showError(error.message);
    }
});

async function toggleTask(id) {
    try {
        const response = await fetch(`/api/tasks/${id}/toggle/`, { method: 'POST', headers: { 'X-CSRFToken': csrfToken } });
        if (!response.ok) throw new Error('Unable to update the task. Please try again.');
        await fetchTasks();
    } catch (error) {
        showError(error.message);
    }
}

async function deleteTask(id) {
    const task = tasks.find((item) => item.id === id);
    if (!window.confirm(`Delete "${task?.title || 'this task'}"?`)) return;
    try {
        const response = await fetch(`/api/tasks/${id}/delete/`, { method: 'DELETE', headers: { 'X-CSRFToken': csrfToken } });
        if (!response.ok) throw new Error('Unable to delete the task. Please try again.');
        await fetchTasks();
    } catch (error) {
        showError(error.message);
    }
}

taskSearch.addEventListener('input', renderTasks);
document.querySelectorAll('.filter-btn').forEach((button) => {
    button.addEventListener('click', () => {
        activeFilter = button.dataset.filter;
        document.querySelectorAll('.filter-btn').forEach((item) => item.classList.toggle('active', item === button));
        renderTasks();
    });
});

fetchTasks();
