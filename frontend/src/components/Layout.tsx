import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export default function Layout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const navigate = useNavigate();

  function handleLogout(): void {
    clearAuth();
    navigate("/login");
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-xl font-bold tracking-tight text-indigo-400">
            CineThink
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/search"
              className="text-sm font-medium text-gray-300 transition hover:text-white"
            >
              Buscar
            </Link>

            <Link
              to="/library"
              className="text-sm font-medium text-gray-300 transition hover:text-white"
            >
              Mi biblioteca
            </Link>

            <Link
              to="/history"
              className="text-sm font-medium text-gray-300 transition hover:text-white"
            >
              Historial
            </Link>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-red-500"
            >
              Cerrar sesión
            </button>
          </div>
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
