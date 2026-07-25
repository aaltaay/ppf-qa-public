// Lesson detector — reads data-module-id from the page
window.CourseQALessonDetector = {
    detect: function() {
        const container = document.querySelector('[data-module-id]');
        if (container) {
            return parseInt(container.getAttribute('data-module-id'), 10);
        }
        return null;
    }
};
