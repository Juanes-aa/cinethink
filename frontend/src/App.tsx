import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import RegisterPage from "./pages/RegisterPage";
import LoginPage from "./pages/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import { useInitAuth } from "./hooks/useInitAuth";
import { useAuthStore } from "./store/authStore";

function DashboardPage() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const navigate = useNavigate();

  function handleLogout(): void {
    clearAuth();
    navigate("/login");
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-950 text-white">
      <h1 className="text-2xl">Dashboard — próximamente</h1>
      <button
        onClick={handleLogout}
        className="rounded-lg bg-red-600 px-6 py-2.5 font-semibold text-white transition hover:bg-red-500"
      >
        Cerrar sesión
      </button>
    </div>
  );
}

function AppRoutes() {
  const { isReady } = useInitAuth();

  if (!isReady) {
    return null;
  }

  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="*" element={<Navigate to="/register" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
