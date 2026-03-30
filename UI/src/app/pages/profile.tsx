import { useState } from "react";
import { useNavigate } from "react-router";
import { authService, mockVideos } from "../data/mock-data";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
import { VideoCard } from "../components/video-card";
import { User, Video, Bell, Eye, Heart, Settings } from "lucide-react";
import { toast } from "sonner";

export function Profile() {
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();
  const [editMode, setEditMode] = useState(false);
  const [username, setUsername] = useState(currentUser?.username || '');
  const [bio, setBio] = useState(currentUser?.bio || '');

  if (!currentUser) {
    navigate('/login');
    return null;
  }

  const userVideos = mockVideos.filter(v => v.authorId === currentUser.id);
  const subscribedVideos = mockVideos.filter(v => 
    currentUser.subscribedTo.includes(v.authorId)
  );

  const handleSaveProfile = () => {
    authService.updateUser({ username, bio });
    setEditMode(false);
    toast.success('Profile updated successfully!');
  };

  const totalViews = userVideos.reduce((sum, v) => sum + v.views, 0);
  const totalLikes = userVideos.reduce((sum, v) => sum + v.likes, 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Profile Header */}
      <Card className="bg-[#1a1a1a] border-white/10 mb-8">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-6">
            <Avatar className="w-32 h-32 shrink-0">
              <AvatarImage src={currentUser.avatar} alt={currentUser.username} />
              <AvatarFallback className="text-3xl">{currentUser.username[0].toUpperCase()}</AvatarFallback>
            </Avatar>

            <div className="flex-1 space-y-4">
              {editMode ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-white">Username</Label>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="bg-[#0f0f0f] border-white/20 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bio" className="text-white">Bio</Label>
                    <Textarea
                      id="bio"
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      rows={3}
                      className="bg-[#0f0f0f] border-white/20 text-white resize-none"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleSaveProfile} className="bg-red-600 hover:bg-red-700">
                      Save Changes
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setEditMode(false)}
                      className="bg-transparent border-white/20 text-white hover:bg-white/10"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div>
                    <h1 className="text-2xl font-semibold text-white mb-2">{currentUser.username}</h1>
                    <p className="text-gray-400">{currentUser.email}</p>
                    {currentUser.bio && (
                      <p className="text-gray-300 mt-2">{currentUser.bio}</p>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-6 text-sm">
                    <div className="flex items-center gap-2">
                      <Video className="w-5 h-5 text-red-500" />
                      <span className="text-white">{userVideos.length} videos</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Eye className="w-5 h-5 text-blue-500" />
                      <span className="text-white">{totalViews.toLocaleString()} views</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Heart className="w-5 h-5 text-pink-500" />
                      <span className="text-white">{totalLikes.toLocaleString()} likes</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Bell className="w-5 h-5 text-yellow-500" />
                      <span className="text-white">{currentUser.subscribedTo.length} subscriptions</span>
                    </div>
                  </div>

                  <Button
                    onClick={() => setEditMode(true)}
                    variant="outline"
                    className="bg-transparent border-white/20 text-white hover:bg-white/10"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Edit Profile
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content Tabs */}
      <Tabs defaultValue="videos" className="space-y-6">
        <TabsList className="bg-[#1a1a1a] border border-white/10">
          <TabsTrigger value="videos" className="data-[state=active]:bg-red-600 data-[state=active]:text-white">
            My Videos
          </TabsTrigger>
          <TabsTrigger value="subscriptions" className="data-[state=active]:bg-red-600 data-[state=active]:text-white">
            Subscriptions
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-red-600 data-[state=active]:text-white">
            Notifications
          </TabsTrigger>
        </TabsList>

        <TabsContent value="videos">
          {userVideos.length === 0 ? (
            <Card className="bg-[#1a1a1a] border-white/10">
              <CardContent className="py-12 text-center">
                <Video className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 mb-4">You haven't uploaded any videos yet</p>
                <Button onClick={() => navigate('/upload')} className="bg-red-600 hover:bg-red-700">
                  Upload Your First Video
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8">
              {userVideos.map(video => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="subscriptions">
          {subscribedVideos.length === 0 ? (
            <Card className="bg-[#1a1a1a] border-white/10">
              <CardContent className="py-12 text-center">
                <Bell className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 mb-4">You're not subscribed to any channels yet</p>
                <Button onClick={() => navigate('/')} className="bg-red-600 hover:bg-red-700">
                  Discover Channels
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8">
              {subscribedVideos.map(video => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="notifications">
          <Card className="bg-[#1a1a1a] border-white/10">
            <CardHeader>
              <CardTitle className="text-white">Recent Notifications</CardTitle>
            </CardHeader>
            <CardContent>
              {currentUser.notifications.length === 0 ? (
                <div className="py-8 text-center">
                  <Bell className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No notifications yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {currentUser.notifications.map(notif => (
                    <div
                      key={notif.id}
                      className={`p-4 rounded-lg ${notif.read ? 'bg-white/5' : 'bg-red-600/10'} border border-white/10`}
                    >
                      <p className="text-white text-sm">{notif.message}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(notif.timestamp).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
