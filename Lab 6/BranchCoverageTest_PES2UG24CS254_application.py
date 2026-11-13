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


# ---------- process_resort_bookings: validation ----------

def test_single_adult_full_day():
    groups = [make_group(skiers=[make_skier(30)])]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 80.0, "status": "COMPLETED"}


@pytest.mark.parametrize("bad_groups", ["text", None, {"a": 1}, 42])
def test_non_list_groups_raise(bad_groups):
    with pytest.raises(ValueError):
        process_resort_bookings(bad_groups, 10.0)


def test_negative_fee_with_valid_list_raises():
    with pytest.raises(ValueError):
        process_resort_bookings([], -0.01)


def test_zero_fee_is_valid():
    assert process_resort_bookings([], 0.0)["status"] == "ZERO_SALES"


def test_empty_groups_list_is_zero_sales():
    assert process_resort_bookings([], 10.0) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


# ---------- group-level branches ----------

def test_inactive_group_skipped():
    groups = [make_group(active=False, skiers=[make_skier(30)], locker=True)]
    assert process_resort_bookings(groups, 10.0)["status"] == "ZERO_SALES"


def test_group_missing_is_active_defaults_to_inactive():
    assert process_resort_bookings([{}], 10.0)["status"] == "ZERO_SALES"


def test_defaults_for_duration_and_skiers_when_missing():
    # active, no duration (-> full_day), no skiers, no locker
    result = process_resort_bookings([{"is_active": True}], 10.0)
    assert result["status"] == "ZERO_SALES"


def test_default_duration_is_full_day_rate():
    groups = [{"is_active": True, "skiers": [make_skier(30)]}]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 80.0


