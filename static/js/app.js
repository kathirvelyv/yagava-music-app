document.addEventListener('DOMContentLoaded', () => {
    // Get elements
    const playlist = document.getElementById('playlist');
    const currentSongElement = document.getElementById('currentSong');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const seekBar = document.getElementById('seekBar');
    const volumeControl = document.getElementById('volumeControl');
    const currentTimeElement = document.getElementById('currentTime');
    const durationElement = document.getElementById('duration');
    const progressBar = document.getElementById('progress');
    const uploadForm = document.getElementById('uploadForm');
    const uploadToggleBtn = document.getElementById('uploadToggleBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const adminLoginBtn = document.getElementById('adminLoginBtn');
    const loadingSpinner = document.getElementById('loading');
    
    let currentAudio = null;
    let songs = [];
    let currentSongIndex = -1;
    let isPlaying = false;

    // Format time in MM:SS
    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // Admin authentication functions
    async function adminLogin(password) {
        try {
            const response = await fetch('/admin-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password }),
            });

            const data = await response.json();

            if (response.ok) {
                window.location.reload();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('An error occurred during login');
        }
    }

    async function adminLogout() {
        try {
            const response = await fetch('/admin-logout', {
                method: 'POST',
            });

            const data = await response.json();

            if (response.ok) {
                window.location.reload();
            } else {
                alert(data.error || 'Logout failed');
            }
        } catch (error) {
            console.error('Logout error:', error);
            alert('An error occurred during logout');
        }
    }

    // Music player functions
    function playSong(index) {
        if (index < 0 || index >= songs.length) return;

        currentSongIndex = index;
        const song = songs[index];

        if (currentAudio) {
            currentAudio.pause();
            currentAudio.removeEventListener('timeupdate', updateProgress);
            currentAudio.removeEventListener('loadedmetadata', updateDuration);
            currentAudio.removeEventListener('ended', playNext);
            currentAudio.removeEventListener('error', handleAudioError);
        }

        currentAudio = new Audio(song.url);
        currentAudio.volume = volumeControl.value / 100;

        currentAudio.addEventListener('loadedmetadata', updateDuration);
        currentAudio.addEventListener('timeupdate', updateProgress);
        currentAudio.addEventListener('ended', playNext);
        currentAudio.addEventListener('error', handleAudioError);

        // Add playing animation to album art
        const albumArt = document.getElementById('albumArt');
        albumArt.classList.add('playing');

        currentAudio.play().catch(err => {
            console.error('Playback error:', err);
            alert(`Failed to play "${song.name}". Error: ${err.message}`);
            albumArt.classList.remove('playing');
        });
        
        isPlaying = true;
        updatePlayButton();
        
        // Animate song title
        currentSongElement.style.animation = 'none';
        setTimeout(() => {
            currentSongElement.textContent = song.name;
            currentSongElement.style.animation = 'slideInLeft 0.5s ease';
        }, 10);
        
        updatePlaylistUI();
    }

    function handleAudioError(e) {
        console.error('Audio error:', e);
        const song = songs[currentSongIndex];
        alert(`Error loading "${song.name}". The file may be corrupted or the URL has expired.`);
        isPlaying = false;
        updatePlayButton();
        
        // Remove playing animation
        const albumArt = document.getElementById('albumArt');
        albumArt.classList.remove('playing');
    }

    function togglePlayPause() {
        if (!currentAudio) {
            if (songs.length > 0) {
                playSong(0);
            }
            return;
        }

        if (isPlaying) {
            currentAudio.pause();
            isPlaying = false;
        } else {
            currentAudio.play();
            isPlaying = true;
        }
        updatePlayButton();
    }

    function updatePlayButton() {
        const icon = playPauseBtn.querySelector('i');
        if (isPlaying) {
            icon.classList.remove('fa-play');
            icon.classList.add('fa-pause');
        } else {
            icon.classList.remove('fa-pause');
            icon.classList.add('fa-play');
        }
    }

    function playNext() {
        if (currentSongIndex < songs.length - 1) {
            playSong(currentSongIndex + 1);
        } else {
            playSong(0); // Loop to first song
        }
    }

    function playPrevious() {
        if (currentSongIndex > 0) {
            playSong(currentSongIndex - 1);
        } else {
            playSong(songs.length - 1); // Loop to last song
        }
    }

    function updateProgress() {
        if (!currentAudio) return;

        const percent = (currentAudio.currentTime / currentAudio.duration) * 100;
        seekBar.value = percent;
        progressBar.style.width = percent + '%';
        currentTimeElement.textContent = formatTime(currentAudio.currentTime);
    }

    function updateDuration() {
        if (!currentAudio) return;
        durationElement.textContent = formatTime(currentAudio.duration);
    }

    function seek() {
        if (!currentAudio) return;
        const seekTime = (seekBar.value / 100) * currentAudio.duration;
        currentAudio.currentTime = seekTime;
    }

    function updateVolume() {
        if (currentAudio) {
            currentAudio.volume = volumeControl.value / 100;
        }
    }

    function updatePlaylistUI() {
        const items = playlist.querySelectorAll('li');
        items.forEach((item, index) => {
            if (index === currentSongIndex) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // Load and display music list (accessible to everyone)
    async function loadMusicList() {
        try {
            loadingSpinner.style.display = 'block';
            const response = await fetch('/music-list');
            const data = await response.json();

            if (Array.isArray(data)) {
                songs = data;
                playlist.innerHTML = '';
                
                if (songs.length === 0) {
                    playlist.innerHTML = '<li class="no-songs">No songs available yet</li>';
                } else {
                    songs.forEach((song, index) => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <span class="song-name">${song.name}</span>
                            <button class="play-btn"><i class="fas fa-play"></i></button>
                        `;
                        li.querySelector('.play-btn').onclick = () => playSong(index);
                        playlist.appendChild(li);
                    });
                }
            } else {
                console.error('Invalid response format:', data);
                playlist.innerHTML = '<li class="error">Failed to load music list</li>';
            }
        } catch (error) {
            console.error('Error loading music list:', error);
            playlist.innerHTML = '<li class="error">Failed to load music list</li>';
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    // File upload handler (admin only)
    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                alert('File uploaded successfully!');
                uploadForm.reset();
                uploadForm.style.display = 'none';
                loadMusicList();
            } else {
                alert(data.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            alert('An error occurred during upload');
        }
    }

    // Event listeners
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', playPrevious);
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', playNext);
    }

    if (seekBar) {
        seekBar.addEventListener('input', seek);
    }

    if (volumeControl) {
        volumeControl.addEventListener('input', updateVolume);
    }

    // Admin-only features
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const file = document.getElementById('musicFile').files[0];
            if (file) {
                await handleFileUpload(file);
            }
        });
    }

    if (uploadToggleBtn) {
        uploadToggleBtn.addEventListener('click', () => {
            if (uploadForm.style.display === 'none') {
                uploadForm.style.display = 'block';
            } else {
                uploadForm.style.display = 'none';
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', adminLogout);
    }

    if (adminLoginBtn) {
        adminLoginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const password = document.getElementById('adminPassword').value;
            if (password) {
                adminLogin(password);
            } else {
                alert('Please enter the admin password');
            }
        });

        // Allow Enter key to submit login
        const passwordInput = document.getElementById('adminPassword');
        if (passwordInput) {
            passwordInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    adminLoginBtn.click();
                }
            });
        }
    }

    // Load music list on page load (available to all users)
    loadMusicList();
});