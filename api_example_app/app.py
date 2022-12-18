#!/usr/bin/env python3
from ipaddress import ip_address
from ipaddress import ip_network
import flask
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import Forbidden, Unauthorized, BadRequest
from prometheus_flask_exporter import PrometheusMetrics
from flask import request, jsonify, abort
import time

# Setup flask app
app = flask.Flask(__name__)
auth = HTTPTokenAuth(scheme="Bearer")
# These should be pulled from a secret management system API
tokens = {"xxxxxxxx": "User 1", "foobar": "User 2"}
# app.config["DEBUG"] = True
# Setup prometheus metrics on /metrics
metrics = PrometheusMetrics(app, path="/metrics")

# Version metric
__version__ = 1.0
metrics.info("version", "App version", version="__version__")

# Register default metrics for all endpoints
metrics.register_default(
    metrics.counter(
        "by_path_counter",
        "Request count by request paths",
        labels={"path": lambda: request.path},
    )
)

# Set up some metrics for blocked vs accepted api requests
blocked_requests_metric = metrics.info("blocked_requests", "Blocked API Requests")
accepted_requests_metric = metrics.info("accepted_requests", "Accepted API Requests")

# Tracking of blocked CIDRs - should be in a database
blocked_cidrs = {}
# Counters for blocked/accepted requests
# Could be in a database, but can also be tracked by metrics from the sum of all pods
blocked_requests = 0
accepted_requests = 0


"""
Worker and helper functions
"""


def check_allowed(ip_addr):
    # Check if an API request is allowed to accesss our app
    global blocked_requests
    global accepted_requests
    for blocked_cidr in blocked_cidrs.keys():
        if ip_address(ip_addr) in ip_network(blocked_cidr):
            blocked_requests += 1
            blocked_requests_metric.set(blocked_requests)
            raise Forbidden
    accepted_requests += 1
    accepted_requests_metric.set(accepted_requests)


def check_exempt(cidr):
    # Check if the range provided is in a block we should not accept
    # check.is_private can be used to see if the range is on a private network
    # if we don't want to target private networks
    check = ip_network(cidr)
    return any([check.is_loopback, check.is_link_local])


def add_block(payload):
    # Add a CIDR range to be blocked
    # Check data sanity
    cidr = payload.get("cidr")
    ttl = payload.get("ttl")
    # Check for missing fields
    if not all([cidr, ttl]):
        raise BadRequest("Request payload missing cidr, ttl or both")
    try:
        ttl = int(ttl)
        assert ttl > 0
    except (ValueError, AssertionError):
        raise BadRequest("ttl is not a positive integer")
    try:
        ip_network(cidr)
    except ValueError:
        raise BadRequest("cidr is not valid")
    if check_exempt(cidr):
        raise Forbidden
    if cidr not in blocked_cidrs.keys():
        blocked_cidrs[cidr] = {"ttl": ttl}


@auth.verify_token
def verify_token(token):
    # Verify token is acceptable for access
    # Should be changed to use secrets API in prod
    if token in tokens:
        return tokens[token]


"""
HTTP Routes
"""


@app.route("/", methods=["GET"])
def home():
    # Default homepage for top level
    check_allowed(request.remote_addr)
    return """
    <h1>API Example App</h1>
    <p>Example that responds on /healthcheck /metrics /stats and /block</p>
    """


@app.route("/healthcheck", methods=["GET"])
def health():
    # Healthcheck endpoint to be sure flask is up and running
    # This probably needs to allow all private traffic so it doesn't get killed
    # Uncomment to block global requests
    # if ip_address(request.remote_addr).is_global:
    #     raise werkzeug.exceptions.Forbidden
    return "success"


@app.route("/stats", methods=["GET"])
def stats():
    # Return stats on CIDRs blocked and request counts
    global blocked_cidrs
    global blocked_requests
    global accepted_requests
    check_allowed(request.remote_addr)
    return jsonify(
        {
            "cidrs": len(blocked_cidrs),
            "blocked_requests": blocked_requests,
            "accepted_requests": accepted_requests,
        }
    )


@app.route("/block", methods=["POST"])
@auth.login_required
@metrics.gauge("block_request_in_progress", "Block requests in progress")
def block():
    # Add CIDRs to be blocked by the API
    check_allowed(request.remote_addr)
    # The get_json method checks and only accepts content type of application/JSON
    # To require the explicit header of 'Content-Type: application/json' remove the force
    payload = request.get_json(force=True)
    add_block(payload)
    return "success"


"""
Error handling functions
"""


@app.errorhandler(404)
def not_found(e):
    return "<h1>404</h1><p>Nothing to see here</p>", 404


@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(Unauthorized)
@auth.error_handler
def handle_unauthorized(e):
    return jsonify(error=str(e)), 401


@app.errorhandler(Forbidden)
def handle_forbidden(e):
    return jsonify(error=str(e)), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
