// Mock data for the video hosting platform

export interface User {
  id: string;
  username: string;
  email: string;
  bio: string;
  avatar: string;
  isAdmin: boolean;
  subscribedTo: string[];
  notifications: Notification[];
}

export interface Video {
  id: string;
  title: string;
  description: string;
  thumbnail: string;
  videoUrl: string;
  authorId: string;
  authorName: string;
  authorAvatar: string;
  views: number;
  likes: number;
  uploadDate: string;
  duration: string;
  tags: string[];
  category: string;
}

export interface Notification {
  id: string;
  type: 'new_video' | 'subscription' | 'chat' | 'system';
  message: string;
  timestamp: string;
  read: boolean;
  videoId?: string;
}

export const mockUsers: User[] = [
  {
    id: '1',
    username: 'TechExplorer',
    email: 'tech@example.com',
    bio: 'Tech enthusiast sharing the latest in technology',
    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    isAdmin: false,
    subscribedTo: ['2', '3'],
    notifications: [
      {
        id: 'n1',
        type: 'new_video',
        message: 'NatureFilms uploaded a new video: Mountain Expeditions',
        timestamp: '2026-03-22T10:30:00Z',
        read: false,
        videoId: '3'
      }
    ]
  },
  {
    id: '2',
    username: 'NatureFilms',
    email: 'nature@example.com',
    bio: 'Documenting the beauty of nature',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
    isAdmin: false,
    subscribedTo: ['1'],
    notifications: []
  },
  {
    id: '3',
    username: 'CookingMaster',
    email: 'cooking@example.com',
    bio: 'Professional chef sharing recipes',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    isAdmin: false,
    subscribedTo: ['2'],
    notifications: []
  },
  {
    id: 'admin',
    username: 'admin',
    email: 'admin@example.com',
    bio: 'Platform Administrator',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
    isAdmin: true,
    subscribedTo: [],
    notifications: []
  }
];

