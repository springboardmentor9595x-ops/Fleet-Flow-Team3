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
import "./Trip.css";

function TripList() {
  const { user } = useContext(AuthContext);
  const [trips, setTrips] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const canSchedule = ["Admin", "FleetManager"].includes(user?.role);

  useEffect(() => {
    const loadTrips = async () => {
      try {
        const [tripResponse, driverResponse, vehicleResponse] =
          await Promise.all([
            api.get("/trips/"),
            api.get("/drivers/"),
            api.get("/vehicles/"),
          ]);

        setTrips(tripResponse.data);
        setDrivers(driverResponse.data);
        setVehicles(vehicleResponse.data);
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail || "Unable to load trips."
        );
      } finally {
        setLoading(false);
      }
    };

    const timer = window.setTimeout(loadTrips, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const detailsFor = (trip) => ({
    driver: drivers.find((driver) => driver.driver_id === trip.driver_id),
    vehicle: vehicles.find((vehicle) => vehicle.vehicle_id === trip.vehicle_id),
  });

  const filteredTrips = useMemo(() => {
    const query = search.trim().toLowerCase();

    return trips.filter((trip) => {
      const { driver, vehicle } = detailsFor(trip);

      const matchesSearch =
        !query ||
        trip.trip_id.toLowerCase().includes(query) ||
        driver?.full_name?.toLowerCase().includes(query) ||
        vehicle?.registration_number?.toLowerCase().includes(query) ||
        trip.driver_id.toLowerCase().includes(query) ||
        trip.vehicle_id.toLowerCase().includes(query);

      const matchesStatus =
        statusFilter === "All" || trip.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [drivers, search, statusFilter, trips, vehicles]);

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading trip records..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Trip Management"
        title="Trips"
        description="Manage scheduled, active, and completed delivery trips."
        actionLabel={canSchedule ? "Schedule Trip" : undefined}
        actionTo={canSchedule ? "/trips/schedule" : undefined}
      />

      {error && <div className="trip-saas-error">{error}</div>}

      <section className="trip-saas-toolbar">
        <div>
          <h2>Trip directory</h2>
          <p>{filteredTrips.length} of {trips.length} trips shown</p>
        </div>

        <div className="trip-saas-controls">
          <SearchBar
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search trip, driver, or vehicle"
          />

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter trips by status"
          >
            <option value="All">All statuses</option>
            <option value="Scheduled">Scheduled</option>
            <option value="Active">Active</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
      </section>

      {filteredTrips.length === 0 ? (
        <EmptyState
          title={trips.length ? "No matching trips" : "No trips scheduled"}
          description={
            trips.length
              ? "Try another search term or status filter."
              : "Scheduled trips will appear here."
          }
          action={
            canSchedule ? (
              <Link className="primary-button" to="/trips/schedule">
                Schedule Trip
              </Link>
            ) : null
          }
        />
      ) : (
        <section className="trip-saas-table-card">
          <div className="trip-saas-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Trip</th>
                  <th>Route</th>
                  <th>Driver</th>
                  <th>Vehicle</th>
                  <th>ETA</th>
                  <th>Status</th>
                  <th className="trip-actions-column">Action</th>
                </tr>
              </thead>

              <tbody>
                {filteredTrips.map((trip) => {
                  const { driver, vehicle } = detailsFor(trip);

                  return (
                    <tr key={trip.trip_id}>
                      <td>
                        <strong>{trip.trip_id.slice(0, 8)}</strong>
                        <span>{trip.route_type}</span>
                      </td>
                      <td>
                        <strong>{trip.source}</strong>
                        <span>to {trip.destination}</span>
                      </td>
                      <td>{driver?.full_name || "Assigned driver"}</td>
                      <td>
                        {vehicle?.registration_number || "Assigned vehicle"}
                      </td>
                      <td>
                        {trip.eta
                          ? new Date(trip.eta).toLocaleString()
                          : "Not calculated"}
                      </td>
                      <td>
                        <StatusBadge status={trip.status} />
                      </td>
                      <td className="trip-row-actions">
                        <Link to={`/trips/${trip.trip_id}`}>View</Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </MainLayout>
  );
}

export default TripList;