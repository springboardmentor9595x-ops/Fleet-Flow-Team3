import { useContext, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./vehicle.css";

function Vehicles() {
  const { user } = useContext(AuthContext);
  const [vehicles, setVehicles] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [maintenanceHistory, setMaintenanceHistory] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const canManageVehicles = ["Admin", "FleetManager"].includes(user?.role);

  const loadVehicles = async () => {
    try {
      const response = await api.get("/vehicles/");
      setVehicles(response.data);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || "Unable to load vehicles."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(loadVehicles, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!selectedVehicle) {
      setMaintenanceHistory([]);
      return;
    }
    api.get(`/maintenance/vehicle/${selectedVehicle.vehicle_id}`)
      .then((response) => setMaintenanceHistory(response.data))
      .catch(() => setMaintenanceHistory([]));
  }, [selectedVehicle]);

  const filteredVehicles = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return vehicles.filter((vehicle) => {
      const matchesSearch =
        !normalizedSearch ||
        vehicle.registration_number.toLowerCase().includes(normalizedSearch);

      const matchesStatus =
        statusFilter === "All" || vehicle.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [vehicles, search, statusFilter]);

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading fleet vehicles..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Fleet Management"
        title="Vehicles"
        description="View fleet readiness, update vehicle records, and monitor operational assignments."
        actionLabel={canManageVehicles ? "Add Vehicle" : undefined}
        actionTo={canManageVehicles ? "/vehicles/add" : undefined}
      />

      {error && <div className="vehicle-page-error">{error}</div>}

      <section className="vehicle-toolbar">
        <div>
          <h2>Fleet records</h2>
          <p>
            {filteredVehicles.length} of {vehicles.length} vehicles shown
          </p>
        </div>

        <div className="vehicle-toolbar-controls">
          <SearchBar
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search vehicle number"
          />

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter vehicles by status"
          >
            <option value="All">All statuses</option>
            <option value="Available">Available</option>
            <option value="Assigned">Assigned</option>
            <option value="Maintenance">Maintenance</option>
            <option value="In Transit">In Transit</option>
          </select>
        </div>
      </section>

      {filteredVehicles.length === 0 ? (
        <EmptyState
          title={vehicles.length ? "No matching vehicles" : "No vehicles yet"}
          description={
            vehicles.length
              ? "Try another vehicle number or status filter."
              : "Vehicle records will appear here once they are registered."
          }
          action={
            canManageVehicles ? (
              <Link className="primary-button" to="/vehicles/add">
                Add Vehicle
              </Link>
            ) : null
          }
        />
      ) : (
        <section className="vehicle-table-card">
          <div className="vehicle-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Vehicle</th>
                  <th>Type</th>
                  <th>Fuel</th>
                  <th>Capacity</th>
                  <th>Status</th>
                  <th className="vehicle-actions-column">Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredVehicles.map((vehicle) => (
                  <tr key={vehicle.vehicle_id}>
                    <td>
                      <strong>{vehicle.registration_number}</strong>
                      <span>
                        {vehicle.brand} {vehicle.model} ·{" "}
                        {vehicle.manufacture_year}
                      </span>
                    </td>
                    <td>{vehicle.vehicle_type}</td>
                    <td>{vehicle.fuel_type}</td>
                    <td>{vehicle.capacity}</td>
                    <td>
                      <StatusBadge status={vehicle.status} />
                    </td>
                    <td className="vehicle-row-actions">
                      <button
                        className="vehicle-view-button"
                        onClick={() => setSelectedVehicle(vehicle)}
                      >
                        View
                      </button>

                      {canManageVehicles && (
                        <Link
                          className="vehicle-edit-button"
                          to={`/vehicles/edit/${vehicle.vehicle_id}`}
                        >
                          Edit
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {selectedVehicle && (
        <div
          className="vehicle-modal-backdrop"
          onClick={() => setSelectedVehicle(null)}
        >
          <section
            className="vehicle-detail-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="vehicle-modal-heading">
              <div>
                <p>Vehicle summary</p>
                <h2>{selectedVehicle.registration_number}</h2>
              </div>

              <button
                onClick={() => setSelectedVehicle(null)}
                aria-label="Close vehicle summary"
              >
                ×
              </button>
            </div>

            <div className="vehicle-modal-grid">
              <div>
                <span>Type</span>
                <strong>{selectedVehicle.vehicle_type}</strong>
              </div>
              <div>
                <span>Status</span>
                <StatusBadge status={selectedVehicle.status} />
              </div>
              <div>
                <span>Brand and model</span>
                <strong>
                  {selectedVehicle.brand} {selectedVehicle.model}
                </strong>
              </div>
              <div>
                <span>Manufacture year</span>
                <strong>{selectedVehicle.manufacture_year}</strong>
              </div>
              <div>
                <span>Fuel type</span>
                <strong>{selectedVehicle.fuel_type}</strong>
              </div>
              <div>
                <span>Capacity</span>
                <strong>{selectedVehicle.capacity}</strong>
              </div>
            </div>

            <section className="vehicle-maintenance-history">
              <p>Maintenance history</p>
              {maintenanceHistory.length ? (
                maintenanceHistory.slice(0, 5).map((record) => (
                  <div key={record.maintenance_id}>
                    <strong>{record.maintenance_type}</strong>
                    <span>
                      {record.next_service_date
                        ? `Next service: ${new Date(record.next_service_date).toLocaleDateString()}`
                        : "No next service date"}
                    </span>
                  </div>
                ))
              ) : (
                <span>No maintenance records yet.</span>
              )}
            </section>

            <button
              className="vehicle-modal-close"
              onClick={() => setSelectedVehicle(null)}
            >
              Close
            </button>
          </section>
        </div>
      )}
    </MainLayout>
  );
}

export default Vehicles;
