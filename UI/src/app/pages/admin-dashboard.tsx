import { useNavigate } from "react-router";
import { authService, mockVideos, mockUsers } from "../data/mock-data";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { 
  Users, 
  Video, 
  Eye, 
  Activity, 
  TrendingUp,
  AlertCircle,
  Trash2,
  Ban,
  CheckCircle
} from "lucide-react";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { toast } from "sonner";

export function AdminDashboard() {
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();

  if (!currentUser?.isAdmin) {
    navigate('/');
    return null;
  }

  const totalUsers = mockUsers.length;
  const totalVideos = mockVideos.length;
  const totalViews = mockVideos.reduce((sum, v) => sum + v.views, 0);
  const avgViewsPerVideo = Math.floor(totalViews / totalVideos);

  const handleBanUser = (userId: string) => {
    toast.success(`User ${userId} has been banned`);
  };

  const handleDeleteVideo = (videoId: string) => {
    toast.success(`Video ${videoId} has been deleted`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-white mb-2">Admin Dashboard</h1>
        <p className="text-gray-400">Monitor and manage your platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-600/20 to-blue-900/20 border-blue-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-300 mb-1">Total Users</p>
                <p className="text-3xl font-bold text-white">{totalUsers}</p>
                <p className="text-xs text-blue-400 mt-1">+12% this month</p>
              </div>
              <Users className="w-12 h-12 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-600/20 to-purple-900/20 border-purple-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-300 mb-1">Total Videos</p>
                <p className="text-3xl font-bold text-white">{totalVideos}</p>
                <p className="text-xs text-purple-400 mt-1">+8% this month</p>
              </div>
              <Video className="w-12 h-12 text-purple-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-600/20 to-green-900/20 border-green-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-300 mb-1">Total Views</p>
                <p className="text-3xl font-bold text-white">{totalViews.toLocaleString()}</p>
                <p className="text-xs text-green-400 mt-1">+25% this month</p>
              </div>
              <Eye className="w-12 h-12 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-600/20 to-orange-900/20 border-orange-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-300 mb-1">Avg Views/Video</p>
                <p className="text-3xl font-bold text-white">{avgViewsPerVideo.toLocaleString()}</p>
                <p className="text-xs text-orange-400 mt-1">+5% this month</p>
              </div>
              <TrendingUp className="w-12 h-12 text-orange-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="bg-[#1a1a1a] border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-500" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">API Server</span>
              <Badge className="bg-green-600 text-white">
                <CheckCircle className="w-3 h-3 mr-1" />
                Online
              </Badge>
            </div>
            <Separator className="bg-white/10" />
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Database</span>
              <Badge className="bg-green-600 text-white">
                <CheckCircle className="w-3 h-3 mr-1" />
                Online
              </Badge>
            </div>
            <Separator className="bg-white/10" />
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Storage</span>
              <Badge className="bg-green-600 text-white">
                <CheckCircle className="w-3 h-3 mr-1" />
                Online
              </Badge>
            </div>
            <Separator className="bg-white/10" />
            <div className="flex items-center justify-between">
              <span className="text-gray-300">CDN</span>
              <Badge className="bg-green-600 text-white">
                <CheckCircle className="w-3 h-3 mr-1" />
                Online
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#1a1a1a] border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">New user registered: TechExplorer</p>
                  <p className="text-xs text-gray-400">2 hours ago</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-green-500 mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">Video uploaded: Mountain Expeditions</p>
                  <p className="text-xs text-gray-400">3 hours ago</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">System update completed</p>
                  <p className="text-xs text-gray-400">5 hours ago</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">High traffic detected on /video/3</p>
                  <p className="text-xs text-gray-400">6 hours ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* User Management */}
      <Card className="bg-[#1a1a1a] border-white/10 mb-8">
        <CardHeader>
          <CardTitle className="text-white">User Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mockUsers.filter(u => !u.isAdmin).map(user => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="flex items-center gap-3">
                  <img
                    src={user.avatar}
                    alt={user.username}
                    className="w-10 h-10 rounded-full"
                  />
                  <div>
                    <p className="text-white font-medium">{user.username}</p>
                    <p className="text-sm text-gray-400">{user.email}</p>
                  </div>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleBanUser(user.id)}
                  className="bg-red-600/20 text-red-400 hover:bg-red-600/30"
                >
                  <Ban className="w-4 h-4 mr-2" />
                  Ban
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Video Management */}
      <Card className="bg-[#1a1a1a] border-white/10">
        <CardHeader>
          <CardTitle className="text-white">Recent Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mockVideos.slice(0, 5).map(video => (
              <div
                key={video.id}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="flex items-center gap-3 flex-1">
                  <img
                    src={video.thumbnail}
                    alt={video.title}
                    className="w-20 h-12 object-cover rounded"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{video.title}</p>
                    <p className="text-sm text-gray-400">
                      {video.authorName} • {video.views.toLocaleString()} views
                    </p>
                  </div>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDeleteVideo(video.id)}
                  className="bg-red-600/20 text-red-400 hover:bg-red-600/30 shrink-0"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
