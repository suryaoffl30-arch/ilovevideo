# YouTube Playlist Download Feature ✅

## New Feature: Batch Download from Playlists

Users can now download multiple videos from YouTube playlists with selective video picking!

## How It Works

### 1. Paste Playlist URL
User pastes either:
- Direct playlist URL: `https://www.youtube.com/playlist?list=PLAYLIST_ID`
- Video URL from playlist: `https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID`

### 2. Fetch Playlist Info
- System detects playlist URL automatically
- Fetches all videos in the playlist using yt-dlp
- Displays video list with thumbnails, titles, and durations

### 3. Select Videos
- All videos selected by default
- User can:
  - ✓ Select All
  - ✗ Deselect All
  - Toggle individual videos with checkboxes
- Shows count of selected videos

### 4. Download
- Click "📥 Download X Videos"
- Downloads happen **one by one** (sequential)
- Real-time progress tracking
- Shows current video being downloaded
- Displays completed/failed counts

### 5. Results
- Shows list of all downloads
- ✓ Successful downloads with download buttons
- ✗ Failed downloads with error messages
- Summary: X successful, Y failed

## Features

### Backend
✅ **Playlist Info Endpoint** - `/api/youtube/playlist/info`
- Fetches all videos in playlist
- Returns video metadata (title, duration, thumbnail, etc.)
- Uses `yt-dlp --flat-playlist`

✅ **Batch Download Endpoint** - `/api/youtube/playlist/download`
- Accepts comma-separated video IDs
- Downloads sequentially (one at a time)
- Progress tracking for entire batch
- Individual video status tracking

✅ **Sequential Processing**
- Downloads videos one by one
- Prevents overwhelming the system
- Better progress tracking
- Handles failures gracefully

### Frontend
✅ **Automatic Detection** - Detects playlist URLs
✅ **Video List UI** - Shows all videos with checkboxes
✅ **Bulk Selection** - Select/Deselect all buttons
✅ **Progress Tracking** - Real-time updates during batch download
✅ **Results Display** - Shows success/failure for each video
✅ **Individual Downloads** - Download button for each successful video

## UI Components

### Playlist Selection Screen
```
📋 Playlist: [Playlist Name]
[X videos found]

[✓ Select All] [✗ Deselect All]     [5 selected]

┌─────────────────────────────────────────┐
│ ☑ [Thumbnail] Video Title 1             │
│              Duration: 5:30              │
├─────────────────────────────────────────┤
│ ☑ [Thumbnail] Video Title 2             │
│              Duration: 10:15             │
└─────────────────────────────────────────┘

[📥 Download 5 Videos] [Cancel]
```

### Download Progress
```
Downloading video 3/5...
Progress: 60%
```

### Results Screen
```
✅ Playlist download completed!
✓ 4 successful | ✗ 1 failed

✓ Video Title 1 [Download]
✓ Video Title 2 [Download]
✗ Video Title 3: HTTP Error 403
✓ Video Title 4 [Download]
✓ Video Title 5 [Download]
```

## API Endpoints

### Get Playlist Info
```http
POST /api/youtube/playlist/info
Content-Type: application/json

{
  "url": "https://www.youtube.com/playlist?list=PLAYLIST_ID"
}
```

Response:
```json
{
  "playlist_title": "My Playlist",
  "video_count": 10,
  "videos": [
    {
      "id": "VIDEO_ID",
      "title": "Video Title",
      "url": "https://www.youtube.com/watch?v=VIDEO_ID",
      "duration": 300,
      "thumbnail": "https://...",
      "uploader": "Channel Name"
    }
  ]
}
```

### Download Playlist
```http
POST /api/youtube/playlist/download?video_ids=ID1,ID2,ID3&quality=720p&format_type=video
Content-Type: application/json

{
  "url": "https://www.youtube.com/playlist?list=PLAYLIST_ID"
}
```

Response:
```json
{
  "status": "downloading",
  "message": "Playlist download started (3 videos)",
  "task_id": "...",
  "total_videos": 3
}
```

### Check Progress
```http
GET /api/progress/{task_id}
```

Response (in progress):
```json
{
  "status": "downloading",
  "progress": 60,
  "message": "Downloading video 3/5...",
  "total_videos": 5,
  "completed_videos": 2,
  "failed_videos": 0,
  "current_video": "VIDEO_ID"
}
```

Response (completed):
```json
{
  "status": "completed",
  "progress": 100,
  "message": "Playlist download completed! 4 successful, 1 failed",
  "completed_videos": 4,
  "failed_videos": 1,
  "downloads": [
    {
      "video_id": "ID1",
      "title": "Video 1",
      "download_url": "/api/youtube/file/youtube_xxx.mp4",
      "file_size_mb": "50.5",
      "status": "success"
    },
    {
      "video_id": "ID2",
      "status": "failed",
      "error": "HTTP Error 403"
    }
  ]
}
```

## Technical Details

### Sequential Download
Videos are downloaded **one at a time** to:
- Avoid overwhelming the system
- Prevent rate limiting
- Better resource management
- Clearer progress tracking

### Error Handling
- Individual video failures don't stop the batch
- Failed videos are tracked separately
- Error messages provided for each failure
- Successful downloads still available

### Progress Tracking
- Overall progress (0-100%)
- Current video being downloaded
- Completed count
- Failed count
- Individual video status

## Use Cases

### Educational Content
- Download entire course playlists
- Save lecture series
- Archive tutorials

### Music Playlists
- Download music collections
- Save albums
- Archive concerts

### Podcast Series
- Download podcast episodes
- Save interview series
- Archive shows

## Limitations

### Current
- Sequential download only (not parallel)
- No resume capability
- No playlist refresh
- Downloads to server (not direct to user)

### YouTube Restrictions
- Some playlists may be private
- Age-restricted content may fail
- Very large playlists (100+ videos) may timeout
- Rate limiting may occur

## Future Enhancements

Could add:
- Parallel downloads (2-3 at a time)
- Resume failed downloads
- Playlist refresh/update
- Download queue management
- Estimated time remaining
- Bandwidth throttling
- Direct-to-user streaming
- Playlist monitoring (auto-download new videos)

## Example Usage

1. **Go to** http://localhost:3000
2. **Paste** playlist URL
3. **Click** "▶️ YouTube" button
4. **Review** video list
5. **Select** videos to download (or keep all selected)
6. **Choose** quality and format
7. **Click** "📥 Download X Videos"
8. **Wait** for downloads to complete
9. **Download** individual videos from results

## Test Results

✅ Successfully fetched playlist with 2 videos
✅ Displayed video list with metadata
✅ Selection/deselection working
✅ Sequential download working
✅ Progress tracking accurate
✅ Results display correct

## Notes

- Playlist detection is automatic
- All videos selected by default for convenience
- Downloads are sequential to avoid issues
- Each video can be downloaded individually after batch completes
- Failed videos don't affect successful ones
- Perfect for downloading entire courses, series, or collections!
