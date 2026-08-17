import { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../context/AuthContext";
import { useGoogleConfig } from "../context/GoogleConfigContext";

export default function LoginPage() {
  const { loginWithGoogle, loginDev } = useAuth();
  const { clientId, devAuthEnabled } = useGoogleConfig();
  const [devLoading, setDevLoading] = useState(false);
  const [showSetup, setShowSetup] = useState(false);

  async function handleDevLogin() {
    setDevLoading(true);
    try {
      await loginDev();
    } catch {
      alert("Dev login failed. Is the backend running?");
    } finally {
      setDevLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="login-hero-overlay">
          <p className="eyebrow">A DEBT-FREEDOM COMPANION</p>
          <h1>Calmly map the way out of your debt.</h1>
        </div>
      </div>
      <div className="login-panel">
        <div className="login-panel-inner">
          <h2 className="display-heading">
            Your money, working
            <br />
            for your freedom.
          </h2>
          <p className="lead">
            Tell AiFin about every asset and every loan you carry. We&apos;ll show you the shortest,
            calmest route to zero debt — what to sell, what to keep, and exactly how many months it
            will take.
          </p>
          <div className="google-btn-wrap">
            {clientId ? (
              <GoogleLogin
                onSuccess={(res) => {
                  if (res.credential) loginWithGoogle(res.credential);
                }}
                onError={() => alert("Google sign-in failed. Check your OAuth client settings.")}
                theme="filled_black"
                size="large"
                shape="pill"
                text="continue_with"
                width="320"
              />
            ) : devAuthEnabled ? (
              <>
                <button type="button" className="btn-primary login-cta" onClick={handleDevLogin} disabled={devLoading}>
                  {devLoading ? "Signing in…" : "Continue locally →"}
                </button>
                <p className="login-hint">
                  Google Sign-In isn&apos;t set up yet. Using local dev mode — your data still saves to
                  your account.
                </p>
                <button type="button" className="link-setup" onClick={() => setShowSetup(!showSetup)}>
                  {showSetup ? "Hide" : "Set up Google Sign-In"}
                </button>
              </>
            ) : (
              <div className="oauth-setup">
                <strong>Google Sign-In is not configured</strong>
                <ol>
                  <li>
                    Create an OAuth client at{" "}
                    <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer">
                      Google Cloud Console
                    </a>{" "}
                    (type: <em>Web application</em>).
                  </li>
                  <li>
                    Add authorized origin: <code>http://localhost:5173</code>
                  </li>
                  <li>
                    Add to <code>backend/.env</code>:
                    <pre>{`GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com`}</pre>
                  </li>
                  <li>Restart the backend, then refresh.</li>
                </ol>
              </div>
            )}
            {showSetup && !clientId && (
              <div className="oauth-setup" style={{ marginTop: "1rem" }}>
                <strong>Google OAuth setup</strong>
                <ol>
                  <li>
                    <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer">
                      Google Cloud Console
                    </a>{" "}
                    → OAuth client (Web) → origin <code>http://localhost:5173</code>
                  </li>
                  <li>
                    Add to <code>backend/.env</code>:
                    <pre>GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com</pre>
                  </li>
                  <li>Restart backend &amp; refresh — Google button will appear.</li>
                </ol>
              </div>
            )}
          </div>
          <div className="login-stats">
            <div>
              <strong>4</strong>
              <span>Strategies compared</span>
            </div>
            <div>
              <strong>∞</strong>
              <span>Assets supported</span>
            </div>
            <div>
              <strong>0</strong>
              <span>Spam, ever</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
