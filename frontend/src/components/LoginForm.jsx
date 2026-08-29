import { useContext, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/auth-context";
import "../styles/auth.css";

function LoginForm() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Invalid email or password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand">FleetFlow</div>
        <div className="auth-brand-copy">
          <h1>Keep your fleet moving.</h1>
          <p>Monitor vehicle availability, manage records, and keep your operations organized in one place.</p>
        </div>
        <span className="auth-brand-footer">Fleet management made clear.</span>
      </section>

      <section className="auth-content">
        <div className="auth-card">
          <p className="auth-kicker">Welcome back</p>
          <h2 className="auth-title">Sign in to FleetFlow</h2>
          <p className="auth-subtitle">Use your account credentials to access the fleet dashboard.</p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {error && <p className="auth-error">{error}</p>}

            <label className="auth-field">
              Email address
              <input className="auth-input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="name@example.com" required />
            </label>

            <label className="auth-field">
              Password
              <span className="password-container">
                <input className="auth-input" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" required />
                <button className="show-password" type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? "Hide" : "Show"}</button>
              </span>
            </label>

            <div className="auth-options">
              <label><input type="checkbox" /> Remember me</label>
              <span>Contact an admin if you need access.</span>
            </div>

            <button className="auth-button" type="submit" disabled={submitting}>{submitting ? "Signing in..." : "Sign in"}</button>
            <p className="auth-footer">New to FleetFlow? <Link className="auth-link" to="/signup">Create an account</Link></p>
          </form>
        </div>
      </section>
    </main>
  );
}

export default LoginForm;
