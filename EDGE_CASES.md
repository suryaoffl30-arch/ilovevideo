# Edge Cases and Limitations

## Supported Scenarios

### ✅ What Works

1. **Direct Video Links**
   - Simple HTML5 video players
   - Direct .mp4, .webm file URLs
   - Example: Personal blogs, simple video hosting

2. **HLS Streams**
   - .m3u8 playlist files
   - Adaptive bitrate streaming
   - Example: Many live streaming platforms

3. **Progressive Download**
   - Videos loaded via standard HTTP
   - No encryption or DRM
   - Example: Educational sites, news sites

4. **Embedded Players**
   - iframe-embedded videos (if source is accessible)
   - Custom JavaScript players
   - Example: Vimeo embeds, custom players

## Unsupported Scenarios

### ❌ What Doesn't Work

1. **DRM-Protected Content**
   - Netflix, Disney+, Hulu, HBO Max
   - Widevine/PlayReady/FairPlay encryption
   - **Reason:** Encrypted streams require decryption keys
   - **Detection:** Basic domain check implemented

2. **Authentication-Required Content**
   - Login-protected videos
   - Subscription-only content
   - **Reason:** No credentials provided to browser
   - **Workaround:** Manual cookie injection (not implemented)

3. **DASH Streams (Partial Support)**
   - .mpd manifest files
   - Separate audio/video tracks
   - **Reason:** Requires merging separate streams
   - **Status:** Not implemented (FFmpeg could handle this)

4. **WebRTC Streams**
   - Real-time peer-to-peer video
   - Live conference calls
   - **Reason:** No persistent URL to extract
   - **Status:** Not feasible with current approach

5. **Blob URLs**
   - blob:https://example.com/...
   - In-memory video data
   - **Reason:** Temporary, browser-specific URLs
   - **Workaround:** Could intercept before blob creation

## Edge Cases by Category

### 1. Network Issues

#### Slow Loading Sites
```
Problem: Page takes too long to load
Solution: Increase PLAYWRIGHT_TIMEOUT
Default: 30000ms (30 seconds)
Recommended: 60000ms for slow sites
```

#### Network Errors
```
Problem: Connection timeout, DNS failure
Behavior: Returns 500 error with message
User Action: Retry or check URL
```

#### Rate Limiting
```
Problem: Site blocks automated requests
Symptoms: 429 Too Many Requests, CAPTCHA
Solution: Add delays, rotate user agents (not implemented)
```

### 2. Video Detection Issues

#### No Media Found
```
Problem: Extractor returns empty result
Possible Causes:
  - Video loads after page load (lazy loading)
  - Video in iframe from different domain
  - Video uses blob URLs
  - JavaScript-heavy site needs more time
  
Solutions:
  - Increase wait time after page load
  - Scroll page to trigger lazy load (implemented)
  - Check browser console for actual requests
```

#### Multiple Videos Detected
```
Problem: Page has multiple videos
Current Behavior: Returns first video found
Improvement: Could return all videos and let user choose
```

#### Wrong Video Extracted
```
Problem: Extracts ad instead of main video
Current Solution: Exclude patterns for known ad domains
Patterns: doubleclick.net, googlesyndication, analytics
Limitation: New ad networks may not be filtered
```

### 3. Format Issues

#### Unsupported Formats
```
Supported: .mp4, .webm, .m3u8, .ts, .mov, .avi, .mkv, .flv
Unsupported: .wmv, .f4v, proprietary formats

Behavior: May still extract URL but download might fail
```

#### HLS Conversion Failures
```
Problem: FFmpeg fails to convert .m3u8
Possible Causes:
  - FFmpeg not installed
  - Encrypted HLS (AES-128)
  - Invalid playlist
  - Network issues during download
  
Fallback: Returns original .m3u8 URL
User Action: Use VLC or other HLS-capable player
```

#### Corrupted Files
```
Problem: Downloaded file won't play
Causes:
  - Incomplete download
  - Unsupported codec
  - Server-side issues
  
Solution: Retry extraction, try different player
```

### 4. Size and Performance

#### Large Files
```
Problem: Video exceeds MAX_VIDEO_SIZE_MB
Default Limit: 500 MB
Behavior: May timeout or fail during conversion
Solution: Increase limit or disable conversion
```

#### Memory Issues
```
Problem: Server runs out of memory
Causes:
  - Multiple concurrent extractions
  - Large video conversions
  - Browser memory leaks
  
Solution: Limit concurrent tasks, restart workers
```

#### Disk Space
```
Problem: Downloads directory fills up
Solution: Implement cleanup job for old files
Recommendation: Delete files older than 24 hours
```

### 5. Browser-Specific Issues

#### JavaScript Errors
```
Problem: Page JavaScript crashes
Behavior: Playwright continues but may miss video
Solution: Ignore JavaScript errors (implemented)
```

#### Popup Blockers
```
Problem: Site requires popup interaction
Behavior: May block video load
Solution: Disable popup blockers in Playwright (implemented)
```

