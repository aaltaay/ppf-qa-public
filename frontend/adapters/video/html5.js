// HTML5 Video Adapter
window.CourseQAVideoAdapter = {
    seek: function(seconds) {
        const video = document.querySelector('video');
        if (video) {
            video.currentTime = seconds;
            video.play().catch(e => console.log("Autoplay prevented:", e));
            video.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            console.error("No video element found on the page.");
        }
    }
};
