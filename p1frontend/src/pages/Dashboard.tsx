import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { clearTokens } from "../services/authStorage";
import API from "../services/api";

interface NewSendForm {
  name: string;
  textToShare: string;
  deletionDate: string;
  whoCanView: "Anyone with the link" | "Anyone with a password set by you";
  accessPassword: string;
  limitViews: string;
  privateNote: string;
  uploadFile: File | null;
}

interface SendListItem {
  id: string;
  name: string;
  send_type?: "text" | "file";
  deletion_date: string;
  share_token: string;
  share_link: string;
}

interface SendContentPreview {
  id?: string;
  name: string;
  send_type?: "text" | "file";
  text_to_share: string;
  file_name?: string | null;
  file_size?: number | null;
  deletion_date: string;
  who_can_view: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [showNewSendForm, setShowNewSendForm] = useState(false);
  const [sendMode, setSendMode] = useState<"text" | "file">("text");
  const [generatedShareLink, setGeneratedShareLink] = useState("");
  const [mySends, setMySends] = useState<SendListItem[]>([]);
  const [sendSearch, setSendSearch] = useState("");
  const [selectedSend, setSelectedSend] = useState<SendContentPreview | null>(null);
  const [newSendForm, setNewSendForm] = useState<NewSendForm>({
    name: "",
    textToShare: "",
    deletionDate: "",
    whoCanView: "Anyone with the link",
    accessPassword: "",
    limitViews: "",
    privateNote: "",
    uploadFile: null,
  });

  const handleLogout = () => {
    clearTokens();
    navigate("/login");
  };

  const loadMySends = async () => {
    try {
      const response = await API.get("/send/mine");
      setMySends((response.data?.sends as SendListItem[] | undefined) ?? []);
    } catch {
      setMySends([]);
    }
  };

  useEffect(() => {
    void loadMySends();
  }, []);

