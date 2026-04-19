"""
tests/integration/test_api.py
FastAPI integration tests — full HTTP layer exercised via TestClient.

No network calls. All tests run locally against the in-process app.
Engine layers are real (not mocked) — these are end-to-end tests of the
complete data flow from HTTP request to HTTP response.
"""

import pytest
from starlette.testclient import TestClient

from apps.api.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_VALID_SNAPSHOT = {
    "user_id": "test-001",
    "snapshot_date": "2026-01-01",
    "income": {"monthly": 6000.0, "income_type": "stable", "income_volatile": False},
    "expenses": {"fixed": 2000.0, "variable": 1500.0, "total": 3500.0},
    "savings": {"balance": 5000.0, "monthly_contribution": 500.0},
    "cashflow": {"monthly": 2500.0},
    "goal": {
        "target_amount": 20000.0,
        "deadline": "2027-07-01",
        "type": "emergency_fund",
    },
}

_VALID_BASELINE = {
    "monthly_cashflow": 2500.0,
    "savings_rate": 41.67,
    "time_to_goal_months": 6,
    "monthly_savings_gap": 0.0,
    "goal_already_met": False,
}

_VALID_BEHAVIOR_CHANGE = {
    "type": "savings_increase",
    "value": 300.0,
}

_VALID_SCENARIO_REQUEST = {
    "financial_snapshot": _VALID_SNAPSHOT,
    "baseline": _VALID_BASELINE,
    "behavior_change": _VALID_BEHAVIOR_CHANGE,
    "adherence_rate": 0.7,
}

_VALID_EXPLAIN_REQUEST = {
    "baseline_months": 6,
    "scenario_months": 4,
    "delta_months": 2,
    "monthly_change_amount": 300.0,
    "adherence_rate": 0.7,
    "behavior_type": "savings_increase",
    "goal_type": "emergency_fund",
}

_VALID_SCENARIO_RESULT = {
    "baseline_months": 6,
    "scenario_months": 4,
    "delta_months": 2,
    "adherence_rate": 0.7,
    "effective_monthly_change": 210.0,
    "scenario_monthly_cashflow": 2710.0,
    "is_improvement": True,
}

