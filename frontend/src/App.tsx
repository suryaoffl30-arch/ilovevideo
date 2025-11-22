import { useState, useEffect } from 'react';
import { extractVideo, getProgress, getHistory, HistoryItem } from './api';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [progress, setProgress] = useState(0);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [taskId, setTaskId] = useState('');
  const [mediaFiles, setMediaFiles] = useState<any[]>([]);
  const [socialMediaResult, setSocialMediaResult] = useState<any>(null);
  const [youtubeQuality, setYoutubeQuality] = useState<string>('720p');
  const [youtubeFormat, setYoutubeFormat] = useState<string>('video');
  const [instagramFormat, setInstagramFormat] = useState<string>('video');
  const [playlistInfo, setPlaylistInfo] = useState<any>(null);
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
  const [showPlaylist, setShowPlaylist] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [showUpload, setShowUpload] = useState<boolean>(false);
  const [compressFile, setCompressFile] = useState<File | null>(null);
  const [showCompress, setShowCompress] = useState<boolean>(false);
  const [compressionQuality, setCompressionQuality] = useState<string>('medium');
  const [showLivestream, setShowLivestream] = useState<boolean>(false);
  const [livestreamUrl, setLivestreamUrl] = useState<string>('');
  const [livestreamStatus, setLivestreamStatus] = useState<any>(null);
  const [recordingId, setRecordingId] = useState<string>('');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingInfo, setRecordingInfo] = useState<any>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const items = await getHistory();
      setHistory(items);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleExtract = async () => {
    if (!url.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Starting extraction...');
    setProgress(0);
    setDownloadUrl('');

    try {
      // Start extraction
      const response = await extractVideo({ url, convert_hls: true, direct_url: false });
      
      if (response.task_id) {
        // Store task ID for proxy download
        setTaskId(response.task_id);
        // Poll for progress
        pollProgress(response.task_id);
      } else {
        setError('Failed to start extraction');
        setLoading(false);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Extraction failed');
      setLoading(false);
    }
  };

  const pollProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const progressData = await getProgress(taskId);
        
        setStatus(progressData.message);
        setProgress(progressData.progress);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          setDownloadUrl(progressData.download_url || '');
          // Get media files list if available
          if (progressData.media_files) {
            setMediaFiles(progressData.media_files);
          }
          loadHistory();
        } else if (progressData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          setError(progressData.message);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get progress');
      }
    }, 1000);

    // Timeout after 2 minutes
    setTimeout(() => {
      clearInterval(interval);
      if (loading) {
        setLoading(false);
        setError('Extraction timeout');
      }
    }, 120000);
  };

  const handleDownload = () => {
    if (taskId) {
      // Use proxy download with authentication
      const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
      const proxyUrl = `${apiBaseUrl}/api/proxy-download/${taskId}`;
      window.open(proxyUrl, '_blank');
    } else if (downloadUrl) {
      // Fallback to direct URL
      const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
      const fullUrl = downloadUrl.startsWith('http') 
        ? downloadUrl 
        : `${apiBaseUrl}${downloadUrl}`;
      
      window.open(fullUrl, '_blank');
    }
  };

  const handleInstagram = async () => {
    if (!url.trim()) {
      setError('Please enter an Instagram URL');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Extracting from Instagram...');
    setSocialMediaResult(null);

    try {
      const { downloadInstagram } = await import('./api');
      const result = await downloadInstagram(url, instagramFormat);
      setSocialMediaResult(result);
      const formatLabel = instagramFormat === 'audio' ? 'audio' : 'video';
      setStatus(`Instagram ${formatLabel} extracted!`);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Instagram extraction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleYouTube = async () => {
    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    // Check if it's a playlist URL
    if (url.includes('list=') || url.includes('/playlist')) {
      handlePlaylistFetch();
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Starting YouTube download...');
    setSocialMediaResult(null);
    setProgress(0);

    try {
      const { downloadYouTube } = await import('./api');
      const result = await downloadYouTube(url, youtubeQuality, youtubeFormat);
      
      // If we get a task_id, poll for progress
      if (result.task_id) {
        setTaskId(result.task_id);
        pollYouTubeProgress(result.task_id);
      } else {
        // Direct result (old format)
        setSocialMediaResult(result);
        setStatus('YouTube ready!');
        setLoading(false);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'YouTube extraction failed');
      setLoading(false);
    }
  };

  const handlePlaylistFetch = async () => {
    setLoading(true);
    setError('');
    setStatus('Fetching playlist information...');
    setPlaylistInfo(null);
    setSelectedVideos(new Set());

    try {
      const { getYouTubePlaylistInfo } = await import('./api');
      const info = await getYouTubePlaylistInfo(url);
      setPlaylistInfo(info);
      setShowPlaylist(true);
      setStatus(`Found ${info.video_count} videos in playlist`);
      // Select all by default
      setSelectedVideos(new Set(info.videos.map((v: any) => v.id)));
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to fetch playlist');
    } finally {
      setLoading(false);
    }
  };

  const handlePlaylistDownload = async () => {
    if (selectedVideos.size === 0) {
      setError('Please select at least one video');
      return;
    }

    setLoading(true);
    setError('');
    setStatus(`Starting download of ${selectedVideos.size} videos...`);
    setProgress(0);
    setShowPlaylist(false);

    try {
      const { downloadYouTubePlaylist } = await import('./api');
      const result = await downloadYouTubePlaylist(
        url,
        Array.from(selectedVideos),
        youtubeQuality,
        youtubeFormat
      );

      if (result.task_id) {
        setTaskId(result.task_id);
        pollPlaylistProgress(result.task_id);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Playlist download failed');
      setLoading(false);
    }
  };

  const pollPlaylistProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const progressData = await getProgress(taskId);
        
        setStatus(progressData.message);
        setProgress(progressData.progress);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          // Show results
          setSocialMediaResult({
            status: 'playlist_complete',
            downloads: progressData.downloads || [],
            completed: progressData.completed_videos || 0,
            failed: progressData.failed_videos || 0
          });
        } else if (progressData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          setError(progressData.message);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get download progress');
      }
    }, 2000);

    setTimeout(() => {
      clearInterval(interval);
      if (loading) {
        setLoading(false);
        setError('Download timeout');
      }
    }, 600000); // 10 minutes for playlist
  };

  const toggleVideoSelection = (videoId: string) => {
    const newSelection = new Set(selectedVideos);
    if (newSelection.has(videoId)) {
      newSelection.delete(videoId);
    } else {
      newSelection.add(videoId);
    }
    setSelectedVideos(newSelection);
  };

  const selectAllVideos = () => {
    if (playlistInfo) {
      setSelectedVideos(new Set(playlistInfo.videos.map((v: any) => v.id)));
    }
  };

  const deselectAllVideos = () => {
    setSelectedVideos(new Set());
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadFile(file);
    }
  };

  const handleCompressFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setCompressFile(file);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) {
      setError('Please select a video file');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Uploading video...');
    setProgress(0);
    setSocialMediaResult(null);

    try {
      const { uploadVideoForConversion } = await import('./api');
      const result = await uploadVideoForConversion(uploadFile);

      if (result.task_id) {
        setTaskId(result.task_id);
        setStatus(`Uploaded ${result.filename} (${result.file_size_mb} MB), converting...`);
        pollConversionProgress(result.task_id);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Upload failed');
      setLoading(false);
    }
  };

  const pollConversionProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const progressData = await getProgress(taskId);
        
        setStatus(progressData.message);
        setProgress(progressData.progress);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          setSocialMediaResult({
            status: 'conversion_complete',
            download_url: progressData.download_url,
            output_filename: progressData.output_filename,
            output_size_mb: progressData.output_size_mb
          });
          setUploadFile(null);
          setShowUpload(false);
        } else if (progressData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          setError(progressData.message);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get conversion progress');
      }
    }, 1000);

    setTimeout(() => {
      clearInterval(interval);
      if (loading) {
        setLoading(false);
        setError('Conversion timeout');
      }
    }, 300000); // 5 minutes
  };

  const handleVideoCompress = async () => {
    if (!compressFile) {
      setError('Please select a video file');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Uploading video for compression...');
    setProgress(0);
    setSocialMediaResult(null);

    try {
      const { uploadVideoForCompression } = await import('./api');
      const result = await uploadVideoForCompression(compressFile, compressionQuality);

      if (result.task_id) {
        setTaskId(result.task_id);
        setStatus(`Uploaded ${result.filename} (${result.file_size_mb} MB), compressing to ${result.quality}...`);
        pollCompressionProgress(result.task_id);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Upload failed');
      setLoading(false);
    }
  };

  const pollCompressionProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const progressData = await getProgress(taskId);
        
        setStatus(progressData.message);
        setProgress(progressData.progress);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          setSocialMediaResult({
            status: 'compression_complete',
            download_url: progressData.download_url,
            output_filename: progressData.output_filename,
            output_size_mb: progressData.output_size_mb,
            compression_ratio: progressData.compression_ratio,
            quality_description: progressData.quality_description
          });
          setCompressFile(null);
          setShowCompress(false);
        } else if (progressData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          setError(progressData.message);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get compression progress');
      }
    }, 1000);

    setTimeout(() => {
      clearInterval(interval);
      if (loading) {
        setLoading(false);
        setError('Compression timeout');
      }
    }, 600000); // 10 minutes for large videos
  };

  const getEstimatedSize = () => {
    if (!compressFile) return '0';
    const sizeMB = compressFile.size / (1024 * 1024);
    const reductions = { high: 0.6, medium: 0.4, low: 0.2 };
    return (sizeMB * reductions[compressionQuality as keyof typeof reductions]).toFixed(2);
  };

  const handleCheckLivestream = async () => {
    if (!livestreamUrl.trim()) {
      setError('Please enter a YouTube livestream URL');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Checking livestream status...');
    setLivestreamStatus(null);

    try {
      const { checkLivestreamStatus } = await import('./api');
      const result = await checkLivestreamStatus(livestreamUrl);
      setLivestreamStatus(result);
      setStatus(`Status: ${result.status}`);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to check livestream status');
    } finally {
      setLoading(false);
    }
  };

  const handleStartRecording = async () => {
    if (!livestreamUrl.trim()) {
      setError('Please enter a YouTube livestream URL');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Starting recording...');

    try {
      const { startRecording } = await import('./api');
      const result = await startRecording(livestreamUrl);
      setRecordingId(result.recording_id);
      setIsRecording(true);
      setStatus('Recording started!');
      
      // Start polling for recording status
      pollRecordingStatus(result.recording_id);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to start recording');
    } finally {
      setLoading(false);
    }
  };

  const handleStopRecording = async () => {
    if (!recordingId) {
      setError('No active recording');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Stopping recording...');

    try {
      const { stopRecording } = await import('./api');
      const result = await stopRecording(recordingId);
      setIsRecording(false);
      setStatus('Recording stopped!');
      setSocialMediaResult({
        status: 'recording_complete',
        filename: result.filename,
        file_size_mb: result.file_size_mb,
        download_url: result.download_url
      });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to stop recording');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadArchive = async () => {
    if (!livestreamUrl.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Downloading archived stream...');
    setProgress(0);

    try {
      const { downloadArchive } = await import('./api');
      const result = await downloadArchive(livestreamUrl);

      if (result.task_id) {
        setTaskId(result.task_id);
        pollArchiveProgress(result.task_id);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to download archive');
      setLoading(false);
    }
  };

  const pollRecordingStatus = async (recId: string) => {
    const interval = setInterval(async () => {
      try {
        const { getRecordingStatus } = await import('./api');
        const result = await getRecordingStatus(recId);
        
        setRecordingInfo(result);
        
        if (result.status === 'stopped') {
          clearInterval(interval);
          setIsRecording(false);
        }
      } catch (err) {
        // Recording might have been stopped
        clearInterval(interval);
      }
    }, 2000);

    // Store interval ID for cleanup
    return interval;
  };

  const pollArchiveProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const progressData = await getProgress(taskId);
        
        setStatus(progressData.message);
        setProgress(progressData.progress);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          setSocialMediaResult({
            status: 'archive_complete',
            filename: progressData.filename,
            file_size_mb: progressData.file_size_mb,
            download_url: progressData.download_url
          });
        } else if (progressData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          setError(progressData.message);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get download progress');
      }
    }, 2000);

    setTimeout(() => {
      clearInterval(interval);
      if (loading) {
        setLoading(false);
        setError('Download timeout');
      }
    }, 600000); // 10 minutes
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const pollYouTubeProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const progressData = await getProgress(taskId);
        
        setStatus(progressData.message);
        setProgress(progressData.progress);

        if (progressData.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          // Set the result with download info
          setSocialMediaResult({
            status: 'success',
            title: progressData.title,
            thumbnail: progressData.thumbnail,
            duration: progressData.duration,
            uploader: progressData.uploader,
            file_size_mb: progressData.file_size_mb,
            download_url: progressData.download_url
          });
        } else if (progressData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          setError(progressData.message);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get download progress');
      }
    }, 2000); // Poll every 2 seconds for YouTube (slower than regular extraction)

    // Timeout after 5 minutes (YouTube downloads can be large)
    setTimeout(() => {
      clearInterval(interval);
      if (loading) {
        setLoading(false);
        setError('Download timeout - video may be too large or slow connection');
      }
    }, 300000);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎥 Video Downloader</h1>
        <p>Extract videos using network request interception</p>
        <div className="instructions">
          <p><strong>How to use:</strong></p>
          <p>1. Open the video page in your browser</p>
          <p>2. Press F12 → Network tab → Filter by "Media"</p>
          <p>3. Play the video and copy the .mp4/.m3u8 URL</p>
          <p>4. Paste it here and check "Direct video URL"</p>
        </div>
      </header>

      <div className="card">
        <div className="input-group">
          <input
            type="text"
            value={url}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUrl(e.target.value)}
            placeholder="Enter webpage URL (e.g., https://example.com/video)"
            disabled={loading}
            onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleExtract()}
          />
          <button 
            onClick={handleExtract} 
            disabled={loading || !url.trim()}
            className="btn-primary"
          >
            {loading ? 'Extracting...' : 'Extract Video'}
          </button>
        </div>

        <div className="social-buttons">
          <div className="instagram-section">
            <button 
              onClick={handleInstagram} 
              disabled={loading || !url.trim()}
              className="btn-instagram"
            >
              📷 Instagram
            </button>
            <select 
              value={instagramFormat} 
              onChange={(e) => setInstagramFormat(e.target.value)}
              disabled={loading}
              className="format-selector"
            >
              <option value="video">🎬 Video</option>
              <option value="audio">🎵 Audio (Note)</option>
            </select>
          </div>
          <div className="youtube-section">
            <button 
              onClick={handleYouTube} 
              disabled={loading || !url.trim()}
              className="btn-youtube"
            >
              ▶️ YouTube
            </button>
            <select 
              value={youtubeFormat} 
              onChange={(e) => setYoutubeFormat(e.target.value)}
              disabled={loading}
              className="format-selector"
            >
              <option value="video">🎬 Video</option>
              <option value="audio">🎵 MP3</option>
            </select>
            {youtubeFormat === 'video' && (
              <select 
                value={youtubeQuality} 
                onChange={(e) => setYoutubeQuality(e.target.value)}
                disabled={loading}
                className="quality-selector"
              >
                <option value="360p">360p</option>
                <option value="480p">480p</option>
                <option value="720p">720p ⭐</option>
                <option value="1080p">1080p</option>
                <option value="best">Best</option>
              </select>
            )}
          </div>
        </div>

        <div className="upload-section">
          <button 
            onClick={() => setShowUpload(!showUpload)}
            disabled={loading}
            className="btn-upload"
          >
            🎵 Convert Video to MP3
          </button>
          <button 
            onClick={() => setShowCompress(!showCompress)}
            disabled={loading}
            className="btn-compress"
          >
            🗜️ Compress Video
          </button>
          <button 
            onClick={() => setShowLivestream(!showLivestream)}
            disabled={loading}
            className="btn-livestream"
          >
            🔴 Livestream Recorder
          </button>
        </div>

        {showUpload && !loading && (
          <div className="upload-box">
            <h3>Upload Video for Audio Extraction</h3>
            <p className="upload-info">Supported formats: MP4, AVI, MOV, MKV, WEBM, FLV, WMV</p>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              className="file-input"
            />
            {uploadFile && (
              <div className="file-selected">
                <p>Selected: {uploadFile.name} ({(uploadFile.size / (1024 * 1024)).toFixed(2)} MB)</p>
                <div className="upload-buttons">
                  <button onClick={handleFileUpload} className="btn-convert">
                    🎵 Convert to MP3
                  </button>
                  <button onClick={() => setUploadFile(null)} className="btn-cancel-upload">
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {showCompress && !loading && (
          <div className="compress-box">
            <h3>Compress Video</h3>
            <p className="compress-info">Reduce video file size while maintaining quality</p>
            
            <div className="quality-options">
              <label className="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value="high"
                  checked={compressionQuality === 'high'}
                  onChange={(e) => setCompressionQuality(e.target.value)}
                />
                <div className="quality-details">
                  <strong>High Quality</strong>
                  <span>720p, 2MB/s (~60% of original)</span>
                </div>
              </label>
              
              <label className="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value="medium"
                  checked={compressionQuality === 'medium'}
                  onChange={(e) => setCompressionQuality(e.target.value)}
                />
                <div className="quality-details">
                  <strong>Medium Quality ⭐</strong>
                  <span>480p, 1MB/s (~40% of original)</span>
                </div>
              </label>
              
              <label className="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value="low"
                  checked={compressionQuality === 'low'}
                  onChange={(e) => setCompressionQuality(e.target.value)}
                />
                <div className="quality-details">
                  <strong>Low Quality</strong>
                  <span>360p, 500KB/s (~20% of original)</span>
                </div>
              </label>
            </div>

            <input
              type="file"
              accept="video/*"
              onChange={handleCompressFileSelect}
              className="file-input"
            />
            
            {compressFile && (
              <div className="file-selected">
                <p>Selected: {compressFile.name} ({(compressFile.size / (1024 * 1024)).toFixed(2)} MB)</p>
                <p className="estimated-size">Estimated output: ~{getEstimatedSize()} MB</p>
                <div className="upload-buttons">
                  <button onClick={handleVideoCompress} className="btn-compress-action">
                    🗜️ Compress Video
                  </button>
                  <button onClick={() => setCompressFile(null)} className="btn-cancel-upload">
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {showLivestream && !loading && (
          <div className="livestream-box">
            <h3>🔴 YouTube Livestream Recorder</h3>
            <p className="livestream-info">Record live streams or download archived streams</p>
            
            <div className="livestream-input">
              <input
                type="text"
                value={livestreamUrl}
                onChange={(e) => setLivestreamUrl(e.target.value)}
                placeholder="Enter YouTube livestream URL"
                className="livestream-url-input"
              />
              <button onClick={handleCheckLivestream} className="btn-check-status">
                Check Status
              </button>
            </div>

            {livestreamStatus && (
              <div className={`status-box status-${livestreamStatus.status}`}>
                <h4>Stream Status: {livestreamStatus.status.replace(/_/g, ' ').toUpperCase()}</h4>
                {livestreamStatus.title && <p><strong>{livestreamStatus.title}</strong></p>}
                {livestreamStatus.uploader && <p>By: {livestreamStatus.uploader}</p>}
                
                <div className="livestream-actions">
                  {livestreamStatus.status === 'live_now' && !isRecording && (
                    <button onClick={handleStartRecording} className="btn-record">
                      ⏺️ Start Recording
                    </button>
                  )}
                  
                  {isRecording && (
                    <button onClick={handleStopRecording} className="btn-stop-record">
                      ⏹️ Stop Recording
                    </button>
                  )}
                  
                  {livestreamStatus.status === 'ended_and_archived' && (
                    <button onClick={handleDownloadArchive} className="btn-download-archive">
                      📥 Download Archive
                    </button>
                  )}
                  
                  {livestreamStatus.status === 'upcoming' && livestreamStatus.scheduled_time && (
                    <p className="scheduled-info">
                      Scheduled for: {new Date(livestreamStatus.scheduled_time * 1000).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            )}

            {isRecording && recordingInfo && (
              <div className="recording-progress">
                <div className="recording-indicator">
                  <span className="red-dot"></span>
                  <span>Recording...</span>
                </div>
                <p>Duration: {formatDuration(recordingInfo.duration_seconds)}</p>
                <p>File Size: {recordingInfo.file_size_mb} MB</p>
                <p>File: {recordingInfo.filename}</p>
              </div>
            )}
          </div>
        )}

        {loading && (
          <div className="status-section">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="status-text">{status}</p>
            <p className="progress-text">{progress}%</p>
          </div>
        )}

        {error && (
          <div className="error-box">
            <strong>Error:</strong> {error}
          </div>
        )}

        {showPlaylist && playlistInfo && !loading && (
          <div className="playlist-section">
            <h2>📋 Playlist: {playlistInfo.playlist_title}</h2>
            <p className="playlist-info">{playlistInfo.video_count} videos found</p>
            
            <div className="playlist-controls">
              <button onClick={selectAllVideos} className="btn-select">
                ✓ Select All
              </button>
              <button onClick={deselectAllVideos} className="btn-select">
                ✗ Deselect All
              </button>
              <span className="selected-count">
                {selectedVideos.size} selected
              </span>
            </div>

            <div className="video-list">
              {playlistInfo.videos.map((video: any) => (
                <div key={video.id} className="video-item">
                  <input
                    type="checkbox"
                    checked={selectedVideos.has(video.id)}
                    onChange={() => toggleVideoSelection(video.id)}
                    className="video-checkbox"
                  />
                  <img src={video.thumbnail} alt={video.title} className="video-thumb" />
                  <div className="video-details">
                    <h3 className="video-title">{video.title}</h3>
                    <p className="video-meta">
                      {video.duration ? `${Math.floor(video.duration / 60)}:${String(video.duration % 60).padStart(2, '0')}` : 'Unknown duration'}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="playlist-download-section">
              <button
                onClick={handlePlaylistDownload}
                disabled={selectedVideos.size === 0}
                className="btn-download-playlist"
              >
                📥 Download {selectedVideos.size} Video{selectedVideos.size !== 1 ? 's' : ''}
              </button>
              <button
                onClick={() => setShowPlaylist(false)}
                className="btn-cancel"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {socialMediaResult && !loading && socialMediaResult.status === 'playlist_complete' && (
          <div className="success-box">
            <p>✅ Playlist download completed!</p>
            <p className="playlist-stats">
              ✓ {socialMediaResult.completed} successful | ✗ {socialMediaResult.failed} failed
            </p>
            <div className="playlist-downloads">
              {socialMediaResult.downloads?.map((download: any, idx: number) => (
                <div key={idx} className={`download-item ${download.status}`}>
                  {download.status === 'success' ? (
                    <>
                      <span className="download-title">✓ {download.title}</span>
                      <button
                        onClick={() => {
                          const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                          window.open(`${apiBaseUrl}${download.download_url}`, '_blank');
                        }}
                        className="btn-download-small"
                      >
                        Download
                      </button>
                    </>
                  ) : (
                    <span className="download-title">✗ {download.video_id}: {download.error}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {socialMediaResult && !loading && socialMediaResult.status === 'conversion_complete' && (
          <div className="success-box">
            <p>✅ Audio extracted successfully!</p>
            <p className="conversion-info">
              Output: {socialMediaResult.output_filename} ({socialMediaResult.output_size_mb} MB)
            </p>
            <button
              onClick={() => {
                const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                window.open(`${apiBaseUrl}${socialMediaResult.download_url}`, '_blank');
              }}
              className="btn-download"
            >
              📥 Download MP3
            </button>
          </div>
        )}

        {socialMediaResult && !loading && socialMediaResult.status === 'recording_complete' && (
          <div className="success-box">
            <p>✅ Recording stopped successfully!</p>
            <p className="conversion-info">
              File: {socialMediaResult.filename} ({socialMediaResult.file_size_mb} MB)
            </p>
            <button
              onClick={() => {
                const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                window.open(`${apiBaseUrl}${socialMediaResult.download_url}`, '_blank');
              }}
              className="btn-download"
            >
              📥 Download Recording
            </button>
          </div>
        )}

        {socialMediaResult && !loading && socialMediaResult.status === 'archive_complete' && (
          <div className="success-box">
            <p>✅ Archive downloaded successfully!</p>
            <p className="conversion-info">
              File: {socialMediaResult.filename} ({socialMediaResult.file_size_mb} MB)
            </p>
            <button
              onClick={() => {
                const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                window.open(`${apiBaseUrl}${socialMediaResult.download_url}`, '_blank');
              }}
              className="btn-download"
            >
              📥 Download Archive
            </button>
          </div>
        )}

        {socialMediaResult && !loading && socialMediaResult.status === 'compression_complete' && (
          <div className="success-box">
            <p>✅ Video compressed successfully!</p>
            <p className="compression-stats">
              {socialMediaResult.quality_description} | {socialMediaResult.compression_ratio}% size reduction
            </p>
            <p className="conversion-info">
              Output: {socialMediaResult.output_filename} ({socialMediaResult.output_size_mb} MB)
            </p>
            <button
              onClick={() => {
                const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                window.open(`${apiBaseUrl}${socialMediaResult.download_url}`, '_blank');
              }}
              className="btn-download"
            >
              📥 Download Compressed Video
            </button>
          </div>
        )}

        {socialMediaResult && !loading && socialMediaResult.status !== 'playlist_complete' && socialMediaResult.status !== 'conversion_complete' && (
          <div className="success-box">
            <p>✅ {socialMediaResult.title || 'Video extracted successfully!'}</p>
            {socialMediaResult.thumbnail && (
              <img src={socialMediaResult.thumbnail} alt="Thumbnail" className="video-thumbnail" />
            )}
            {socialMediaResult.duration && (
              <p className="video-info">Duration: {Math.floor(socialMediaResult.duration / 60)}:{String(socialMediaResult.duration % 60).padStart(2, '0')}</p>
            )}
            {socialMediaResult.uploader && (
              <p className="video-info">Uploader: {socialMediaResult.uploader}</p>
            )}
            {socialMediaResult.file_size_mb && (
              <p className="video-info">File Size: {socialMediaResult.file_size_mb} MB</p>
            )}
            {socialMediaResult.status === 'success' && socialMediaResult.download_url && (
              <div className="download-buttons">
                <button 
                  onClick={() => {
                    const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                    const fullUrl = `${apiBaseUrl}${socialMediaResult.download_url}`;
                    window.open(fullUrl, '_blank');
                  }} 
                  className="btn-download"
                >
                  📥 Download Video (Merged)
                </button>
              </div>
            )}
            {socialMediaResult.requires_merge && (
              <p className="warning-text">⚠️ {socialMediaResult.message}</p>
            )}
            {!socialMediaResult.status && (
              <div className="download-buttons">
                {socialMediaResult.combined_download_url && (
                  <button onClick={() => window.open(socialMediaResult.combined_download_url, '_blank')} className="btn-download">
                    📥 Download Video ({socialMediaResult.video_quality || 'Best'})
                  </button>
                )}
                {socialMediaResult.video_only_url && !socialMediaResult.combined_download_url && (
                  <button onClick={() => window.open(socialMediaResult.video_only_url, '_blank')} className="btn-download">
                    🎬 Video Only ({socialMediaResult.video_only_quality || 'HD'})
                  </button>
                )}
                {socialMediaResult.audio_url && (
                  <button onClick={() => window.open(socialMediaResult.audio_url, '_blank')} className="btn-download">
                    🎵 Audio Only ({socialMediaResult.audio_quality || 'Best'})
                  </button>
                )}
                {socialMediaResult.video_url && !socialMediaResult.combined_download_url && (
                  <button onClick={() => window.open(socialMediaResult.video_url, '_blank')} className="btn-download">
                    Download Video
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {downloadUrl && !loading && (
          <div className="success-box">
            <p>✅ {mediaFiles.length > 0 ? `Found ${mediaFiles.length} media file(s)!` : 'Video extracted successfully!'}</p>
            
            {mediaFiles.length > 0 ? (
              <div className="media-files-list">
                {mediaFiles.map((media, idx) => {
                  const sizeMB = media.size ? (media.size / (1024 * 1024)).toFixed(2) : '?';
                  return (
                    <div key={idx} className="media-file-item">
                      <div className="media-info">
                        <strong>File {idx + 1}</strong>
                        <span>{media.extension} - {sizeMB} MB</span>
                      </div>
                      <div className="download-buttons">
                        <button 
                          onClick={() => {
                            const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
                            const proxyUrl = `${apiBaseUrl}/api/proxy-download/${taskId}/${idx}`;
                            window.open(proxyUrl, '_blank');
                          }} 
                          className="btn-download-small"
                        >
                          Download
                        </button>
                        <button 
                          onClick={() => {
                            navigator.clipboard.writeText(media.url);
                            alert('URL copied!');
                          }} 
                          className="btn-copy-small"
                        >
                          Copy URL
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="download-buttons">
                <button onClick={handleDownload} className="btn-download">
                  Download Video
                </button>
                <button onClick={() => {
                  navigator.clipboard.writeText(downloadUrl);
                  alert('Video URL copied to clipboard!');
                }} className="btn-copy">
                  Copy URL
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {history.length > 0 && (
        <div className="card history-section">
          <h2>Recent Downloads</h2>
          <div className="history-list">
            {history.map((item: HistoryItem, index: number) => (
              <div key={index} className="history-item">
                <div className="history-url">{item.url}</div>
                <div className="history-time">
                  {new Date(item.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <footer className="footer">
        <p>
          ⚠️ Legal Notice: This tool only extracts publicly accessible media files.
          Do not use for DRM-protected or copyrighted content without permission.
        </p>
      </footer>
    </div>
  );
}

export default App;