  const handleSendInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setNewSendForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setNewSendForm((prev) => ({
      ...prev,
      uploadFile: e.target.files?.[0] ?? null,
    }));
  };

  const handleCreateSend = async () => {
    if (!newSendForm.name || !newSendForm.deletionDate) {
      toast.error("Name and deletion date are required");
      return;
    }
    if (sendMode === "text" && !newSendForm.textToShare) {
      toast.error("Text to share is required");
      return;
    }
    if (sendMode === "file" && !newSendForm.uploadFile) {
      toast.error("Upload file is required");
      return;
    }
    if (newSendForm.whoCanView === "Anyone with a password set by you" && !newSendForm.accessPassword) {
      toast.error("Password is required for protected sends");
      return;
    }

    try {
      const basePayload = {
        name: newSendForm.name,
        deletion_date: new Date(newSendForm.deletionDate).toISOString(),
        who_can_view: newSendForm.whoCanView,
        access_password:
          newSendForm.whoCanView === "Anyone with a password set by you"
            ? newSendForm.accessPassword
            : null,
        limit_views: newSendForm.limitViews ? Number(newSendForm.limitViews) : null,
        private_note: newSendForm.privateNote || null,
      };

      const response =
        sendMode === "text"
          ? await API.post("/send/text", {
              ...basePayload,
              text_to_share: newSendForm.textToShare,
            })
          : await API.post(
              "/send/file",
              (() => {
                const formData = new FormData();
                formData.append("name", basePayload.name);
                formData.append("deletion_date", basePayload.deletion_date);
                formData.append("who_can_view", basePayload.who_can_view);
                if (basePayload.access_password) {
                  formData.append("access_password", basePayload.access_password);
                }
                if (basePayload.limit_views) {
                  formData.append("limit_views", String(basePayload.limit_views));
                }
                if (basePayload.private_note) {
                  formData.append("private_note", basePayload.private_note);
                }
                formData.append("upload", newSendForm.uploadFile as File);
                return formData;
              })(),
              { headers: { "Content-Type": "multipart/form-data" } }
            );

      const shareLink = response.data?.share_link as string | undefined;
      if (!shareLink) {
        toast.error(response.data?.message ?? "Failed to create send");
        return;
      }

      setGeneratedShareLink(shareLink);
      setShowNewSendForm(false);
      setNewSendForm({
        name: "",
        textToShare: "",
        deletionDate: "",
        whoCanView: "Anyone with the link",
        accessPassword: "",
        limitViews: "",
        privateNote: "",
        uploadFile: null,
      });
      await loadMySends();
      toast.success("Send created successfully");
    } catch (error: unknown) {
      const message =
        typeof error === "object" &&
        error !== null &&
        "response" in error &&
        typeof (error as { response?: { data?: { message?: string } } }).response?.data?.message ===
          "string"
          ? (error as { response?: { data?: { message?: string } } }).response?.data?.message
          : "Failed to create send";

      toast.error(message);
    }
  };

  const handleOpenSend = async (shareToken: string) => {
    try {
      const response = await API.get(`/send/public-data/${shareToken}`);
      if (response.data?.message && !response.data?.text_to_share) {
        toast.error(response.data.message as string);
        return;
      }

      setSelectedSend({
        ...(response.data as SendContentPreview),
        id: mySends.find((send) => send.share_token === shareToken)?.id,
      });
    } catch {
      toast.error("Unable to open send content");
    }
  };

  const handleDeleteSend = async (sendId: string) => {
    try {
      const response = await API.delete(`/send/${sendId}`);
      if (response.data?.message !== "send deleted successfully") {
        toast.error(response.data?.message ?? "Failed to delete send");
        return;
      }

      if (selectedSend?.id === sendId) {
        setSelectedSend(null);
      }
      await loadMySends();
      toast.success("Send deleted successfully");
    } catch {
      toast.error("Failed to delete send");
    }
  };

  const handleCopyLink = async (shareLink: string) => {
    try {
      await navigator.clipboard.writeText(shareLink);
      toast.success("Share link copied");
    } catch {
      toast.error("Failed to copy link");
    }
  };

  const filteredSends = mySends.filter((send) =>
    send.name.toLowerCase().includes(sendSearch.trim().toLowerCase())
  );

  return (
    <main className="dashboard-page">
      <div className="dashboard-layout">
        <aside className="dashboard-sidebar">
          <h2 className="dashboard-brand">Safeguard</h2>
          <nav className="dashboard-nav">
            <button className="dashboard-nav-item is-active">Send</button>
          </nav>
          <button onClick={handleLogout} className="btn btn-secondary">
            Logout
          </button>
        </aside>

        <section className="dashboard-content hero-card">
            <>
              <div className="send-header">
                <h1 className="send-title">Send</h1>
                <button className="btn btn-primary" onClick={() => setShowNewSendForm(true)}>
                  New
                </button>
              </div>

              <div className="send-user-chip">TA</div>

              <p className="send-subheading">All Sends</p>

              <input
                className="send-search-input"
                placeholder="Search sends by name"
                value={sendSearch}
                onChange={(event) => setSendSearch(event.target.value)}
              />

              <div className="send-tabs">
                <button className={`send-tab ${sendMode === "text" ? "is-active" : ""}`} onClick={() => setSendMode("text")}>
                  Text
                </button>
                <button className={`send-tab ${sendMode === "file" ? "is-active" : ""}`} onClick={() => setSendMode("file")}>
                  File
                </button>
              </div>

              <div className="send-table-container">
                <table className="send-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Deletion date</th>
                      <th>Options</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSends.length > 0 ? (
                      filteredSends.map((send) => (
                        <tr key={send.id}>
                          <td>{send.name}</td>
                          <td>{new Date(send.deletion_date).toLocaleString()}</td>
                          <td>
                            <div className="send-actions">
                              <button
                                className="send-tab is-active"
                                onClick={() => void handleOpenSend(send.share_token)}
                              >
                                Open
                              </button>
                              <button
                                className="send-tab"
                                onClick={() => void handleDeleteSend(send.id)}
                              >
                                Delete
                              </button>
                              <button
                                className="send-tab"
                                onClick={() => void handleCopyLink(send.share_link)}
                              >
                                Copy link
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="send-empty">
                          {mySends.length > 0 ? "No sends match your search" : "Send sensitive information safely"}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <p className="send-description">
                Share files and data securely with anyone, on any platform.
                Your information will remain end-to-end encrypted while
                limiting exposure.
              </p>

              {generatedShareLink ? (
                <div className="send-link-card">
                  <p className="send-subheading">Generated link</p>
                  <input value={generatedShareLink} readOnly />
                </div>
              ) : null}

              {selectedSend ? (
                <div className="send-link-card">
                  <p className="send-subheading">{selectedSend.name}</p>
                  {selectedSend.send_type === "file" ? (
                    <>
                      <p className="send-help-text">File: {selectedSend.file_name}</p>
                      <p className="send-help-text">
                        Size: {selectedSend.file_size ? `${Math.round(selectedSend.file_size / 1024)} KB` : "Unknown"}
                      </p>
                      <a
                        className="btn btn-primary"
                        target="_blank"
                        rel="noreferrer"
                        href={`${import.meta.env.VITE_API_BASE_URL}/send/public-file/${mySends.find((item) => item.id === selectedSend.id)?.share_token ?? ""}`}
                      >
                        Download file
                      </a>
                    </>
                  ) : (
                    <p className="public-send-text">{selectedSend.text_to_share}</p>
                  )}
                  <p className="send-help-text">
                    Deletion date: {new Date(selectedSend.deletion_date).toLocaleString()}
                  </p>
                  <p className="send-help-text">Who can view: {selectedSend.who_can_view}</p>
                </div>
              ) : null}

              {showNewSendForm ? (
                <div className="new-send-modal" onClick={() => setShowNewSendForm(false)}>
                  <div
                    className="new-send-card new-send-card-modal"
                    onClick={(event) => event.stopPropagation()}
                  >
                  <h2 className="vaults-heading">New {sendMode === "text" ? "Text" : "File"} Send</h2>
                  <div className="send-tabs">
                    <button className={`send-tab ${sendMode === "text" ? "is-active" : ""}`} onClick={() => setSendMode("text")}>
                      Text
                    </button>
                    <button className={`send-tab ${sendMode === "file" ? "is-active" : ""}`} onClick={() => setSendMode("file")}>
                      File
                    </button>
                  </div>

                  <p className="send-subheading">Send details</p>
                  <label className="vaults-label" htmlFor="send-name">
                    Name (required)
                  </label>
                  <input
                    id="send-name"
                    name="name"
                    value={newSendForm.name}
                    onChange={handleSendInputChange}
                  />

                  {sendMode === "text" ? (
                    <>
                      <label className="vaults-label" htmlFor="send-text">
                        Text to share (required)
                      </label>
                      <textarea
                        id="send-text"
                        name="textToShare"
                        className="send-textarea"
                        value={newSendForm.textToShare}
                        onChange={handleSendInputChange}
                      />
                    </>
                  ) : (
                    <>
                      <label className="vaults-label" htmlFor="send-file">
                        Upload file (required, max 50MB)
                      </label>
                      <input id="send-file" type="file" onChange={handleFileChange} />
                    </>
                  )}

                  <label className="vaults-label" htmlFor="send-deletion-date">
                    Deletion date (required)
                  </label>
                  <input
                    id="send-deletion-date"
                    type="datetime-local"
                    name="deletionDate"
                    value={newSendForm.deletionDate}
                    onChange={handleSendInputChange}
                  />
                  <p className="send-help-text">
                    The Send will be permanently deleted on this date.
                  </p>

                  <p className="vaults-label">Who can view</p>
                  <div className="send-tabs">
                    <button
                      type="button"
                      className={`send-tab ${newSendForm.whoCanView === "Anyone with the link" ? "is-active" : ""}`}
                      onClick={() =>
                        setNewSendForm((prev) => ({
                          ...prev,
                          whoCanView: "Anyone with the link",
                          accessPassword: "",
                        }))
                      }
                    >
                      Anyone with the link
                    </button>
                    <button
                      type="button"
                      className={`send-tab ${newSendForm.whoCanView === "Anyone with a password set by you" ? "is-active" : ""}`}
                      onClick={() =>
                        setNewSendForm((prev) => ({
                          ...prev,
                          whoCanView: "Anyone with a password set by you",
                        }))
                      }
                    >
                      Anyone with a password set by you
                    </button>
                  </div>
                  {newSendForm.whoCanView === "Anyone with a password set by you" ? (
                    <>
                      <p className="send-help-text">
                        Individuals will need to enter the password to view this Send
                      </p>
                      <label className="vaults-label" htmlFor="send-access-password">
                        Password (required)
                      </label>
                      <input
                        id="send-access-password"
                        name="accessPassword"
                        type="password"
                        value={newSendForm.accessPassword}
                        onChange={handleSendInputChange}
                      />
                    </>
                  ) : null}

                  <p className="send-subheading">Additional options</p>
                  <label className="vaults-label" htmlFor="send-limit-views">
                    Limit views
                  </label>
                  <input
                    id="send-limit-views"
                    name="limitViews"
                    type="number"
                    min={1}
                    value={newSendForm.limitViews}
                    onChange={handleSendInputChange}
                  />
                  <p className="send-help-text">
                    No one can view this Send after the limit is reached.
                  </p>

                  <label className="vaults-label" htmlFor="send-private-note">
                    Private note
                  </label>
                  <textarea
                    id="send-private-note"
                    name="privateNote"
                    className="send-textarea"
                    value={newSendForm.privateNote}
                    onChange={handleSendInputChange}
                  />

                  <div className="hero-actions">
                    <button className="btn btn-primary" onClick={handleCreateSend}>
                      Save
                    </button>
                    <button className="btn btn-secondary" onClick={() => setShowNewSendForm(false)}>
                      Cancel
                    </button>
                  </div>
                  </div>
                </div>
              ) : null}
            </>
        </section>
      </div>
    </main>
  );
}
