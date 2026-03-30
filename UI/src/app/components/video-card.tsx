import { Link } from "react-router";
import { Video } from "../data/mock-data";
import { Eye, Clock } from "lucide-react";

interface VideoCardProps {
  video: Video;
}

export function VideoCard({ video }: VideoCardProps) {
  const formatViews = (views: number) => {
    if (views >= 1000000) {
      return `${(views / 1000000).toFixed(1)}M`;
    } else if (views >= 1000) {
      return `${(views / 1000).toFixed(1)}K`;
    }
    return views.toString();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  return (
    <Link to={`/video/${video.id}`} className="group">
      <div className="space-y-3">
        {/* Thumbnail */}
        <div className="relative aspect-video rounded-xl overflow-hidden bg-[#282828]">
          <img
            src={video.thumbnail}
            alt={video.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
            {video.duration}
          </div>
        </div>

        {/* Info */}
        <div className="flex gap-3">
          <img
            src={video.authorAvatar}
            alt={video.authorName}
            className="w-9 h-9 rounded-full shrink-0"
          />
          <div className="flex-1 min-w-0">
            <h3 className="text-white font-medium line-clamp-2 group-hover:text-gray-300 transition-colors">
              {video.title}
            </h3>
            <p className="text-sm text-gray-400 mt-1">{video.authorName}</p>
            <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                {formatViews(video.views)} views
              </span>
              <span>•</span>
              <span>{formatDate(video.uploadDate)}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
