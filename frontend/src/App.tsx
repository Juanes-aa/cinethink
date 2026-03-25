import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import RegisterPage from "./pages/RegisterPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/dashboard"
          element={
            <div className="flex min-h-screen items-center justify-center bg-gray-950 text-white text-2xl">
              Dashboard — próximamente
            </div>
          }
        />
        <Route
          path="/login"
          element={
            <div className="flex min-h-screen items-center justify-center bg-gray-950 text-white text-2xl">
              Login — próximamente
            </div>
          }
        />
        <Route path="*" element={<Navigate to="/register" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
