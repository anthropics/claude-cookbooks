"""
Example Mock API for Drone Delivery Demo

This is a domain-specific API used in the programmatic tool calling cookbook.
It provides mock tools for drone delivery operations including delivery logs,
container logs, and pod health checks.
"""

import json
import random
import time
from datetime import datetime, timedelta

from anthropic import beta_tool

DELIVERY_LOGS_COUNT = 500
CONTAINER_LOGS_COUNT = 500
DELAY_MULTIPLIER = 0  # Adjust this to speed up or slow down simulated delays


@beta_tool
def get_delivery_logs(start_time: str | None = None, end_time: str | None = None) -> str:
    """Returns unstructured backend application logs for drone delivery operations.

    Includes order creation, job assignments, delivery status, warnings, and errors from the
    drone delivery system. Use this to identify which jobs failed and what error codes were
    reported. Logs include timestamp, log level (INFO/WARN/ERROR), job_id, drone_id, and message.
    Logs should be processed programmatically to extract relevant information.

    Example log line format: '2025-06-02T13:30:45Z [ERROR] Job J_42 FAILED: BATTERY_CRITICAL'.
    Note this is a toy API, therefore subsequent calls will return different logs and timestamps.
    For demo purposes, this is okay.

    Args:
        start_time: ISO format timestamp (e.g., '2024-01-15T10:00:00Z') for the beginning of
            the log range. Defaults to 1 hour ago if not specified.
        end_time: ISO format timestamp (e.g., '2024-01-15T11:00:00Z') for the end of the log
            range. Defaults to current time if not specified.

    Returns:
        Newline-separated log entries
    """
    # Parse time range
    start_dt: datetime
    end_dt: datetime

    if start_time is None:
        start_dt = datetime.now() - timedelta(hours=1)
    else:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

    if end_time is None:
        end_dt = datetime.now()
    else:
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    # Validate time range
    if start_dt >= end_dt:
        raise ValueError(
            f"start_time must be before end_time. Got start_time={start_dt}, end_time={end_dt}"
        )

    logs = []
    num_logs = DELIVERY_LOGS_COUNT  # Total number of logs to generate

    # Log templates
    log_templates = [
        ("[INFO]", "Order O_{order_id} created"),
        ("[INFO]", "Order O_{order_id} validated"),
        ("[INFO]", "Order O_{order_id} payment processed"),
        ("[INFO]", "Order O_{order_id} item picked from warehouse"),
        ("[INFO]", "Order O_{order_id} package sealed"),
        ("[INFO]", "Order O_{order_id} ready for dispatch"),
        ("[INFO]", "Job J_{job_id} assigned drone_{drone_id}"),
        ("[INFO]", "Job J_{job_id} pre-flight check initiated"),
        ("[INFO]", "Job J_{job_id} pre-flight check passed"),
        ("[INFO]", "Job J_{job_id} takeoff authorized"),
        ("[INFO]", "Job J_{job_id} takeoff complete"),
        ("[INFO]", "Job J_{job_id} in progress - altitude 50m"),
        ("[INFO]", "Job J_{job_id} in progress - altitude 100m"),
        ("[INFO]", "Job J_{job_id} in progress - altitude 150m"),
        ("[INFO]", "Job J_{job_id} in progress - altitude 200m"),
        ("[INFO]", "Job J_{job_id} waypoint 1 reached"),
        ("[INFO]", "Job J_{job_id} waypoint 2 reached"),
        ("[INFO]", "Job J_{job_id} waypoint 3 reached"),
        ("[INFO]", "Job J_{job_id} approaching destination"),
        ("[INFO]", "Job J_{job_id} descent initiated"),
        ("[INFO]", "Job J_{job_id} landing sequence started"),
        ("[INFO]", "Job J_{job_id} package released"),
        ("[INFO]", "Job J_{job_id} delivery successful"),
        ("[INFO]", "Job J_{job_id} delivery confirmation sent"),
        ("[INFO]", "Job J_{job_id} customer notified"),
        ("[INFO]", "Job J_{job_id} returning to base"),
        ("[INFO]", "Job J_{job_id} return altitude 150m"),
        ("[INFO]", "Job J_{job_id} return waypoint reached"),
        ("[INFO]", "Job J_{job_id} base approach initiated"),
        ("[INFO]", "Job J_{job_id} landing at base"),
        ("[INFO]", "Job J_{job_id} completed successfully"),
        ("[INFO]", "Drone drone_{drone_id} system check initiated"),
        ("[INFO]", "Drone drone_{drone_id} GPS lock acquired"),
        ("[INFO]", "Drone drone_{drone_id} compass calibrated"),
        ("[INFO]", "Drone drone_{drone_id} motors online"),
        ("[INFO]", "Drone drone_{drone_id} telemetry link established"),
        ("[INFO]", "Drone drone_{drone_id} charging initiated"),
        ("[INFO]", "Drone drone_{drone_id} charging at 50%"),
        ("[INFO]", "Drone drone_{drone_id} charging at 75%"),
        ("[INFO]", "Drone drone_{drone_id} charging complete"),
        ("[INFO]", "Drone drone_{drone_id} battery health check passed"),
        ("[INFO]", "Drone drone_{drone_id} firmware version verified"),
        ("[INFO]", "Drone drone_{drone_id} temperature nominal 28C"),
        ("[INFO]", "Drone drone_{drone_id} available for assignment"),
        ("[INFO]", "Drone drone_{drone_id} maintenance log updated"),
        ("[INFO]", "Weather data updated - conditions nominal"),
        ("[INFO]", "Air traffic control clearance received"),
        ("[INFO]", "Base station communication nominal"),
        ("[INFO]", "Fleet status synchronized"),
        ("[INFO]", "Network latency 45ms nominal"),
        ("[INFO]", "Database backup completed"),
        ("[WARN]", "Job J_{job_id} weather advisory - wind speed 25mph"),
        ("[WARN]", "Drone drone_{drone_id} battery at 30%"),
        ("[ERROR]", "Job J_{job_id} {drone_id} FAILED: BATTERY_CRITICAL"),
        ("[ERROR]", "Job J_{job_id} {drone_id} FAILED: WEATHER_ABORT"),
        ("[ERROR]", "Drone drone_{drone_id} sensor malfunction"),
    ]

    current_time = start_dt
    time_delta = (end_dt - start_dt) / num_logs
    random.seed(42)  # For reproducibility
    for i in range(num_logs):
        level, msg_template = random.choice(log_templates)  # noqa: S311

        # Generate IDs
        order_id = random.randint(1, 9)
        job_id = random.randint(1, 90)
        drone_id = f"{random.randint(1, 100):04d}"

        # Format message
        msg = msg_template.format(order_id=order_id, job_id=job_id, drone_id=drone_id)

        # Format timestamp
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        log_line = f"{timestamp} {level} {msg}"
        logs.append((current_time, log_line))

        current_time += time_delta

    # Generate some specific logs for J_42 failure
    failure_time = start_dt + (end_dt - start_dt) / 2
    return_time = failure_time + timedelta(minutes=5)

    # Add J_42 specific logs with their timestamps
    logs.append(
        (
            failure_time,
            f"{failure_time.strftime('%Y-%m-%dT%H:%M:%SZ')} [ERROR] Job J_42 FAILED: BATTERY_CRITICAL",
        )
    )
    logs.append(
        (
            return_time,
            f"{return_time.strftime('%Y-%m-%dT%H:%M:%SZ')} [INFO] Job J_42 returning to base",
        )
    )

    # Sort logs by timestamp and extract just the log lines
    logs.sort(key=lambda x: x[0])
    log_lines = [log[1] for log in logs]

    return "\n".join(log_lines)


