import { useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";
import { Toaster } from "sonner";
import "./App.css";

import HomePage from "./pages/HomePage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import PublicSend from "./pages/PublicSend";
import { bootstrapAuthSession } from "./services/api";

function App() {
  useEffect(() => {
    void bootstrapAuthSession();
  }, []);

  return (
    <div className="app-root">
      <BrowserRouter>
        <Toaster position="top-right" richColors />
        <Routes>
          <Route
            path="/"
            element={<HomePage />}
          />

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/signup"
            element={<Signup />}
          />

          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/send/public/:token"
            element={<PublicSend />}
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;