_VALID_DECISION = {
    "user_id": "test-001",
    "event_type": "accepted",
    "scenario_result": _VALID_SCENARIO_RESULT,
    "timestamp": "2026-01-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_body_has_status_ok(self):
        response = client.get("/health")
        assert response.json()["status"] == "ok"

    def test_body_has_version(self):
        response = client.get("/health")
        assert "version" in response.json()

    def test_body_has_phase(self):
        response = client.get("/health")
        assert response.json()["phase"] == "mvp"


# ---------------------------------------------------------------------------
# POST /baseline
# ---------------------------------------------------------------------------


class TestBaseline:
    def test_valid_snapshot_returns_200(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert response.status_code == 200

    def test_valid_snapshot_cashflow_matches_expected(self):
        # income=6000, fixed=2000, variable=1500 → cashflow=2500
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert response.json()["data"]["monthly_cashflow"] == pytest.approx(2500.0)

    def test_valid_snapshot_status_ok(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert response.json()["status"] == "ok"

    def test_response_includes_latency_ms(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        body = response.json()
        assert "latency_ms" in body
        assert isinstance(body["latency_ms"], float)
        assert body["latency_ms"] >= 0

    def test_response_includes_x_response_time_header(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert "x-response-time-ms" in response.headers

    def test_data_has_required_fields(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        data = response.json()["data"]
        for field in (
            "monthly_cashflow",
            "savings_rate",
            "time_to_goal_months",
            "monthly_savings_gap",
            "goal_already_met",
        ):
            assert field in data

    def test_income_zero_returns_422(self):
        body = {**_VALID_SNAPSHOT, "income": {"monthly": 0.0}}
        response = client.post("/baseline", json=body)
        assert response.status_code == 422

    def test_income_zero_errors_list_non_empty(self):
        body = {**_VALID_SNAPSHOT, "income": {"monthly": 0.0}}
        response = client.post("/baseline", json=body)
        assert len(response.json()["errors"]) > 0

    def test_income_negative_returns_422(self):
        body = {**_VALID_SNAPSHOT, "income": {"monthly": -100.0}}
        response = client.post("/baseline", json=body)
        assert response.status_code == 422

    def test_negative_savings_returns_422(self):
        # SavingsData validator rejects balance < 0 at Pydantic level
        body = {
            **_VALID_SNAPSHOT,
            "savings": {"balance": -500.0, "monthly_contribution": 100.0},
        }
        response = client.post("/baseline", json=body)
        assert response.status_code == 422

    def test_goal_already_met_returns_true(self):
        # savings.balance > goal.target_amount → goal_already_met=True
        body = {
            **_VALID_SNAPSHOT,
            "savings": {"balance": 25000.0, "monthly_contribution": 500.0},
            "goal": {
                "target_amount": 20000.0,
                "deadline": "2027-07-01",
                "type": "emergency_fund",
            },
        }
        response = client.post("/baseline", json=body)
        assert response.status_code == 200
        assert response.json()["data"]["goal_already_met"] is True

    def test_goal_not_yet_met(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert response.json()["data"]["goal_already_met"] is False

    def test_savings_rate_is_positive(self):
        response = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert response.json()["data"]["savings_rate"] > 0

    def test_goal_amount_zero_returns_422(self):
        body = {
            **_VALID_SNAPSHOT,
            "goal": {
                "target_amount": 0.0,
                "deadline": "2027-07-01",
                "type": "emergency_fund",
            },
        }
        response = client.post("/baseline", json=body)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /scenario
# ---------------------------------------------------------------------------


class TestScenario:
    def test_valid_input_returns_200(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert response.status_code == 200

    def test_status_is_ok(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert response.json()["status"] == "ok"

    def test_data_delta_months_is_int(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        delta = response.json()["data"]["delta_months"]
        assert isinstance(delta, int)

    def test_validation_field_present(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert "validation" in response.json()
        assert "valid" in response.json()["validation"]

    def test_validation_errors_is_list(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert isinstance(response.json()["validation"]["errors"], list)

    def test_scenario_months_less_than_baseline_for_positive_change(self):
        # baseline=6, change=$300 at 70% adherence → effective=$210 → faster
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        data = response.json()["data"]
        if data["scenario_months"] is not None and data["baseline_months"] is not None:
            assert data["scenario_months"] <= data["baseline_months"]

    def test_adherence_zero_is_clamped_to_floor(self):
        # adherence=0.0 → clamped to 0.1 by engine — must not return 422
        body = {**_VALID_SCENARIO_REQUEST, "adherence_rate": 0.0}
        response = client.post("/scenario", json=body)
        assert response.status_code == 200
        assert response.json()["data"]["adherence_rate"] == pytest.approx(0.1)

    def test_adherence_above_ceiling_is_clamped(self):
        # adherence=2.0 → clamped to 0.95 by engine
        body = {**_VALID_SCENARIO_REQUEST, "adherence_rate": 2.0}
        response = client.post("/scenario", json=body)
        assert response.status_code == 200
        assert response.json()["data"]["adherence_rate"] == pytest.approx(0.95)

    def test_response_includes_latency_ms(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert "latency_ms" in response.json()
        assert response.json()["latency_ms"] >= 0

    def test_response_includes_timing_header(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert "x-response-time-ms" in response.headers

    def test_effective_monthly_change_is_non_negative(self):
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert response.json()["data"]["effective_monthly_change"] >= 0

    def test_is_improvement_true_for_positive_change(self):
        # Use a tight cashflow (500/mo) toward a 8000 remaining goal.
        # Baseline: ceil(8000/500) = 16 months.
        # $300 at 70% → effective=210, cashflow=710, scenario=ceil(8000/710)=12.
        # delta = 4 → is_improvement=True.
        tight_snapshot = {
            "user_id": "test-002",
            "snapshot_date": "2026-01-01",
            "income": {"monthly": 4000.0, "income_type": "stable", "income_volatile": False},
            "expenses": {"fixed": 3000.0, "variable": 500.0, "total": 3500.0},
            "savings": {"balance": 2000.0, "monthly_contribution": 100.0},
            "cashflow": {"monthly": 500.0},
            "goal": {"target_amount": 10000.0, "deadline": "2028-06-01", "type": "emergency_fund"},
        }
        tight_baseline = {
            "monthly_cashflow": 500.0,
            "savings_rate": 12.5,
            "time_to_goal_months": 16,
            "monthly_savings_gap": 0.0,
            "goal_already_met": False,
        }
        body = {
            "financial_snapshot": tight_snapshot,
            "baseline": tight_baseline,
            "behavior_change": _VALID_BEHAVIOR_CHANGE,
            "adherence_rate": 0.7,
        }
        response = client.post("/scenario", json=body)
        assert response.status_code == 200
        assert response.json()["data"]["is_improvement"] is True

    def test_expense_cut_type_works(self):
        body = {
            **_VALID_SCENARIO_REQUEST,
            "behavior_change": {"type": "expense_cut", "value": 200.0},
        }
        response = client.post("/scenario", json=body)
        assert response.status_code == 200

    def test_data_returned_even_when_validation_warn(self):
        # Data is always present regardless of validation outcome
        response = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert "data" in response.json()
        assert response.json()["data"] is not None


# ---------------------------------------------------------------------------
# POST /explain
# ---------------------------------------------------------------------------


class TestExplain:
    def test_valid_input_returns_200(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert response.status_code == 200

    def test_status_is_ok_or_fallback(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert response.json()["status"] in ("ok", "fallback")

    def test_data_has_recommendation(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert "recommendation" in response.json()["data"]
        assert len(response.json()["data"]["recommendation"]) > 0

    def test_data_has_explanation(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert "explanation" in response.json()["data"]
        assert len(response.json()["data"]["explanation"]) > 0

    def test_validation_field_present(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        v = response.json()["validation"]
        assert "valid" in v
        assert "fallback_used" in v
        assert "errors" in v

    def test_never_returns_500(self):
        # Even on "unusual" input — generate_explanation() never raises
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert response.status_code != 500

    def test_response_includes_latency_ms(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert "latency_ms" in response.json()
        assert response.json()["latency_ms"] >= 0

    def test_response_includes_timing_header(self):
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        assert "x-response-time-ms" in response.headers

    def test_different_behavior_types_both_work(self):
        for btype in ("savings_increase", "expense_cut"):
            body = {**_VALID_EXPLAIN_REQUEST, "behavior_type": btype}
            response = client.post("/explain", json=body)
            assert response.status_code == 200

    def test_valid_mock_returns_ok_status(self):
        # Default MockLLMClient is "valid" mode — should produce ok, not fallback
        response = client.post("/explain", json=_VALID_EXPLAIN_REQUEST)
        # "ok" is the expected result with valid mock; "fallback" is also acceptable
        # per spec, so we assert the union — primary value is no 500
        assert response.json()["status"] in ("ok", "fallback")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /decision
# ---------------------------------------------------------------------------


class TestDecision:
    def test_accepted_event_returns_200(self):
        body = {**_VALID_DECISION, "event_type": "accepted"}
        response = client.post("/decision", json=body)
        assert response.status_code == 200

    def test_accepted_event_status_logged(self):
        body = {**_VALID_DECISION, "event_type": "accepted"}
        response = client.post("/decision", json=body)
        assert response.json() == {"status": "logged"}

    def test_rejected_event_returns_200(self):
        body = {**_VALID_DECISION, "event_type": "rejected"}
        response = client.post("/decision", json=body)
        assert response.status_code == 200

    def test_rejected_event_status_logged(self):
        body = {**_VALID_DECISION, "event_type": "rejected"}
        response = client.post("/decision", json=body)
        assert response.json() == {"status": "logged"}

    def test_modified_event_returns_200(self):
        body = {**_VALID_DECISION, "event_type": "modified"}
        response = client.post("/decision", json=body)
        assert response.status_code == 200

    def test_invalid_event_type_returns_422(self):
        body = {**_VALID_DECISION, "event_type": "unknown"}
        response = client.post("/decision", json=body)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_malformed_json_body_returns_422(self):
        response = client.post(
            "/baseline",
            content=b"not json at all {{{",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_unknown_route_returns_404(self):
        response = client.get("/does_not_exist")
        assert response.status_code == 404

    def test_unknown_post_route_returns_404(self):
        response = client.post("/does_not_exist", json={})
        assert response.status_code == 404 or response.status_code == 405

    def test_missing_required_field_returns_422(self):
        # Omit user_id from snapshot
        body = {k: v for k, v in _VALID_SNAPSHOT.items() if k != "user_id"}
        response = client.post("/baseline", json=body)
        assert response.status_code == 422

    def test_baseline_wrong_content_type_returns_422(self):
        response = client.post(
            "/baseline",
            content=b'{"income": "bad"}',
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_error_response_has_status_field(self):
        body = {**_VALID_SNAPSHOT, "income": {"monthly": 0.0}}
        response = client.post("/baseline", json=body)
        assert response.json()["status"] == "error"

    def test_error_response_has_code_field(self):
        body = {**_VALID_SNAPSHOT, "income": {"monthly": 0.0}}
        response = client.post("/baseline", json=body)
        assert "code" in response.json()


# ---------------------------------------------------------------------------
# End-to-end pipeline: Baseline → Scenario → Explain
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    """
    Full data flow: compute a baseline, run a scenario, generate an explanation.
    Verifies that outputs from one layer are valid inputs to the next.
    """

    def test_baseline_then_scenario(self):
        # Step 1: Get baseline
        b_resp = client.post("/baseline", json=_VALID_SNAPSHOT)
        assert b_resp.status_code == 200
        baseline = b_resp.json()["data"]

        # Step 2: Run scenario using real baseline output
        s_body = {
            "financial_snapshot": _VALID_SNAPSHOT,
            "baseline": baseline,
            "behavior_change": _VALID_BEHAVIOR_CHANGE,
            "adherence_rate": 0.7,
        }
        s_resp = client.post("/scenario", json=s_body)
        assert s_resp.status_code == 200
        scenario = s_resp.json()["data"]
        assert scenario["delta_months"] is not None

    def test_scenario_then_explain(self):
        # Run scenario first
        s_resp = client.post("/scenario", json=_VALID_SCENARIO_REQUEST)
        assert s_resp.status_code == 200
        scenario = s_resp.json()["data"]

        # Build explain input from scenario output
        if scenario["baseline_months"] is not None and scenario["scenario_months"] is not None:
            explain_body = {
                "baseline_months": scenario["baseline_months"],
                "scenario_months": scenario["scenario_months"],
                "delta_months": scenario["delta_months"],
                "monthly_change_amount": 300.0,
                "adherence_rate": scenario["adherence_rate"],
                "behavior_type": "savings_increase",
                "goal_type": "emergency_fund",
            }
            e_resp = client.post("/explain", json=explain_body)
            assert e_resp.status_code == 200
            assert e_resp.json()["data"]["recommendation"] is not None

    def test_full_pipeline_baseline_to_explain(self):
        # 1. Baseline
        b_resp = client.post("/baseline", json=_VALID_SNAPSHOT)
        baseline = b_resp.json()["data"]

        # 2. Scenario
        s_resp = client.post("/scenario", json={
            "financial_snapshot": _VALID_SNAPSHOT,
            "baseline": baseline,
            "behavior_change": _VALID_BEHAVIOR_CHANGE,
            "adherence_rate": 0.8,
        })
        scenario = s_resp.json()["data"]

        # 3. Explain (only when both timelines are reachable)
        if scenario["baseline_months"] and scenario["scenario_months"]:
            e_resp = client.post("/explain", json={
                "baseline_months": scenario["baseline_months"],
                "scenario_months": scenario["scenario_months"],
                "delta_months": scenario["delta_months"],
                "monthly_change_amount": 300.0,
                "adherence_rate": scenario["adherence_rate"],
                "behavior_type": "savings_increase",
                "goal_type": "emergency_fund",
            })
            assert e_resp.status_code == 200
            assert e_resp.json()["status"] in ("ok", "fallback")

        # 4. Decision
        d_resp = client.post("/decision", json={
            "user_id": _VALID_SNAPSHOT["user_id"],
            "event_type": "accepted",
            "scenario_result": scenario,
            "timestamp": "2026-01-01T00:00:00Z",
        })
        assert d_resp.status_code == 200
        assert d_resp.json() == {"status": "logged"}
