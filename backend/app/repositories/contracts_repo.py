from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.contracts import ContractStrategy, ContractStrategyScenario
from app.models.enums import ContractStrategyType
from app.services.contracts.engine import ContractEngineAnalysisResult, StrategyDetail

class ContractStrategyRepository:
    """
    Data repository for persisting and querying contract procurement strategies.
    """

    @staticmethod
    def save_analysis(
        db: Session,
        analysis: ContractEngineAnalysisResult
    ) -> List[ContractStrategy]:
        saved_records: List[ContractStrategy] = []

        for strat_key, strat in analysis.strategies.items():
            record = ContractStrategy(
                cargo_request_id=analysis.cargo_request_id,
                strategy_type=strat.strategy_type,
                contract_duration=strat.contract_duration,
                voyage_count=strat.voyage_count,
                total_quantity=strat.total_quantity,
                contracted_quantity=strat.contracted_quantity,
                spot_quantity=strat.spot_quantity,
                reference_rate=strat.reference_rate,
                expected_rate=strat.expected_rate,
                expected_cost=strat.expected_cost,
                p10_cost=strat.p10_cost,
                p50_cost=strat.p50_cost,
                p90_cost=strat.p90_cost,
                market_exposure=strat.market_exposure,
                flexibility_measure=strat.flexibility_measure,
                risk_adjusted_cost=strat.risk_adjusted_cost,
                break_even_rate=strat.break_even_rate,
                decision_confidence=strat.decision_confidence,
                data_status=strat.data_status,
            )
            db.add(record)
            db.flush() # populate record.id

            # Save scenarios
            for scen in strat.scenarios:
                s_rec = ContractStrategyScenario(
                    strategy_id=record.id,
                    scenario_name=scen.scenario_name,
                    market_assumption=scen.market_assumption,
                    rate=scen.rate,
                    quantity=scen.quantity,
                    cost=scen.cost,
                    probability=scen.probability
                )
                db.add(s_rec)

            strat.id = record.id
            saved_records.append(record)

        db.commit()
        return saved_records

    @staticmethod
    def get_by_id(db: Session, strategy_id: str) -> Optional[ContractStrategy]:
        return db.query(ContractStrategy).filter(ContractStrategy.id == strategy_id).first()

    @staticmethod
    def get_latest(
        db: Session,
        cargo_request_id: Optional[str] = None
    ) -> List[ContractStrategy]:
        query = db.query(ContractStrategy)
        if cargo_request_id:
            query = query.filter(ContractStrategy.cargo_request_id == cargo_request_id)
        return query.order_by(desc(ContractStrategy.created_at)).limit(3).all()

    @staticmethod
    def get_scenarios(db: Session, strategy_id: str) -> List[ContractStrategyScenario]:
        return db.query(ContractStrategyScenario).filter(
            ContractStrategyScenario.strategy_id == strategy_id
        ).all()
