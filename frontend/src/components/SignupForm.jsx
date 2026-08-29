import { useContext, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/auth-context";
import "../styles/auth.css";

function SignupForm() {
  const { signup } = useContext(AuthContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ full_name: "", email: "", password: "", phone: "", role: "Admin" });
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const passwordRules = {
    length: formData.password.length >= 8 && formData.password.length <= 12,
    uppercase: /[A-Z]/.test(formData.password),
    lowercase: /[a-z]/.test(formData.password),
    number: /\d/.test(formData.password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password),
  };

  const passwordValid = Object.values(passwordRules).every(Boolean);
  const passwordMatches = formData.password === confirmPassword;

  const handleChange = (event) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!passwordValid) {
      setError("Please meet all password requirements.");
      return;
    }

    if (!passwordMatches) {
      setError("Password and confirmation do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await signup(formData);
      navigate("/verify-email", { state: { email: formData.email } });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to create account.");
    } finally {
      setSubmitting(false);
    }
  };

  const ruleClass = (isValid) => (isValid ? "password-rule-valid" : "password-rule-invalid");

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand">FleetFlow</div>
        <div className="auth-brand-copy">
          <h1>Build a smarter fleet operation.</h1>
          <p>Create your account to manage vehicles, fleet status, and team access from a single dashboard.</p>
        </div>
        <span className="auth-brand-footer">Fleet management made clear.</span>
      </section>

      <section className="auth-content">
        <div className="auth-card">
          <p className="auth-kicker">Get started</p>
          <h2 className="auth-title">Create your account</h2>
          <p className="auth-subtitle">Fill in your details to access FleetFlow.</p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {error && <p className="auth-error">{error}</p>}

            <label className="auth-field">Full name<input className="auth-input" type="text" name="full_name" value={formData.full_name} onChange={handleChange} placeholder="Your full name" required /></label>
            <label className="auth-field">Email address<input className="auth-input" type="email" name="email" value={formData.email} onChange={handleChange} placeholder="name@example.com" required /></label>

            <label className="auth-field">
              Password
              <span className="password-container">
                <input className="auth-input" type={showPassword ? "text" : "password"} name="password" value={formData.password} onChange={handleChange} placeholder="Create a password" required />
                <button className="show-password" type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? "Hide" : "Show"}</button>
              </span>
            </label>

            {formData.password && (
              <div className="password-rules">
                <span className={ruleClass(passwordRules.length)}>8-12 characters</span>
                <span className={ruleClass(passwordRules.uppercase)}>One uppercase letter</span>
                <span className={ruleClass(passwordRules.lowercase)}>One lowercase letter</span>
                <span className={ruleClass(passwordRules.number)}>One number</span>
                <span className={ruleClass(passwordRules.special)}>One special character</span>
              </div>
            )}

            <label className="auth-field">
              Confirm password
              <span className="password-container">
                <input className="auth-input" type={showConfirmPassword ? "text" : "password"} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Confirm your password" required />
                <button className="show-password" type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>{showConfirmPassword ? "Hide" : "Show"}</button>
              </span>
            </label>

            {confirmPassword && <p className={passwordMatches ? "password-match" : "password-mismatch"}>{passwordMatches ? "Passwords match" : "Passwords do not match"}</p>}

            <label className="auth-field">Phone number<input className="auth-input" type="tel" name="phone" value={formData.phone} onChange={handleChange} placeholder="9876543210" required /></label>
            <label className="auth-field">Role<select className="auth-input auth-select" name="role" value={formData.role} onChange={handleChange}><option value="Admin">Admin</option><option value="FleetManager">Fleet Manager</option><option value="Driver">Driver</option><option value="Dispatcher">Dispatcher</option></select></label>

            <button className="auth-button" type="submit" disabled={submitting || !passwordValid || !passwordMatches}>{submitting ? "Creating account..." : "Create account"}</button>
            <p className="auth-footer">Already have an account? <Link className="auth-link" to="/login">Sign in</Link></p>
          </form>
        </div>
      </section>
    </main>
  );
}

export default SignupForm;
