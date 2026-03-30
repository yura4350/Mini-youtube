export interface VideoItem {
  id: string
  title: string
  description: string
  thumbnail: string
  videoUrl: string
  authorId: string
  authorName: string
  authorAvatar: string
  views: number
  likes: number
  uploadDate: string
  duration: string
  tags: string[]
  category: string
}

export interface VideoApiItem {
  id: string
  title: string
  description: string
  category: string
  tags: string[]
  thumbnail_url: string
  uploader_id: number
  original_filename: string
  saved_filename: string
  content_type: string
  size: number
  path: string
  views: number
  likes: number
  duration_seconds: number
  playback_url: string
  created_at?: string
}

const DEFAULT_THUMBNAIL =
  'https://images.unsplash.com/photo-1492619375914-88005aa9e8fb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080'

function formatDuration(totalSeconds: number): string {
  if (totalSeconds <= 0) return '00:00'
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

export function mapVideoApiItemToVideoItem(video: VideoApiItem): VideoItem {
  const createdAt = video.created_at || new Date().toISOString()

  return {
    id: video.id,
    title: video.title,
    description: video.description,
    thumbnail: video.thumbnail_url || DEFAULT_THUMBNAIL,
    videoUrl: video.playback_url,
    authorId: String(video.uploader_id),
    authorName: `Uploader ${video.uploader_id}`,
    authorAvatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
    views: video.views,
    likes: video.likes,
    uploadDate: createdAt,
    duration: formatDuration(video.duration_seconds),
    tags: video.tags,
    category: video.category,
  }
}
