import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";
import "../styles/auth.css";

function VerifyEmail() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || "");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const verifyEmail = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!/^\d{6}$/.test(code)) {
      setError("Enter the six-digit code from your email.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/verify-email", { email, code });
      navigate("/login", { state: { message: "Email verified. You can now sign in." } });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to verify this code.");
    } finally {
      setLoading(false);
    }
  };

  const resendCode = async () => {
    setError("");
    setMessage("");
    if (!email) {
      setError("Enter your email address first.");
      return;
    }
    setLoading(true);
    try {
      const response = await api.post("/auth/resend-verification", { email });
      setMessage(response.data.message);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to resend the code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand">FleetFlow</div>
        <div className="auth-brand-copy"><h1>One more secure step.</h1><p>We sent a six-digit code to confirm your email address.</p></div>
        <span className="auth-brand-footer">Fleet management made clear.</span>
      </section>
      <section className="auth-content">
        <div className="auth-card">
          <p className="auth-kicker">Account verification</p>
          <h2 className="auth-title">Check your inbox</h2>
          <p className="auth-subtitle">The code expires after 10 minutes.</p>
          <form className="auth-form" onSubmit={verifyEmail}>
            {error && <p className="auth-error">{error}</p>}
            {message && <p className="auth-success">{message}</p>}
            <label className="auth-field">Email address<input className="auth-input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label className="auth-field">Verification code<input className="auth-input" type="text" inputMode="numeric" maxLength="6" value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))} placeholder="123456" required /></label>
            <button className="auth-button" type="submit" disabled={loading}>{loading ? "Verifying..." : "Verify email"}</button>
            <button className="auth-link-button" type="button" onClick={resendCode} disabled={loading}>Resend code</button>
            <p className="auth-footer">Already verified? <Link className="auth-link" to="/login">Sign in</Link></p>
          </form>
        </div>
      </section>
    </main>
  );
}

export default VerifyEmail;
