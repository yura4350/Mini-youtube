import { mockVideos } from "../data/mock-data";
import { VideoCard } from "../components/video-card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";

export function Home() {
  const categories = ['All', 'Technology', 'Education', 'Nature', 'Food', 'Fitness', 'Music', 'Gaming'];

  return (
    <div className="max-w-[1800px] mx-auto px-4 py-6">
      {/* Category Tabs */}
      <Tabs defaultValue="All" className="mb-8">
        <TabsList className="bg-transparent border-b border-white/10 rounded-none w-full justify-start gap-4 overflow-x-auto">
          {categories.map(category => (
            <TabsTrigger
              key={category}
              value={category}
              className="data-[state=active]:bg-white/10 data-[state=active]:text-white text-gray-400 rounded-lg px-4"
            >
              {category}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="All" className="mt-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8">
            {mockVideos.map(video => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        </TabsContent>

        {categories.slice(1).map(category => (
          <TabsContent key={category} value={category} className="mt-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8">
              {mockVideos
                .filter(video => video.category === category)
                .map(video => (
                  <VideoCard key={video.id} video={video} />
                ))}
            </div>
            {mockVideos.filter(video => video.category === category).length === 0 && (
              <div className="text-center text-gray-400 py-12">
                No videos in this category yet.
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
