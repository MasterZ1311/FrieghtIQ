import uuid
import math
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.enums import (
    CargoType, VesselClass, VesselStatus, MatchStatus, FeasibilityStatus,
    ConstraintSeverity, RequirementStatus, ForecastModelType, DataSourceType,
    MarketRegimeType, DataStatusType, WaitFixDecision, DecisionConfidence,
    RiskType, RiskSeverity, RiskStatus, TidalWindowStatus, CongestionIndicator,
    EmploymentEventType, IdleScenarioType, RepositioningDecision
)
from app.models.ports import Port, Berth, PortConstraint, BerthConstraint, PortDataSource
from app.models.vessels import Vessel, VesselParticulars, VesselAvailability, OperationalSnapshotVessel
from app.models.cargo import CargoRequirement
from app.models.freight import FreightRoute, FreightObservation
from app.models.regime import MarketRegime, MarketRegimeTransition
from app.models.wait_fix import WaitFixAnalysis, WaitFixScenario
from app.models.contracts import ContractStrategy, ContractStrategyScenario
from app.models.idle_repositioning import VesselEmploymentEvent, IdleScenario, RepositioningOption
from app.models.risk import PortCongestion, WeatherObservation, TidalWindow, RiskEvent
from app.models.economics import VoyageEconomicAnalysis, VoyageCostComponent, SpeedScenario, VoyageScenario
from app.services.economics.voyage_economics_service import VoyageEconomicsService

