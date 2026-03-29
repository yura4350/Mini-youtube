import { createBrowserRouter } from "react-router";
import { Root } from "./pages/root";
import { Home } from "./pages/home";
import { Login } from "./pages/login";
import { Register } from "./pages/register";
import { VideoPlayer } from "./pages/video-player";
import { Upload } from "./pages/upload";
import { Profile } from "./pages/profile";
import { AdminDashboard } from "./pages/admin-dashboard";
import { Search } from "./pages/search";
import { NotFound } from "./pages/not-found";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: Home },
      { path: "login", Component: Login },
      { path: "register", Component: Register },
      { path: "video/:id", Component: VideoPlayer },
      { path: "upload", Component: Upload },
      { path: "profile", Component: Profile },
      { path: "admin", Component: AdminDashboard },
      { path: "search", Component: Search },
      { path: "*", Component: NotFound }
    ]
  }
]);
