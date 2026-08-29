import { useContext, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import PageHeader from "../components/PageHeader";
import StatsCard from "../components/StatsCard";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Profile.css";
import "./ProfilePolish.css";

function getInitials(name) {
  return String(name || "FleetFlow User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function passwordStrength(password) {
  if (!password) return { label: "Enter a new password", score: 0 };

  const score = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[a-z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length;

  if (score <= 2) return { label: "Weak", score };
  if (score <= 3) return { label: "Fair", score };
  return { label: "Strong", score };
}

function ProfileSkeleton() {
  return (
    <MainLayout>
      <section className="profile-skeleton" aria-label="Loading profile">
        <div className="profile-skeleton-hero">
          <span className="profile-skeleton-circle" />
          <div><i /><i className="short" /></div>
        </div>
        <div className="profile-skeleton-grid">
          {[0, 1, 2, 3].map((item) => <span key={item} />)}
        </div>
        <div className="profile-skeleton-card" />
      </section>
    </MainLayout>
  );
}

function Profile() {
  const { user, loadCurrentUser, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [profile, setProfile] = useState({ full_name: "", phone: "", email: "" });
  const [originalEmail, setOriginalEmail] = useState("");
  const [passwords, setPasswords] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [showPasswords, setShowPasswords] = useState({ current: false, next: false, confirm: false });
  const [vehicles, setVehicles] = useState([]);
  const [trips, setTrips] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [profileErrors, setProfileErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    if (!user) return undefined;

    const profileResetTimer = window.setTimeout(() => {
      setProfile({
        full_name: user.full_name || "",
        phone: user.phone || "",
        email: user.email || "",
      });
      setOriginalEmail(user.email || "");
    }, 0);

    let active = true;
    const loadOverview = async () => {
      const results = await Promise.allSettled([
        api.get("/vehicles/"),
        api.get("/trips/"),
        api.get("/drivers/"),
      ]);
      if (!active) return;

      setVehicles(results[0].status === "fulfilled" ? results[0].value.data : []);
      setTrips(results[1].status === "fulfilled" ? results[1].value.data : []);
      setDrivers(results[2].status === "fulfilled" ? results[2].value.data : []);
    };

    void loadOverview();
    return () => {
      active = false;
      window.clearTimeout(profileResetTimer);
    };
  }, [user]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 4500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const driverRecord = drivers.find((driver) => driver.user_id === user?.user_id);
  const assignedVehicle = vehicles.find((vehicle) => vehicle.assigned_driver === driverRecord?.driver_id);
  const activeTrip = trips.find(
    (trip) =>
      trip.driver_id === driverRecord?.driver_id &&
      ["Active", "Scheduled"].includes(trip.status)
  );
  const isDriver = user?.role === "Driver";
  const isManagement = ["Admin", "FleetManager", "Dispatcher"].includes(user?.role);
  const activeTrips = trips.filter((trip) => trip.status === "Active").length;
  const strength = passwordStrength(passwords.new_password);
  const passwordsMatch =
    Boolean(passwords.confirm_password) &&
    passwords.new_password === passwords.confirm_password;

  const overviewCards = useMemo(() => {
    if (isDriver) {
      return [
        { label: "Account Role", value: "Driver", detail: "Fleet operations access", icon: "DR" },
        { label: "Account Status", value: "Active", detail: "Authenticated account", icon: "OK", tone: "green" },
        { label: "Assigned Vehicle", value: assignedVehicle?.registration_number || "None", detail: assignedVehicle?.vehicle_type || "No vehicle assigned", icon: "VH" },
        { label: "Active Trip", value: activeTrip ? "In progress" : "None", detail: activeTrip ? `${activeTrip.source} to ${activeTrip.destination}` : "No current trip", icon: "TR" },
      ];
    }

    return [
      { label: "Account Role", value: user?.role || "User", detail: "Role-based access enabled", icon: "RL" },
      { label: "Account Status", value: "Active", detail: "Authenticated account", icon: "OK", tone: "green" },
      { label: "Managed Vehicles", value: vehicles.length, detail: "Fleet vehicles available", icon: "VH" },
      { label: "Active Trips", value: activeTrips, detail: isManagement ? "Live operational trips" : "Current trip activity", icon: "TR" },
    ];
  }, [activeTrip, activeTrips, assignedVehicle, isDriver, isManagement, user?.role, vehicles.length]);

  const showToast = (type, message) => setToast({ type, message });

  const validateProfile = () => {
    const nextErrors = {};
    if (profile.full_name.trim().length < 2) nextErrors.full_name = "Enter at least two characters.";
    if (!/^\S+@\S+\.\S+$/.test(profile.email)) nextErrors.email = "Enter a valid email address.";
    if (profile.phone && profile.phone.trim().length < 7) nextErrors.phone = "Enter a valid phone number.";
    setProfileErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleProfileSubmit = async (event) => {
    event.preventDefault();
    if (!validateProfile()) return;

    setSavingProfile(true);
    try {
      await api.put("/auth/me", {
        full_name: profile.full_name.trim(),
        phone: profile.phone.trim() || null,
      });

      if (profile.email.trim().toLowerCase() !== originalEmail.toLowerCase()) {
        await api.put("/auth/me/email", { email: profile.email.trim() });
        showToast("success", "Email updated. Please sign in again using your new email.");
        window.setTimeout(() => {
          logout();
          navigate("/login");
        }, 1400);
        return;
      }

      await loadCurrentUser();
      showToast("success", "Your profile has been updated.");
    } catch (requestError) {
      showToast(
        "error",
        requestError.response?.data?.detail || "Unable to update your profile."
      );
    } finally {
      setSavingProfile(false);
    }
  };

  const handleProfileCancel = () => {
    setProfile({
      full_name: user?.full_name || "",
      phone: user?.phone || "",
      email: originalEmail,
    });
    setProfileErrors({});
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    if (passwords.new_password.length < 8) {
      showToast("error", "Your new password must contain at least 8 characters.");
      return;
    }
    if (passwords.new_password !== passwords.confirm_password) {
      showToast("error", "New password and confirmation do not match.");
      return;
    }

    setSavingPassword(true);
    try {
      await api.put("/auth/me/password", {
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      });
      setPasswords({ current_password: "", new_password: "", confirm_password: "" });
      showToast("success", "Password updated successfully.");
    } catch (requestError) {
      showToast(
        "error",
        requestError.response?.data?.detail || "Unable to change your password."
      );
    } finally {
      setSavingPassword(false);
    }
  };

  if (!user) return <ProfileSkeleton />;

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Account Management"
        title="My Profile"
        description="Manage your account details, security, and FleetFlow access."
      />

      {toast && <div className={`profile-toast ${toast.type}`} role="status" aria-live="polite">{toast.message}</div>}

      <section className="profile-hero-card">
        <div className="profile-avatar" aria-label={`${user.full_name}'s avatar`}>
          <span>{getInitials(user.full_name)}</span>
        </div>
        <div className="profile-hero-info">
          <div className="profile-hero-title"><div><p>FleetFlow account</p><h2>{user.full_name}</h2></div><span className="profile-role-badge">{user.role}</span></div>
          <div className="profile-hero-meta"><span>{user.email}</span><span>{user.phone || "Phone number not set"}</span><span>{user.created_at ? `Joined ${new Date(user.created_at).toLocaleDateString()}` : "Joined date not available"}</span></div>
        </div>
        <StatusBadge status="Active" />
      </section>

      <section className="profile-overview-grid" aria-label="Account overview">
        {overviewCards.map((card) => <StatsCard key={card.label} {...card} />)}
      </section>

      <section className="profile-content-grid">
        <div className="profile-main-column">
          <section className="profile-panel">
            <div className="profile-panel-heading"><div><p>Account details</p><h2>Edit Profile</h2></div><span>Required fields are marked</span></div>
            <form className="profile-form" onSubmit={handleProfileSubmit} noValidate>
              <label htmlFor="profile-full-name">Full Name<span aria-hidden="true"> *</span></label>
              <input id="profile-full-name" value={profile.full_name} onChange={(event) => setProfile({ ...profile, full_name: event.target.value })} aria-invalid={Boolean(profileErrors.full_name)} aria-describedby={profileErrors.full_name ? "profile-full-name-error" : undefined} />
              {profileErrors.full_name && <small id="profile-full-name-error" className="profile-field-error">{profileErrors.full_name}</small>}

              <label htmlFor="profile-email">Email Address<span aria-hidden="true"> *</span></label>
              <input id="profile-email" type="email" value={profile.email} onChange={(event) => setProfile({ ...profile, email: event.target.value })} aria-invalid={Boolean(profileErrors.email)} aria-describedby="profile-email-help" />
              <small id="profile-email-help" className={profileErrors.email ? "profile-field-error" : "profile-help"}>{profileErrors.email || "Changing email requires signing in again."}</small>

              <label htmlFor="profile-phone">Phone Number</label>
              <input id="profile-phone" type="tel" value={profile.phone} onChange={(event) => setProfile({ ...profile, phone: event.target.value })} aria-invalid={Boolean(profileErrors.phone)} />
              {profileErrors.phone && <small className="profile-field-error">{profileErrors.phone}</small>}

              <div className="profile-form-actions"><button className="primary-button" type="submit" disabled={savingProfile}>{savingProfile ? "Saving changes..." : "Save Changes"}</button><button className="profile-secondary-button" type="button" onClick={handleProfileCancel} disabled={savingProfile}>Cancel</button></div>
            </form>
          </section>

          <section className="profile-panel profile-security-panel">
            <div className="profile-panel-heading"><div><p>Security</p><h2>Change Password</h2></div><span>Use a strong, unique password</span></div>
            <form className="profile-form" onSubmit={handlePasswordSubmit}>
              {[
                ["current", "current_password", "Current Password"],
                ["next", "new_password", "New Password"],
                ["confirm", "confirm_password", "Confirm New Password"],
              ].map(([key, field, label]) => <div key={key}><label htmlFor={`password-${key}`}>{label}</label><div className="profile-password-field"><input id={`password-${key}`} type={showPasswords[key] ? "text" : "password"} value={passwords[field]} minLength={field === "current_password" ? undefined : 8} onChange={(event) => setPasswords({ ...passwords, [field]: event.target.value })} required /><button type="button" onClick={() => setShowPasswords({ ...showPasswords, [key]: !showPasswords[key] })} aria-label={`${showPasswords[key] ? "Hide" : "Show"} ${label}`}>{showPasswords[key] ? "Hide" : "Show"}</button></div></div>)}
              <div className="password-strength" aria-live="polite"><div><span>Password strength</span><b>{strength.label}</b></div><i><em className={`strength-${strength.score}`} /></i>{passwords.confirm_password && <small className={passwordsMatch ? "password-match" : "profile-field-error"}>{passwordsMatch ? "Passwords match" : "Passwords do not match"}</small>}</div>
              <div className="profile-form-actions"><button className="primary-button" type="submit" disabled={savingPassword}>{savingPassword ? "Updating password..." : "Update Password"}</button></div>
            </form>
          </section>
        </div>

        <aside className="profile-side-column">
          <section className="profile-panel"><div className="profile-panel-heading"><div><p>Shortcuts</p><h2>Quick Actions</h2></div></div><div className="profile-quick-actions">{isDriver && assignedVehicle && <Link to="/vehicles">View Assigned Vehicle</Link>}{isDriver && activeTrip && <Link to={`/trips/${activeTrip.trip_id}`}>View Current Trip</Link>}<Link to="/live-tracking">Open Live Tracking</Link><Link to="/dashboard">Back to Dashboard</Link></div></section>
          <section className="profile-panel"><div className="profile-panel-heading"><div><p>Session</p><h2>Recent Activity</h2></div></div><ul className="profile-activity-list"><li><i className="activity-dot" /><div><strong>Current session</strong><span>You are signed in securely.</span></div></li><li><i className="activity-dot purple" /><div><strong>Active role</strong><span>{user.role} permissions are active.</span></div></li><li><i className="activity-dot gray" /><div><strong>Last profile update</strong><span>Not available yet.</span></div></li><li><i className="activity-dot gray" /><div><strong>Last login</strong><span>Not available yet.</span></div></li></ul></section>
        </aside>
      </section>
    </MainLayout>
  );
}

export default Profile;