def seed_database():
    print("Beginning FREIGHT IQ database seeding...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Port).count() > 0:
            print("Database already contains records. Clearing existing demo records for clean seed...")
            db.query(VoyageScenario).delete()
            db.query(SpeedScenario).delete()
            db.query(VoyageCostComponent).delete()
            db.query(VoyageEconomicAnalysis).delete()
            db.query(RiskEvent).delete()
            db.query(TidalWindow).delete()
            db.query(WeatherObservation).delete()
            db.query(PortCongestion).delete()
            db.query(RepositioningOption).delete()
            db.query(IdleScenario).delete()
            db.query(VesselEmploymentEvent).delete()
            db.query(ContractStrategyScenario).delete()
            db.query(ContractStrategy).delete()
            db.query(WaitFixScenario).delete()
            db.query(WaitFixAnalysis).delete()
            db.query(MarketRegimeTransition).delete()
            db.query(MarketRegime).delete()
            db.query(FreightObservation).delete()
            db.query(FreightRoute).delete()
            db.query(CargoRequirement).delete()
            db.query(OperationalSnapshotVessel).delete()
            db.query(VesselAvailability).delete()
            db.query(VesselParticulars).delete()
            db.query(Vessel).delete()
            db.query(BerthConstraint).delete()
            db.query(Berth).delete()
            db.query(PortConstraint).delete()
            db.query(PortDataSource).delete()
            db.query(Port).delete()
            db.commit()

        # -------------------------------------------------------------
        # 1. SEED PORTS & BERTHS
        # -------------------------------------------------------------
        print("Seeding ports, berths, and official constraints...")
        
        # Paradip Port
        paradip = Port(
            id="port-inprt",
            unlocode="INPRT",
            name="Paradip Port",
            country="India",
            coast="East Coast India",
            latitude=20.2644,
            longitude=86.6698,
            channel_max_draft_m=16.0,
            channel_max_loa_m=300.0,
            channel_max_beam_m=48.0,
            tide_range_m=2.5,
            night_navigation=True,
            tug_requirement_count=4,
            notes="Primary deep-water bulk hub servicing SAIL Rourkela, Bokaro, and IISCO steel plants."
        )
        db.add(paradip)

        # Paradip Berths
        cb1 = Berth(
            id="berth-inprt-cb1",
            port_id=paradip.id,
            berth_code="CB-1",
            berth_name="Coal Berth 1 (Mechanised)",
            berth_type="Mechanised Coal",
            max_loa_m=260.0,
            max_beam_m=32.5,
            max_draft_m=14.5,
            max_air_draft_m=18.0,
            max_dwt=85000.0,
            discharge_rate_tpd=25000.0,
            loading_rate_tpd=0.0,
            equipment_summary="2 x Continuous Ship Unloaders (CSUs) + conveyor network to SAIL stackyard",
            night_berthing=True,
            notes="Dedicated mechanised thermal & coking coal discharge berth."
        )
        cb2 = Berth(
            id="berth-inprt-cb2",
            port_id=paradip.id,
            berth_code="CB-2",
            berth_name="Coal Berth 2 (Mechanised)",
            berth_type="Mechanised Coal",
            max_loa_m=260.0,
            max_beam_m=32.5,
            max_draft_m=14.5,
            max_air_draft_m=18.0,
            max_dwt=85000.0,
            discharge_rate_tpd=25000.0,
            loading_rate_tpd=0.0,
            equipment_summary="2 x CSUs + high-speed stacker reclaimers",
            night_berthing=True,
            notes="Panamax / Kamsarmax mechanised discharge."
        )
        mcb = Berth(
            id="berth-inprt-mcb",
            port_id=paradip.id,
            berth_code="MCB",
            berth_name="Mechanised Coal Terminal (Deep Draft)",
            berth_type="Deep Bulk Coal",
            max_loa_m=300.0,
            max_beam_m=48.0,
            max_draft_m=16.0,
            max_air_draft_m=22.0,
            max_dwt=150000.0,
            discharge_rate_tpd=40000.0,
            loading_rate_tpd=0.0,
            equipment_summary="High-capacity grab unloaders (40,000 TPD design)",
            night_berthing=True,
            notes="Capable of handling Capesize and Baby-Cape bulkers up to 16.0m draft."
        )
        cq1 = Berth(
            id="berth-inprt-cq1",
            port_id=paradip.id,
            berth_code="CQ-1",
            berth_name="Central Quay 1",
            berth_type="Dry Bulk Multipurpose",
            max_loa_m=230.0,
            max_beam_m=32.5,
            max_draft_m=12.5,
            max_air_draft_m=16.0,
            max_dwt=65000.0,
            discharge_rate_tpd=15000.0,
            loading_rate_tpd=0.0,
            equipment_summary="Mobile harbour cranes (MHC) + shore hoppers",
            night_berthing=True,
            notes="Supramax / Handymax dry bulk discharge."
        )
        db.add_all([cb1, cb2, mcb, cq1])

        # Visakhapatnam Port
        vizag = Port(
            id="port-invtz",
            unlocode="INVTZ",
            name="Visakhapatnam Port",
            country="India",
            coast="East Coast India",
            latitude=17.6868,
            longitude=83.2185,
            channel_max_draft_m=18.1,
            channel_max_loa_m=300.0,
            channel_max_beam_m=50.0,
            tide_range_m=1.8,
            night_navigation=True,
            tug_requirement_count=4,
            notes="Major natural deep-water harbour with outer and inner harbour facilities."
        )
        v_ost = Berth(
            id="berth-invtz-ost",
            port_id=vizag.id,
            berth_code="OST",
            berth_name="Outer Harbour General Cargo Berth (Coal)",
            berth_type="Deep Bulk Coal",
            max_loa_m=300.0,
            max_beam_m=48.0,
            max_draft_m=18.1,
            max_air_draft_m=22.0,
            max_dwt=200000.0,
            discharge_rate_tpd=35000.0,
            loading_rate_tpd=0.0,
            equipment_summary="Continuous twin CSUs + conveyor system",
            night_berthing=True
        )
        v_wq1 = Berth(
            id="berth-invtz-wq1",
            port_id=vizag.id,
            berth_code="WQ-1",
            berth_name="West Quay 1 (Inner Harbour)",
            berth_type="Dry Bulk",
            max_loa_m=230.0,
            max_beam_m=32.5,
            max_draft_m=14.5,
            max_air_draft_m=17.0,
            max_dwt=80000.0,
            discharge_rate_tpd=18000.0,
            loading_rate_tpd=0.0,
            equipment_summary="Shore cranes and grabs",
            night_berthing=True
        )
        db.add_all([vizag, v_ost, v_wq1])

        # Haldia Dock Complex
        haldia = Port(
            id="port-inhal",
            unlocode="INHAL",
            name="Haldia Dock Complex",
            country="India",
            coast="East Coast India (Hooghly River)",
            latitude=22.0232,
            longitude=88.0645,
            channel_max_draft_m=8.8,
            channel_max_loa_m=230.0,
            channel_max_beam_m=32.2,
            tide_range_m=3.5,
            night_navigation=False,
            tug_requirement_count=3,
            notes="Riverine lock gate port. Subject to severe tidal and river bar draft limitations."
        )
        h_b4 = Berth(
            id="berth-inhal-b4",
            port_id=haldia.id,
            berth_code="Berth-4A",
            berth_name="Berth 4A (Mechanised Bulk)",
            berth_type="Dry Bulk",
            max_loa_m=230.0,
            max_beam_m=32.2,
            max_draft_m=8.8,
            max_air_draft_m=15.0,
            max_dwt=65000.0,
            discharge_rate_tpd=12000.0,
            loading_rate_tpd=0.0,
            equipment_summary="Shore unloader + conveyor",
            night_berthing=False
        )
        db.add_all([haldia, h_b4])

        # Dhamra Port
        dhamra = Port(
            id="port-indhm",
            unlocode="INDHM",
            name="Dhamra Port",
            country="India",
            coast="East Coast India",
            latitude=20.8286,
            longitude=86.9744,
            channel_max_draft_m=18.0,
            channel_max_loa_m=330.0,
            channel_max_beam_m=50.0,
            tide_range_m=2.8,
            night_navigation=True,
            tug_requirement_count=4,
            notes="Privately operated deep draft bulk terminal in Odisha."
        )
        d_b1 = Berth(
            id="berth-indhm-b1",
            port_id=dhamra.id,
            berth_code="Berth-1",
            berth_name="Import Berth 1 (Capesize Coal)",
            berth_type="Deep Bulk Coal",
            max_loa_m=330.0,
            max_beam_m=50.0,
            max_draft_m=18.0,
            max_air_draft_m=22.0,
            max_dwt=180000.0,
            discharge_rate_tpd=45000.0,
            loading_rate_tpd=0.0,
            equipment_summary="High speed grab unloaders (4,500 TPH rated)",
            night_berthing=True
        )
        db.add_all([dhamra, d_b1])

        # Gangavaram, Gopalpur, Chennai
        gangavaram = Port(
            id="port-inggp",
            unlocode="INGGP",
            name="Gangavaram Port",
            country="India",
            coast="East Coast India",
            latitude=17.6186,
            longitude=83.2389,
            channel_max_draft_m=20.0,
            channel_max_loa_m=350.0,
            channel_max_beam_m=55.0,
            tide_range_m=1.8,
            night_navigation=True,
            tug_requirement_count=4,
            notes="Deepest port in India, capable of handling fully laden Capesize bulkers."
        )
        g_b1 = Berth(
            id="berth-inggp-b1",
            port_id=gangavaram.id,
            berth_code="Berth-1",
            berth_name="Deep Draft Coal Berth",
            berth_type="Deep Bulk Coal",
            max_loa_m=350.0,
            max_beam_m=55.0,
            max_draft_m=20.0,
            max_air_draft_m=25.0,
            max_dwt=220000.0,
            discharge_rate_tpd=50000.0,
            loading_rate_tpd=0.0,
            equipment_summary="Continuous CSUs + rapid rake loading system",
            night_berthing=True
        )
        gopalpur = Port(
            id="port-ingpl",
            unlocode="INGPL",
            name="Gopalpur Port",
            country="India",
            coast="East Coast India",
            latitude=19.3056,
            longitude=84.9753,
            channel_max_draft_m=13.5,
            channel_max_loa_m=230.0,
            channel_max_beam_m=32.5,
            tide_range_m=2.0,
            night_navigation=True,
            tug_requirement_count=2
        )
        gp_b1 = Berth(
            id="berth-ingpl-b1",
            port_id=gopalpur.id,
            berth_code="Berth-2",
            berth_name="Dry Bulk Multi-Cargo",
            berth_type="Dry Bulk",
            max_loa_m=230.0,
            max_beam_m=32.5,
            max_draft_m=13.0,
            max_air_draft_m=16.0,
            max_dwt=75000.0,
            discharge_rate_tpd=14000.0,
            loading_rate_tpd=0.0,
            equipment_summary="Mobile harbour cranes",
            night_berthing=True
        )
        chennai = Port(
            id="port-inmaa",
            unlocode="INMAA",
            name="Chennai Port",
            country="India",
            coast="East Coast India",
            latitude=13.0827,
            longitude=80.2707,
            channel_max_draft_m=14.0,
            channel_max_loa_m=260.0,
            channel_max_beam_m=35.0,
            tide_range_m=1.2,
            night_navigation=True,
            tug_requirement_count=3
        )
        c_b1 = Berth(
            id="berth-inmaa-b1",
            port_id=chennai.id,
            berth_code="JD-2",
            berth_name="Jawahar Dock 2 (Bulk)",
            berth_type="Dry Bulk",
            max_loa_m=230.0,
            max_beam_m=32.5,
            max_draft_m=12.0,
            max_air_draft_m=16.0,
            max_dwt=70000.0,
            discharge_rate_tpd=12000.0,
            loading_rate_tpd=0.0,
            equipment_summary="MHC cranes",
            night_berthing=True
        )
        db.add_all([gangavaram, g_b1, gopalpur, gp_b1, chennai, c_b1])

        # Overseas load ports
        newcastle = Port(
            id="port-auncb",
            unlocode="AUNCB",
            name="Newcastle Port (PWCS / Kooragang)",
            country="Australia",
            coast="East Coast Australia",
            latitude=-32.9283,
            longitude=151.7817,
            channel_max_draft_m=15.2,
            channel_max_loa_m=300.0,
            channel_max_beam_m=50.0,
            tide_range_m=1.9,
            night_navigation=True,
            tug_requirement_count=4,
            notes="World's largest coal export terminal."
        )
        gladstone = Port(
            id="port-auglt",
            unlocode="AUGLT",
            name="Gladstone Port (RG Tanna)",
            country="Australia",
            coast="Queensland Australia",
            latitude=-23.8431,
            longitude=151.2555,
            channel_max_draft_m=16.5,
            channel_max_loa_m=300.0,
            channel_max_beam_m=50.0,
            tide_range_m=3.5,
            night_navigation=True,
            tug_requirement_count=4
        )
        richards_bay = Port(
            id="port-zarcb",
            unlocode="ZARCB",
            name="Richards Bay Coal Terminal",
            country="South Africa",
            coast="Indian Ocean South Africa",
            latitude=-28.7807,
            longitude=32.0383,
            channel_max_draft_m=17.5,
            channel_max_loa_m=320.0,
            channel_max_beam_m=52.0,
            tide_range_m=2.0,
            night_navigation=True,
            tug_requirement_count=4
        )
        singapore = Port(
            id="port-sgsin",
            unlocode="SGSIN",
            name="Singapore Port",
            country="Singapore",
            coast="Malacca Strait",
            latitude=1.2903,
            longitude=103.8520,
            channel_max_draft_m=19.0,
            channel_max_loa_m=350.0,
            channel_max_beam_m=55.0,
            tide_range_m=2.5,
            night_navigation=True,
            tug_requirement_count=4,
            notes="Global bunkering hub, prompt anchorage, and transshipment port."
        )
        db.add_all([newcastle, gladstone, richards_bay, singapore])

        # Port constraints
        paradip_c1 = PortConstraint(
            id=str(uuid.uuid4()),
            port_id=paradip.id,
            constraint_type="DRAFT",
            parameter_name="Approach Channel Maximum Draft",
            limit_value=16.0,
            unit="m",
            severity=ConstraintSeverity.BLOCKING,
            condition_description="Standard draft for vessels up to 300m LOA at Mean High Water Springs."
        )
        db.add(paradip_c1)

        # Port Data Sources
        p_src = PortDataSource(
            id=str(uuid.uuid4()),
            port_id=paradip.id,
            source_name="Paradip Port Authority Official Marine Operations Guidelines",
            source_type=DataSourceType.PORT_AUTHORITY_OFFICIAL,
            doc_reference="PPA/DC/CIR-2026/04",
            publication_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            verified=True,
            verified_by="Deputy Conservator, PPA"
        )
        db.add(p_src)

        db.commit()

        # -------------------------------------------------------------
        # 2. SEED VESSELS
        # -------------------------------------------------------------
        print("Seeding operational snapshot vessels & commercial bulkers...")
        now = datetime.now(timezone.utc)

        # Operational Snapshot Vessel 1: Vishva Vijay
        vv = Vessel(
            id="vessel-vishva-vijay",
            imo_number="9484807",
            vessel_name="Vishva Vijay",
            vessel_class=VesselClass.KAMSARMAX,
            flag="India",
            year_built=2012,
            call_sign="AVVJ",
            classification_society="Indian Register of Shipping (IRS)",
            is_snapshot_vessel=True
        )
        vv_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=vv.id,
            summer_dwt=79800.0,
            summer_draft_m=14.45,
            loa_m=229.0,
            beam_m=32.26,
            depth_m=20.0,
            gross_tonnage=43500.0,
            gear_summary="Gearless",
            speed_laden_knots=12.5,
            consumption_laden_mtpd=28.0,
            is_verified=True
        )
        vv_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=vv.id,
            current_status=VesselStatus.BALLAST_TRANSIT,
            current_latitude=8.5,
            current_longitude=82.0,
            open_port_name="Singapore",
            open_date_start=now + timedelta(days=5),
            open_date_end=now + timedelta(days=12),
            data_confidence="HIGH",
            source_evidence="AIS Stream / SCI Fleet Schedule"
        )
        vv_snap = OperationalSnapshotVessel(
            id=str(uuid.uuid4()),
            vessel_id=vv.id,
            snapshot_vessel_name="VISHVA VIJAY",
            observed_handled_cargo_mt=74500.0,
            cargo_type="COKING_COAL",
            discharge_port_code="INPRT",
            discharge_berth_code="CB-1",
            observation_date=now - timedelta(days=45),
            data_integrity_note="Handled parcel size of 74,500 MT was discharged at Paradip CB-1 without lighterage. True summer DWT is 79,800 MT."
        )
        db.add_all([vv, vv_part, vv_avail, vv_snap])

        # Operational Snapshot Vessel 2: Lila Shanghai
        ls = Vessel(
            id="vessel-lila-shanghai",
            imo_number="9543885",
            vessel_name="Lila Shanghai",
            vessel_class=VesselClass.CAPESIZE,
            flag="Liberia",
            year_built=2011,
            call_sign="D5QZ8",
            classification_society="DNV",
            is_snapshot_vessel=True
        )
        ls_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=ls.id,
            summer_dwt=176000.0,
            summer_draft_m=18.0,
            loa_m=289.0,
            beam_m=45.0,
            gear_summary="Gearless",
            speed_laden_knots=12.0,
            is_verified=True
        )
        ls_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=ls.id,
            current_status=VesselStatus.LADEN_TRANSIT,
            current_latitude=-15.2,
            current_longitude=105.4,
            open_port_name="Port Hedland",
            open_date_start=now + timedelta(days=14),
            open_date_end=now + timedelta(days=22),
            data_confidence="HIGH",
            source_evidence="AIS Tracking"
        )
        ls_snap = OperationalSnapshotVessel(
            id=str(uuid.uuid4()),
            vessel_id=ls.id,
            snapshot_vessel_name="LILA SHANGHAI",
            observed_handled_cargo_mt=168200.0,
            cargo_type="IRON_ORE_FINES",
            discharge_port_code="INVTZ",
            discharge_berth_code="OST",
            observation_date=now - timedelta(days=60),
            data_integrity_note="Handled parcel size of 168,200 MT at Vizag Outer Harbour. DWT is 176,000 MT."
        )
        db.add_all([ls, ls_part, ls_avail, ls_snap])

        # Operational Snapshot Vessel 3: Lyric Harmony
        lh = Vessel(
            id="vessel-lyric-harmony",
            imo_number="9612088",
            vessel_name="Lyric Harmony",
            vessel_class=VesselClass.SUPRAMAX,
            flag="Panama",
            year_built=2013,
            call_sign="3FOE4",
            classification_society="ClassNK",
            is_snapshot_vessel=True
        )
        lh_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=lh.id,
            summer_dwt=56800.0,
            summer_draft_m=12.8,
            loa_m=189.9,
            beam_m=32.26,
            gear_summary="4 x 30t Cranes + 12cbm Grabs",
            speed_laden_knots=13.0,
            is_verified=True
        )
        lh_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=lh.id,
            current_status=VesselStatus.AT_ANCHORAGE,
            current_latitude=20.2,
            current_longitude=86.7,
            current_port_name="Paradip Anchorage",
            open_port_name="Paradip",
            open_date_start=now + timedelta(days=2),
            open_date_end=now + timedelta(days=8),
            data_confidence="HIGH",
            source_evidence="Port Anchorage Log"
        )
        lh_snap = OperationalSnapshotVessel(
            id=str(uuid.uuid4()),
            vessel_id=lh.id,
            snapshot_vessel_name="LYRIC HARMONY",
            observed_handled_cargo_mt=56200.0,
            cargo_type="COKING_COAL",
            discharge_port_code="INPRT",
            discharge_berth_code="CQ-1",
            observation_date=now - timedelta(days=20),
            data_integrity_note="Handled 56,200 MT parcel at Paradip CQ-1. Self-discharging cranes deployed."
        )
        db.add_all([lh, lh_part, lh_avail, lh_snap])

        # Operational Snapshot Vessel 4: Alam Sayang
        asay = Vessel(
            id="vessel-alam-sayang",
            imo_number="9683934",
            vessel_name="Alam Sayang",
            vessel_class=VesselClass.ULTRAMAX,
            flag="Singapore",
            year_built=2015,
            call_sign="9V2356",
            classification_society="ABS",
            is_snapshot_vessel=True
        )
        as_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=asay.id,
            summer_dwt=63500.0,
            summer_draft_m=13.3,
            loa_m=199.9,
            beam_m=32.26,
            gear_summary="4 x 30t Cranes + Grabs",
            is_verified=True
        )
        as_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=asay.id,
            current_status=VesselStatus.BALLAST_TRANSIT,
            current_latitude=14.0,
            current_longitude=82.5,
            open_port_name="Vizag",
            open_date_start=now + timedelta(days=6),
            open_date_end=now + timedelta(days=14),
            data_confidence="HIGH"
        )
        as_snap = OperationalSnapshotVessel(
            id=str(uuid.uuid4()),
            vessel_id=asay.id,
            snapshot_vessel_name="ALAM SAYANG",
            observed_handled_cargo_mt=61000.0,
            cargo_type="THERMAL_COAL",
            discharge_port_code="INHAL",
            discharge_berth_code="Berth-4A",
            observation_date=now - timedelta(days=35),
            data_integrity_note="Handled 61,000 MT via two-port discharge (lightened at Paradip before Haldia completion)."
        )
        db.add_all([asay, as_part, as_avail, as_snap])

        # Operational Snapshot Vessel 5: Red Cosmos (Unverified Particulars)
        rc = Vessel(
            id="vessel-red-cosmos",
            imo_number="9401234",
            vessel_name="Red Cosmos",
            vessel_class=VesselClass.PANAMAX,
            flag="Panama",
            year_built=2008,
            is_snapshot_vessel=True
        )
        rc_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=rc.id,
            summer_dwt=None,  # STRICT INTEGRITY: UNKNOWN in register
            summer_draft_m=None,
            loa_m=None,
            beam_m=None,
            gear_summary="Unverified",
            is_verified=False,
            unverified_fields="summer_dwt, summer_draft_m, loa_m, beam_m"
        )
        rc_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=rc.id,
            current_status=VesselStatus.WAITING_ORDERS,
            open_port_name="Bay of Bengal (Unconfirmed)",
            open_date_start=None,
            open_date_end=None,
            data_confidence="LOW",
            source_evidence="Broker Circular (Unconfirmed)"
        )
        rc_snap = OperationalSnapshotVessel(
            id=str(uuid.uuid4()),
            vessel_id=rc.id,
            snapshot_vessel_name="RED COSMOS",
            observed_handled_cargo_mt=73800.0,
            cargo_type="COKING_COAL",
            discharge_port_code="INPRT",
            observation_date=now - timedelta(days=70),
            data_integrity_note="Observed handled parcel was 73,800 MT. Particulars are intentionally NULL/UNKNOWN to prevent false capacity assumptions."
        )
        db.add_all([rc, rc_part, rc_avail, rc_snap])

        # Operational Snapshot Vessel 6: Pu An Tong
        pat = Vessel(
            id="vessel-pu-an-tong",
            imo_number="9588123",
            vessel_name="Pu An Tong",
            vessel_class=VesselClass.SUPRAMAX,
            flag="China",
            year_built=2010,
            call_sign="BRP9",
            classification_society="CCS",
            is_snapshot_vessel=True
        )
        pat_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=pat.id,
            summer_dwt=53800.0,
            summer_draft_m=12.5,
            loa_m=190.0,
            beam_m=32.2,
            gear_summary="4 x 30t Cranes",
            is_verified=True
        )
        pat_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=pat.id,
            current_status=VesselStatus.BERTHED_DISCHARGING,
            current_port_name="Paradip",
            open_port_name="Paradip",
            open_date_start=now + timedelta(days=4),
            open_date_end=now + timedelta(days=9),
            data_confidence="HIGH"
        )
        pat_snap = OperationalSnapshotVessel(
            id=str(uuid.uuid4()),
            vessel_id=pat.id,
            snapshot_vessel_name="PU AN TONG",
            observed_handled_cargo_mt=53500.0,
            cargo_type="THERMAL_COAL",
            discharge_port_code="INPRT",
            observation_date=now - timedelta(days=12),
            data_integrity_note="Observed handled: 53,500 MT parcel at Paradip."
        )
        db.add_all([pat, pat_part, pat_avail, pat_snap])

        # Additional Commercial Bulkers (Perfect fit & variations)
        # MV Steel Glory (Panamax - ideal candidate for 75k coal)
        sg = Vessel(
            id="vessel-steel-glory",
            imo_number="9788001",
            vessel_name="MV Steel Glory",
            vessel_class=VesselClass.PANAMAX,
            flag="Marshall Islands",
            year_built=2018,
            call_sign="V7AB9",
            classification_society="Lloyd's Register",
            is_snapshot_vessel=False
        )
        sg_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=sg.id,
            summer_dwt=75500.0,
            summer_draft_m=14.1,
            loa_m=225.0,
            beam_m=32.2,
            gear_summary="Gearless",
            speed_laden_knots=13.2,
            is_verified=True
        )
        sg_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=sg.id,
            current_status=VesselStatus.BALLAST_TRANSIT,
            open_port_name="Newcastle",
            open_date_start=now + timedelta(days=8),
            open_date_end=now + timedelta(days=14),
            data_confidence="HIGH",
            source_evidence="Broker Prompt Position List"
        )
        db.add_all([sg, sg_part, sg_avail])

        # MV Odisha Star (Kamsarmax - 82k DWT)
        os = Vessel(
            id="vessel-odisha-star",
            imo_number="9821900",
            vessel_name="MV Odisha Star",
            vessel_class=VesselClass.KAMSARMAX,
            flag="Singapore",
            year_built=2021,
            call_sign="9V8712",
            classification_society="DNV",
            is_snapshot_vessel=False
        )
        os_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=os.id,
            summer_dwt=82000.0,
            summer_draft_m=14.5,
            loa_m=229.0,
            beam_m=32.26,
            gear_summary="Gearless",
            speed_laden_knots=13.5,
            is_verified=True
        )
        os_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=os.id,
            current_status=VesselStatus.BALLAST_TRANSIT,
            open_port_name="Newcastle",
            open_date_start=now + timedelta(days=9),
            open_date_end=now + timedelta(days=15),
            data_confidence="HIGH",
            source_evidence="Direct Owner Offer"
        )
        db.add_all([os, os_part, os_avail])

        # MV Kalinga Pioneer (Capesize - 180k DWT - oversized for 75k)
        kp = Vessel(
            id="vessel-kalinga-pioneer",
            imo_number="9812345",
            vessel_name="MV Kalinga Pioneer",
            vessel_class=VesselClass.CAPESIZE,
            flag="Liberia",
            year_built=2019,
            call_sign="D5KP1",
            classification_society="Bureau Veritas",
            is_snapshot_vessel=False
        )
        kp_part = VesselParticulars(
            id=str(uuid.uuid4()),
            vessel_id=kp.id,
            summer_dwt=180000.0,
            summer_draft_m=18.2,
            loa_m=292.0,
            beam_m=45.0,
            gear_summary="Gearless",
            is_verified=True
        )
        kp_avail = VesselAvailability(
            id=str(uuid.uuid4()),
            vessel_id=kp.id,
            current_status=VesselStatus.BALLAST_TRANSIT,
            open_port_name="Port Hedland",
            open_date_start=now + timedelta(days=10),
            open_date_end=now + timedelta(days=18),
            data_confidence="HIGH"
        )
        db.add_all([kp, kp_part, kp_avail])

        db.commit()

        # -------------------------------------------------------------
        # 3. SEED CHARTERING REQUIREMENTS
        # -------------------------------------------------------------
        print("Seeding SAIL chartering requirements...")
        cr1 = CargoRequirement(
            id="req-sail-2026-001",
            requirement_code="CR-2026-001",
            title="SAIL Rourkela / Bokaro — 75,000 MT Coking Coal Ex-Newcastle to Paradip",
            cargo_type=CargoType.COKING_COAL,
            quantity_mt=75000.0,
            tolerance_pct=10.0,
            load_port_id=newcastle.id,
            discharge_port_id=paradip.id,
            laycan_start=now + timedelta(days=7),
            laycan_end=now + timedelta(days=16),
            target_freight_usd_pmt=27.50,
            max_vessel_age_years=15,
            preferred_vessel_classes="PANAMAX,KAMSARMAX",
            gear_requirement="ANY",
            status=RequirementStatus.MARKET_SCAN,
            created_by="SAIL Commercial Division (Chartering Wing)",
            notes="Direct import of prime hard coking coal for SAIL steel plant blast furnaces. Discharging via mechanised CB-1 or CB-2."
        )
        cr2 = CargoRequirement(
            id="req-sail-2026-002",
            requirement_code="CR-2026-002",
            title="SAIL IISCO Burnpur — 55,000 MT PCI Coal Ex-Gladstone to Haldia/Paradip",
            cargo_type=CargoType.PCI_COAL,
            quantity_mt=55000.0,
            tolerance_pct=10.0,
            load_port_id=gladstone.id,
            discharge_port_id=paradip.id,
            laycan_start=now + timedelta(days=15),
            laycan_end=now + timedelta(days=25),
            target_freight_usd_pmt=29.00,
            max_vessel_age_years=15,
            preferred_vessel_classes="SUPRAMAX,ULTRAMAX",
            gear_requirement="GEARED",
            status=RequirementStatus.MARKET_SCAN,
            created_by="SAIL Commercial Division",
            notes="PCI coal shipment with optional geared discharge capability."
        )
        db.add_all([cr1, cr2])
        db.commit()

        # -------------------------------------------------------------
        # 4. SEED FREIGHT ROUTES & 730 DAYS OF OBSERVATIONS
        # -------------------------------------------------------------
        print("Seeding freight routes and 2 years of synthetic market observations...")
        route_newc_prt = FreightRoute(
            id="route-newcastle-paradip-capesize",
            route_code="NEWCASTLE_PARADIP_CAPESIZE",
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            default_vessel_class=VesselClass.CAPESIZE,
            distance_nm=5850.0,
            typical_duration_days=18.5
        )
        route_newc_prt_pan = FreightRoute(
            id="route-newcastle-paradip-panamax",
            route_code="NEWCASTLE_PARADIP_PANAMAX",
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            default_vessel_class=VesselClass.PANAMAX,
            distance_nm=5850.0,
            typical_duration_days=18.5
        )
        route_glt_hal = FreightRoute(
            id="route-gladstone-haldia-panamax",
            route_code="GLADSTONE_HALDIA_PANAMAX",
            origin_port_id=gladstone.id,
            destination_port_id=haldia.id,
            default_vessel_class=VesselClass.PANAMAX,
            distance_nm=5420.0,
            typical_duration_days=17.0
        )
        route_rcb_vtz = FreightRoute(
            id="route-richardsbay-vizag-capesize",
            route_code="RICHARDSBAY_VIZAG_CAPESIZE",
            origin_port_id=richards_bay.id,
            destination_port_id=vizag.id,
            default_vessel_class=VesselClass.CAPESIZE,
            distance_nm=4750.0,
            typical_duration_days=15.0
        )
        db.add_all([route_newc_prt, route_newc_prt_pan, route_glt_hal, route_rcb_vtz])
        db.commit()

        # Generate 730 days of daily observations for Newcastle -> Paradip Panamax
        start_date = now - timedelta(days=730)
        observations = []

        base_rate = 26.50
        base_bunker = 620.0
        base_baltic = 1450.0

        for day_idx in range(730):
            obs_dt = start_date + timedelta(days=day_idx)
            
            # Seasonal cycle: annual sinusoids (cyclone season Jan-Mar, monsoon July-Aug, winter demand Nov-Dec)
            day_of_year = obs_dt.timetuple().tm_yday
            seasonal_factor = 2.8 * math.sin(2 * math.pi * (day_of_year - 60) / 365.25)
            
            # Multi-month market cycle
            market_cycle = 3.5 * math.sin(2 * math.pi * day_idx / 220)
            
            # Correlated random walk
            # Pseudo-deterministic noise using day_idx
            noise = ((day_idx * 9301 + 49297) % 233280) / 233280.0 - 0.5
            rate_noise = noise * 1.2
            
            freight_rate = round(base_rate + seasonal_factor + market_cycle + rate_noise, 2)
            freight_rate = max(14.50, freight_rate)
            
            bunker_price = round(base_bunker + (seasonal_factor * 12.0) + (noise * 45.0), 1)
            baltic_idx = round(base_baltic + (seasonal_factor * 85.0) + (market_cycle * 110.0) + (noise * 120.0), 0)
            
            cong_orig = round(max(1.0, 2.5 + 1.2 * math.sin(day_idx / 15.0) + noise * 1.5), 1)
            cong_dest = round(max(1.0, 3.2 + 1.5 * math.sin(day_idx / 22.0) + noise * 1.8), 1)

            obs = FreightObservation(
                id=str(uuid.uuid4()),
                route_id=route_newc_prt_pan.id,
                observation_date=obs_dt,
                freight_rate_usd_pmt=freight_rate,
                bunker_vlsfo_usd=bunker_price,
                bunker_mgo_usd=bunker_price + 180.0,
                baltic_index_value=baltic_idx,
                congestion_origin_days=cong_orig,
                congestion_dest_days=cong_dest,
                is_interpolated=False,
                source_type="SYNTHETIC_CALIBRATED"
            )
            observations.append(obs)

            # Also generate observations for Capesize route
            obs_cape = FreightObservation(
                id=str(uuid.uuid4()),
                route_id=route_newc_prt.id,
                observation_date=obs_dt,
                freight_rate_usd_pmt=round(freight_rate * 0.82, 2), # Capesize economy of scale
                bunker_vlsfo_usd=bunker_price,
                bunker_mgo_usd=bunker_price + 180.0,
                baltic_index_value=baltic_idx,
                congestion_origin_days=cong_orig,
                congestion_dest_days=cong_dest,
                is_interpolated=False,
                source_type="SYNTHETIC_CALIBRATED"
            )
            observations.append(obs_cape)

        db.add_all(observations)
        db.commit()
        print(f"Successfully seeded {len(observations)} freight observations.")

        # -------------------------------------------------------------
        # 5. SEED INITIAL MARKET REGIME & TRANSITION INTELLIGENCE
        # -------------------------------------------------------------
        print("Seeding initial market regime classifications and transition intelligence...")
        import json
        from app.services.regime.service import MarketRegimeService

        regime_service = MarketRegimeService(db)
        
        # Analyze and persist current regime for Newcastle -> Paradip Panamax
        current_panamax = regime_service.analyze_regime(
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            cargo_type=CargoType.COKING_COAL,
            vessel_class=VesselClass.PANAMAX
        )
        print(f"Calibrated Panamax Regime: {current_panamax.regime} (Confidence: {current_panamax.confidence * 100:.1f}%)")

        # Analyze and persist current regime for Newcastle -> Paradip Capesize
        current_capesize = regime_service.analyze_regime(
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            cargo_type=CargoType.COKING_COAL,
            vessel_class=VesselClass.CAPESIZE
        )
        print(f"Calibrated Capesize Regime: {current_capesize.regime} (Confidence: {current_capesize.confidence * 100:.1f}%)")

        # Seed historical transitions for rich timeline & transitions view
        latest_reg = db.query(MarketRegime).filter(
            MarketRegime.origin_port_id == newcastle.id,
            MarketRegime.destination_port_id == paradip.id,
            MarketRegime.vessel_class == VesselClass.PANAMAX
        ).order_by(MarketRegime.detected_at.desc()).first()

        if latest_reg:
            t1 = MarketRegimeTransition(
                id=str(uuid.uuid4()),
                market_regime_id=latest_reg.id,
                previous_regime=MarketRegimeType.NEUTRAL,
                new_regime=latest_reg.regime,
                transition_date=now - timedelta(days=18),
                confidence=0.82,
                trigger_features=json.dumps({
                    "rate_return_7d": 0.042,
                    "rate_return_30d": 0.098,
                    "rolling_volatility_14d": 0.021,
                    "forecast_slope": 0.065
                }),
                model_version_id="hmm-v1.0-4s",
                created_at=now - timedelta(days=18)
            )
            t2 = MarketRegimeTransition(
                id=str(uuid.uuid4()),
                market_regime_id=latest_reg.id,
                previous_regime=MarketRegimeType.BEAR,
                new_regime=MarketRegimeType.NEUTRAL,
                transition_date=now - timedelta(days=52),
                confidence=0.76,
                trigger_features=json.dumps({
                    "rate_return_7d": 0.012,
                    "rate_return_30d": -0.015,
                    "rolling_volatility_14d": 0.016,
                    "forecast_slope": 0.008
                }),
                model_version_id="hmm-v1.0-4s",
                created_at=now - timedelta(days=52)
            )
            t3 = MarketRegimeTransition(
                id=str(uuid.uuid4()),
                market_regime_id=latest_reg.id,
                previous_regime=MarketRegimeType.SEASONAL,
                new_regime=MarketRegimeType.BEAR,
                transition_date=now - timedelta(days=95),
                confidence=0.79,
                trigger_features=json.dumps({
                    "rate_return_7d": -0.054,
                    "rate_return_30d": -0.112,
                    "rolling_volatility_14d": 0.028,
                    "forecast_slope": -0.072
                }),
                model_version_id="hmm-v1.0-4s",
                created_at=now - timedelta(days=95)
            )
            db.add_all([t1, t2, t3])
            db.commit()
            print("Successfully seeded 3 historical regime transitions.")

        # -------------------------------------------------------------
        # 6. SEED INITIAL WAIT vs FIX DECISION EVALUATION
        # -------------------------------------------------------------
        print("Seeding initial Wait vs Fix charter-timing decision evaluation...")
        from app.services.wait_fix.engine import WaitFixDecisionEngine
        wait_fix_engine = WaitFixDecisionEngine(db)
        
        # Analyze for CR-2026-001 (75k MT Coal, Newcastle -> Paradip, Panamax)
        wf_res = wait_fix_engine.analyze(
            cargo_request_id=cr1.id,
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            cargo_type=CargoType.COKING_COAL,
            cargo_quantity=75000.0,
            vessel_class=VesselClass.PANAMAX,
            decision_horizon_days=30
        )
        print(f"Calibrated Wait vs Fix Decision: {wf_res.decision} (Confidence: {wf_res.decision_confidence}, Modeled Diff: ${wf_res.expected_modeled_difference:,.0f})")

        # -------------------------------------------------------------
        # 7. SEED INITIAL CONTRACT STRATEGY SIMULATION
        # -------------------------------------------------------------
        print("Seeding initial Contract Strategy evaluation for multi-voyage bulk procurement...")
        from app.services.contracts.engine import ContractStrategyEngine
        from app.repositories.contracts_repo import ContractStrategyRepository

        contract_analysis = ContractStrategyEngine.analyze_strategies(
            total_requirement_mt=300000.0,
            parcel_size_mt=75000.0,
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            cargo_type="COKING_COAL",
            vessel_class="PANAMAX",
            planning_horizon_days=180,
            reference_contract_rate=24.00,
            cargo_request_id=cr1.id,
            port_feasibility="PASS",
            current_spot_rate=24.50,
            p10_rate=22.80,
            p50_rate=24.10,
            p90_rate=26.50,
            regime_type="BEAR",
            regime_probability=0.65,
            wait_fix_decision=wf_res.decision,
            volatility_annualized=0.28
        )
        # -------------------------------------------------------------
        # 8. SEED PHASE 9 IDLE SCENARIOS & REPOSITIONING OPTIONS
        # -------------------------------------------------------------
        print("Seeding Phase 9 Vessel Employment Events, Idle Scenarios & Repositioning...")

        # 8.1 Employment Events
        # Vishva Vijay events
        ev_vv1 = VesselEmploymentEvent(
            id=str(uuid.uuid4()),
            vessel_id=vv.id,
            event_type=EmploymentEventType.DISCHARGE,
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            event_start=now - timedelta(days=45),
            event_end=now - timedelta(days=42),
            status="COMPLETED",
            source_id="PARADIP_PORT_LOG_2026_01",
            data_status=DataStatusType.RECENT
        )
        ev_vv2 = VesselEmploymentEvent(
            id=str(uuid.uuid4()),
            vessel_id=vv.id,
            event_type=EmploymentEventType.BALLAST_REPOSITION,
            origin_port_id=paradip.id,
            destination_port_id=singapore.id,
            event_start=now - timedelta(days=2),
            event_end=now + timedelta(days=5),
            status="ACTIVE",
            source_id="AIS_STREAM_SINGAPORE_STRAITS",
            data_status=DataStatusType.RECENT
        )
        # Lyric Harmony events (at anchorage)
        ev_lh1 = VesselEmploymentEvent(
            id=str(uuid.uuid4()),
            vessel_id=lh.id,
            event_type=EmploymentEventType.ANCHORAGE_WAIT,
            destination_port_id=paradip.id,
            event_start=now - timedelta(days=1),
            event_end=now + timedelta(days=2),
            status="ACTIVE",
            source_id="PARADIP_BERTHING_LINEUP",
            data_status=DataStatusType.RECENT
        )
        # Pu An Tong events (discharging at berth)
        ev_pat1 = VesselEmploymentEvent(
            id=str(uuid.uuid4()),
            vessel_id=pat.id,
            event_type=EmploymentEventType.DISCHARGE,
            destination_port_id=paradip.id,
            event_start=now - timedelta(days=1),
            event_end=now + timedelta(days=4),
            status="ACTIVE",
            source_id="PARADIP_CB1_LOG",
            data_status=DataStatusType.RECENT
        )
        db.add_all([ev_vv1, ev_vv2, ev_lh1, ev_pat1])

        # 8.2 Idle Scenarios
        # Vishva Vijay: Employment gap between Singapore arrival and potential Newcastle loading
        sc_vv = IdleScenario(
            id=str(uuid.uuid4()),
            vessel_id=vv.id,
            scenario_type=IdleScenarioType.EMPLOYMENT_GAP,
            current_location="Singapore Roads",
            next_known_employment="BHP Newcastle Coking Coal Fixture (Pending Confirmation)",
            estimated_available_at=now + timedelta(days=5),
            estimated_next_employment_at=now + timedelta(days=13),
            idle_days=8.0,
            idle_cost=112000.0, # 8 days * $14,000/day charter rate assumption
            confidence=DecisionConfidence.HIGH,
            data_status=DataStatusType.RECENT
        )

        # Lyric Harmony: Port delay at Paradip Anchorage with unknown next fixture
        sc_lh = IdleScenario(
            id=str(uuid.uuid4()),
            vessel_id=lh.id,
            scenario_type=IdleScenarioType.PORT_DELAY,
            current_location="Paradip Anchorage",
            next_known_employment=None, # UNKNOWN next employment
            estimated_available_at=now + timedelta(days=2),
            estimated_next_employment_at=None,
            idle_days=None, # UNKNOWN: Strict integrity, never replace with 0
            idle_cost=None, # UNAVAILABLE
            confidence=DecisionConfidence.MEDIUM,
            data_status=DataStatusType.RECENT
        )

        # Red Cosmos: Demand gap with unverified particulars
        sc_rc = IdleScenario(
            id=str(uuid.uuid4()),
            vessel_id=rc.id,
            scenario_type=IdleScenarioType.DEMAND_GAP,
            current_location="Bay of Bengal (Unconfirmed)",
            next_known_employment=None,
            estimated_available_at=None,
            estimated_next_employment_at=None,
            idle_days=None,
            idle_cost=None,
            confidence=DecisionConfidence.LOW,
            data_status=DataStatusType.SYNTHETIC
        )
        db.add_all([sc_vv, sc_lh, sc_rc])
        db.flush()

        # 8.3 Repositioning Options for Vishva Vijay
        opt_vv1 = RepositioningOption(
            id=str(uuid.uuid4()),
            idle_scenario_id=sc_vv.id,
            vessel_id=vv.id,
            target_port_id=newcastle.id,
            target_cargo_request_id=cr1.id,
            distance=3950.0,
            distance_method="NAUTICAL_CHART",
            estimated_sailing_days=13.2,
            estimated_bunker_cost=108500.0, # 13.2 days * 28 MT/day * $294 approx or calibrated
            estimated_total_cost=293300.0,
            port_compatibility="PASS",
            timing_compatibility="ON_TIME",
            status=RepositioningDecision.REPOSITION,
            data_status=DataStatusType.RECENT
        )
        opt_vv2 = RepositioningOption(
            id=str(uuid.uuid4()),
            idle_scenario_id=sc_vv.id,
            vessel_id=vv.id,
            target_port_id=richards_bay.id,
            target_cargo_request_id=None,
            distance=4680.0,
            distance_method="GEODESIC_APPROXIMATION",
            estimated_sailing_days=15.6,
            estimated_bunker_cost=131040.0,
            estimated_total_cost=349440.0,
            port_compatibility="PASS",
            timing_compatibility="TIGHT",
            status=RepositioningDecision.DO_NOT_REPOSITION,
            data_status=DataStatusType.SYNTHETIC
        )
        db.add_all([opt_vv1, opt_vv2])
        db.commit()
        print("Successfully seeded Phase 9 Idle Scenarios, Repositioning Options & Timeline Events.")

        # -------------------------------------------------------------
        # 9. SEED PHASE 10 OPERATIONAL RISK INTELLIGENCE
        # -------------------------------------------------------------
        print("Seeding Phase 10 Congestion, Weather Observations, Tidal Windows & Operational Risk Events...")

        # 9.1 Port Congestion
        pc_paradip = PortCongestion(
            id=f"PC-INPRT-{now.strftime('%Y%m%d')}",
            port_id=paradip.id,
            observed_at=now,
            vessels_in_port=22,
            vessels_waiting=14,
            berths_occupied=8,
            estimated_wait_hours=42.0,
            congestion_indicator=CongestionIndicator.SEVERE,
            methodology="AIS_GEOFENCE_TELEMETRY",
            source_id="AIS_SYNTHETIC_PROXY",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        pc_haldia = PortCongestion(
            id=f"PC-INHLD-{now.strftime('%Y%m%d')}",
            port_id=haldia.id,
            observed_at=now,
            vessels_in_port=14,
            vessels_waiting=9,
            berths_occupied=5,
            estimated_wait_hours=34.0,
            congestion_indicator=CongestionIndicator.MODERATE,
            methodology="PORT_AUTHORITY_DAILY_REPORT",
            source_id="PORT_REPORTED",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        pc_vizag = PortCongestion(
            id=f"PC-INVIZ-{now.strftime('%Y%m%d')}",
            port_id=vizag.id,
            observed_at=now,
            vessels_in_port=12,
            vessels_waiting=6,
            berths_occupied=6,
            estimated_wait_hours=11.5,
            congestion_indicator=CongestionIndicator.LOW,
            methodology="PORT_AUTHORITY_DAILY_REPORT",
            source_id="PORT_REPORTED",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        pc_dhamra = PortCongestion(
            id=f"PC-INDHM-{now.strftime('%Y%m%d')}",
            port_id=dhamra.id,
            observed_at=now,
            vessels_in_port=8,
            vessels_waiting=4,
            berths_occupied=4,
            estimated_wait_hours=8.0,
            congestion_indicator=CongestionIndicator.LOW,
            methodology="PORT_AUTHORITY_DAILY_REPORT",
            source_id="PORT_REPORTED",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        pc_singapore = PortCongestion(
            id=f"PC-SGSIN-{now.strftime('%Y%m%d')}",
            port_id=singapore.id,
            observed_at=now,
            vessels_in_port=36,
            vessels_waiting=22,
            berths_occupied=14,
            estimated_wait_hours=48.0,
            congestion_indicator=CongestionIndicator.SEVERE,
            methodology="AIS_GEOFENCE_TELEMETRY",
            source_id="AIS_SYNTHETIC_PROXY",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        pc_newcastle = PortCongestion(
            id=f"PC-AUNCT-{now.strftime('%Y%m%d')}",
            port_id=newcastle.id,
            observed_at=now,
            vessels_in_port=25,
            vessels_waiting=16,
            berths_occupied=9,
            estimated_wait_hours=38.5,
            congestion_indicator=CongestionIndicator.SEVERE,
            methodology="PORT_AUTHORITY_DAILY_REPORT",
            source_id="PORT_REPORTED",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        pc_richards_bay = PortCongestion(
            id=f"PC-ZARBA-{now.strftime('%Y%m%d')}",
            port_id=richards_bay.id,
            observed_at=now,
            vessels_in_port=28,
            vessels_waiting=18,
            berths_occupied=10,
            estimated_wait_hours=52.0,
            congestion_indicator=CongestionIndicator.SEVERE,
            methodology="PORT_AUTHORITY_DAILY_REPORT",
            source_id="PORT_REPORTED",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        db.add_all([pc_paradip, pc_haldia, pc_vizag, pc_dhamra, pc_singapore, pc_newcastle, pc_richards_bay])

        # 9.2 Weather Observations
        w_paradip = WeatherObservation(
            id=f"WX-INPRT-{now.strftime('%Y%m%d%H')}",
            location_type="PORT",
            location_id=paradip.id,
            latitude=paradip.latitude,
            longitude=paradip.longitude,
            observed_at=now,
            wind_speed=22.5,
            wind_direction=195.0,
            wave_height=2.4,
            rainfall=1.8,
            visibility=8.5,
            storm_indicator="NONE",
            source_id="MET_WEATHER_SYNTHETIC",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        w_haldia = WeatherObservation(
            id=f"WX-INHLD-{now.strftime('%Y%m%d%H')}",
            location_type="PORT",
            location_id=haldia.id,
            latitude=haldia.latitude,
            longitude=haldia.longitude,
            observed_at=now,
            wind_speed=14.0,
            wind_direction=170.0,
            wave_height=1.3,
            rainfall=0.4,
            visibility=9.0,
            storm_indicator="NONE",
            source_id="MET_WEATHER_SYNTHETIC",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        w_vizag = WeatherObservation(
            id=f"WX-INVIZ-{now.strftime('%Y%m%d%H')}",
            location_type="PORT",
            location_id=vizag.id,
            latitude=vizag.latitude,
            longitude=vizag.longitude,
            observed_at=now,
            wind_speed=12.0,
            wind_direction=180.0,
            wave_height=1.5,
            rainfall=0.0,
            visibility=10.0,
            storm_indicator="NONE",
            source_id="MET_WEATHER_SYNTHETIC",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        w_singapore = WeatherObservation(
            id=f"WX-SGSIN-{now.strftime('%Y%m%d%H')}",
            location_type="PORT",
            location_id=singapore.id,
            latitude=singapore.latitude,
            longitude=singapore.longitude,
            observed_at=now,
            wind_speed=11.0,
            wind_direction=240.0,
            wave_height=0.9,
            rainfall=3.2,
            visibility=8.0,
            storm_indicator="NONE",
            source_id="MET_WEATHER_SYNTHETIC",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        w_newcastle = WeatherObservation(
            id=f"WX-AUNCT-{now.strftime('%Y%m%d%H')}",
            location_type="PORT",
            location_id=newcastle.id,
            latitude=newcastle.latitude,
            longitude=newcastle.longitude,
            observed_at=now,
            wind_speed=17.5,
            wind_direction=140.0,
            wave_height=2.6,
            rainfall=0.2,
            visibility=10.0,
            storm_indicator="NONE",
            source_id="MET_WEATHER_SYNTHETIC",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        w_richards_bay = WeatherObservation(
            id=f"WX-ZARBA-{now.strftime('%Y%m%d%H')}",
            location_type="PORT",
            location_id=richards_bay.id,
            latitude=richards_bay.latitude,
            longitude=richards_bay.longitude,
            observed_at=now,
            wind_speed=21.0,
            wind_direction=210.0,
            wave_height=3.1,
            rainfall=0.0,
            visibility=9.5,
            storm_indicator="NONE",
            source_id="MET_WEATHER_SYNTHETIC",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        db.add_all([w_paradip, w_haldia, w_vizag, w_singapore, w_newcastle, w_richards_bay])

        # 9.3 Tidal Windows for Tidal Ports
        tw_haldia_hw1 = TidalWindow(
            id=str(uuid.uuid4()),
            port_id=haldia.id,
            berth_id=h_b4.id,
            window_start=now + timedelta(hours=2),
            window_end=now + timedelta(hours=5.5),
            predicted_tide=5.4,
            required_depth=13.0,
            available_depth=13.9,
            vessel_draft=12.5,
            status=TidalWindowStatus.PASS,
            source_id="PORT_TIDAL_TABLE",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        tw_haldia_lw1 = TidalWindow(
            id=str(uuid.uuid4()),
            port_id=haldia.id,
            berth_id=h_b4.id,
            window_start=now + timedelta(hours=8),
            window_end=now + timedelta(hours=11.5),
            predicted_tide=1.2,
            required_depth=13.0,
            available_depth=9.7,
            vessel_draft=12.5,
            status=TidalWindowStatus.CONDITIONAL,
            source_id="PORT_TIDAL_TABLE",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        tw_paradip_hw1 = TidalWindow(
            id=str(uuid.uuid4()),
            port_id=paradip.id,
            berth_id=mcb.id,
            window_start=now + timedelta(hours=3),
            window_end=now + timedelta(hours=6.5),
            predicted_tide=2.7,
            required_depth=17.6,
            available_depth=19.8,
            vessel_draft=17.1,
            status=TidalWindowStatus.PASS,
            source_id="PORT_TIDAL_TABLE",
            data_status=DataStatusType.RECENT,
            created_at=now
        )
        db.add_all([tw_haldia_hw1, tw_haldia_lw1, tw_paradip_hw1])

        # 9.4 Operational Risk Events
        re_cyclone = RiskEvent(
            id="RISK-CYC-2026-01",
            entity_type="PORT",
            entity_id=paradip.id,
            voyage_id=None,
            risk_type=RiskType.WEATHER,
            severity=RiskSeverity.HIGH,
            status=RiskStatus.ACTIVE,
            title="Bay of Bengal Squall & Swell Watch",
            description="Developing low-pressure trough in Bay of Bengal generating 2.5m-3.2m swell. Pilot cutter boarding ground operations intermittently disrupted.",
            evidence="IMD weather advisory: significant wave height 2.5m-3.2m at Paradip outer anchorage.",
            potential_impact="Estimated delay: 24h. Potential demurrage exposure: $45,000 USD. Advise holding at outer anchorage.",
            affected_start=now - timedelta(hours=6),
            affected_end=now + timedelta(hours=36),
            source_id="MET_WEATHER_ALERT",
            data_status=DataStatusType.RECENT,
            confidence=DecisionConfidence.HIGH,
            created_at=now
        )
        re_mchp = RiskEvent(
            id="RISK-OPS-2026-02",
            entity_type="PORT",
            entity_id=paradip.id,
            voyage_id=None,
            risk_type=RiskType.PORT_OPERATION,
            severity=RiskSeverity.MEDIUM,
            status=RiskStatus.ACTIVE,
            title="MCHP Conveyor Stream Maintenance",
            description="Mechanical Coal Handling Plant stream B undergoing routine maintenance for 48h. Discharge throughput reduced by approximately 20%.",
            evidence="PPT Engineering circular: Conveyor line B motor overhaul in progress.",
            potential_impact="Estimated delay: 16h. Demurrage exposure: $18,000 USD. Request alternate berth CQ-1/CQ-2.",
            affected_start=now - timedelta(hours=12),
            affected_end=now + timedelta(hours=36),
            source_id="PORT_AUTHORITY_NOTICE",
            data_status=DataStatusType.RECENT,
            confidence=DecisionConfidence.HIGH,
            created_at=now
        )
        re_lock = RiskEvent(
            id="RISK-TDL-2026-03",
            entity_type="PORT",
            entity_id=haldia.id,
            voyage_id=None,
            risk_type=RiskType.TIDAL,
            severity=RiskSeverity.HIGH,
            status=RiskStatus.ACTIVE,
            title="Haldia Lock Siltation Draft Advisory",
            description="Recent hydrographic soundings show localized siltation at lock gate entrance. Authorized draft restricted to 8.2m CD during low water.",
            evidence="Kolkata Port Trust soundings dated 2026-03-15 indicate bar buildup at lock entrance.",
            potential_impact="Estimated delay: 18h. Financial exposure: $28,000 USD. Vessels drafting >8.0m must await High Water spring tide.",
            affected_start=now - timedelta(days=2),
            affected_end=now + timedelta(days=5),
            source_id="HYDROGRAPHIC_SURVEY",
            data_status=DataStatusType.RECENT,
            confidence=DecisionConfidence.HIGH,
            created_at=now
        )
        re_hedland_cong = RiskEvent(
            id="RISK-CNG-2026-04",
            entity_type="PORT",
            entity_id=singapore.id,
            voyage_id=None,
            risk_type=RiskType.PORT_CONGESTION,
            severity=RiskSeverity.HIGH,
            status=RiskStatus.ACTIVE,
            title="Bunkering and Anchorage Queue Surge at Singapore Roads",
            description="22 bulk carriers waiting at anchorage. Average pre-berthing waiting time has increased to 48 hours due to barge congestion.",
            evidence="MPA Singapore anchorage lineup telemetry: 22 bulkers anchored; berth occupancy 91%.",
            potential_impact="Estimated delay: 48h. Financial demurrage exposure: $95,000 USD. Negotiate laytime minimum 72h.",
            affected_start=now - timedelta(days=1),
            affected_end=now + timedelta(days=4),
            source_id="AIS_TERMINAL_TELEMETRY",
            data_status=DataStatusType.RECENT,
            confidence=DecisionConfidence.HIGH,
            created_at=now
        )
        re_timing = RiskEvent(
            id="RISK-TIM-2026-05",
            entity_type="VESSEL",
            entity_id=vv.id,
            voyage_id=cr1.id,
            risk_type=RiskType.TIMING,
            severity=RiskSeverity.MEDIUM,
            status=RiskStatus.MONITORED,
            title="Tight Laycan Buffer for CR-2026-001 Loading",
            description=f"Estimated arrival at load port Newcastle leaves an 18-hour buffer before the laycan cancelling date closes.",
            evidence="Voyage projection at 12.5 knots gives ETA Newcastle 18 hours prior to cancelling date.",
            potential_impact="Estimated delay risk: 12h. Exposure: $15,000 USD. Instruct master to steam at 13.0+ knots.",
            affected_start=now - timedelta(hours=8),
            affected_end=now + timedelta(days=3),
            source_id="VOYAGE_PROJECTION_ENGINE",
            data_status=DataStatusType.RECENT,
            confidence=DecisionConfidence.MEDIUM,
            created_at=now
        )
        re_repo = RiskEvent(
            id="RISK-REP-2026-06",
            entity_type="VESSEL",
            entity_id=vv.id,
            voyage_id=None,
            risk_type=RiskType.REPOSITIONING,
            severity=RiskSeverity.MEDIUM,
            status=RiskStatus.MONITORED,
            title="Adverse Swell on Ballast Repositioning Corridor",
            description="Southern Indian Ocean frontal system forecasting 3.5m head-swells along the Great Australian Bight / Indian Ocean ballast leg.",
            evidence="NOAA GFS marine wave model projects 3.5m swell across ballast transit corridor.",
            potential_impact="Estimated weather delay: 14h. Bunker consumption penalty: $22,000 USD. Weather routing recommended.",
            affected_start=now - timedelta(hours=4),
            affected_end=now + timedelta(days=6),
            source_id="WEATHER_ROUTING_PROJECTION",
            data_status=DataStatusType.SYNTHETIC,
            confidence=DecisionConfidence.MEDIUM,
            created_at=now
        )
        re_vizag_tug = RiskEvent(
            id="RISK-OPS-2026-07",
            entity_type="PORT",
            entity_id=vizag.id,
            voyage_id=None,
            risk_type=RiskType.PORT_OPERATION,
            severity=RiskSeverity.LOW,
            status=RiskStatus.ACTIVE,
            title="Harbor Escort Tug Roster Nominal",
            description="Visakhapatnam port escort tug fleet operating with standard standby capacity; no delays reported.",
            evidence="Visakhapatnam Port Authority marine operations log: full tug fleet active.",
            potential_impact="Nominal turnaround expected; standard 24h pilot booking applies.",
            affected_start=now - timedelta(days=1),
            affected_end=now + timedelta(days=7),
            source_id="PORT_OPERATIONAL_LOG",
            data_status=DataStatusType.RECENT,
            confidence=DecisionConfidence.HIGH,
            created_at=now
        )
        re_dq = RiskEvent(
            id="RISK-DQ-2026-08",
            entity_type="VESSEL",
            entity_id=rc.id,
            voyage_id=None,
            risk_type=RiskType.DATA_QUALITY,
            severity=RiskSeverity.LOW,
            status=RiskStatus.ACTIVE,
            title="Hydrostatic Particulars Verification Pending",
            description="MV Red Cosmos draught and hatch dimensions are sourced from synthetic AIS proxies without owner superintendent confirmation.",
            evidence="Particulars marked as SYNTHETIC proxy without Lloyd's Register confirmation.",
            potential_impact="Moderate uncertainty in berth draft margin calculation. Request verified Q88 questionnaire.",
            affected_start=now - timedelta(days=2),
            affected_end=now + timedelta(days=10),
            source_id="DATA_QUALITY_SERVICE",
            data_status=DataStatusType.SYNTHETIC,
            confidence=DecisionConfidence.LOW,
            created_at=now
        )
        db.add_all([re_cyclone, re_mchp, re_lock, re_hedland_cong, re_timing, re_repo, re_vizag_tug, re_dq])
        db.commit()
        print("Successfully seeded Phase 10 Operational Risk Intelligence tables.")

        # -------------------------------------------------------------
        # 11. SEED PHASE 11: VOYAGE FINANCIAL ECONOMICS
        # -------------------------------------------------------------
        print("Seeding Phase 11 Voyage Financial Economics & Speed Scenarios...")
        econ_service = VoyageEconomicsService(db=db)
        
        # Benchmark Scenario 1: Newcastle to Paradip 75,000 MT Coking Coal (MV Steel Glory)
        econ_service.analyze_voyage_economics(
            origin_port_id=newcastle.id,
            destination_port_id=paradip.id,
            cargo_quantity_mt=75000.0,
            cargo_type="COKING_COAL",
            vessel_id=sg.id,
            cargo_request_id=cr1.id,
            custom_speed_knots=11.5,
            custom_freight_rate_usd_per_mt=14.50,
            congestion_delay_hours=36.0,
            weather_delay_hours=8.0,
            tidal_delay_hours=4.0,
            laytime_allowed_hours=36.0,
            demurrage_rate_usd_per_day=18000.0,
            persist=True
        )

        # Scenario 2: Newcastle to Visakhapatnam 168,000 MT Capesize (MV Lila Shanghai)
        econ_service.analyze_voyage_economics(
            origin_port_id=newcastle.id,
            destination_port_id=vizag.id,
            cargo_quantity_mt=168000.0,
            cargo_type="COKING_COAL",
            vessel_id=ls.id,
            custom_speed_knots=11.0,
            custom_freight_rate_usd_per_mt=11.80,
            congestion_delay_hours=24.0,
            weather_delay_hours=4.0,
            tidal_delay_hours=0.0,
            laytime_allowed_hours=48.0,
            demurrage_rate_usd_per_day=28000.0,
            persist=True
        )

        print("Successfully seeded Phase 11 Voyage Economics tables.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()
    
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
