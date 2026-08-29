import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import SearchBar from "../components/SearchBar";
import StatsCard from "../components/StatsCard";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Drivers.css";

const managementRoles = ["Admin", "FleetManager"];
const directoryRoles = [...managementRoles, "Dispatcher"];
const statusFilters = ["All", "Available", "On Trip", "Offline", "Inactive"];

function initials(name) {
  return String(name || "Driver")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function displayDate(value) {
  return value ? new Date(value).toLocaleString() : "Not started";
}

function sortActivities(items) {
  return [...(Array.isArray(items) ? items : [])]
    .sort(
      (first, second) => new Date(second.occurred_at || 0) - new Date(first.occurred_at || 0)
    )
    .slice(0, 5);
}

function formatActivityType(activityType) {
  const normalized = String(activityType || "Activity").replace(/[_-]/g, " ");
  return normalized.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function toDriverRecord(driver, vehicles) {
  const vehicle =
    driver.assigned_vehicle ||
    vehicles.find((item) => item.vehicle_id === driver.assigned_vehicle_id) ||
    null;

  return {
    driver,
    vehicle,
    currentTrip: driver.current_trip || null,
    status: driver.status || "Available",
  };
}

function RecentActivity({ activities, loading, error, emptyMessage, heading = "Recent activity" }) {
  return (
    <section className="driver-activity-section" aria-labelledby="driver-activity-heading">
      <div className="driver-activity-heading">
        <div>
          <p>Driver activity</p>
          <h3 id="driver-activity-heading">{heading}</h3>
        </div>
      </div>

      {loading ? (
        <div className="driver-activity-list" aria-label="Loading recent activity">
          {[0, 1, 2].map((item) => (
            <div className="driver-activity-row driver-activity-skeleton" key={item}>
              <span className="driver-skeleton driver-activity-dot" />
              <div>
                <span className="driver-skeleton driver-skeleton-line wide" />
                <span className="driver-skeleton driver-skeleton-line short" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <p className="driver-activity-error" role="alert">{error}</p>
      ) : activities.length === 0 ? (
        <p className="driver-activity-empty">{emptyMessage}</p>
      ) : (
        <div className="driver-activity-list">
          {activities.map((activity) => (
            <article className="driver-activity-row" key={activity.attendance_id}>
              <span className="driver-activity-dot" aria-hidden="true" />
              <div className="driver-activity-content">
                <div>
                  <strong>{formatActivityType(activity.activity_type)}</strong>
                  <time dateTime={activity.occurred_at}>{displayDate(activity.occurred_at)}</time>
                </div>
                {activity.trip_id && <small>Trip ID: {activity.trip_id}</small>}
                {activity.notes && <p>{activity.notes}</p>}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function DriverCardSkeleton() {
  return (
    <article className="driver-card driver-card-skeleton" aria-label="Loading driver">
      <div className="driver-card-head">
        <span className="driver-skeleton driver-skeleton-avatar" />
        <div className="driver-card-title">
          <span className="driver-skeleton driver-skeleton-line wide" />
          <span className="driver-skeleton driver-skeleton-line short" />
        </div>
        <span className="driver-skeleton driver-skeleton-badge" />
      </div>
      <div className="driver-card-details">
        <span className="driver-skeleton driver-skeleton-line" />
        <span className="driver-skeleton driver-skeleton-line" />
        <span className="driver-skeleton driver-skeleton-line" />
      </div>
    </article>
  );
}

function DriverStatus({ status }) {
  return <StatusBadge status={status} />;
}

function Drivers() {
  const { user } = useContext(AuthContext);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [vehicleFilter, setVehicleFilter] = useState("All");
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [latestLocation, setLatestLocation] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [profileActivity, setProfileActivity] = useState([]);
  const [profileActivityLoading, setProfileActivityLoading] = useState(false);
  const [profileActivityError, setProfileActivityError] = useState("");
  const [detailActivity, setDetailActivity] = useState([]);
  const [detailActivityLoading, setDetailActivityLoading] = useState(false);
  const [detailActivityError, setDetailActivityError] = useState("");
  const [assignmentMode, setAssignmentMode] = useState(null);
  const [assignmentVehicleId, setAssignmentVehicleId] = useState("");
  const [assignmentSubmitting, setAssignmentSubmitting] = useState(false);
  const [assignmentError, setAssignmentError] = useState("");
  const [assignmentMessage, setAssignmentMessage] = useState("");
  const [confirmUnassign, setConfirmUnassign] = useState(false);
  const detailActivityRequestRef = useRef(0);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const isDriver = user?.role === "Driver";
  const canManageDrivers = managementRoles.includes(user?.role);
  const canViewDirectory = directoryRoles.includes(user?.role);

  useEffect(() => {
    let active = true;

    const loadDrivers = async () => {
      try {
        const [driverResponse, vehicleResponse] = await Promise.all([
          api.get("/drivers/"),
          api.get("/vehicles/"),
        ]);

        if (!active) return;
        setDrivers(driverResponse.data);
        setVehicles(vehicleResponse.data);
      } catch (requestError) {
        if (active) {
          setError(
            requestError.response?.data?.detail ||
              "Unable to load driver information."
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    void loadDrivers();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isDriver) {
      return undefined;
    }

    let active = true;
    const loadProfileActivity = async () => {
      setProfileActivityLoading(true);
      setProfileActivityError("");

      try {
        const response = await api.get("/attendance/me");
        if (active) setProfileActivity(sortActivities(response.data));
      } catch (requestError) {
        if (active) {
          setProfileActivityError(
            requestError.response?.data?.detail || "Unable to load your recent activity."
          );
        }
      } finally {
        if (active) setProfileActivityLoading(false);
      }
    };

    void loadProfileActivity();
    return () => {
      active = false;
    };
  }, [isDriver]);

  const driverRecords = useMemo(
    () => drivers.map((driver) => toDriverRecord(driver, vehicles)),
    [drivers, vehicles]
  );

  const filteredDrivers = useMemo(() => {
    const query = search.trim().toLowerCase();

    return driverRecords.filter(({ driver, vehicle, status }) => {
      const matchesSearch =
        !query ||
        driver.full_name?.toLowerCase().includes(query) ||
        driver.driver_id.toLowerCase().includes(query) ||
        driver.license_number?.toLowerCase().includes(query) ||
        driver.address?.toLowerCase().includes(query) ||
        driver.phone?.toLowerCase().includes(query) ||
        vehicle?.registration_number?.toLowerCase().includes(query);
      const matchesStatus = statusFilter === "All" || status === statusFilter;
      const matchesVehicle =
        vehicleFilter === "All" || vehicle?.vehicle_id === vehicleFilter;

      return matchesSearch && matchesStatus && matchesVehicle;
    });
  }, [driverRecords, search, statusFilter, vehicleFilter]);

  const overview = useMemo(
    () => ({
      total: driverRecords.length,
      available: driverRecords.filter((record) => record.status === "Available").length,
      onTrip: driverRecords.filter((record) => record.status === "On Trip").length,
      offline: driverRecords.filter((record) => record.status === "Offline").length,
    }),
    [driverRecords]
  );

  const openDetails = async (record) => {
    if (!canViewDirectory) return;

    setSelectedDriver(record);
    setLatestLocation(null);
    setDetailActivity([]);
    setDetailActivityError("");
    setAssignmentMode(null);
    setAssignmentVehicleId("");
    setAssignmentError("");
    setAssignmentMessage("");
    setConfirmUnassign(false);
    setCopied(false);

    void loadDetailActivity(record.driver.driver_id);

    if (!record.vehicle?.vehicle_id) {
      setDetailsLoading(false);
      return;
    }

    setDetailsLoading(true);
    try {
      const response = await api.get(`/gps/latest/${record.vehicle.vehicle_id}`);
      setLatestLocation(response.data);
    } catch (requestError) {
      if (requestError.response?.status !== 404) {
        setError(
          requestError.response?.data?.detail ||
            "Unable to load the driver's latest GPS location."
        );
      }
    } finally {
      setDetailsLoading(false);
    }
  };

  const closeDetails = () => {
    detailActivityRequestRef.current += 1;
    setSelectedDriver(null);
  };

  const loadDetailActivity = async (driverId) => {
    const requestId = detailActivityRequestRef.current + 1;
    detailActivityRequestRef.current = requestId;
    setDetailActivity([]);
    setDetailActivityError("");
    setDetailActivityLoading(true);

    try {
      const response = await api.get(`/attendance/driver/${driverId}`);
      if (detailActivityRequestRef.current === requestId) {
        setDetailActivity(sortActivities(response.data));
      }
    } catch (requestError) {
      if (detailActivityRequestRef.current === requestId) {
        setDetailActivityError(
          requestError.response?.data?.detail || "Unable to load recent activity."
        );
      }
    } finally {
      if (detailActivityRequestRef.current === requestId) setDetailActivityLoading(false);
    }
  };

  const refreshAssignmentData = async (driverId) => {
    const [driverResponse, vehicleResponse] = await Promise.all([
      api.get("/drivers/"),
      api.get("/vehicles/"),
    ]);
    const updatedDrivers = driverResponse.data;
    const updatedVehicles = vehicleResponse.data;
    const updatedDriver = updatedDrivers.find((item) => item.driver_id === driverId);

    setDrivers(updatedDrivers);
    setVehicles(updatedVehicles);
    if (updatedDriver) setSelectedDriver(toDriverRecord(updatedDriver, updatedVehicles));
    await loadDetailActivity(driverId);
  };

  const openAssignment = (mode) => {
    setAssignmentMode(mode);
    setAssignmentVehicleId("");
    setAssignmentError("");
    setAssignmentMessage("");
    setConfirmUnassign(false);
  };

  const submitAssignment = async (event) => {
    event.preventDefault();
    if (!selectedDriver || !assignmentVehicleId) {
      setAssignmentError("Select an available vehicle before continuing.");
      return;
    }

    setAssignmentSubmitting(true);
    setAssignmentError("");
    setAssignmentMessage("");

    try {
      const action = assignmentMode === "reassign" ? "reassign-vehicle" : "assign-vehicle";
      await api.post(
        `/drivers/${selectedDriver.driver.driver_id}/${action}/${assignmentVehicleId}`
      );
      await refreshAssignmentData(selectedDriver.driver.driver_id);
      setAssignmentMode(null);
      setAssignmentVehicleId("");
      setAssignmentMessage(
        assignmentMode === "reassign"
          ? "Vehicle reassigned successfully."
          : "Vehicle assigned successfully."
      );
    } catch (requestError) {
      setAssignmentError(
        requestError.response?.data?.detail || "Unable to update the vehicle assignment."
      );
    } finally {
      setAssignmentSubmitting(false);
    }
  };

  const submitUnassignment = async () => {
    if (!selectedDriver) return;

    setAssignmentSubmitting(true);
    setAssignmentError("");
    setAssignmentMessage("");

    try {
      await api.delete(`/drivers/${selectedDriver.driver.driver_id}/unassign-vehicle`);
      await refreshAssignmentData(selectedDriver.driver.driver_id);
      setConfirmUnassign(false);
      setAssignmentMessage("Vehicle unassigned successfully.");
    } catch (requestError) {
      setAssignmentError(
        requestError.response?.data?.detail || "Unable to unassign the vehicle."
      );
    } finally {
      setAssignmentSubmitting(false);
    }
  };

  const copyPhone = async () => {
    if (!selectedDriver?.driver.phone) return;

    try {
      await navigator.clipboard.writeText(selectedDriver.driver.phone);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <PageHeader
          eyebrow="Fleet Management"
          title="Drivers"
          description="Loading driver availability and assignments."
        />
        <section className="drivers-summary-grid" aria-label="Loading driver overview">
          {[0, 1, 2, 3].map((item) => <DriverCardSkeleton key={item} />)}
        </section>
      </MainLayout>
    );
  }

  if (isDriver) {
    const record = driverRecords[0];

    return (
      <MainLayout>
        <PageHeader
          eyebrow="Fleet Management / Drivers"
          title="My Driver Profile"
          description="Your FleetFlow assignment, contact information, and current trip overview."
        />

        {error && <div className="drivers-error" role="alert">{error}</div>}

        {!record ? (
          <EmptyState
            title="No driver profile found"
            description="Your account is not linked to a driver record yet. Please contact a Fleet Manager."
          />
        ) : (
          <section className="driver-profile-card">
            <div className="driver-card-head">
              <span className="driver-avatar" aria-hidden="true">{initials(record.driver.full_name || user?.full_name)}</span>
              <div className="driver-card-title">
                <p>FleetFlow Driver</p>
                <h2>{record.driver.full_name || user?.full_name || "Driver"}</h2>
                <span>{record.driver.driver_id}</span>
              </div>
              <DriverStatus status={record.status} />
            </div>

            <div className="driver-profile-info-grid">
              <article><span>License number</span><strong>{record.driver.license_number || "Not provided"}</strong></article>
              <article><span>Experience</span><strong>{record.driver.experience_years ?? 0} years</strong></article>
              <article><span>Address</span><strong>{record.driver.address || "Not provided"}</strong></article>
              <article><span>Email</span><strong>{record.driver.email || user?.email || "Not set"}</strong></article>
              <article><span>Phone</span><strong>{record.driver.phone || user?.phone || "Not set"}</strong></article>
              <article><span>Assigned vehicle</span><strong>{record.vehicle?.registration_number || "No assigned vehicle"}</strong><small>{record.vehicle?.status || "No vehicle status"}</small></article>
              <article><span>Current trip</span><strong>{record.currentTrip ? `${record.currentTrip.source} to ${record.currentTrip.destination}` : "No active trip"}</strong><small>{record.currentTrip?.status || "No trip status"}</small></article>
              <article><span>Trip start time</span><strong>{displayDate(record.currentTrip?.started_at)}</strong></article>
            </div>

            <RecentActivity
              activities={profileActivity}
              loading={profileActivityLoading}
              error={profileActivityError}
              emptyMessage="No recent activity recorded."
            />

            <div className="driver-card-actions">
              <Link className="primary-button" to="/live-tracking">Live Tracking</Link>
              <Link className="driver-secondary-action" to="/trips">Trip History</Link>
            </div>
          </section>
        )}
      </MainLayout>
    );
  }

  const eligibleAssignmentVehicles = vehicles.filter(
    (vehicle) =>
      vehicle.status === "Available" &&
      vehicle.vehicle_id !== selectedDriver?.vehicle?.vehicle_id
  );

  return (
    <MainLayout>
      <PageHeader
        eyebrow={canViewDirectory ? "Fleet Management" : "Fleet Management / Read Only"}
        title="Drivers"
        description="Monitor driver availability, active assignments, and contact details from one workspace."
        actionLabel={canManageDrivers ? "Add Driver" : undefined}
        actionTo={canManageDrivers ? "/drivers/new" : undefined}
      />

      {error && <div className="drivers-error" role="alert">{error}</div>}

      <section className="drivers-summary-grid" aria-label="Driver overview">
        <StatsCard label="Total Drivers" value={overview.total} detail="Registered fleet drivers" icon="DR" />
        <StatsCard label="Available Drivers" value={overview.available} detail="Ready for assignment" icon="OK" tone="green" />
        <StatsCard label="Drivers On Trip" value={overview.onTrip} detail="Currently delivering" icon="GO" />
        <StatsCard label="Offline Drivers" value={overview.offline} detail="Scheduled, not active" icon="ZZ" tone="gray" />
      </section>

      <section className="drivers-toolbar">
        <div>
          <h2>{user?.role === "Dispatcher" ? "Driver directory (read only)" : "Driver directory"}</h2>
          <p>{filteredDrivers.length} of {drivers.length} drivers shown</p>
        </div>
        <div className="drivers-toolbar-controls">
          <SearchBar
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search name, license, vehicle, or phone"
          />
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} aria-label="Filter drivers by status">
            {statusFilters.map((status) => <option key={status} value={status}>{status === "All" ? "All statuses" : status}</option>)}
          </select>
          <select value={vehicleFilter} onChange={(event) => setVehicleFilter(event.target.value)} aria-label="Filter drivers by assigned vehicle">
            <option value="All">All vehicles</option>
            {vehicles.map((vehicle) => <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>{vehicle.registration_number}</option>)}
          </select>
        </div>
      </section>

      {filteredDrivers.length === 0 ? (
        <EmptyState
          title={drivers.length ? "No drivers found" : "No drivers yet"}
          description={drivers.length ? "Try another search term or filter." : "Driver records will appear here when they are linked to user accounts."}
        />
      ) : (
        <section className="drivers-card-grid" aria-label="Driver cards">
          {filteredDrivers.map((record) => (
            <article className="driver-card" key={record.driver.driver_id}>
              <div className="driver-card-head">
                <span className="driver-avatar" aria-hidden="true">{initials(record.driver.full_name)}</span>
                <div className="driver-card-title">
                  <h2>{record.driver.full_name || "Unnamed driver"}</h2>
                  <span>{record.driver.driver_id}</span>
                </div>
                <DriverStatus status={record.status} />
              </div>

              <div className="driver-card-details">
                <div><span>License</span><strong>{record.driver.license_number || "Not provided"}</strong></div>
                <div><span>Experience</span><strong>{record.driver.experience_years ?? 0} years</strong></div>
                <div><span>Address</span><strong>{record.driver.address || "Not provided"}</strong></div>
                <div><span>Assigned vehicle</span><strong>{record.vehicle?.registration_number || "Unassigned"}</strong><small>{record.vehicle?.status || "No vehicle status"}</small></div>
                <div><span>Current trip</span><strong>{record.currentTrip ? `${record.currentTrip.source} to ${record.currentTrip.destination}` : "No active trip"}</strong><small>{record.currentTrip?.status || "No trip status"}</small></div>
                <div><span>Phone</span><strong>{record.driver.phone || "Not provided"}</strong></div>
                <div><span>Email</span><strong>{record.driver.email || "Not provided"}</strong></div>
              </div>

              <button className="driver-view-button" type="button" onClick={() => void openDetails(record)} aria-label={`View details for ${record.driver.full_name || "driver"}`}>View details</button>
            </article>
          ))}
        </section>
      )}

      {selectedDriver && (
        <div className="driver-modal-backdrop" role="presentation" onMouseDown={closeDetails}>
          <section className="driver-modal" role="dialog" aria-modal="true" aria-labelledby="driver-details-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="driver-modal-close" type="button" onClick={closeDetails} aria-label="Close driver details">x</button>
            <div className="driver-card-head">
              <span className="driver-avatar" aria-hidden="true">{initials(selectedDriver.driver.full_name)}</span>
              <div className="driver-card-title"><p>Driver profile</p><h2 id="driver-details-title">{selectedDriver.driver.full_name || "Unnamed driver"}</h2><span>{selectedDriver.driver.driver_id}</span></div>
              <DriverStatus status={selectedDriver.status} />
            </div>

            <div className="driver-modal-grid">
              <article><span>License number</span><strong>{selectedDriver.driver.license_number || "Not provided"}</strong></article>
              <article><span>Experience</span><strong>{selectedDriver.driver.experience_years ?? 0} years</strong></article>
              <article><span>Address</span><strong>{selectedDriver.driver.address || "Not provided"}</strong></article>
              <article><span>Assigned vehicle</span><strong>{selectedDriver.vehicle?.registration_number || "Unassigned"}</strong><small>{selectedDriver.vehicle ? `${selectedDriver.vehicle.status} · ${selectedDriver.vehicle.vehicle_id}` : "No vehicle information"}</small></article>
              <article><span>Current trip</span><strong>{selectedDriver.currentTrip ? `${selectedDriver.currentTrip.source} to ${selectedDriver.currentTrip.destination}` : "No active trip"}</strong><small>{selectedDriver.currentTrip?.status || "No trip status"}</small></article>
              <article><span>Trip start time</span><strong>{displayDate(selectedDriver.currentTrip?.started_at)}</strong></article>
              <article><span>Last GPS update</span><strong>{detailsLoading ? "Loading..." : latestLocation?.recorded_time ? new Date(latestLocation.recorded_time).toLocaleString() : "No location received"}</strong></article>
              <article><span>Contact</span><strong>{selectedDriver.driver.phone || "Phone not provided"}</strong><small>{selectedDriver.driver.email || "Email not provided"}</small></article>
            </div>

            {selectedDriver.currentTrip && <div className="driver-route-summary"><span>Trip route</span><strong>{selectedDriver.currentTrip.source} to {selectedDriver.currentTrip.destination}</strong><small>{selectedDriver.currentTrip.status} · Started {displayDate(selectedDriver.currentTrip.started_at)}</small></div>}

            <RecentActivity
              activities={detailActivity}
              loading={detailActivityLoading}
              error={detailActivityError}
              emptyMessage="No recent activity recorded."
              heading="Recent activity"
            />

            {canManageDrivers && (
              <section className="driver-assignment-panel" aria-labelledby="driver-assignment-title">
                <div>
                  <p>Vehicle assignment</p>
                  <h3 id="driver-assignment-title">Manage assigned vehicle</h3>
                </div>

                {assignmentError && <p className="driver-assignment-error" role="alert">{assignmentError}</p>}
                {assignmentMessage && <p className="driver-assignment-success" role="status">{assignmentMessage}</p>}

                {assignmentMode ? (
                  <form className="driver-assignment-form" onSubmit={submitAssignment}>
                    <label>
                      <span>{assignmentMode === "reassign" ? "New available vehicle" : "Available vehicle"}</span>
                      <select
                        value={assignmentVehicleId}
                        onChange={(event) => setAssignmentVehicleId(event.target.value)}
                        disabled={assignmentSubmitting || eligibleAssignmentVehicles.length === 0}
                        aria-label="Select an available vehicle"
                      >
                        <option value="">
                          {eligibleAssignmentVehicles.length ? "Select a vehicle" : "No available vehicles"}
                        </option>
                        {eligibleAssignmentVehicles.map((vehicle) => (
                          <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                            {vehicle.registration_number} · {vehicle.vehicle_id} · {vehicle.status}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="driver-assignment-actions">
                      <button className="primary-button" type="submit" disabled={assignmentSubmitting || !assignmentVehicleId}>
                        {assignmentSubmitting ? "Saving..." : assignmentMode === "reassign" ? "Confirm Reassignment" : "Assign Vehicle"}
                      </button>
                      <button className="driver-secondary-action" type="button" disabled={assignmentSubmitting} onClick={() => setAssignmentMode(null)}>Cancel</button>
                    </div>
                  </form>
                ) : confirmUnassign ? (
                  <div className="driver-unassign-confirmation">
                    <p>Are you sure you want to unassign vehicle {selectedDriver.vehicle?.registration_number} from this driver?</p>
                    <div className="driver-assignment-actions">
                      <button className="driver-danger-action" type="button" disabled={assignmentSubmitting} onClick={() => void submitUnassignment()}>
                        {assignmentSubmitting ? "Unassigning..." : "Yes, Unassign"}
                      </button>
                      <button className="driver-secondary-action" type="button" disabled={assignmentSubmitting} onClick={() => setConfirmUnassign(false)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="driver-assignment-actions">
                    {selectedDriver.vehicle ? (
                      <>
                        <button className="primary-button" type="button" onClick={() => openAssignment("reassign")}>Reassign Vehicle</button>
                        <button className="driver-danger-action" type="button" onClick={() => { setConfirmUnassign(true); setAssignmentError(""); setAssignmentMessage(""); }}>Unassign Vehicle</button>
                      </>
                    ) : (
                      <button className="primary-button" type="button" onClick={() => openAssignment("assign")}>Assign Vehicle</button>
                    )}
                  </div>
                )}
              </section>
            )}

            <div className="driver-card-actions">
              {selectedDriver.vehicle && <Link className="driver-secondary-action" to="/vehicles">View Vehicle</Link>}
              {selectedDriver.currentTrip && <Link className="driver-secondary-action" to={`/trips/${selectedDriver.currentTrip.trip_id}`}>View Trip</Link>}
              {selectedDriver.driver.phone && <a className="primary-button" href={`tel:${selectedDriver.driver.phone}`}>Call Driver</a>}
              {selectedDriver.driver.phone && <button className="driver-secondary-action" type="button" onClick={() => void copyPhone()}>{copied ? "Phone copied" : "Copy phone number"}</button>}
              {canManageDrivers && <Link className="driver-secondary-action" to={`/drivers/${selectedDriver.driver.driver_id}/edit`}>Edit Driver</Link>}
            </div>
          </section>
        </div>
      )}
    </MainLayout>
  );
}

export default Drivers;
