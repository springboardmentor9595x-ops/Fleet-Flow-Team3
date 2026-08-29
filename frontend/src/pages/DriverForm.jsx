import { useContext, useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import LoadingCard from "../components/LoadingCard";
import MainLayout from "../layouts/MainLayout";
import PageHeader from "../components/PageHeader";
import { AuthContext } from "../context/auth-context";
import api from "../services/api";
import "./DriverForm.css";

const supportedStatuses = ["Available", "On Trip", "Offline", "Inactive"];
const emptyDriver = {
  full_name: "",
  user_id: "",
  license_number: "",
  experience_years: "",
  address: "",
  status: "Available",
};

function getApiError(requestError, fallback) {
  const detail = requestError.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || "Invalid value").join(" ");
  }

  return detail || fallback;
}

function DriverForm() {
  const { user } = useContext(AuthContext);
  const { driverId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(driverId);
  const canManageDrivers = ["Admin", "FleetManager"].includes(user?.role);

  const [driver, setDriver] = useState(emptyDriver);
  const [driverUsers] = useState([]);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(isEditing);
  const [submitting, setSubmitting] = useState(false);

  // No safe user-list endpoint currently exists. Keeping this state/select ready
  // avoids inventing IDs and allows a future existing user source to populate it.
  const hasDriverUserSource = driverUsers.length > 0;

  useEffect(() => {
    if (!isEditing) return undefined;

    let active = true;
    const loadDriver = async () => {
      try {
        const response = await api.get(`/drivers/${driverId}`);
        const existing = response.data;

        if (!active) return;
        setDriver({
          full_name: existing.full_name || "",
          user_id: existing.user_id || "",
          license_number: existing.license_number || "",
          experience_years: String(existing.experience_years ?? ""),
          address: existing.address || "",
          status: supportedStatuses.includes(existing.status)
            ? existing.status
            : "Available",
        });
      } catch (requestError) {
        if (active) setError(getApiError(requestError, "Unable to load driver details."));
      } finally {
        if (active) setLoading(false);
      }
    };

    const timer = window.setTimeout(loadDriver, 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [driverId, isEditing]);

  if (user && !canManageDrivers) {
    return <Navigate to="/drivers" replace />;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;
    setDriver((currentDriver) => ({ ...currentDriver, [name]: value }));
    setFieldErrors((currentErrors) => ({ ...currentErrors, [name]: "" }));
  };

  const validate = () => {
    const errors = {};

    if (!isEditing && !driver.user_id) errors.user_id = "Select a Driver-role user.";
    if (!driver.full_name.trim()) errors.full_name = "Full name is required.";
    if (!driver.license_number.trim()) errors.license_number = "License number is required.";
    if (driver.experience_years === "") {
      errors.experience_years = "Experience years is required.";
    } else if (!Number.isInteger(Number(driver.experience_years)) || Number(driver.experience_years) < 0) {
      errors.experience_years = "Experience years must be a non-negative whole number.";
    }
    if (!driver.address.trim()) errors.address = "Address is required.";
    if (!supportedStatuses.includes(driver.status)) errors.status = "Choose a supported driver status.";

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!isEditing && !hasDriverUserSource) {
      setError("Driver registration is unavailable until the application provides a safe list of Driver-role users.");
      return;
    }

    if (!validate()) return;

    setSubmitting(true);
    const payload = {
      full_name: driver.full_name.trim(),
      license_number: driver.license_number.trim(),
      experience_years: Number(driver.experience_years),
      address: driver.address.trim(),
      status: driver.status,
    };

    try {
      if (isEditing) {
        await api.put(`/drivers/${driverId}`, payload);
      } else {
        await api.post("/drivers/", { ...payload, user_id: driver.user_id });
      }

      navigate("/drivers");
    } catch (requestError) {
      setError(getApiError(requestError, "Unable to save driver details."));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading driver details..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Fleet Management / Drivers"
        title={isEditing ? "Edit Driver" : "Register Driver"}
        description={isEditing ? "Update the driver profile and operational status." : "Link an existing Driver-role user to a FleetFlow driver profile."}
      />

      <form className="driver-form-card" onSubmit={handleSubmit} noValidate>
        {error && <div className="driver-form-error" role="alert">{error}</div>}

        {!isEditing && !hasDriverUserSource && (
          <div className="driver-form-notice" role="status">
            A Driver-user list API is not currently available. This form cannot submit a registration until a safe existing user source is available.
          </div>
        )}

        <div className="driver-form-grid">
          <label className="driver-select-field">
            <span>Driver User <b aria-hidden="true">*</b></span>
            {isEditing ? (
              <input value={driver.user_id} readOnly aria-label="Linked Driver user ID" />
            ) : (
              <select
                name="user_id"
                value={driver.user_id}
                onChange={handleChange}
                disabled={!hasDriverUserSource || submitting}
                aria-invalid={Boolean(fieldErrors.user_id)}
                aria-describedby={fieldErrors.user_id ? "driver-user-error" : undefined}
              >
                <option value="">
                  {hasDriverUserSource ? "Select a Driver-role user" : "Driver user source unavailable"}
                </option>
                {driverUsers
                  .filter((candidate) => candidate.role === "Driver")
                  .map((candidate) => (
                    <option key={candidate.user_id} value={candidate.user_id}>
                      {candidate.full_name || candidate.name || "Unnamed user"} · {candidate.email || candidate.user_id}
                    </option>
                  ))}
              </select>
            )}
            {isEditing && <small>The linked user cannot be changed from this form.</small>}
            {fieldErrors.user_id && <em id="driver-user-error">{fieldErrors.user_id}</em>}
          </label>

          <label className="driver-floating-field">
            <input name="full_name" value={driver.full_name} onChange={handleChange} placeholder=" " disabled={submitting} aria-invalid={Boolean(fieldErrors.full_name)} />
            <span>Full Name <b aria-hidden="true">*</b></span>
            {fieldErrors.full_name && <em>{fieldErrors.full_name}</em>}
          </label>

          <label className="driver-floating-field">
            <input name="license_number" value={driver.license_number} onChange={handleChange} placeholder=" " disabled={submitting} aria-invalid={Boolean(fieldErrors.license_number)} />
            <span>License Number <b aria-hidden="true">*</b></span>
            {fieldErrors.license_number && <em>{fieldErrors.license_number}</em>}
          </label>

          <label className="driver-floating-field">
            <input name="experience_years" type="number" min="0" step="1" value={driver.experience_years} onChange={handleChange} placeholder=" " disabled={submitting} aria-invalid={Boolean(fieldErrors.experience_years)} />
            <span>Experience Years <b aria-hidden="true">*</b></span>
            {fieldErrors.experience_years && <em>{fieldErrors.experience_years}</em>}
          </label>

          <label className="driver-floating-field driver-form-full-width">
            <textarea name="address" value={driver.address} onChange={handleChange} placeholder=" " rows="3" disabled={submitting} aria-invalid={Boolean(fieldErrors.address)} />
            <span>Address <b aria-hidden="true">*</b></span>
            {fieldErrors.address && <em>{fieldErrors.address}</em>}
          </label>

          <label className="driver-select-field">
            <span>Status <b aria-hidden="true">*</b></span>
            <select name="status" value={driver.status} onChange={handleChange} disabled={submitting} aria-invalid={Boolean(fieldErrors.status)}>
              {supportedStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
            {fieldErrors.status && <em>{fieldErrors.status}</em>}
          </label>
        </div>

        <div className="driver-form-actions">
          <Link to="/drivers" className="driver-form-cancel">Cancel</Link>
          <button type="submit" disabled={submitting || (!isEditing && !hasDriverUserSource)}>
            {submitting ? "Saving Driver..." : isEditing ? "Save Changes" : "Register Driver"}
          </button>
        </div>
      </form>
    </MainLayout>
  );
}

export default DriverForm;
