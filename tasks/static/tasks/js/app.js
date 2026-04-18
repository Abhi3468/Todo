const taskList = document.getElementById('taskList');
const addTaskForm = document.getElementById('addTaskForm');
const taskTitleInput = document.getElementById('taskTitle');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// Fetch all tasks
async function fetchTasks() {
    const response = await fetch('/api/tasks/');
    const tasks = await response.json();
    renderTasks(tasks);
}

// Render tasks to the DOM
function renderTasks(tasks) {
    taskList.innerHTML = '';

    if (tasks.length === 0) {
        taskList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✨</div>
                <p>No tasks yet. You're all caught up!</p>
            </div>`;
        return;
    }

    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = `task-item ${task.completed ? 'completed' : ''}`;

        li.innerHTML = `
            <a href="javascript:void(0)" onclick="toggleTask(${task.id})" class="task-toggle">
                <div class="checkbox ${task.completed ? 'checked' : ''}"></div>
            </a>

            <span class="task-title">${task.title}</span>

            <a href="javascript:void(0)" onclick="deleteTask(${task.id})" class="task-delete" title="Delete task">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2">
                    </path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
            </a>
        `;
        taskList.appendChild(li);
    });
}

// Add a new task
addTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = taskTitleInput.value;
    if (!title) return;

    const response = await fetch('/api/tasks/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ title: title })
    });

    if (response.ok) {
        taskTitleInput.value = '';
        fetchTasks();
    }
});

// Toggle task completion
async function toggleTask(id) {
    const response = await fetch(`/api/tasks/${id}/toggle/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    });
    if (response.ok) {
        fetchTasks();
    }
}

// Delete a task
async function deleteTask(id) {
    const response = await fetch(`/api/tasks/${id}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken
        }
    });
    if (response.ok) {
        fetchTasks();
    }
}

// Initial fetch
fetchTasks();
