import { Outlet } from "react-router";
import { Header } from "../components/header";

export function Root() {
  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      <Header />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
