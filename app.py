from flask import Flask, render_template_string, jsonify
import requests

app = Flask(__name__)

# Configure your GitHub repository
GITHUB_USER = "kathirvelyv"
GITHUB_REPO = "yagava"
GITHUB_BRANCH = "main"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yagava Music Player</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
            min-height: 100vh;
            padding: 20px;
            overflow-x: hidden;
        }

        .container {
            max-width: 450px;
            margin: 0 auto;
        }

        .player-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.5s ease;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 5px;
        }

        .header p {
            color: #666;
            font-size: 14px;
        }

        .album-art {
            width: 100%;
            aspect-ratio: 1;
            border-radius: 20px;
            object-fit: cover;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            margin-bottom: 25px;
            transition: transform 0.3s ease;
        }

        .album-art.playing {
            transform: scale(1.02);
        }

        .song-info {
            text-align: center;
            margin-bottom: 20px;
        }

        .song-title {
            font-size: 22px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }

        .song-artist {
            font-size: 16px;
            color: #666;
        }

        .progress-container {
            margin: 25px 0;
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            cursor: pointer;
        }

        .progress {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.1s;
        }

        .time-display {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 12px;
            color: #666;
        }

        .controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin: 25px 0;
        }

        .control-btn {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            padding: 10px;
            border-radius: 50%;
            transition: all 0.3s;
            color: #333;
        }

        .control-btn:hover {
            background: #f0f0f0;
            transform: scale(1.1);
        }

        .control-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        .play-btn {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 32px;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }

        .play-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }

        .volume-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 15px;
        }

        .volume-icon {
            font-size: 20px;
        }

        .volume-slider {
            flex: 1;
            height: 6px;
            -webkit-appearance: none;
            background: #ddd;
            border-radius: 10px;
            outline: none;
        }

        .volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            cursor: pointer;
        }

        .volume-slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }

        .playlist {
            margin-top: 30px;
            max-height: 300px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .playlist::-webkit-scrollbar {
            width: 6px;
        }

        .playlist::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }

        .playlist::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }

        .playlist-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .song-count {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
        }

        .song-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 12px;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .song-item:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateX(5px);
        }

        .song-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }

        .song-item-cover {
            width: 50px;
            height: 50px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 24px;
            flex-shrink: 0;
        }

        .song-item.active .song-item-cover {
            background: white;
            color: #667eea;
        }

        .song-item:hover .song-item-cover {
            background: white;
            color: #667eea;
        }

        .song-item-info {
            flex: 1;
            min-width: 0;
        }

        .song-item-title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .song-item-artist {
            font-size: 12px;
            opacity: 0.8;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            text-align: center;
            padding: 20px;
            color: #dc3545;
            background: #fee;
            border-radius: 10px;
            margin: 10px 0;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }

        @media (max-width: 480px) {
            .container {
                padding: 10px;
            }
            
            .player-card {
                padding: 20px;
                border-radius: 20px;
            }
            
            .song-title {
                font-size: 18px;
            }
            
            .play-btn {
                width: 60px;
                height: 60px;
                font-size: 28px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="player-card">
            <div class="header">
                <h1>🎵 Yagava Music</h1>
                <p>Streaming from GitHub</p>
            </div>

            <img id="albumArt" class="album-art" src="https://via.placeholder.com/300x300/667eea/ffffff?text=🎵" alt="Album Art">

            <div class="song-info">
                <div class="song-title" id="songTitle">Select a song</div>
                <div class="song-artist" id="songArtist">No song playing</div>
            </div>

            <div class="progress-container">
                <div class="progress-bar" id="progressBar">
                    <div class="progress" id="progress"></div>
                </div>
                <div class="time-display">
                    <span id="currentTime">0:00</span>
                    <span id="duration">0:00</span>
                </div>
            </div>

            <div class="controls">
                <button class="control-btn" id="prevBtn" disabled>⏮️</button>
                <button class="control-btn play-btn" id="playBtn" disabled>▶️</button>
                <button class="control-btn" id="nextBtn" disabled>⏭️</button>
            </div>

            <div class="volume-container">
                <span class="volume-icon">🔊</span>
                <input type="range" class="volume-slider" id="volumeSlider" min="0" max="100" value="70">
            </div>

            <div class="playlist">
                <div class="playlist-title">
                    <span>📋 Playlist</span>
                    <span class="song-count" id="songCount">0</span>
                </div>
                <div id="playlistContainer">
                    <div class="loading">
                        <div class="spinner"></div>
                        Loading songs from GitHub...
                    </div>
                </div>
            </div>
        </div>
    </div>

    <audio id="audio" preload="metadata"></audio>

    <script>
        const audio = document.getElementById('audio');
        const playBtn = document.getElementById('playBtn');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const albumArt = document.getElementById('albumArt');
        const songTitle = document.getElementById('songTitle');
        const songArtist = document.getElementById('songArtist');
        const progress = document.getElementById('progress');
        const progressBar = document.getElementById('progressBar');
        const currentTimeEl = document.getElementById('currentTime');
        const durationEl = document.getElementById('duration');
        const volumeSlider = document.getElementById('volumeSlider');
        const playlistContainer = document.getElementById('playlistContainer');
        const songCount = document.getElementById('songCount');

        let songs = [];
        let currentIndex = 0;

        // Fetch songs from backend
        async function loadSongs() {
            try {
                const response = await fetch('/api/songs');
                
                if (!response.ok) {
                    throw new Error('Failed to fetch songs');
                }
                
                songs = await response.json();
                
                if (songs.length === 0) {
                    playlistContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📂</div>
                            <div>No songs found in the repository</div>
                            <div style="font-size: 12px; margin-top: 10px;">Add .mp3 files to your GitHub repo</div>
                        </div>
                    `;
                    return;
                }
                
                songCount.textContent = songs.length;
                renderPlaylist();
                loadSong(0);
                enableControls();
                
            } catch (error) {
                console.error('Error loading songs:', error);
                playlistContainer.innerHTML = `
                    <div class="error">
                        ❌ Error loading songs<br>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        }

        function enableControls() {
            playBtn.disabled = false;
            prevBtn.disabled = false;
            nextBtn.disabled = false;
        }

        function renderPlaylist() {
            playlistContainer.innerHTML = '';
            songs.forEach((song, index) => {
                const songItem = document.createElement('div');
                songItem.className = 'song-item';
                if (index === currentIndex) {
                    songItem.classList.add('active');
                }
                
                songItem.innerHTML = `
                    <div class="song-item-cover">🎵</div>
                    <div class="song-item-info">
                        <div class="song-item-title">${song.title}</div>
                        <div class="song-item-artist">${song.artist}</div>
                    </div>
                `;
                
                songItem.onclick = () => {
                    loadSong(index);
                    playSong();
                };
                
                playlistContainer.appendChild(songItem);
            });
        }

        function loadSong(index) {
            if (songs.length === 0) return;
            
            currentIndex = index;
            const song = songs[index];
            
            audio.src = song.url;
            albumArt.src = song.cover;
            songTitle.textContent = song.title;
            songArtist.textContent = song.artist;
            
            renderPlaylist();
        }

        function playSong() {
            audio.play().catch(err => {
                console.error('Playback error:', err);
                alert('Cannot play this song. The file might be too large or unavailable.');
            });
            playBtn.textContent = '⏸️';
            albumArt.classList.add('playing');
        }

        function pauseSong() {
            audio.pause();
            playBtn.textContent = '▶️';
            albumArt.classList.remove('playing');
        }

        playBtn.addEventListener('click', () => {
            if (audio.paused) {
                playSong();
            } else {
                pauseSong();
            }
        });

        prevBtn.addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + songs.length) % songs.length;
            loadSong(currentIndex);
            playSong();
        });

        nextBtn.addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % songs.length;
            loadSong(currentIndex);
            playSong();
        });

        audio.addEventListener('timeupdate', () => {
            const progressPercent = (audio.currentTime / audio.duration) * 100;
            progress.style.width = progressPercent + '%';
            
            currentTimeEl.textContent = formatTime(audio.currentTime);
            durationEl.textContent = formatTime(audio.duration);
        });

        progressBar.addEventListener('click', (e) => {
            const width = progressBar.clientWidth;
            const clickX = e.offsetX;
            const duration = audio.duration;
            
            audio.currentTime = (clickX / width) * duration;
        });

        volumeSlider.addEventListener('input', (e) => {
            audio.volume = e.target.value / 100;
        });

        audio.addEventListener('ended', () => {
            nextBtn.click();
        });

        audio.addEventListener('error', (e) => {
            console.error('Audio error:', e);
            pauseSong();
        });

        function formatTime(seconds) {
            if (isNaN(seconds)) return '0:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }

        // Set initial volume
        audio.volume = 0.7;

        // Load songs on page load
        loadSongs();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/songs')
def get_songs():
    try:
        # url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}?recursive=1"
        # response = requests.get(url, timeout=10)
        # response.raise_for_status()
        # data = response.json()
        
        # songs = []
        # for item in data.get("tree", []):
        #     if item["path"].endswith(".mp3"):
        #         filename = item["path"].split("/")[-1]
        #         song_title = filename.replace(".mp3", "").replace("_", " ").replace("-", " ")
                
        #         # Use jsDelivr CDN for better performance and reliability
        #         song_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USER}/{GITHUB_REPO}@{GITHUB_BRANCH}/{item['path']}"
                
        #         songs.append({
        #             "id": len(songs) + 1,
        #             "title": song_title,
        #             "artist": "Yagava Music",
        #             "cover": f"https://via.placeholder.com/300x300/667eea/ffffff?text={song_title[:1]}",
        #             "url": song_url
        #         })
        songs = [
    {
        "id": 1,
        "title": "File Example 5MG",
        "artist": "Yagava Music",
        "cover": "https://via.placeholder.com/300x300/667eea/ffffff?text=F",
        "url": "https://cdn.jsdelivr.net/gh/kathirvelyv/yagava@main/file_example_MP3_5MG.mp3"
    },
    {
        "id": 2,
        "title": "Another Song",
        "artist": "Yagava Music",
        "cover": "https://via.placeholder.com/300x300/764ba2/ffffff?text=A",
        "url": "https://cdn.jsdelivr.net/gh/kathirvelyv/yagava@main/another_song.mp3"
    }
]

        
        return jsonify(songs)
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5006)
