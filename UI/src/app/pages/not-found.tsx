import { Link } from "react-router";
import { Button } from "../components/ui/button";
import { Video } from "lucide-react";

export function NotFound() {
  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4">
      <div className="text-center">
        <Video className="w-24 h-24 text-gray-600 mx-auto mb-6" />
        <h1 className="text-6xl font-bold text-white mb-4">404</h1>
        <h2 className="text-2xl text-gray-300 mb-6">Page Not Found</h2>
        <p className="text-gray-400 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/">
          <Button className="bg-red-600 hover:bg-red-700 text-white">
            Go Home
          </Button>
        </Link>
      </div>
    </div>
  );
}
