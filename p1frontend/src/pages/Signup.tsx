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

interface SignupForm {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState<SignupForm>({
    firstName: "",
    lastName: "",
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

  const handleSignup = async () => {
    if (!form.firstName || !form.lastName || !form.email || !form.password) {
      toast.error("All fields are required");
      return;
    }

    try {
      const res = await API.post(
        "/auth/register",
        form
      );

      const accessToken = res.data?.access_token as string | undefined;
      const refreshToken = res.data?.refresh_token as string | undefined;
      const message = res.data?.message as string | undefined;

      if (!accessToken || !refreshToken) {
        toast.error(message ?? "Signup failed");
        return;
      }

      setAccessToken(accessToken);
      setRefreshToken(refreshToken);
      toast.success(message ?? "Signup successful");
      navigate("/dashboard");
    } catch (error) {
      const axiosError = error as AxiosError<{ message?: string }>;
      const serverMessage = axiosError.response?.data?.message;
      toast.error(serverMessage ?? "Signup failed");
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-card">
        <h1>Signup</h1>
        <p>Create your account and start securing your credentials.</p>

        <input
          name="firstName"
          placeholder="First Name"
          onChange={handleChange}
        />

        <input
          name="lastName"
          placeholder="Last Name"
          onChange={handleChange}
        />

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

        <button className="btn btn-primary auth-btn" onClick={handleSignup}>
          Signup
        </button>

        <button
          className="btn btn-secondary auth-switch-btn"
          onClick={() => navigate("/login")}
        >
          Already have an account? Login
        </button>
      </div>
    </main>
  );
}