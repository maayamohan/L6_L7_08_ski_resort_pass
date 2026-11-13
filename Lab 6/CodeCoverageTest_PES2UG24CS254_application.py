import pytest
from ski_resort_pass import process_resort_bookings, check_chairlift_anemometer


def make_group(duration="full_day", skiers=None, locker=False, active=True):
    return {
        "is_active": active,
        "duration": duration,
        "includes_lodge_locker": locker,
        "skiers": skiers if skiers is not None else [],
    }


def make_skier(age=30, gear=False, blackout=False):
    return {"age": age, "gear_rental": gear, "blackout_override": blackout}


# ---------- process_resort_bookings ----------

def test_single_adult_full_day():
    groups = [make_group(skiers=[make_skier(30)])]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 80.0, "status": "COMPLETED"}


def test_invalid_groups_type_raises():
    with pytest.raises(ValueError):
        process_resort_bookings("not a list", 10.0)


def test_negative_facility_fee_raises():
    with pytest.raises(ValueError):
        process_resort_bookings([], -1.0)


def test_inactive_group_is_skipped():
    groups = [make_group(active=False, skiers=[make_skier(30)])]
    result = process_resort_bookings(groups, 10.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_season_pass_adult():
    groups = [make_group("season", [make_skier(30)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 300.0


def test_half_day_pass_adult():
    groups = [make_group("half_day", [make_skier(30)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 50.0


def test_invalid_duration_is_rejected():
    groups = [make_group("weekend", [make_skier(30)])]
    result = process_resort_bookings(groups, 0.0)
    assert result["status"] == "ZERO_SALES"


def test_child_discount():
    groups = [make_group(skiers=[make_skier(8)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 48.0


def test_senior_discount():
    groups = [make_group(skiers=[make_skier(70)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 56.0


def test_invalid_age_is_rejected_and_adult_still_counted():
    groups = [make_group(skiers=[make_skier(0), make_skier(30)])]
    result = process_resort_bookings(groups, 0.0)
    assert result == {"total_revenue": 80.0, "status": "COMPLETED"}


def test_blackout_override_full_day_charges_half_rate():
    groups = [make_group(skiers=[make_skier(30, blackout=True)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 40.0


def test_blackout_override_half_day_voids_group():
    groups = [make_group("half_day", [make_skier(30), make_skier(30, blackout=True), make_skier(30)])]
    result = process_resort_bookings(groups, 0.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_gear_rental_adds_fee():
    groups = [make_group(skiers=[make_skier(30, gear=True)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 115.0


def test_lodge_locker_adds_facility_fee():
    groups = [make_group(skiers=[make_skier(30)], locker=True)]
    assert process_resort_bookings(groups, 15.0)["total_revenue"] == 95.0


def test_audit_review_when_more_than_four_rejections():
    skiers = [make_skier(0) for _ in range(5)] + [make_skier(30)]
    groups = [make_group(skiers=skiers)]
    result = process_resort_bookings(groups, 0.0)
    assert result == {"total_revenue": 80.0, "status": "AUDIT_REVIEW"}


# ---------- check_chairlift_anemometer ----------

def test_anemometer_no_data():
    assert check_chairlift_anemometer([]) == "NO_DATA"


def test_anemometer_suspend_on_consecutive_gusts():
    assert check_chairlift_anemometer([[10, 50, 60]]) == "SUSPEND_LIFT"


def test_anemometer_safe_operation():
    assert check_chairlift_anemometer([[10, 20], [30, 40]]) == "SAFE_OPERATION"
