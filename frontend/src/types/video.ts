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
