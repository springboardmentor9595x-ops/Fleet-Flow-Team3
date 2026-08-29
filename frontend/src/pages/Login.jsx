import { useContext, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/auth-context";
import "../styles/auth.css";
import "../styles/Login.css";

const REMEMBERED_EMAIL_KEY = "fleetflow_remembered_email";
const dashboardForRole = {
  Admin: "/analytics/admin",
  FleetManager: "/dashboard",
  Dispatcher: "/analytics/logistics",
  Driver: "/dashboard",
};

function Login() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const restoreTimer = window.setTimeout(() => {
      const rememberedEmail = localStorage.getItem(REMEMBERED_EMAIL_KEY);
      if (rememberedEmail) {
        setEmail(rememberedEmail);
        setRememberMe(true);
      }
    }, 0);
    return () => window.clearTimeout(restoreTimer);
  }, []);

  useEffect(() => {
    if (!toast) return undefined;
    const toastTimer = window.setTimeout(() => setToast(null), 4500);
    return () => window.clearTimeout(toastTimer);
  }, [toast]);

  const validate = () => {
    const errors = {};
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) errors.email = "Enter a valid email address.";
    if (!password) errors.password = "Enter your password.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitting || !validate()) return;

    setSubmitting(true);
    setToast(null);
    try {
      const loginResult = await login(email.trim(), password);
      if (rememberMe) localStorage.setItem(REMEMBERED_EMAIL_KEY, email.trim());
      else localStorage.removeItem(REMEMBERED_EMAIL_KEY);

      setToast({ type: "success", message: "Login successful. Opening your dashboard..." });
      window.setTimeout(() => navigate(dashboardForRole[loginResult.user?.role] || "/dashboard"), 450);
    } catch (requestError) {
      const status = requestError.response?.status;
      const message = status === 401
        ? "Invalid email or password."
        : status === 403
          ? requestError.response?.data?.detail || "Please verify your account before signing in."
          : !requestError.response
            ? "Network error. Check your connection and try again."
            : requestError.response?.data?.detail || "Server unavailable. Please try again shortly.";
      setToast({ type: "error", message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleForgotPassword = () => setToast({ type: "info", message: "Password recovery is not configured yet. Please contact your FleetFlow administrator." });

  return (
    <main className="login-page">
      <section className="login-brand-panel" aria-label="FleetFlow introduction">
        <Link className="login-brand" to="/login" aria-label="FleetFlow login"><span>FF</span>FleetFlow</Link>
        <div className="login-brand-copy"><p>Fleet operations, simplified</p><h1>Keep every mile in motion.</h1><p className="login-brand-description">Plan shipments, monitor vehicles, and make smarter fleet decisions from one connected workspace.</p></div>
        <div className="login-brand-stats" aria-label="FleetFlow capabilities"><span><b>Live</b> GPS tracking</span><span><b>Smart</b> trip operations</span><span><b>Secure</b> role access</span></div>
      </section>

      <section className="login-content">
        <div className="login-card">
          <div className="login-card-heading"><p>Welcome back</p><h2>Sign in to FleetFlow</h2><span>Enter your credentials to continue to your fleet workspace.</span></div>
          {toast && <div className={`login-toast ${toast.type}`} role="status" aria-live="polite">{toast.message}</div>}
          <form className="login-form" onSubmit={handleSubmit} noValidate>
            <label htmlFor="login-email">Email address</label>
            <div className={`login-input-wrap ${fieldErrors.email ? "has-error" : ""}`}><span className="login-input-icon" aria-hidden="true">@</span><input id="login-email" type="email" value={email} onChange={(event) => { setEmail(event.target.value); setFieldErrors({ ...fieldErrors, email: undefined }); }} placeholder="name@company.com" autoComplete="email" aria-invalid={Boolean(fieldErrors.email)} aria-describedby={fieldErrors.email ? "login-email-error" : undefined} disabled={submitting} /></div>
            {fieldErrors.email && <small id="login-email-error" className="login-field-error">{fieldErrors.email}</small>}

            <div className="login-password-label"><label htmlFor="login-password">Password</label><button type="button" onClick={handleForgotPassword}>Forgot Password?</button></div>
            <div className={`login-input-wrap ${fieldErrors.password ? "has-error" : ""}`}><span className="login-input-icon" aria-hidden="true">*</span><input id="login-password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => { setPassword(event.target.value); setFieldErrors({ ...fieldErrors, password: undefined }); }} placeholder="Enter your password" autoComplete="current-password" aria-invalid={Boolean(fieldErrors.password)} aria-describedby={fieldErrors.password ? "login-password-error" : undefined} disabled={submitting} /><button className="login-show-password" type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? "Hide password" : "Show password"} disabled={submitting}>{showPassword ? "Hide" : "Show"}</button></div>
            {fieldErrors.password && <small id="login-password-error" className="login-field-error">{fieldErrors.password}</small>}

            <label className="login-remember"><input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} disabled={submitting} /><span>Remember my email on this device</span></label>
            <button className="login-submit" type="submit" disabled={submitting}>{submitting && <i className="login-spinner" aria-hidden="true" />}{submitting ? "Signing In..." : "Sign In"}</button>
          </form>
          <p className="login-footer">New to FleetFlow? <Link to="/signup">Create an account</Link></p>
        </div>
      </section>
    </main>
  );
}

export default Login;
