import { useEffect, useState } from "react";
import {
  Plus,
  Pencil,
  Trash2,
  Search,
  X,
  RefreshCw,
} from "lucide-react";

import Sidebar from "../../components/layout/Sidebar";
import api from "../../api/axios";

export default function Trips() {
  const [trips, setTrips] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingTrip, setEditingTrip] = useState(null);

  const [form, setForm] = useState({
    vehicle_id: "",
    driver_id: "",
    shipment_id: "",
    start_location: "",
    destination: "",
    start_time: "",
    end_time: "",
    distance: "",
  });

  // =========================================================
  // LOAD ALL TRIP DATA
  // =========================================================

  const loadData = async () => {
    setLoading(true);

    try {
      const [
        tripsResponse,
        vehiclesResponse,
        driversResponse,
        shipmentsResponse,
        usersResponse,
      ] = await Promise.all([
        api.get("/trips/"),
        api.get("/vehicles/"),
        api.get("/drivers/"),
        api.get("/shipments/"),
        api.get("/users/"),
      ]);

      console.log("Trips:", tripsResponse.data);
      console.log("Vehicles:", vehiclesResponse.data);
      console.log("Drivers:", driversResponse.data);
      console.log("Shipments:", shipmentsResponse.data);
      console.log("Users:", usersResponse.data);

      setTrips(
        Array.isArray(tripsResponse.data)
          ? tripsResponse.data
          : []
      );

      setVehicles(
        Array.isArray(vehiclesResponse.data)
          ? vehiclesResponse.data
          : []
      );

      setDrivers(
        Array.isArray(driversResponse.data)
          ? driversResponse.data
          : []
      );

      setShipments(
        Array.isArray(shipmentsResponse.data)
          ? shipmentsResponse.data
          : []
      );

      setUsers(
        Array.isArray(usersResponse.data)
          ? usersResponse.data
          : []
      );
    } catch (error) {
      console.error("Failed to load trip data:", error);

      alert(
        error.response?.data?.detail ||
          "Unable to load trip data."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // =========================================================
  // RESET FORM
  // =========================================================

  const resetForm = () => {
    setForm({
      vehicle_id: "",
      driver_id: "",
      shipment_id: "",
      start_location: "",
      destination: "",
      start_time: "",
      end_time: "",
      distance: "",
    });
  };

  // =========================================================
  // OPEN ADD FORM
  // =========================================================

  const openAddForm = () => {
    setEditingTrip(null);
    resetForm();
    setShowForm(true);
  };

  // =========================================================
  // OPEN EDIT FORM
  // =========================================================

  const openEditForm = (trip) => {
    setEditingTrip(trip);

    setForm({
      vehicle_id: trip.vehicle_id || "",
      driver_id: trip.driver_id || "",
      shipment_id: trip.shipment_id || "",
      start_location: trip.start_location || "",
      destination: trip.destination || "",
      start_time: formatDateTimeForInput(
        trip.start_time
      ),
      end_time: formatDateTimeForInput(
        trip.end_time
      ),
      distance:
        trip.distance !== null &&
        trip.distance !== undefined
          ? String(trip.distance)
          : "",
    });

    setShowForm(true);
  };

  // =========================================================
  // CLOSE FORM
  // =========================================================

  const closeForm = () => {
    if (saving) {
      return;
    }

    setShowForm(false);
    setEditingTrip(null);
    resetForm();
  };

  // =========================================================
  // DATE FORMATTER
  // =========================================================

  const formatDateTimeForInput = (value) => {
    if (!value) {
      return "";
    }

    try {
      const date = new Date(value);

      if (Number.isNaN(date.getTime())) {
        return "";
      }

      const year = date.getFullYear();

      const month = String(
        date.getMonth() + 1
      ).padStart(2, "0");

      const day = String(
        date.getDate()
      ).padStart(2, "0");

      const hours = String(
        date.getHours()
      ).padStart(2, "0");

      const minutes = String(
        date.getMinutes()
      ).padStart(2, "0");

      return `${year}-${month}-${day}T${hours}:${minutes}`;
    } catch {
      return "";
    }
  };

  // =========================================================
  // GET VEHICLE DISPLAY NAME
  // =========================================================

  const getVehicleName = (vehicleId) => {
    if (!vehicleId) {
      return "Not assigned";
    }

    const vehicle = vehicles.find(
      (item) =>
        String(item.vehicle_id) ===
        String(vehicleId)
    );

    if (!vehicle) {
      return String(vehicleId);
    }

    return (
      vehicle.registration_number ||
      vehicle.license_plate ||
      vehicle.vehicle_number ||
      vehicle.vehicle_name ||
      vehicle.vehicle_id
    );
  };

  // =========================================================
  // GET USER DISPLAY NAME
  // =========================================================

  const getUserName = (userId) => {
    if (!userId) {
      return null;
    }

    const user = users.find(
      (item) =>
        String(item.user_id) ===
        String(userId)
    );

    if (!user) {
      return null;
    }

    return (
      user.full_name ||
      user.name ||
      user.email ||
      null
    );
  };

  // =========================================================
  // GET DRIVER DISPLAY NAME
  // =========================================================

  const getDriverName = (driverId) => {
    if (!driverId) {
      return "Not assigned";
    }

    const driver = drivers.find(
      (item) =>
        String(item.driver_id) ===
        String(driverId)
    );

    if (!driver) {
      return String(driverId);
    }

    // If Driver API already returns nested user
    if (
      driver.user &&
      driver.user.full_name
    ) {
      return driver.user.full_name;
    }

    // If driver directly contains full_name
    if (driver.full_name) {
      return driver.full_name;
    }

    // If driver directly contains name
    if (driver.name) {
      return driver.name;
    }

    // If driver has user_id, find user
    if (driver.user_id) {
      const userName = getUserName(
        driver.user_id
      );

      if (userName) {
        return userName;
      }
    }

    // Final fallback
    return driver.driver_id;
  };

  // =========================================================
  // GET SHIPMENT DISPLAY NAME
  // =========================================================

  const getShipmentName = (shipmentId) => {
    if (!shipmentId) {
      return "Not assigned";
    }

    const shipment = shipments.find(
      (item) =>
        String(item.shipment_id) ===
        String(shipmentId)
    );

    if (!shipment) {
      return String(shipmentId);
    }

    return (
      shipment.tracking_number ||
      shipment.shipment_id
    );
  };

  // =========================================================
  // AUTO-FILL LOCATION FROM SHIPMENT
  // =========================================================

  const handleShipmentChange = (event) => {
    const shipmentId = event.target.value;

    const shipment = shipments.find(
      (item) =>
        String(item.shipment_id) ===
        String(shipmentId)
    );

    setForm((previous) => ({
      ...previous,
      shipment_id: shipmentId,

      start_location:
        previous.start_location ||
        shipment?.source ||
        "",

      destination:
        previous.destination ||
        shipment?.destination ||
        "",
    }));
  };

  // =========================================================
  // FORM CHANGE
  // =========================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // =========================================================
  // SUBMIT
  // =========================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!form.vehicle_id) {
      alert("Please select a vehicle.");
      return;
    }

    if (!form.driver_id) {
      alert("Please select a driver.");
      return;
    }

    if (!form.shipment_id) {
      alert("Please select a shipment.");
      return;
    }

    if (!form.start_location.trim()) {
      alert("Please enter the start location.");
      return;
    }

    if (!form.destination.trim()) {
      alert("Please enter the destination.");
      return;
    }

    setSaving(true);

    try {
      const data = {
        vehicle_id: form.vehicle_id,
        driver_id: form.driver_id,
        shipment_id: form.shipment_id,

        start_location:
          form.start_location.trim(),

        destination:
          form.destination.trim(),

        start_time:
          form.start_time || null,

        end_time:
          form.end_time || null,

        distance:
          form.distance !== ""
            ? Number(form.distance)
            : null,
      };

      console.log(
        editingTrip
          ? "Updating trip:"
          : "Creating trip:",
        data
      );

      if (editingTrip) {
        await api.put(
          `/trips/${editingTrip.trip_id}`,
          data
        );
      } else {
        await api.post(
          "/trips/",
          data
        );
      }

      setShowForm(false);
      setEditingTrip(null);
      resetForm();

      await loadData();
    } catch (error) {
      console.error(
        "Trip save failed:",
        error
      );

      const detail =
        error.response?.data?.detail;

      if (Array.isArray(detail)) {
        alert(
          detail
            .map(
              (item) =>
                item.msg || String(item)
            )
            .join("\n")
        );
      } else {
        alert(
          detail ||
            "Unable to save trip."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  // =========================================================
  // DELETE TRIP
  // =========================================================

  const deleteTrip = async (tripId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this trip?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await api.delete(
        `/trips/${tripId}`
      );

      await loadData();
    } catch (error) {
      console.error(
        "Trip deletion failed:",
        error
      );

      alert(
        error.response?.data?.detail ||
          "Unable to delete trip."
      );
    }
  };

  // =========================================================
  // SEARCH
  // =========================================================

  const filteredTrips = trips.filter(
    (trip) => {
      const query =
        search.toLowerCase();

      const vehicleName =
        getVehicleName(
          trip.vehicle_id
        ).toLowerCase();

      const driverName =
        getDriverName(
          trip.driver_id
        ).toLowerCase();

      const shipmentName =
        getShipmentName(
          trip.shipment_id
        ).toLowerCase();

      return (
        String(
          trip.trip_id || ""
        )
          .toLowerCase()
          .includes(query) ||

        vehicleName.includes(query) ||

        driverName.includes(query) ||

        shipmentName.includes(query) ||

        String(
          trip.start_location || ""
        )
          .toLowerCase()
          .includes(query) ||

        String(
          trip.destination || ""
        )
          .toLowerCase()
          .includes(query) ||

        String(
          trip.status || ""
        )
          .toLowerCase()
          .includes(query)
      );
    }
  );

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div style={styles.app}>
      <Sidebar />

      <div style={styles.content}>
        {/* HEADER */}

        <header style={styles.header}>
          <div>
            <h1 style={styles.title}>
              Trips
            </h1>

            <p style={styles.subtitle}>
              Schedule and manage fleet trips
            </p>
          </div>

          <div style={styles.headerActions}>
            <button
              style={styles.refreshButton}
              onClick={loadData}
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw size={18} />
              Refresh
            </button>

            <button
              style={styles.addButton}
              onClick={openAddForm}
            >
              <Plus size={18} />
              Add Trip
            </button>
          </div>
        </header>

        {/* MAIN */}

        <main style={styles.main}>
          {/* TOOLBAR */}

          <div style={styles.toolbar}>
            <div style={styles.searchBox}>
              <Search
                size={19}
                color="#64748b"
              />

              <input
                type="text"
                placeholder="Search trips..."
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                style={styles.searchInput}
              />
            </div>

            <div style={styles.count}>
              {filteredTrips.length} trip
              {filteredTrips.length !== 1
                ? "s"
                : ""}
            </div>
          </div>

          {/* TABLE */}

          <section style={styles.tableCard}>
            {loading ? (
              <div style={styles.message}>
                Loading trips...
              </div>
            ) : filteredTrips.length === 0 ? (
              <div style={styles.empty}>
                <h3>
                  No trips found
                </h3>

                <p>
                  Create your first trip
                  to get started.
                </p>

                <button
                  style={styles.addButton}
                  onClick={openAddForm}
                >
                  <Plus size={18} />
                  Add Trip
                </button>
              </div>
            ) : (
              <div
                style={
                  styles.tableWrapper
                }
              >
                <table
                  style={styles.table}
                >
                  <thead>
                    <tr>
                      <th>Trip ID</th>
                      <th>Vehicle</th>
                      <th>Driver</th>
                      <th>Shipment</th>
                      <th>Route</th>
                      <th>Distance</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredTrips.map(
                      (trip) => (
                        <tr
                          key={
                            trip.trip_id
                          }
                        >
                          <td>
                            <strong>
                              {String(
                                trip.trip_id
                              ).slice(
                                0,
                                8
                              )}
                              ...
                            </strong>
                          </td>

                          <td>
                            {getVehicleName(
                              trip.vehicle_id
                            )}
                          </td>

                          <td>
                            {getDriverName(
                              trip.driver_id
                            )}
                          </td>

                          <td>
                            {getShipmentName(
                              trip.shipment_id
                            )}
                          </td>

                          <td>
                            <strong>
                              {trip.start_location ||
                                "Unknown"}
                            </strong>

                            {" → "}

                            <strong>
                              {trip.destination ||
                                "Unknown"}
                            </strong>
                          </td>

                          <td>
                            {trip.distance !==
                              null &&
                            trip.distance !==
                              undefined
                              ? `${trip.distance} km`
                              : "—"}
                          </td>

                          <td>
                            <span
                              style={{
                                ...styles.status,
                                ...getStatusStyle(
                                  trip.status
                                ),
                              }}
                            >
                              {trip.status ||
                                "Scheduled"}
                            </span>
                          </td>

                          <td>
                            <div
                              style={
                                styles.actions
                              }
                            >
                              <button
                                style={
                                  styles.editButton
                                }
                                onClick={() =>
                                  openEditForm(
                                    trip
                                  )
                                }
                                title="Edit trip"
                              >
                                <Pencil
                                  size={17}
                                />
                              </button>

                              <button
                                style={
                                  styles.deleteButton
                                }
                                onClick={() =>
                                  deleteTrip(
                                    trip.trip_id
                                  )
                                }
                                title="Delete trip"
                              >
                                <Trash2
                                  size={17}
                                />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </main>

        {/* ADD / EDIT MODAL */}

        {showForm && (
          <div style={styles.overlay}>
            <div style={styles.modal}>
              {/* MODAL HEADER */}

              <div
                style={
                  styles.modalHeader
                }
              >
                <div>
                  <h2
                    style={
                      styles.modalTitle
                    }
                  >
                    {editingTrip
                      ? "Edit Trip"
                      : "Add Trip"}
                  </h2>

                  <p
                    style={
                      styles.modalSubtitle
                    }
                  >
                    Select the vehicle,
                    driver and shipment
                    for this trip.
                  </p>
                </div>

                <button
                  style={
                    styles.closeButton
                  }
                  onClick={closeForm}
                  disabled={saving}
                >
                  <X size={22} />
                </button>
              </div>

              <form
                onSubmit={handleSubmit}
              >
                {/* VEHICLE */}

                <label
                  style={styles.label}
                >
                  Vehicle
                </label>

                <select
                  name="vehicle_id"
                  value={
                    form.vehicle_id
                  }
                  onChange={
                    handleChange
                  }
                  style={styles.input}
                  disabled={saving}
                  required
                >
                  <option value="">
                    Select Vehicle
                  </option>

                  {vehicles.map(
                    (vehicle) => (
                      <option
                        key={
                          vehicle.vehicle_id
                        }
                        value={
                          vehicle.vehicle_id
                        }
                      >
                        {vehicle.registration_number ||
                          vehicle.license_plate ||
                          vehicle.vehicle_number ||
                          vehicle.vehicle_id}
                      </option>
                    )
                  )}
                </select>

                {/* DRIVER */}

                <label
                  style={styles.label}
                >
                  Driver
                </label>

                <select
                  name="driver_id"
                  value={
                    form.driver_id
                  }
                  onChange={
                    handleChange
                  }
                  style={styles.input}
                  disabled={saving}
                  required
                >
                  <option value="">
                    Select Driver
                  </option>

                  {drivers.map(
                    (driver) => (
                      <option
                        key={
                          driver.driver_id
                        }
                        value={
                          driver.driver_id
                        }
                      >
                        {getDriverName(
                          driver.driver_id
                        )}
                      </option>
                    )
                  )}
                </select>

                {/* SHIPMENT */}

                <label
                  style={styles.label}
                >
                  Shipment
                </label>

                <select
                  name="shipment_id"
                  value={
                    form.shipment_id
                  }
                  onChange={
                    handleShipmentChange
                  }
                  style={styles.input}
                  disabled={saving}
                  required
                >
                  <option value="">
                    Select Shipment
                  </option>

                  {shipments.map(
                    (shipment) => (
                      <option
                        key={
                          shipment.shipment_id
                        }
                        value={
                          shipment.shipment_id
                        }
                      >
                        {shipment.tracking_number ||
                          shipment.shipment_id}
                      </option>
                    )
                  )}
                </select>

                {/* LOCATION GRID */}

                <div
                  style={
                    styles.twoColumn
                  }
                >
                  <div>
                    <label
                      style={
                        styles.label
                      }
                    >
                      Start Location
                    </label>

                    <input
                      type="text"
                      name="start_location"
                      value={
                        form.start_location
                      }
                      onChange={
                        handleChange
                      }
                      placeholder="e.g. Greater Noida"
                      style={
                        styles.input
                      }
                      disabled={saving}
                      required
                    />
                  </div>

                  <div>
                    <label
                      style={
                        styles.label
                      }
                    >
                      Destination
                    </label>

                    <input
                      type="text"
                      name="destination"
                      value={
                        form.destination
                      }
                      onChange={
                        handleChange
                      }
                      placeholder="e.g. Delhi"
                      style={
                        styles.input
                      }
                      disabled={saving}
                      required
                    />
                  </div>
                </div>

                {/* TIME GRID */}

                <div
                  style={
                    styles.twoColumn
                  }
                >
                  <div>
                    <label
                      style={
                        styles.label
                      }
                    >
                      Start Time
                    </label>

                    <input
                      type="datetime-local"
                      name="start_time"
                      value={
                        form.start_time
                      }
                      onChange={
                        handleChange
                      }
                      style={
                        styles.input
                      }
                      disabled={saving}
                    />
                  </div>

                  <div>
                    <label
                      style={
                        styles.label
                      }
                    >
                      End Time
                    </label>

                    <input
                      type="datetime-local"
                      name="end_time"
                      value={
                        form.end_time
                      }
                      onChange={
                        handleChange
                      }
                      style={
                        styles.input
                      }
                      disabled={saving}
                    />
                  </div>
                </div>

                {/* DISTANCE */}

                <label
                  style={styles.label}
                >
                  Distance (km)
                </label>

                <input
                  type="number"
                  name="distance"
                  value={
                    form.distance
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="e.g. 35"
                  min="0"
                  step="0.1"
                  style={styles.input}
                  disabled={saving}
                />

                {/* BUTTONS */}

                <div
                  style={
                    styles.modalActions
                  }
                >
                  <button
                    type="button"
                    style={
                      styles.cancelButton
                    }
                    onClick={
                      closeForm
                    }
                    disabled={saving}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    style={
                      styles.saveButton
                    }
                    disabled={saving}
                  >
                    {saving
                      ? "Saving..."
                      : editingTrip
                      ? "Update Trip"
                      : "Create Trip"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =========================================================
// STATUS STYLE
// =========================================================

function getStatusStyle(status) {
  const value = String(
    status || "Scheduled"
  ).toLowerCase();

  if (value === "completed") {
    return {
      background: "#dcfce7",
      color: "#166534",
    };
  }

  if (value === "in progress") {
    return {
      background: "#dbeafe",
      color: "#1d4ed8",
    };
  }

  if (value === "cancelled") {
    return {
      background: "#fee2e2",
      color: "#b91c1c",
    };
  }

  return {
    background: "#fef3c7",
    color: "#92400e",
  };
}

// =========================================================
// STYLES
// =========================================================

const styles = {
  app: {
    minHeight: "100vh",
    background: "#f4f7fb",
  },

  content: {
    marginLeft: "250px",
    minHeight: "100vh",
  },

  header: {
    padding: "25px 40px",
    background: "white",
    borderBottom:
      "1px solid #e5e7eb",
    display: "flex",
    justifyContent:
      "space-between",
    alignItems: "center",
  },

  title: {
    margin: 0,
    fontSize: "30px",
    color: "#172554",
  },

  subtitle: {
    marginTop: "7px",
    marginBottom: 0,
    color: "#64748b",
    fontSize: "16px",
  },

  headerActions: {
    display: "flex",
    gap: "10px",
    alignItems: "center",
  },

  addButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    padding: "11px 17px",
    border: "none",
    borderRadius: "7px",
    background: "#2563eb",
    color: "white",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
  },

  refreshButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    padding: "10px 16px",
    border:
      "1px solid #dbe2ea",
    borderRadius: "7px",
    background: "white",
    color: "#475569",
    cursor: "pointer",
    fontSize: "14px",
  },

  main: {
    padding: "30px 40px",
  },

  toolbar: {
    display: "flex",
    justifyContent:
      "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },

  searchBox: {
    width: "370px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 13px",
    background: "white",
    border:
      "1px solid #dbe2ea",
    borderRadius: "8px",
  },

  searchInput: {
    width: "100%",
    border: "none",
    outline: "none",
    fontSize: "14px",
  },

  count: {
    color: "#64748b",
    fontSize: "14px",
  },

  tableCard: {
    background: "white",
    borderRadius: "12px",
    boxShadow:
      "0 4px 15px rgba(0,0,0,0.06)",
    overflow: "hidden",
  },

  tableWrapper: {
    overflowX: "auto",
  },

  table: {
    width: "100%",
    borderCollapse:
      "collapse",
    minWidth: "1100px",
  },

  message: {
    padding: "50px",
    textAlign: "center",
    color: "#64748b",
  },

  empty: {
    padding: "70px 20px",
    textAlign: "center",
    color: "#64748b",
  },

  actions: {
    display: "flex",
    gap: "7px",
  },

  editButton: {
    width: "34px",
    height: "34px",
    display: "flex",
    alignItems: "center",
    justifyContent:
      "center",
    border: "none",
    borderRadius: "6px",
    background: "#dbeafe",
    color: "#1d4ed8",
    cursor: "pointer",
  },

  deleteButton: {
    width: "34px",
    height: "34px",
    display: "flex",
    alignItems: "center",
    justifyContent:
      "center",
    border: "none",
    borderRadius: "6px",
    background: "#fee2e2",
    color: "#dc2626",
    cursor: "pointer",
  },

  status: {
    display: "inline-block",
    padding: "6px 10px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: "600",
  },

  overlay: {
    position: "fixed",
    inset: 0,
    background:
      "rgba(15,23,42,0.45)",
    display: "flex",
    alignItems: "center",
    justifyContent:
      "center",
    padding: "20px",
    zIndex: 1000,
    overflowY: "auto",
  },

  modal: {
    width: "650px",
    maxWidth: "100%",
    maxHeight: "90vh",
    overflowY: "auto",
    background: "white",
    borderRadius: "12px",
    padding: "28px",
    boxShadow:
      "0 20px 50px rgba(0,0,0,0.2)",
  },

  modalHeader: {
    display: "flex",
    justifyContent:
      "space-between",
    alignItems:
      "flex-start",
    marginBottom: "25px",
  },

  modalTitle: {
    margin: 0,
    color: "#172554",
    fontSize: "22px",
  },

  modalSubtitle: {
    marginTop: "7px",
    marginBottom: 0,
    color: "#64748b",
    fontSize: "14px",
  },

  closeButton: {
    border: "none",
    background: "transparent",
    cursor: "pointer",
    color: "#64748b",
  },

  label: {
    display: "block",
    marginBottom: "7px",
    marginTop: "18px",
    fontSize: "14px",
    fontWeight: "600",
    color: "#334155",
  },

  input: {
    width: "100%",
    boxSizing: "border-box",
    padding: "11px",
    border:
      "1px solid #cbd5e1",
    borderRadius: "7px",
    outline: "none",
    fontSize: "14px",
    background: "white",
  },

  twoColumn: {
    display: "grid",
    gridTemplateColumns:
      "1fr 1fr",
    gap: "15px",
  },

  modalActions: {
    display: "flex",
    justifyContent:
      "flex-end",
    gap: "10px",
    marginTop: "30px",
    paddingTop: "20px",
    borderTop:
      "1px solid #e5e7eb",
  },

  cancelButton: {
    padding: "11px 18px",
    border:
      "1px solid #cbd5e1",
    borderRadius: "7px",
    background: "white",
    color: "#334155",
    cursor: "pointer",
  },

  saveButton: {
    padding: "11px 20px",
    border: "none",
    borderRadius: "7px",
    background: "#2563eb",
    color: "white",
    fontWeight: "600",
    cursor: "pointer",
  },
};