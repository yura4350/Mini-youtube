import { useState } from "react";
import { useNavigate } from "react-router";
import { authService } from "../data/mock-data";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Upload as UploadIcon, Video, Image, X } from "lucide-react";
import { toast } from "sonner";

export function Upload() {
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [category, setCategory] = useState('Education');
  const [thumbnail, setThumbnail] = useState<File | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  if (!currentUser) {
    navigate('/login');
    return null;
  }

  const handleThumbnailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setThumbnail(e.target.files[0]);
    }
  };

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setVideo(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!video) {
      toast.error('Please select a video file');
      return;
    }

    if (!thumbnail) {
      toast.error('Please select a thumbnail image');
      return;
    }

    setLoading(true);

    // Simulate upload
    setTimeout(() => {
      setLoading(false);
      toast.success('Video uploaded successfully!');
      navigate('/profile');
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Card className="bg-[#1a1a1a] border-white/10">
        <CardHeader>
          <CardTitle className="text-2xl text-white flex items-center gap-2">
            <UploadIcon className="w-6 h-6 text-red-600" />
            Upload Video
          </CardTitle>
          <CardDescription className="text-gray-400">
            Share your content with the community
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Video File */}
            <div className="space-y-2">
              <Label className="text-white">Video File *</Label>
              <div className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center hover:border-red-500/50 transition-colors">
                {video ? (
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Video className="w-8 h-8 text-red-500" />
                      <div className="text-left">
                        <p className="text-white font-medium">{video.name}</p>
                        <p className="text-sm text-gray-400">
                          {(video.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => setVideo(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <Video className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-white mb-2">Click to upload or drag and drop</p>
                    <p className="text-sm text-gray-400">MP4, WebM, or MOV (max. 500MB)</p>
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleVideoChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </>
                )}
              </div>
            </div>

            {/* Thumbnail */}
            <div className="space-y-2">
              <Label className="text-white">Thumbnail *</Label>
              <div className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center hover:border-red-500/50 transition-colors">
                {thumbnail ? (
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Image className="w-8 h-8 text-red-500" />
                      <div className="text-left">
                        <p className="text-white font-medium">{thumbnail.name}</p>
                        <p className="text-sm text-gray-400">
                          {(thumbnail.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => setThumbnail(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <Image className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-white mb-2">Click to upload thumbnail</p>
                    <p className="text-sm text-gray-400">PNG, JPG (recommended: 1280x720)</p>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleThumbnailChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </>
                )}
              </div>
            </div>

            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title" className="text-white">Title *</Label>
              <Input
                id="title"
                type="text"
                placeholder="Enter video title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={100}
                className="bg-[#0f0f0f] border-white/20 text-white placeholder:text-gray-500"
              />
              <p className="text-xs text-gray-400">{title.length}/100</p>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-white">Description</Label>
              <Textarea
                id="description"
                placeholder="Tell viewers about your video"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                maxLength={5000}
                className="bg-[#0f0f0f] border-white/20 text-white placeholder:text-gray-500 resize-none"
              />
              <p className="text-xs text-gray-400">{description.length}/5000</p>
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category" className="text-white">Category</Label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 bg-[#0f0f0f] border border-white/20 rounded-md text-white"
              >
                <option value="Education">Education</option>
                <option value="Technology">Technology</option>
                <option value="Nature">Nature</option>
                <option value="Food">Food</option>
                <option value="Fitness">Fitness</option>
                <option value="Music">Music</option>
                <option value="Gaming">Gaming</option>
                <option value="Other">Other</option>
              </select>
            </div>

            {/* Tags */}
            <div className="space-y-2">
              <Label htmlFor="tags" className="text-white">Tags</Label>
              <Input
                id="tags"
                type="text"
                placeholder="Enter tags separated by commas (e.g., tutorial, tech, guide)"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="bg-[#0f0f0f] border-white/20 text-white placeholder:text-gray-500"
              />
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/')}
                className="flex-1 bg-transparent border-white/20 text-white hover:bg-white/10"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white"
              >
                {loading ? 'Uploading...' : 'Upload Video'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
