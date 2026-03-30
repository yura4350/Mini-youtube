import type { VideoItem } from '@/types/video'

export const categories = [
  'All',
  'Technology',
  'Education',
  'Nature',
  'Food',
  'Fitness',
  'Music',
  'Gaming',
]

export const mockVideos: VideoItem[] = [
  {
    id: '1',
    title: 'Professional Video Production Tips',
    description:
      'Learn the essential techniques for professional video production with industry-standard equipment.',
    thumbnail:
      'https://images.unsplash.com/photo-1654288891700-95f67982cbcc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video1.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 15420,
    likes: 823,
    uploadDate: '2026-03-20T14:30:00Z',
    duration: '12:45',
    tags: ['video', 'production', 'tutorial'],
    category: 'Education',
  },
  {
    id: '2',
    title: 'Modern Tech Workspace Setup',
    description:
      'A complete guide to creating the perfect productive workspace for remote work and content creation.',
    thumbnail:
      'https://images.unsplash.com/photo-1683701251422-912fe98f2b5e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video2.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 28350,
    likes: 1456,
    uploadDate: '2026-03-18T09:15:00Z',
    duration: '15:20',
    tags: ['tech', 'workspace', 'setup'],
    category: 'Technology',
  },
  {
    id: '3',
    title: 'Mountain Expeditions: Epic Journey',
    description: 'Join us on an incredible journey through breathtaking mountain landscapes.',
    thumbnail:
      'https://images.unsplash.com/photo-1600257729950-13a634d32697?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video3.mp4',
    authorId: '2',
    authorName: 'NatureFilms',
    authorAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
    views: 45780,
    likes: 3245,
    uploadDate: '2026-03-21T16:45:00Z',
    duration: '22:30',
    tags: ['nature', 'mountains', 'adventure'],
    category: 'Nature',
  },
  {
    id: '4',
    title: 'Perfect Pasta: Italian Cooking Masterclass',
    description: 'Learn authentic techniques from a professional chef and cook better pasta every time.',
    thumbnail:
      'https://images.unsplash.com/photo-1557573791-7ab7d3d68932?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video4.mp4',
    authorId: '3',
    authorName: 'CookingMaster',
    authorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    views: 32150,
    likes: 2187,
    uploadDate: '2026-03-19T11:00:00Z',
    duration: '18:15',
    tags: ['cooking', 'italian', 'recipe'],
    category: 'Food',
  },
  {
    id: '5',
    title: 'Full Body Workout Routine',
    description: 'Train your full body with a practical routine suitable for different fitness levels.',
    thumbnail:
      'https://images.unsplash.com/photo-1518310383802-640c2de311b2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video5.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 19820,
    likes: 945,
    uploadDate: '2026-03-17T08:30:00Z',
    duration: '25:00',
    tags: ['fitness', 'workout', 'health'],
    category: 'Fitness',
  },
  {
    id: '6',
    title: 'Live Concert Performance Highlights',
    description: 'Experience the best moments from an intense live concert performance.',
    thumbnail:
      'https://images.unsplash.com/photo-1767969457898-51d5e9cf81d2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video6.mp4',
    authorId: '2',
    authorName: 'NatureFilms',
    authorAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
    views: 56230,
    likes: 4321,
    uploadDate: '2026-03-22T19:00:00Z',
    duration: '08:45',
    tags: ['music', 'concert', 'live'],
    category: 'Music',
  },
  {
    id: '7',
    title: 'Pro Gaming Tournament Finals',
    description: 'Watch top-tier gameplay and final-round highlights from a major esports tournament.',
    thumbnail:
      'https://images.unsplash.com/photo-1652734935726-7afd52076e7f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video7.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 67890,
    likes: 5123,
    uploadDate: '2026-03-21T20:30:00Z',
    duration: '32:15',
    tags: ['gaming', 'esports', 'tournament'],
    category: 'Gaming',
  },
  {
    id: '8',
    title: 'Effective Study Techniques for Students',
    description: 'Practical strategies to learn faster and retain knowledge more effectively.',
    thumbnail:
      'https://images.unsplash.com/photo-1721468184185-214871ec4411?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    videoUrl: 'https://example.com/video8.mp4',
    authorId: '3',
    authorName: 'CookingMaster',
    authorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    views: 24560,
    likes: 1678,
    uploadDate: '2026-03-16T13:20:00Z',
    duration: '14:30',
    tags: ['education', 'study', 'learning'],
    category: 'Education',
  },
]

export function formatViews(views: number) {
  if (views >= 1_000_000) return `${(views / 1_000_000).toFixed(1)}M`
  if (views >= 1_000) return `${(views / 1_000).toFixed(1)}K`
  return String(views)
}

export function timeAgo(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const days = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return `${Math.floor(days / 365)} years ago`
}