@beta_tool
def check_pod_health(pod_prefix: str) -> str:
    """Returns health status for a specific pod type in the drone infrastructure.

    Use this for health checks to identify which systems are healthy vs degraded/unhealthy.
    Returns JSON with: status (healthy/degraded/unhealthy), response_time_ms, pod_count,
    healthy_pods, unhealthy_pods, health_percentage, and error_message if applicable.
    Health check can take between 2-5 seconds per call due to API delays.

    Example JSON response format:
    {"pod_prefix": "battery-mgmt", "status": "unhealthy", "response_time_ms": 120,
     "pod_count": 8, "healthy_pods": 3, "unhealthy_pods": 5, "health_percentage": 37.5,
     "error_message": "Critical: 5 of 8 pods are unhealthy"}

    Args:
        pod_prefix: The pod prefix to check health for. Common values: 'flight-controller',
            'battery-mgmt', 'drone-', 'navigation-service', 'weather-monitor', 'telemetry-collector'.

    Returns:
        JSON string with health status
    """

    # Set seed for reproducibility
    random.seed(hash(pod_prefix) % 100)

    # Simulate different health states based on pod type with realistic delays
    pod_health_configs = {
        "flight-controller": {
            "failure_rate": 0.05,
            "avg_response": 50,
            "delay_ms": 200,
        },
        "drone-": {"failure_rate": 0.1, "avg_response": 75, "delay_ms": 500},
        "navigation-service": {
            "failure_rate": 0.03,
            "avg_response": 45,
            "delay_ms": 150,
        },
        "weather-monitor": {"failure_rate": 0.02, "avg_response": 30, "delay_ms": 100},
        "battery-mgmt": {
            "failure_rate": 0.55,
            "avg_response": 100,
            "delay_ms": 800,
        },  # Higher failure rate and slower
        "telemetry-collector": {
            "failure_rate": 0.05,
            "avg_response": 60,
            "delay_ms": 300,
        },
    }

    config = pod_health_configs.get(
        pod_prefix, {"failure_rate": 0.05, "avg_response": 50, "delay_ms": 200}
    )

    # Simulate network/API delay
    delay_seconds = config["delay_ms"] / 1000.0
    time.sleep(delay_seconds * DELAY_MULTIPLIER)

    # Simulate pod count
    pod_count = random.randint(3, 10)
    healthy_pods = sum(1 for _ in range(pod_count) if random.random() > config["failure_rate"])

    # Calculate response time with some variance
    response_time = int(config["avg_response"] * random.uniform(0.8, 1.5))

    # Determine overall status
    health_ratio = healthy_pods / pod_count
    if health_ratio >= 0.9:
        status = "healthy"
        error_msg = None
    elif health_ratio >= 0.7:
        status = "degraded"
        error_msg = f"{pod_count - healthy_pods} of {pod_count} pods are unhealthy"
    else:
        status = "unhealthy"
        error_msg = f"Critical: {pod_count - healthy_pods} of {pod_count} pods are unhealthy"

    result = {
        "pod_prefix": pod_prefix,
        "status": status,
        "response_time_ms": response_time,
        "pod_count": pod_count,
        "healthy_pods": healthy_pods,
        "unhealthy_pods": pod_count - healthy_pods,
        "health_percentage": round(health_ratio * 100, 1),
        "error_message": error_msg,
    }

    return json.dumps(result)


