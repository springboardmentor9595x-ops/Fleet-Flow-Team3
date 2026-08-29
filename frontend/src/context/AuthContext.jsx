import { useEffect, useState } from "react";
import api from "../services/api";
import { AuthContext } from "./auth-context";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(
    localStorage.getItem("token") || ""
  );

  const [user, setUser] = useState(null);

  const loadCurrentUser = async () => {
    const response = await api.get("/auth/me");
    setUser(response.data);
    return response.data;
  };

  useEffect(() => {
    if (!token) {
      return;
    }

    const timer = window.setTimeout(() => {
      loadCurrentUser().catch(() => {
        localStorage.removeItem("token");
        setToken("");
        setUser(null);
      });
    }, 0);

    return () => window.clearTimeout(timer);
  }, [token]);

  // Signup
  const signup = async (userData) => {
    const response = await api.post("/auth/signup", userData);
    return response.data;
  };

  // Login
  const login = async (email, password) => {
    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const response = await api.post(
      "/auth/login",
      formData,
      {
        headers: {
          "Content-Type":
            "application/x-www-form-urlencoded",
        },
      }
    );

    const accessToken = response.data.access_token;

    localStorage.setItem("token", accessToken);

    setToken(accessToken);

    const currentUser = await loadCurrentUser();

    return { ...response.data, user: currentUser };
  };

  // Logout
  const logout = () => {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        signup,
        login,
        logout,
        loadCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
