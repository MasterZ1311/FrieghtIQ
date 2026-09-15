from app.services.forecast_service import forecast, get_history, ensure_model_trained
from app.services.port_service import check_compatibility, list_ports
from app.services.vessel_service import recommend_vessels
from app.services.economics_service import calculate_economics
from app.services.market_entry_service import generate_signal
from app.services.risk_service import score_risk
from app.services.contract_service import compare_contracts
from app.services.scenario_service import simulate_scenarios
from app.services.idle_service import calculate_idle_scenario
