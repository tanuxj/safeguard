import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  KeyRound,
  Lock,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

export default function HomePage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Lock,
      title: "Secure by default",
      description: "Store your passwords safely with a privacy-first setup.",
    },
    {
      icon: KeyRound,
      title: "Simple access",
      description: "Login quickly and manage credentials in one clear place.",
    },
    {
      icon: Zap,
      title: "Fast workflow",
      description: "Find and use your saved passwords without friction.",
    },
    {
      icon: ShieldCheck,
      title: "Built for reliability",
      description: "Designed to keep your credentials organized and protected.",
    },
  ];

  return (
    <main className="home-page">
      <div className="home-shell">
        <section className="hero-card">
          <span className="hero-badge">
            <Sparkles size={16} />
            Secure Password Manager
          </span>

          <h1 className="hero-title">
            Keep your passwords safe, accessible, and organized.
          </h1>

          <p className="hero-description">
            Safeguard helps you manage credentials with a clean experience and
            strong security-focused defaults.
          </p>

          <div className="hero-actions">
            <button
              onClick={() => navigate("/signup")}
              className="btn btn-primary"
            >
              Create account
              <ArrowRight size={16} />
            </button>

            <button
              onClick={() => navigate("/login")}
              className="btn btn-secondary"
            >
              Login
            </button>
          </div>
        </section>

        <section className="features-section">
          <div className="features-header">
            <h2>Why use Safeguard</h2>
            <p>Everything you need for better credential management.</p>
          </div>

          <ul className="features-grid">
            {features.map(({ icon: Icon, title, description }) => (
              <li key={title} className="feature-card">
                <div className="feature-icon">
                  <Icon size={18} />
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}