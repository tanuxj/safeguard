import { useState } from "react";
import type { ChangeEvent } from "react";
import type { AxiosError } from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import API from "../services/api";
import {
  setAccessToken,
  setRefreshToken,
} from "../services/authStorage";

interface LoginForm {
  email: string;
  password: string;
}

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
  });

  const handleChange = (
    e: ChangeEvent<HTMLInputElement>
  ) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleLogin = async () => {
    if (!form.email || !form.password) {
      toast.error("Email and password are required");
      return;
    }

    try {
      const res = await API.post(
        "/auth/login",
        form
      );

      const accessToken = res.data?.access_token as string | undefined;
      const refreshToken = res.data?.refresh_token as string | undefined;
      const message = res.data?.message as string | undefined;

      if (!accessToken || !refreshToken) {
        toast.error(message ?? "Login failed");
        return;
      }

      setAccessToken(accessToken);
      setRefreshToken(refreshToken);
      toast.success(message ?? "Login successful");
      navigate("/dashboard");
    } catch (error) {
      const axiosError = error as AxiosError<{ message?: string }>;
      const serverMessage = axiosError.response?.data?.message;
      toast.error(serverMessage ?? "Login failed");
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-card">
        <h1>Login</h1>
        <p>Welcome back. Enter your credentials to continue.</p>

        <input
          name="email"
          placeholder="Email"
          onChange={handleChange}
        />

        <input
          name="password"
          type="password"
          placeholder="Password"
          onChange={handleChange}
        />

        <button className="btn btn-primary auth-btn" onClick={handleLogin}>
          Login
        </button>

        <button
          className="btn btn-secondary auth-switch-btn"
          onClick={() => navigate("/signup")}
        >
          Need an account? Signup
        </button>
      </div>
    </main>
  );
}