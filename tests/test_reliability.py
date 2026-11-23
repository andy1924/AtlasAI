"""Offline regressions: real agent graph/API, stubbed paid and external services."""
import importlib
import os
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

from decision_policy import parse_decision, requires_approval
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

memory = ModuleType('memory')
memory.get_past_poa = Mock(return_value={'poa': 'Prior action', 'action_type': 'REROUTE', 'confidence_hint': 85})
memory.add_learned_action = Mock()
memory.mark_outcome = Mock()
news = ModuleType('newsEngine')
news.get_latest_news = Mock(return_value=[])
predictor = ModuleType('predictor')
predictor.refresh_predictions = Mock(return_value={})
predictor.get_all_predictions = Mock(return_value={})
predictor.get_predicted_reliability = Mock(return_value=0.95)
predictor.get_forecast = Mock(return_value=[])

with patch.dict(sys.modules, {'memory': memory, 'newsEngine': news, 'predictor': predictor, 'uvicorn': ModuleType('uvicorn')}):
    with patch('langchain_openai.ChatOpenAI'):
        agent = importlib.import_module('agent')
        api = importlib.import_module('main')

from state import Shipment, Alert


def shipment(**overrides):
    values = dict(shipment_id='S1', origin='Mumbai', destination='Singapore', carrier='DHL',
                  weight_kg=100, distance_km=1000, eta_hours=36, status='In Transit',
                  delay_probability=0.1, operational_cost=1000, partner_reliability=0.95,
                  timestamp='2026-11-23T00:00:00')
    return Shipment(**(values | overrides))


class DecisionPolicyTests(unittest.TestCase):
    def test_valid_actions(self):
        for action in ['REROUTE', 'HOLD', 'SWITCH_CARRIER', 'EXPEDITE', 'MONITOR']:
            with self.subTest(action=action):
                parsed, confidence, _ = parse_decision(f'Action: {action}\nConfidence: 85\nReasoning: example', 'Medium')
                self.assertEqual((parsed, confidence), (action, 85))

    def test_high_severity_always_escalates(self):
        self.assertEqual(parse_decision('Action: EXPEDITE\nConfidence: 99', 'High')[0], 'ESCALATE')

    def test_malformed_output_never_uses_historical_confidence(self):
        for content in ['nonsense', 'Action: REROUTE', 'Confidence: 95',
                        'Action: REROUTE\nConfidence: 101', 'Action: REROUTE\nConfidence: -1',
                        'Action: REROUTE\nConfidence: 90.5', 'Action: REROUTE_EVIL\nConfidence: 99',
                        'Action: HOLD\nAction: REROUTE\nConfidence: 99',
                        'Action: REROUTE\nConfidence: 99\nConfidence: 45']:
            with self.subTest(content=content):
                self.assertEqual(parse_decision(content, 'Low')[0], 'ESCALATE')

    def test_confidence_boundary(self):
        self.assertTrue(requires_approval('HOLD', 44, 'Low'))
        self.assertFalse(requires_approval('HOLD', 45, 'Low'))
        self.assertTrue(requires_approval('HOLD', 101, 'Low'))

    def test_explicit_approval_marker_is_respected(self):
        self.assertEqual(parse_decision('Action: HOLD\nConfidence: 99\n[needs approval]', 'Low')[0], 'ESCALATE')

    def test_unknown_severity_fails_closed(self):
        self.assertTrue(requires_approval('EXPEDITE', 99, 'HIGH'))


class AgentAndAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api.app)
        api.current_shipments = [shipment()]
        api.current_alerts = []
        api.agent_history = []
        memory.add_learned_action.reset_mock()
        agent.llm = Mock()
        agent.llm.invoke.return_value = AIMessage(content='Action: EXPEDITE\nConfidence: 99')
        predictor.refresh_predictions.side_effect = None
        agent.LSTM_AVAILABLE = True

    def trigger(self, severity='High'):
        return self.client.post('/api/trigger-chaos', json=dict(type='Port disruption', location='Mumbai',
                                      severity=severity, description='Port closed'))

    def test_high_severity_is_pending_even_when_model_omits_marker(self):
        self.assertEqual(self.trigger().status_code, 200)
        response = self.client.post('/api/run-agent')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['updated_shipments'][0]['status'], 'Pending Approval')
        self.assertEqual(body['updated_shipments'][0]['operational_cost'], 1000)
        self.assertFalse(body['log']['autonomous'])

    def test_act_enforces_policy_when_called_without_decide(self):
        for action, severity, confidence in [('ESCALATE', 'Low', 99), ('REROUTE', 'High', 99),
                                               ('UNKNOWN', 'Low', 99), ('HOLD', 'Low', 20)]:
            with self.subTest(action=action):
                result = agent.act(dict(shipments=[shipment(status='At Risk')], decision='',
                                        action_type=action, severity_level=severity, confidence=confidence))
                self.assertEqual(result['shipments'][0].status, 'Pending Approval')

    def test_medium_severity_executes_valid_action(self):
        self.trigger('Medium')
        response = self.client.post('/api/run-agent').json()
        self.assertEqual(response['updated_shipments'][0]['status'], 'Expedited')
        self.assertAlmostEqual(response['updated_shipments'][0]['operational_cost'], 1150)
        self.assertTrue(response['log']['autonomous'])

    def test_failed_run_rolls_back_observer_changes_and_releases_lock(self):
        api.current_shipments = [shipment(eta_hours=3, delay_probability=0.8)]
        before = api.current_shipments[0].model_dump()
        agent.llm.invoke.side_effect = RuntimeError('provider failed')
        with self.assertLogs(level='ERROR'):
            response = self.client.post('/api/run-agent')
        self.assertEqual(response.status_code, 502)
        self.assertEqual(api.current_shipments[0].model_dump(), before)
        self.assertEqual(api.agent_history, [])
        self.assertFalse(api.mutation_lock.locked())
        self.assertNotIn('provider failed', response.text)

    def test_overlapping_mutations_return_conflict(self):
        with api.mutation_lock:
            for route in ['/api/run-agent', '/api/approve-actions', '/api/evaluate-outcomes']:
                self.assertEqual(self.client.post(route).status_code, 409)
            self.assertEqual(self.trigger().status_code, 409)
            self.assertEqual(self.client.get('/api/shipments').status_code, 200)

    def test_invalid_severity_rejected_before_mutation(self):
        self.assertEqual(self.trigger('high').status_code, 422)
        self.assertEqual(api.current_alerts, [])
        self.assertEqual(api.current_shipments[0].status, 'In Transit')

    def test_delivered_shipments_are_not_reopened(self):
        api.current_shipments[0].status = 'Delivered'
        self.trigger()
        self.assertEqual(api.current_shipments[0].status, 'Delivered')

    def test_repeat_approval_does_not_add_history_or_memory(self):
        self.trigger()
        self.client.post('/api/run-agent')
        self.assertEqual(self.client.post('/api/approve-actions').status_code, 200)
        history_count = len(api.agent_history)
        self.assertEqual(self.client.post('/api/approve-actions').status_code, 200)
        self.assertEqual(len(api.agent_history), history_count)
        memory.add_learned_action.assert_called_once()
        self.assertEqual(memory.add_learned_action.call_args.kwargs['outcome'], 'unknown')

    def test_audit_counts_only_changes_in_this_cycle(self):
        api.current_shipments.append(shipment(shipment_id='S2', origin='Tokyo', destination='Dubai', status='Rerouted (Auto)'))
        self.trigger('Medium')
        response = self.client.post('/api/run-agent').json()
        self.assertEqual(response['log']['shipments_affected'], 1)
        response = self.client.post('/api/run-agent').json()
        self.assertEqual(response['log']['shipments_affected'], 0)

    def test_static_reliability_used_when_forecast_refresh_fails(self):
        predictor.refresh_predictions.side_effect = RuntimeError('model missing')
        value = shipment(partner_reliability=0.6, delay_probability=0.6)
        agent.auto_flag_at_risk([value])
        self.assertEqual(value.status, 'At Risk')

    def test_local_dashboard_cors(self):
        response = self.client.options('/api/run-agent', headers={
            'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST'})
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:3000')


class NewsTests(unittest.TestCase):
    def test_empty_feed_does_not_fabricate_news(self):
        # Import actual news module separately from the API's offline stub.
        spec = importlib.util.spec_from_file_location('actual_news', Path(__file__).resolve().parents[1] / 'backend/newsEngine.py')
        actual_news = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(actual_news)
        with patch.dict(os.environ, {'MEDIA_STACK_API': 'test-only'}), patch.object(actual_news.requests, 'get') as get:
            get.return_value.status_code = 200
            get.return_value.json.return_value = {'data': []}
            self.assertEqual(actual_news.get_latest_news(), [])
            self.assertEqual(get.call_args.kwargs['timeout'], 10)


if __name__ == '__main__':
    unittest.main()
