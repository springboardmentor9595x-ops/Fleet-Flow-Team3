import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Trip.css";

const steps = ["Scheduled", "Active", "Completed"];

function TripDetail() {
  const { tripId } = useParams();
  const { user } = useContext(AuthContext);

  const [trip, setTrip] = useState(null);
  const [route, setRoute] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [shipment, setShipment] = useState(null);
  const [error, setError] = useState("");
  const [routeNotice, setRouteNotice] = useState("");
  const [working, setWorking] = useState(false);

  const isManager = ["Admin", "FleetManager"].includes(user?.role);
  const canRoute = ["Admin", "FleetManager"].includes(user?.role);

  const loadTrip = useCallback(async () => {
    try {
      const tripResponse = await api.get(`/trips/${tripId}`);
      setTrip(tripResponse.data);

      const requests = [
        api.get(`/trips/${tripId}/route`),
        api.get("/drivers/"),
        api.get("/vehicles/"),
        api.get(`/shipments/${tripResponse.data.shipment_id}`),
      ];

      const results = await Promise.allSettled(requests);

      setRoute(
        results[0].status === "fulfilled" ? results[0].value.data : null
      );
      setDrivers(
        results[1].status === "fulfilled" ? results[1].value.data : []
      );
      setVehicles(
        results[2].status === "fulfilled" ? results[2].value.data : []
      );
      setShipment(
        results[3].status === "fulfilled" ? results[3].value.data : null
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || "Unable to load trip."
      );
    }
  }, [tripId]);

  useEffect(() => {
    const timer = window.setTimeout(loadTrip, 0);
    return () => window.clearTimeout(timer);
  }, [loadTrip]);

  const driver = useMemo(
    () => drivers.find((item) => item.driver_id === trip?.driver_id),
    [drivers, trip]
  );

  const vehicle = useMemo(
    () => vehicles.find((item) => item.vehicle_id === trip?.vehicle_id),
    [trip, vehicles]
  );

  const changeState = async (action) => {
    setWorking(true);
    setError("");

    try {
      await api.patch(
        `/trips/${tripId}/${action}`,
        action === "end" ? {} : undefined
      );
      await loadTrip();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          `Unable to ${action} trip.`
      );
    } finally {
      setWorking(false);
    }
  };

  const calculateRoute = async () => {
    setWorking(true);
    setError("");

    try {
      const response = await api.post(`/trips/${tripId}/route`, {
        route_type: trip.route_type,
      });

      setRoute(response.data);
      setRouteNotice("Route calculated and saved for this scheduled trip.");
      setTrip((current) => ({
        ...current,
        route_type: response.data.route_type,
        planned_distance: response.data.planned_distance,
        estimated_duration: response.data.estimated_duration,
        eta: response.data.eta,
      }));
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to calculate the route."
      );
    } finally {
      setWorking(false);
    }
  };

  if (!trip) {
    return (
      <MainLayout>
        {error ? (
          <div className="trip-saas-error">{error}</div>
        ) : (
          <LoadingCard message="Loading trip details..." />
        )}
      </MainLayout>
    );
  }

  const canOperate = isManager || user?.role === "Driver";
  const currentStep = steps.indexOf(trip.status);

  return (
    <MainLayout>
      <PageHeader
        eyebrow={`Trip ${trip.trip_id.slice(0, 8)}`}
        title={`${trip.source} to ${trip.destination}`}
        description={`Route type: ${trip.route_type}`}
      />

      {error && <div className="trip-saas-error">{error}</div>}
      {routeNotice && <div className="trip-saas-notice">{routeNotice}</div>}

      <section className="trip-detail-hero">
        <div>
          <StatusBadge status={trip.status} />
          <h2>{trip.trip_id}</h2>
          <p>
            Created {new Date(trip.created_at).toLocaleString()}
          </p>
        </div>

        <div className="trip-detail-buttons">
          {canRoute && (
            <button
              className="trip-route-button"
              onClick={calculateRoute}
              disabled={working}
            >
              {working ? "Calculating..." : "Calculate Route"}
            </button>
          )}

          {canOperate && trip.status === "Scheduled" && (
            <button
              className="trip-primary-action"
              onClick={() => changeState("start")}
              disabled={working}
            >
              {working ? "Starting..." : "Start Trip"}
            </button>
          )}

          {canOperate && trip.status === "Active" && (
            <button
              className="trip-complete-action"
              onClick={() => changeState("end")}
              disabled={working}
            >
              {working ? "Ending..." : "End Trip"}
            </button>
          )}
        </div>
      </section>

      <section className="trip-timeline-card">
        <div className="trip-card-heading">
          <div>
            <p>Trip lifecycle</p>
            <h2>Progress timeline</h2>
          </div>
          <StatusBadge status={trip.status} />
        </div>

        <div className="trip-timeline">
          {steps.map((step, index) => (
            <div
              className={`trip-timeline-step ${
                currentStep >= index ? "complete" : ""
              }`}
              key={step}
            >
              <span>{index + 1}</span>
              <strong>{step}</strong>
            </div>
          ))}
        </div>
      </section>

      {route && (
        <section className="trip-metric-grid">
          <article>
            <span>Distance</span>
            <strong>{(route.planned_distance / 1000).toFixed(1)} km</strong>
          </article>

          <article>
            <span>Estimated Duration</span>
            <strong>{Math.round(route.estimated_duration / 60)} min</strong>
          </article>

          <article>
            <span>ETA</span>
            <strong>{new Date(route.eta).toLocaleString()}</strong>
          </article>

          {trip.status === "Active" && (
            <article>
              <span>Remaining Distance</span>
              <strong>
                {route.remaining_distance != null
                  ? `${(route.remaining_distance / 1000).toFixed(1)} km`
                  : "Waiting for GPS"}
              </strong>
            </article>
          )}
        </section>
      )}

      <section className="trip-information-grid">
        <article>
          <p>Route summary</p>
          <h2>Delivery route</h2>
          <div>
            <span>Source</span>
            <strong>{trip.source}</strong>
          </div>
          <div>
            <span>Destination</span>
            <strong>{trip.destination}</strong>
          </div>
          <div>
            <span>Route type</span>
            <strong>{trip.route_type}</strong>
          </div>
        </article>

        <article>
          <p>Driver</p>
          <h2>{driver?.full_name || "Assigned driver"}</h2>
          <div>
            <span>Driver ID</span>
            <strong>{trip.driver_id}</strong>
          </div>
          <div>
            <span>Started</span>
            <strong>
              {trip.started_at
                ? new Date(trip.started_at).toLocaleString()
                : "Not started"}
            </strong>
          </div>
        </article>

        <article>
          <p>Vehicle</p>
          <h2>{vehicle?.registration_number || "Assigned vehicle"}</h2>
          <div>
            <span>Vehicle type</span>
            <strong>{vehicle?.vehicle_type || trip.vehicle_id}</strong>
          </div>
          <div>
            <span>Vehicle status</span>
            <strong>{vehicle?.status || "Not available"}</strong>
          </div>
        </article>

        <article>
          <p>Shipment</p>
          <h2>{shipment?.tracking_number || "Linked shipment"}</h2>
          <div>
            <span>Customer</span>
            <strong>{shipment?.customer_name || "Not available"}</strong>
          </div>
          <div>
            <span>Shipment status</span>
            <strong>{shipment?.status || "Not available"}</strong>
          </div>
        </article>
      </section>

      <Link className="trip-back-link" to="/trips">
        Back to Trips
      </Link>
    </MainLayout>
  );
}

export default TripDetail;
