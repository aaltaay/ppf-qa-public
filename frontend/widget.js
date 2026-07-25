// Course Q&A Widget Core Logic

const CourseQAWidget = (function() {
    let config = {
        apiUrl: 'http://localhost:8001',
        videoAdapter: 'html5',
        lessonDetector: 'data-attr',
        lessonMapping: {}
    };

    let state = {
        isOpen: false,
        history: [],
        currentModule: null
    };

    let elements = {};
    let adapters = {};

    function init(userConfig) {
        config = { ...config, ...userConfig };
        
        // Load history from localStorage
        const savedHistory = localStorage.getItem('course_qa_history');
        if (savedHistory) {
            try {
                state.history = JSON.parse(savedHistory);
            } catch (e) {
                console.error('Failed to parse saved history');
            }
        }

        // Detect current module
        detectModule();

        // Render UI
        renderUI();
        
        // Bind events
        bindEvents();
    }

    function detectModule() {
        if (config.lessonDetector === 'data-attr' && window.CourseQALessonDetector) {
            state.currentModule = window.CourseQALessonDetector.detect();
        } else {
            // Default fallback
            state.currentModule = 1;
        }
        console.log("Detected module:", state.currentModule);
    }

    function renderUI() {
        const root = document.createElement('div');
        root.id = 'course-qa-widget-root';
        
        root.innerHTML = `
            <button id="course-qa-widget-btn">💬</button>
            <div id="course-qa-widget-panel">
                <div id="course-qa-widget-header">
                    <h3>Course Assistant</h3>
                    <button id="course-qa-widget-close">×</button>
                </div>
                <div id="course-qa-widget-messages"></div>
                <div id="course-qa-widget-input-area">
                    <input type="text" id="course-qa-widget-input" placeholder="Ask a question..." autocomplete="off">
                    <button id="course-qa-widget-send">Send</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(root);
        
        elements = {
            btn: document.getElementById('course-qa-widget-btn'),
            panel: document.getElementById('course-qa-widget-panel'),
            closeBtn: document.getElementById('course-qa-widget-close'),
            messages: document.getElementById('course-qa-widget-messages'),
            input: document.getElementById('course-qa-widget-input'),
            sendBtn: document.getElementById('course-qa-widget-send')
        };

        renderHistory();
    }

    function renderHistory() {
        elements.messages.innerHTML = '';
        if (state.history.length === 0) {
            appendMessage('bot', 'Hi! Ask me anything about the lessons covered in this course.');
        } else {
            state.history.forEach(msg => {
                appendMessage(msg.role, msg.content, false);
            });
        }
        scrollToBottom();
    }

    function bindEvents() {
        elements.btn.addEventListener('click', togglePanel);
        elements.closeBtn.addEventListener('click', togglePanel);
        
        elements.sendBtn.addEventListener('click', handleSend);
        elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSend();
        });
        
        // Handle citation clicks using event delegation
        elements.messages.addEventListener('click', (e) => {
            const citation = e.target.closest('.course-qa-citation');
            if (citation) {
                e.preventDefault();
                const module = citation.getAttribute('data-module');
                const timeStr = citation.getAttribute('data-time');
                
                // Parse timeStr (MM:SS to seconds)
                let seconds = 0;
                const parts = timeStr.split(':');
                if (parts.length === 2) {
                    seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
                } else if (parts.length === 3) {
                    seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
                } else {
                    seconds = parseInt(timeStr);
                }
                
                seekVideo(module, seconds);
            }
        });
    }

    function togglePanel() {
        state.isOpen = !state.isOpen;
        if (state.isOpen) {
            elements.panel.classList.add('open');
            elements.btn.style.display = 'none';
            elements.input.focus();
        } else {
            elements.panel.classList.remove('open');
            elements.btn.style.display = 'flex';
        }
    }

    function appendCitationLink(container, module, time) {
        const link = document.createElement('a');
        link.href = '#';
        link.className = 'course-qa-citation';
        link.dataset.module = module;
        link.dataset.time = time;
        link.textContent = `▶️ Module ${module} at ${time}`;
        container.appendChild(link);
    }

    function renderBotMessageContent(container, text) {
        // Matches [Module X at MM:SS] — build DOM nodes instead of innerHTML
        const regex = /\[Module\s+(\d+)\s+at\s+(\d+:\d+)\]/g;
        let lastIndex = 0;
        let match;
        while ((match = regex.exec(text)) !== null) {
            if (match.index > lastIndex) {
                container.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
            }
            appendCitationLink(container, match[1], match[2]);
            lastIndex = regex.lastIndex;
        }
        if (lastIndex < text.length) {
            container.appendChild(document.createTextNode(text.slice(lastIndex)));
        }
    }

    function appendMessage(role, content, save = true) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `course-qa-msg ${role}`;
        
        if (role === 'bot') {
            renderBotMessageContent(msgDiv, content);
        } else {
            msgDiv.textContent = content;
        }
        
        elements.messages.appendChild(msgDiv);
        scrollToBottom();
        
        if (save) {
            state.history.push({ role, content });
            // Gemini expects 'user' or 'model', but in UI we use 'bot'
            saveHistory();
        }
    }
    
    function appendLoading() {
        const msgDiv = document.createElement('div');
        msgDiv.className = `course-qa-msg bot loading`;
        msgDiv.id = 'course-qa-loading-msg';
        msgDiv.textContent = "Thinking...";
        elements.messages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function removeLoading() {
        const loader = document.getElementById('course-qa-loading-msg');
        if (loader) loader.remove();
    }

    function scrollToBottom() {
        elements.messages.scrollTop = elements.messages.scrollHeight;
    }

    function saveHistory() {
        localStorage.setItem('course_qa_history', JSON.stringify(state.history));
    }

    async function handleSend() {
        const text = elements.input.value.trim();
        if (!text) return;
        
        elements.input.value = '';
        elements.input.disabled = true;
        elements.sendBtn.disabled = true;
        
        appendMessage('user', text);
        
        appendLoading();
        
        try {
            const response = await fetch(`${config.apiUrl}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: text,
                    current_module: state.currentModule,
                    history: state.history.slice(0, -1) // Excluding the one we just added
                })
            });
            
            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error("You've asked too many questions. Please try again later.");
                }
                throw new Error("Failed to get an answer.");
            }
            
            const data = await response.json();
            removeLoading();
            
            appendMessage('bot', data.answer, false);
            state.history.push({ role: 'model', content: data.answer });
            saveHistory();
            
        } catch (error) {
            removeLoading();
            appendMessage('bot', error.message, false);
            // Don't save error to history
            state.history.pop();
        } finally {
            elements.input.disabled = false;
            elements.sendBtn.disabled = false;
            elements.input.focus();
        }
    }

    function seekVideo(module, seconds) {
        if (state.currentModule && state.currentModule.toString() !== module.toString()) {
            // Need to notify user they need to navigate
            alert(`This is answered in Module ${module}. Please navigate to that module first.`);
            return;
        }
        
        if (config.videoAdapter === 'html5' && window.CourseQAVideoAdapter) {
            window.CourseQAVideoAdapter.seek(seconds);
        } else {
            console.warn("Video adapter not configured for seeking.");
        }
    }

    // Expose registration methods for adapters
    return {
        init,
        registerVideoAdapter: (name, impl) => { adapters[name] = impl; }
    };
})();

// Attach to window
window.CourseQAWidget = CourseQAWidget;
