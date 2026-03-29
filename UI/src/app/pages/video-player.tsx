import { useParams, useNavigate } from "react-router";
import { mockVideos, authService } from "../data/mock-data";
import { Button } from "../components/ui/button";
import { VideoCard } from "../components/video-card";
import { 
  ThumbsUp, 
  Share2, 
  Bell, 
  MoreVertical,
  Eye,
  Calendar
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
import { Separator } from "../components/ui/separator";
import { Badge } from "../components/ui/badge";
import { useState } from "react";
import { toast } from "sonner";

export function VideoPlayer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();
  const video = mockVideos.find(v => v.id === id);
  const [isSubscribed, setIsSubscribed] = useState(
    currentUser?.subscribedTo.includes(video?.authorId || '') || false
  );
  const [liked, setLiked] = useState(false);

  if (!video) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl text-white mb-4">Video not found</h1>
        <Button onClick={() => navigate('/')} className="bg-red-600 hover:bg-red-700">
          Go Home
        </Button>
      </div>
    );
  }

  const relatedVideos = mockVideos.filter(v => 
    v.id !== video.id && (
      v.category === video.category || 
      v.tags.some(tag => video.tags.includes(tag))
    )
  ).slice(0, 4);

  const handleSubscribe = () => {
    if (!currentUser) {
      toast.error('Please login to subscribe');
      navigate('/login');
      return;
    }
    setIsSubscribed(!isSubscribed);
    toast.success(isSubscribed ? 'Unsubscribed' : 'Subscribed!');
  };

  const handleLike = () => {
    if (!currentUser) {
      toast.error('Please login to like videos');
      navigate('/login');
      return;
    }
    setLiked(!liked);
    toast.success(liked ? 'Like removed' : 'Video liked!');
  };

  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toString();
  };

  return (
    <div className="max-w-[1800px] mx-auto px-4 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Video Section */}
        <div className="lg:col-span-2 space-y-4">
          {/* Video Player */}
          <div className="aspect-video bg-black rounded-xl overflow-hidden">
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
              <img
                src={video.thumbnail}
                alt={video.title}
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Video Info */}
          <div className="space-y-4">
            <div>
              <h1 className="text-xl text-white mb-2">{video.title}</h1>
              <div className="flex flex-wrap items-center gap-2 text-sm text-gray-400">
                <span className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  {formatViews(video.views)} views
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {new Date(video.uploadDate).toLocaleDateString()}
                </span>
                <div className="flex gap-1 ml-auto">
                  {video.tags.map(tag => (
                    <Badge key={tag} variant="secondary" className="bg-white/10 text-gray-300">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={video.authorAvatar} alt={video.authorName} />
                  <AvatarFallback>{video.authorName[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-white font-medium">{video.authorName}</p>
                  <p className="text-xs text-gray-400">125K subscribers</p>
                </div>
              </div>
              <Button
                onClick={handleSubscribe}
                className={isSubscribed 
                  ? "bg-white/10 hover:bg-white/20 text-white" 
                  : "bg-red-600 hover:bg-red-700 text-white"
                }
              >
                {isSubscribed ? (
                  <>
                    <Bell className="w-4 h-4 mr-2" />
                    Subscribed
                  </>
                ) : (
                  'Subscribe'
                )}
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={handleLike}
                variant="secondary"
                className={`flex-1 ${liked ? 'bg-red-600/20 text-red-500' : 'bg-white/10 text-white'} hover:bg-white/20`}
              >
                <ThumbsUp className="w-4 h-4 mr-2" />
                {formatViews(video.likes + (liked ? 1 : 0))}
              </Button>
              <Button variant="secondary" className="flex-1 bg-white/10 text-white hover:bg-white/20">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
              <Button variant="secondary" size="icon" className="bg-white/10 text-white hover:bg-white/20">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </div>

            <Separator className="bg-white/10" />

            {/* Description */}
            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-white whitespace-pre-wrap">{video.description}</p>
            </div>

            {/* AI Summary */}
            <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-4 border border-purple-500/20">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
                <p className="text-sm font-medium text-purple-300">AI Summary</p>
              </div>
              <p className="text-sm text-gray-300">
                This video provides a comprehensive guide on {video.category.toLowerCase()} 
                topics, covering key techniques and best practices. The content is suitable 
                for both beginners and intermediate learners looking to improve their skills.
              </p>
            </div>
          </div>
        </div>

        {/* Related Videos */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Related Videos</h2>
          <div className="space-y-4">
            {relatedVideos.map(relatedVideo => (
              <VideoCard key={relatedVideo.id} video={relatedVideo} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
