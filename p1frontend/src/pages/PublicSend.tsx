import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import API from "../services/api";

interface PublicSendData {
  send_type?: "text" | "file";
  name: string;
  text_to_share: string;
  file_name?: string | null;
  file_size?: number | null;
  deletion_date: string;
  who_can_view: string;
}

export default function PublicSend() {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sendData, setSendData] = useState<PublicSendData | null>(null);
  const [passwordInput, setPasswordInput] = useState("");
  const [submittedPassword, setSubmittedPassword] = useState("");
  const [needsPassword, setNeedsPassword] = useState(false);

  useEffect(() => {
    async function loadSend() {
      if (!token) {
        setError("Invalid share link");
        setLoading(false);
        return;
      }

      try {
        const res = await API.get(`/send/public-data/${token}`, {
          params: submittedPassword ? { password: submittedPassword } : undefined,
        });
        if (res.data?.message && !res.data?.text_to_share) {
          if (res.data.message === "password required" || res.data.message === "invalid password") {
            setNeedsPassword(true);
          }
          setError(res.data.message as string);
          setSendData(null);
        } else {
          setNeedsPassword(false);
          setSendData(res.data as PublicSendData);
          setError("");
        }
      } catch {
        setError("Unable to load shared send");
      } finally {
        setLoading(false);
      }
    }

    void loadSend();
  }, [token, submittedPassword]);

  return (
    <main className="public-send-page">
      <section className="public-send-card">
        <h1 className="send-title">Shared Send</h1>

        {loading ? <p className="hero-description">Loading...</p> : null}

        {!loading && error ? <p className="hero-description">{error}</p> : null}

        {!loading && needsPassword ? (
          <div className="public-send-content">
            <label className="vaults-label" htmlFor="public-send-password">
              Password
            </label>
            <input
              id="public-send-password"
              type="password"
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              placeholder="Enter password"
            />
            <button
              className="btn btn-primary"
              onClick={() => setSubmittedPassword(passwordInput)}
            >
              Unlock
            </button>
          </div>
        ) : null}

        {!loading && sendData ? (
          <div className="public-send-content">
            <p className="send-subheading">{sendData.name}</p>
            {sendData.send_type === "file" ? (
              <>
                <p className="send-help-text">File: {sendData.file_name}</p>
                <p className="send-help-text">
                  Size: {sendData.file_size ? `${Math.round(sendData.file_size / 1024)} KB` : "Unknown"}
                </p>
                <a
                  className="btn btn-primary"
                  href={`${import.meta.env.VITE_API_BASE_URL}/send/public-file/${token}${submittedPassword ? `?password=${encodeURIComponent(submittedPassword)}` : ""}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download file
                </a>
              </>
            ) : (
              <p className="public-send-text">{sendData.text_to_share}</p>
            )}
            <p className="send-help-text">
              Deletion date: {new Date(sendData.deletion_date).toLocaleString()}
            </p>
            <p className="send-help-text">Who can view: {sendData.who_can_view}</p>
          </div>
        ) : null}
      </section>
    </main>
  );
}