@beta_tool
def get_container_logs(
    pod_name: str | None = None, start_time: str | None = None, end_time: str | None = None
) -> str:
    """Returns kubernetes-style container logs from the drone infrastructure.

    Includes logs from flight controllers, navigation services, weather monitors, battery
    management systems, and telemetry collectors. Returns JSON-formatted log entries with
    timestamp, pod name, level (INFO/WARN/ERROR), and message. Use this to investigate
    infrastructure issues that may have caused delivery failures. Filter by pod_name prefix
    to narrow results. Logs should be processed programmatically to extract relevant information.

    Example JSON log line format:
    {"timestamp": "2025-06-02T13:20:15Z", "namespace": "skynet-prod", "pod": "battery-mgmt-7a3f",
     "level": "ERROR", "msg": "battery voltage sensor malfunction - reporting incorrect readings across fleet"}

    Note this is a toy API, therefore subsequent calls will return different logs and timestamps.

    Args:
        pod_name: Optional filter to only return logs from pods whose names start with this prefix.
            Common prefixes: 'battery-mgmt' (battery management systems), 'flight-controller'
            (flight control), 'drone-' (specific drone controllers), 'navigation-service'
            (GPS/navigation), 'weather-monitor' (weather systems), 'telemetry-collector'
            (telemetry data). If not specified, returns logs from all pods (200-300 entries).
        start_time: ISO format timestamp (e.g., '2024-01-15T10:00:00Z') for the beginning of
            the log range. Defaults to 1 hour ago if not specified.
        end_time: ISO format timestamp (e.g., '2024-01-15T11:00:00Z') for the end of the log
            range. Defaults to current time if not specified.

    Returns:
        Newline-separated JSON-formatted log entry strings
    """
    random.seed(42)  # For reproducibility

    # Parse time range
    start_dt: datetime
    end_dt: datetime

    if start_time is None:
        start_dt = datetime.now() - timedelta(hours=1)
    else:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

    if end_time is None:
        end_dt = datetime.now()
    else:
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    logs = []
    num_logs = CONTAINER_LOGS_COUNT  # Total number of logs to generate

    # Pod names
    pod_prefixes = [
        "flight-controller",
        "drone-{drone_id}-controller",
        "navigation-service",
        "weather-monitor",
        "battery-mgmt",
        "telemetry-collector",
    ]

    # Log message templates
    log_messages = [
        ("INFO", "flight path calculated successfully"),
        ("INFO", "flight path validation complete"),
        ("INFO", "route optimization applied"),
        ("INFO", "collision avoidance check passed"),
        ("INFO", "no-fly zone verification complete"),
        ("INFO", "altitude clearance received"),
        ("INFO", "telemetry update received"),
        ("INFO", "telemetry data validated"),
        ("INFO", "telemetry stream healthy"),
        ("INFO", "connection established to drone_{drone_id}"),
        ("INFO", "connection health check passed for drone_{drone_id}"),
        ("INFO", "SSL handshake completed with drone_{drone_id}"),
        ("INFO", "heartbeat received from drone_{drone_id}"),
        ("INFO", "heartbeat interval normal from drone_{drone_id}"),
        ("INFO", "status check initiated"),
        ("INFO", "status check completed"),
        ("INFO", "system diagnostics passed"),
        ("INFO", "all subsystems operational"),
        ("INFO", "sensor calibration verified"),
        ("INFO", "GPS coordinates updated"),
        ("INFO", "GPS accuracy within tolerance"),
        ("INFO", "compass heading verified"),
        ("INFO", "barometer reading nominal"),
        ("INFO", "accelerometer data normal"),
        ("INFO", "gyroscope calibration stable"),
        ("INFO", "motor controller responding"),
        ("INFO", "ESC temperature normal"),
        ("INFO", "propeller RPM within limits"),
        ("INFO", "battery health check passed"),
        ("INFO", "voltage reading: 12.4V nominal"),
        ("INFO", "voltage reading: 12.3V nominal"),
        ("INFO", "voltage reading: 12.5V nominal"),
        ("INFO", "current draw nominal 15.2A"),
        ("INFO", "cell balance within tolerance"),
        ("INFO", "cell voltages synchronized"),
        ("INFO", "temperature sensors nominal"),
        ("INFO", "cooling system operating normally"),
        ("INFO", "firmware version check passed"),
        ("INFO", "configuration synchronized"),
        ("INFO", "log rotation completed"),
        ("INFO", "metrics published to monitoring"),
        ("INFO", "health endpoint responding"),
        ("INFO", "API request processed successfully"),
        ("INFO", "cache hit for configuration data"),
        ("INFO", "database query completed in 12ms"),
        ("INFO", "message queue consumer processing"),
        ("INFO", "webhook delivery successful"),
        ("INFO", "authentication token refreshed"),
        ("INFO", "session maintained"),
        ("INFO", "data backup successful"),
        ("[WARN", "battery voltage drop"),
        ("WARN", "wind speed exceeding safe limits"),
        ("WARN", "GPS signal degraded"),
        ("ERROR", "critical battery level, initiating RTB"),
        ("ERROR", "lost connection to drone_{drone_id}"),
        ("ERROR", "navigation system timeout"),
        ("INFO", "landing sequence initiated"),
        ("INFO", "landing gear deployed"),
        ("INFO", "descent rate nominal"),
        ("INFO", "ground proximity sensors active"),
        ("INFO", "touchdown successful"),
        ("INFO", "motors disarmed"),
        ("INFO", "charging cycle started"),
        ("INFO", "charging connector engaged"),
        ("INFO", "power management active"),
    ]
    # Battery management specific messages
    battery_mgmt_messages = [
        ("INFO", "battery voltage reading: 12.4V"),
        ("INFO", "battery voltage reading: 12.3V"),
        ("INFO", "battery voltage reading: 12.5V"),
        ("INFO", "battery voltage stable"),
        ("INFO", "battery health check passed for all cells"),
        ("INFO", "battery health score: 98%"),
        ("INFO", "battery calibration data refreshed"),
        ("INFO", "battery calibration scheduled"),
        ("INFO", "battery temperature: 25C nominal"),
        ("INFO", "battery temperature: 24C nominal"),
        ("INFO", "battery temperature: 26C nominal"),
        ("INFO", "battery cooling system active"),
        ("INFO", "charge cycle count incremented"),
        ("INFO", "charge cycle count: 342"),
        ("INFO", "battery management system online"),
        ("INFO", "battery controller firmware up to date"),
        ("INFO", "battery monitoring active"),
        ("INFO", "cell balancing in progress"),
        ("INFO", "cell balancing complete"),
        ("INFO", "discharge curve nominal"),
        ("INFO", "internal resistance within spec"),
        ("INFO", "charge acceptance normal"),
        ("INFO", "battery pack authenticated"),
        ("INFO", "smart battery data retrieved"),
        ("INFO", "state of health calculation complete"),
        ("INFO", "state of charge updated: 85%"),
        ("INFO", "capacity test scheduled"),
        ("INFO", "battery analytics data published"),
        ("INFO", "predictive maintenance check passed"),
        ("WARN", "battery cell imbalance detected"),
        (
            "ERROR",
            "battery voltage sensor malfunction - reporting incorrect readings across fleet",
        ),
    ]

    current_time = start_dt
    time_delta = (end_dt - current_time) / num_logs

    for _ in range(num_logs):
        # Generate pod name
        pod_prefix = random.choice(pod_prefixes)
        drone_id = f"{random.randint(100, 9999):04d}"
        pod_suffix = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=4))

        # Format pod name
        if "{drone_id}" in pod_prefix:
            pod = f"{pod_prefix.format(drone_id=drone_id)}-{pod_suffix}"
        else:
            pod = f"{pod_prefix}-{pod_suffix}"

        # Apply filter if pod_name specified
        if pod_name and not pod.startswith(pod_name):
            continue

        # Choose appropriate messages based on pod type
        if pod.startswith("battery-mgmt"):
            level, msg_template = random.choice(battery_mgmt_messages)
        else:
            level, msg_template = random.choice(log_messages)

        # Format message
        msg = msg_template.format(drone_id=drone_id)

        # Create log entry
        log_entry = {
            "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "namespace": "skynet-prod",
            "pod": pod,
            "level": level,
            "msg": msg,
        }

        logs.append(json.dumps(log_entry))
        current_time += time_delta

    # Insert specific battery management system failure around the time J_42 failed
    failure_time = current_time + (end_dt - current_time) / 2 - timedelta(minutes=10)
    battery_failure = {
        "timestamp": failure_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "namespace": "skynet-prod",
        "pod": "battery-mgmt-7a3f",
        "level": "ERROR",
        "msg": "battery voltage sensor malfunction - reporting incorrect readings across fleet",
    }

    # Insert failure in the middle of logs
    logs.insert(len(logs) // 2, json.dumps(battery_failure))

    return "\n".join(logs)


if __name__ == "__main__":
    print("=" * 80)
    print("DEMO: get_delivery_logs()")
    print("=" * 80)
    print("\nGenerating unstructured backend application logs...\n")

    delivery_logs = get_delivery_logs()
    # Show first 10 lines
    log_lines = delivery_logs
    for line in log_lines[:10]:
        print(line)
    print(f"\n... ({len(log_lines)} total log entries)\n")

    print("=" * 80)
    print("DEMO: get_container_logs()")
    print("=" * 80)
    print("\nGenerating Kubernetes-style container logs...\n")

    container_logs = get_container_logs()
    # Show first 10 lines
    log_lines = container_logs
    for line in log_lines[:10]:
        print(line)
    print(f"\n... ({len(log_lines)} total log entries)\n")

    print("=" * 80)
    print("DEMO: get_container_logs(pod_name='flight-controller')")
    print("=" * 80)
    print("\nFiltering for flight-controller pods...\n")

    filtered_logs = get_container_logs(pod_name="flight-controller")
    # Show all filtered results
    log_lines = filtered_logs
    for line in log_lines[:5]:
        print(line)
    print(f"\n... ({len(log_lines)} total log entries for flight-controller pods)")