export const mockVideos: Video[] = [
  {
    id: '1',
    title: 'Professional Video Production Tips',
    description: 'Learn the essential techniques for professional video production with industry-standard equipment.',
    thumbnail: 'https://images.unsplash.com/photo-1654288891700-95f67982cbcc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWRlbyUyMHByb2R1Y3Rpb24lMjBjYW1lcmF8ZW58MXx8fHwxNzc0MTk0NjY0fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video1.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 15420,
    likes: 823,
    uploadDate: '2026-03-20T14:30:00Z',
    duration: '12:45',
    tags: ['video', 'production', 'tutorial'],
    category: 'Education'
  },
  {
    id: '2',
    title: 'Modern Tech Workspace Setup',
    description: 'A complete guide to creating the perfect productive workspace for remote work and content creation.',
    thumbnail: 'https://images.unsplash.com/photo-1683701251422-912fe98f2b5e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWNobm9sb2d5JTIwd29ya3NwYWNlJTIwY29tcHV0ZXJ8ZW58MXx8fHwxNzc0Mjc1NjU5fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video2.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 28350,
    likes: 1456,
    uploadDate: '2026-03-18T09:15:00Z',
    duration: '15:20',
    tags: ['tech', 'workspace', 'setup'],
    category: 'Technology'
  },
  {
    id: '3',
    title: 'Mountain Expeditions: Epic Journey',
    description: 'Join us on an incredible journey through the most breathtaking mountain landscapes.',
    thumbnail: 'https://images.unsplash.com/photo-1600257729950-13a634d32697?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuYXR1cmUlMjBsYW5kc2NhcGUlMjBtb3VudGFpbnN8ZW58MXx8fHwxNzc0MjU1MjgxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video3.mp4',
    authorId: '2',
    authorName: 'NatureFilms',
    authorAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
    views: 45780,
    likes: 3245,
    uploadDate: '2026-03-21T16:45:00Z',
    duration: '22:30',
    tags: ['nature', 'mountains', 'adventure'],
    category: 'Nature'
  },
  {
    id: '4',
    title: 'Perfect Pasta: Italian Cooking Masterclass',
    description: 'Learn authentic Italian cooking techniques from a professional chef. Make perfect pasta every time!',
    thumbnail: 'https://images.unsplash.com/photo-1557573791-7ab7d3d68932?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb29raW5nJTIwZm9vZCUyMGtpdGNoZW58ZW58MXx8fHwxNzc0MjU5MDkwfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video4.mp4',
    authorId: '3',
    authorName: 'CookingMaster',
    authorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    views: 32150,
    likes: 2187,
    uploadDate: '2026-03-19T11:00:00Z',
    duration: '18:15',
    tags: ['cooking', 'italian', 'recipe'],
    category: 'Food'
  },
  {
    id: '5',
    title: 'Full Body Workout Routine',
    description: 'Get fit with this comprehensive full body workout routine. Perfect for all fitness levels!',
    thumbnail: 'https://images.unsplash.com/photo-1518310383802-640c2de311b2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmaXRuZXNzJTIwd29ya291dCUyMGV4ZXJjaXNlfGVufDF8fHx8MTc3NDI0NTYwMnww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video5.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 19820,
    likes: 945,
    uploadDate: '2026-03-17T08:30:00Z',
    duration: '25:00',
    tags: ['fitness', 'workout', 'health'],
    category: 'Fitness'
  },
  {
    id: '6',
    title: 'Live Concert Performance Highlights',
    description: 'Experience the energy of live music with these incredible concert performance highlights.',
    thumbnail: 'https://images.unsplash.com/photo-1767969457898-51d5e9cf81d2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtdXNpYyUyMGNvbmNlcnQlMjBwZXJmb3JtYW5jZXxlbnwxfHx8fDE3NzQyMjg3MDN8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video6.mp4',
    authorId: '2',
    authorName: 'NatureFilms',
    authorAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
    views: 56230,
    likes: 4321,
    uploadDate: '2026-03-22T19:00:00Z',
    duration: '8:45',
    tags: ['music', 'concert', 'live'],
    category: 'Music'
  },
  {
    id: '7',
    title: 'Pro Gaming Tournament Finals',
    description: 'Watch the most intense gaming moments from the championship finals. Incredible gameplay!',
    thumbnail: 'https://images.unsplash.com/photo-1652734935726-7afd52076e7f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxnYW1pbmclMjBlc3BvcnRzJTIwcGxheWVyfGVufDF8fHx8MTc3NDI4MjQ4M3ww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video7.mp4',
    authorId: '1',
    authorName: 'TechExplorer',
    authorAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    views: 67890,
    likes: 5123,
    uploadDate: '2026-03-21T20:30:00Z',
    duration: '32:15',
    tags: ['gaming', 'esports', 'tournament'],
    category: 'Gaming'
  },
  {
    id: '8',
    title: 'Effective Study Techniques for Students',
    description: 'Discover proven study methods that will help you learn faster and retain more information.',
    thumbnail: 'https://images.unsplash.com/photo-1721468184185-214871ec4411?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlZHVjYXRpb24lMjBsZWFybmluZyUyMHN0dWRlbnR8ZW58MXx8fHwxNzc0MTg0NDcyfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    videoUrl: 'https://example.com/video8.mp4',
    authorId: '3',
    authorName: 'CookingMaster',
    authorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    views: 24560,
    likes: 1678,
    uploadDate: '2026-03-16T13:20:00Z',
    duration: '14:30',
    tags: ['education', 'study', 'learning'],
    category: 'Education'
  }
];

// Auth state management (simple in-memory store)
let currentUser: User | null = null;

export const authService = {
  login: (email: string, password: string): User | null => {
    // Simple mock authentication
    const user = mockUsers.find(u => u.email === email);
    if (user && password.length > 0) {
      currentUser = user;
      localStorage.setItem('currentUser', JSON.stringify(user));
      return user;
    }
    return null;
  },
  
  register: (username: string, email: string, password: string): User | null => {
    // Simple mock registration
    const newUser: User = {
      id: Date.now().toString(),
      username,
      email,
      bio: '',
      avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
      isAdmin: false,
      subscribedTo: [],
      notifications: []
    };
    mockUsers.push(newUser);
    currentUser = newUser;
    localStorage.setItem('currentUser', JSON.stringify(newUser));
    return newUser;
  },
  
  logout: () => {
    currentUser = null;
    localStorage.removeItem('currentUser');
  },
  
  getCurrentUser: (): User | null => {
    if (currentUser) return currentUser;
    const stored = localStorage.getItem('currentUser');
    if (stored) {
      currentUser = JSON.parse(stored);
      return currentUser;
    }
    return null;
  },
  
  updateUser: (updates: Partial<User>): User | null => {
    if (!currentUser) return null;
    currentUser = { ...currentUser, ...updates };
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    return currentUser;
  }
};
