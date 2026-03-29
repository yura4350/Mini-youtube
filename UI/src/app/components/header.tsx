import { Link, useNavigate } from "react-router";
import { authService } from "../data/mock-data";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { 
  Video, 
  Search, 
  Bell, 
  Upload, 
  User, 
  LogOut,
  Menu,
  Settings
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { useState } from "react";

export function Header() {
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    authService.logout();
    navigate('/');
    window.location.reload();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-[#0f0f0f] border-b border-white/10">
      <div className="flex items-center justify-between px-4 py-3 gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <Video className="w-8 h-8 text-red-600" />
          <span className="text-xl font-semibold text-white">VideoHost</span>
        </Link>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
          <div className="relative">
            <Input
              type="text"
              placeholder="Search videos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#121212] border-white/20 text-white placeholder:text-gray-400 pr-10"
            />
            <button
              type="submit"
              className="absolute right-0 top-0 h-full px-4 text-gray-400 hover:text-white"
            >
              <Search className="w-5 h-5" />
            </button>
          </div>
        </form>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {currentUser ? (
            <>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/upload')}
                className="text-gray-300 hover:text-white"
              >
                <Upload className="w-5 h-5" />
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="text-gray-300 hover:text-white relative p-2 rounded-md hover:bg-white/10 transition-colors">
                    <Bell className="w-5 h-5" />
                    {currentUser.notifications.filter(n => !n.read).length > 0 && (
                      <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-red-600 text-white text-xs">
                        {currentUser.notifications.filter(n => !n.read).length}
                      </Badge>
                    )}
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-80 bg-[#282828] border-white/10 text-white">
                  <div className="px-3 py-2 text-sm font-semibold">Notifications</div>
                  <DropdownMenuSeparator className="bg-white/10" />
                  {currentUser.notifications.length === 0 ? (
                    <div className="px-3 py-4 text-sm text-gray-400">No notifications</div>
                  ) : (
                    currentUser.notifications.map(notif => (
                      <DropdownMenuItem
                        key={notif.id}
                        className="px-3 py-3 cursor-pointer hover:bg-white/10"
                        onClick={() => {
                          if (notif.videoId) {
                            navigate(`/video/${notif.videoId}`);
                          }
                        }}
                      >
                        <div className="flex flex-col gap-1">
                          <p className="text-sm">{notif.message}</p>
                          <p className="text-xs text-gray-400">
                            {new Date(notif.timestamp).toLocaleDateString()}
                          </p>
                        </div>
                      </DropdownMenuItem>
                    ))
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="rounded-full p-0 border-0 bg-transparent">
                    <Avatar className="w-8 h-8">
                      <AvatarImage src={currentUser.avatar} alt={currentUser.username} />
                      <AvatarFallback>{currentUser.username[0].toUpperCase()}</AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 bg-[#282828] border-white/10 text-white">
                  <DropdownMenuItem
                    onClick={() => navigate('/profile')}
                    className="cursor-pointer hover:bg-white/10"
                  >
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </DropdownMenuItem>
                  {currentUser.isAdmin && (
                    <DropdownMenuItem
                      onClick={() => navigate('/admin')}
                      className="cursor-pointer hover:bg-white/10"
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Admin Dashboard</span>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="cursor-pointer hover:bg-white/10 text-red-400"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Logout</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <>
              <Button
                variant="ghost"
                onClick={() => navigate('/login')}
                className="text-gray-300 hover:text-white"
              >
                Sign In
              </Button>
              <Button
                onClick={() => navigate('/register')}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Sign Up
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}