@pytest.mark.parametrize("duration,expected", [
    ("season", 300.0),
    ("full_day", 80.0),
    ("half_day", 50.0),
])
def test_each_duration_base_rate(duration, expected):
    groups = [make_group(duration, [make_skier(30)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == expected


def test_invalid_duration_rejected_and_next_group_processed():
    groups = [make_group("weekend", [make_skier(30)]), make_group("full_day", [make_skier(30)])]
    result = process_resort_bookings(groups, 0.0)
    assert result == {"total_revenue": 80.0, "status": "COMPLETED"}


def test_group_with_no_skiers_but_locker_still_charged():
    groups = [make_group(skiers=[], locker=True)]
    assert process_resort_bookings(groups, 15.0)["total_revenue"] == 15.0


def test_locker_false_branch_no_fee():
    groups = [make_group(skiers=[make_skier(30)], locker=False)]
    assert process_resort_bookings(groups, 99.0)["total_revenue"] == 80.0


def test_locker_true_branch_adds_fee():
    groups = [make_group(skiers=[make_skier(30)], locker=True)]
    assert process_resort_bookings(groups, 15.0)["total_revenue"] == 95.0


# ---------- skier-level branches (with boundaries) ----------

def test_age_zero_rejected():
    groups = [make_group(skiers=[make_skier(0), make_skier(30)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 80.0


def test_negative_age_rejected():
    groups = [make_group(skiers=[make_skier(-5), make_skier(30)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 80.0


def test_skier_missing_age_defaults_to_rejected():
    groups = [make_group(skiers=[{}, make_skier(30)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 80.0


def test_age_one_is_valid_child():
    groups = [make_group(skiers=[make_skier(1)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 48.0


def test_age_11_child_discount():
    groups = [make_group(skiers=[make_skier(11)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 48.0


def test_age_12_pays_full_rate():
    groups = [make_group(skiers=[make_skier(12)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 80.0


def test_age_64_pays_full_rate():
    groups = [make_group(skiers=[make_skier(64)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 80.0


def test_age_65_senior_discount():
    groups = [make_group(skiers=[make_skier(65)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 56.0


def test_gear_rental_true_adds_fee():
    groups = [make_group(skiers=[make_skier(30, gear=True)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 115.0


def test_gear_rental_on_child_senior_and_blackout():
    groups = [make_group(skiers=[
        make_skier(8, gear=True),                  # 48 + 35
        make_skier(70, gear=True),                 # 56 + 35
        make_skier(30, gear=True, blackout=True),  # 40 + 35
    ])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 249.0


def test_invalid_age_with_gear_rental_not_charged():
    groups = [make_group(skiers=[make_skier(0, gear=True)])]
    assert process_resort_bookings(groups, 0.0)["status"] == "ZERO_SALES"


def test_blackout_full_day_half_rate():
    groups = [make_group("full_day", [make_skier(30, blackout=True)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 40.0


def test_blackout_season_half_rate():
    groups = [make_group("season", [make_skier(30, blackout=True)])]
    assert process_resort_bookings(groups, 0.0)["total_revenue"] == 150.0


def test_blackout_half_day_voids_whole_group_and_stops_processing():
    groups = [make_group("half_day", [
        make_skier(30, gear=True),
        make_skier(30, blackout=True),
        make_skier(30),
    ], locker=True)]
    # group total reset to 0, loop breaks, locker fee still added
    result = process_resort_bookings(groups, 20.0)
    assert result == {"total_revenue": 20.0, "status": "COMPLETED"}


def test_blackout_half_day_void_without_locker_is_zero_sales():
    groups = [make_group("half_day", [make_skier(30), make_skier(30, blackout=True)])]
    assert process_resort_bookings(groups, 20.0)["status"] == "ZERO_SALES"


# ---------- final status branches ----------

def test_exactly_four_rejections_not_audit():
    skiers = [make_skier(0) for _ in range(4)] + [make_skier(30)]
    result = process_resort_bookings([make_group(skiers=skiers)], 0.0)
    assert result == {"total_revenue": 80.0, "status": "COMPLETED"}


def test_five_rejections_triggers_audit_review():
    skiers = [make_skier(0) for _ in range(5)] + [make_skier(30)]
    result = process_resort_bookings([make_group(skiers=skiers)], 0.0)
    assert result == {"total_revenue": 80.0, "status": "AUDIT_REVIEW"}


def test_audit_review_takes_priority_over_zero_sales():
    skiers = [make_skier(0) for _ in range(5)]
    result = process_resort_bookings([make_group(skiers=skiers)], 0.0)
    assert result == {"total_revenue": 0.0, "status": "AUDIT_REVIEW"}


def test_rounding_of_total_revenue():
    groups = [make_group(skiers=[make_skier(8)])]
    result = process_resort_bookings(groups, 0.333)
    assert result["total_revenue"] == 48.0


def test_zero_sales_status():
    groups = [make_group(skiers=[make_skier(0)])]
    assert process_resort_bookings(groups, 0.0) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


# ---------- check_chairlift_anemometer ----------

@pytest.mark.parametrize("empty", [[], None])
def test_anemometer_no_data(empty):
    assert check_chairlift_anemometer(empty) == "NO_DATA"


def test_anemometer_two_consecutive_gusts_suspends():
    assert check_chairlift_anemometer([[10, 46, 47]]) == "SUSPEND_LIFT"


def test_anemometer_exactly_45_is_not_a_gust():
    assert check_chairlift_anemometer([[45, 45, 45]]) == "SAFE_OPERATION"


def test_anemometer_single_gust_is_safe():
    assert check_chairlift_anemometer([[10, 50, 10]]) == "SAFE_OPERATION"


def test_anemometer_non_consecutive_gusts_reset_streak():
    assert check_chairlift_anemometer([[50, 10, 50, 10, 50]]) == "SAFE_OPERATION"


def test_anemometer_suspend_detected_on_later_lift():
    assert check_chairlift_anemometer([[10, 20], [50, 60]]) == "SUSPEND_LIFT"


def test_anemometer_streak_resets_between_lifts():
    # one gust at end of lift 1, one at start of lift 2: must NOT combine
    assert check_chairlift_anemometer([[10, 50], [50, 10]]) == "SAFE_OPERATION"


def test_anemometer_lift_with_empty_readings():
    assert check_chairlift_anemometer([[]]) == "SAFE_OPERATION"
