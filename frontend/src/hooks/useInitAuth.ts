import { useEffect, useState } from "react";
import { refreshToken } from "../services/authService";
import { useAuthStore } from "../store/authStore";

interface StoredUser {
  user_id: string;
  email: string;
  username: string;
}

export function useInitAuth(): { isReady: boolean } {
  const [isReady, setIsReady] = useState<boolean>(false);
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    const storedRefreshToken: string | null = localStorage.getItem("ct_refresh_token");
    const storedUserRaw: string | null = localStorage.getItem("ct_user");

    if (!storedRefreshToken || !storedUserRaw) {
      clearAuth();
      setIsReady(true);
      return;
    }

    let storedUser: StoredUser;
    try {
      storedUser = JSON.parse(storedUserRaw) as StoredUser;
    } catch {
      clearAuth();
      setIsReady(true);
      return;
    }

    refreshToken(storedRefreshToken)
      .then((response) => {
        setAuth(storedUser, response.access_token, storedRefreshToken);
      })
      .catch(() => {
        clearAuth();
      })
      .finally(() => {
        setIsReady(true);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { isReady };
}