#### Cookie Consent
```
Problem: Cookie banner blocks content
Current: No automatic handling
Improvement: Could add auto-accept logic
```

### 6. Legal and Ethical

#### Copyright Violations
```
Warning: User is responsible for legal compliance
Tool Purpose: Extract publicly accessible URLs
Not For: Bypassing paywalls, DRM, or access controls
```

#### Terms of Service
```
Warning: Some sites prohibit automated access
Examples: YouTube ToS, social media platforms
Risk: IP bans, legal action
Recommendation: Respect robots.txt and ToS
```

#### Privacy Concerns
```
Issue: Extracting private/unlisted videos
Behavior: Tool will extract if URL is accessible
Ethics: Don't share private content without permission
```

## Testing Edge Cases

### Test Cases Implemented

```python
# Backend tests
test_extract_drm_protected_url()      # Returns 400
test_extract_unsupported_site()       # Returns clear error
test_extractor_no_media_found()       # Returns None
test_media_url_filtering()            # Validates filtering
test_exclude_patterns()               # Validates ad exclusion
test_hls_conversion_failure()         # Handles FFmpeg errors
```

### Manual Test Scenarios

1. **Simple Video Page**
   ```
   URL: https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4
   Expected: Direct .mp4 download
   ```

2. **HLS Stream**
   ```
   URL: https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8
   Expected: Conversion to .mp4
   ```

3. **Slow Loading Site**
   ```
   URL: Site with 10+ second load time
   Expected: Timeout or success with increased timeout
   ```

4. **Multiple Videos**
   ```
   URL: Page with 5 videos
   Expected: Returns first non-ad video
   ```

5. **Protected Content**
   ```
   URL: https://netflix.com/watch/12345
   Expected: 400 error with DRM message
   ```

## Error Messages

### User-Friendly Errors

```python
# DRM Protected
"This site uses DRM protection. Cannot extract protected content."

# No Media Found
"No media files found on this page"

# Timeout
"Extraction timeout - page took too long to load"

# Invalid URL
"Please enter a valid URL"

# Conversion Failed
"Video found but conversion failed. Try downloading the original URL."

# Server Error
"Extraction failed: [technical details]"
```

## Workarounds and Solutions

### For Users

1. **Video Not Found**
   - Wait longer (increase timeout)
   - Try direct video URL instead of page URL
   - Check if video requires login
   - Inspect Network tab manually to verify video exists

2. **Conversion Fails**
   - Disable HLS conversion
   - Download .m3u8 and use VLC player
   - Try different video quality/format

3. **Slow Extraction**
   - Use direct video URL if known
   - Try during off-peak hours
   - Check internet connection

### For Developers

1. **Add New Format Support**
   ```python
   MEDIA_EXTENSIONS.add('.new_format')
   MEDIA_MIME_TYPES.add('video/new-type')
   ```

2. **Add New Ad Domain**
   ```python
   EXCLUDE_PATTERNS.append(r'new-ad-domain\.com')
   ```

3. **Increase Timeout**
   ```python
   PLAYWRIGHT_TIMEOUT=60000  # 60 seconds
   ```

4. **Handle Blob URLs**
   ```python
   # Intercept before blob creation
   page.on('response', capture_video_data)
   ```

## Known Limitations Summary

| Limitation | Impact | Workaround |
|------------|--------|------------|
| DRM content | Cannot extract | None (by design) |
| Login required | Cannot access | Manual cookie injection |
| Blob URLs | May miss video | Intercept earlier |
| Large files | Timeout/memory | Increase limits |
| Rate limiting | Blocked requests | Add delays |
| Multiple videos | Only first returned | Return all (future) |
| DASH streams | Not supported | Add DASH support |
| WebRTC | Not supported | Not feasible |

## Future Improvements

1. **Better Video Detection**
   - Wait for video element to appear
   - Check multiple video qualities
   - Handle lazy loading better

2. **Format Support**
   - DASH (.mpd) streams
   - Fragmented MP4 (fMP4)
   - Better blob URL handling

3. **User Experience**
   - Show all detected videos
   - Preview thumbnails
   - Quality selection

4. **Reliability**
   - Retry logic
   - Better error messages
   - Progress percentage accuracy

5. **Performance**
   - Browser instance pooling
   - Parallel extractions
   - Caching

## Reporting Issues

If you encounter an edge case not covered here:

1. Check browser DevTools Network tab manually
2. Verify video is not DRM-protected
3. Note the exact error message
4. Provide the URL (if public)
5. Include browser console logs
6. Report via GitHub Issues

## Conclusion

This tool works best with:
- ✅ Simple video hosting sites
- ✅ Educational content
- ✅ News sites
- ✅ Personal blogs
- ✅ Non-DRM streaming

This tool does NOT work with:
- ❌ Netflix, Disney+, etc.
- ❌ Login-required content
- ❌ WebRTC streams
- ❌ Heavily protected content

Always respect copyright laws and terms of service.
