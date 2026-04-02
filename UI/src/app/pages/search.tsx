import { useSearchParams, useNavigate } from "react-router";
import { mockVideos } from "../data/mock-data";
import { VideoCard } from "../components/video-card";
import { Search as SearchIcon } from "lucide-react";
import { Card } from "../components/ui/card";

export function Search() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';

  const searchResults = mockVideos.filter(video => {
    const searchLower = query.toLowerCase();
    return (
      video.title.toLowerCase().includes(searchLower) ||
      video.description.toLowerCase().includes(searchLower) ||
      video.tags.some(tag => tag.toLowerCase().includes(searchLower)) ||
      video.authorName.toLowerCase().includes(searchLower) ||
      video.category.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl text-white mb-2">
          Search results for: <span className="text-red-500">"{query}"</span>
        </h1>
        <p className="text-gray-400">{searchResults.length} videos found</p>
      </div>

      {searchResults.length === 0 ? (
        <Card className="bg-[#1a1a1a] border-white/10 p-12 text-center">
          <SearchIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h2 className="text-xl text-white mb-2">No results found</h2>
          <p className="text-gray-400 mb-6">
            Try searching for something else or browse our categories
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Go Home
          </button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8">
          {searchResults.map(video => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      )}
    </div>
  );
}
