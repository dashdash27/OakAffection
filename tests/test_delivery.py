import pytest
from app.checkout.utils import calculate_order_dimensions
from app.checkout.services.yandex import get_allowed_yandex_profiles, get_filtered_yandex_points

MOSCOW_REGION_FIAS = "29251dcf-00a1-4e34-98d4-5c47484a36d4"      # Usual region
AMUR_REGION_FIAS = "844a80d6-5e31-4017-b422-4d9c01e9942c"        # Remote region

DIMENSIONS_TEST_DATA = [
    # Test 1 - 5 mini products 220ml
    (
        [{"quantity": 5, "weight": 220, "length": 6, "height": 14, "depth": 4}], 
        {
            "total_weight": 1188,         # 5 * 220 * 1.08 = 1188
            "max_item_side": 15,          # 14 * 1.05 = 14.7 -> 15
            "max_item_weight": 231,        # 220 * 1.05 = 231
            "cubic_sum_of_sides": 43      
        }
    ),
    
    # Test 2: 1 big product 10000ml
    (
        [{"quantity": 1, "weight": 10500, "length": 23, "height": 38, "depth": 19}],
        {
            "total_weight": 11340,        # 10500 * 1.08 = 11340
            "max_item_side": 40,          # 38 * 1.05 = 39.9 -> 40
            "max_item_weight": 11025,      # 10500 * 1.05 = 11025
            "cubic_sum_of_sides": 92
        }
    ),
    
    # Test 3: 5 mini products 220ml + 1 big product 10000ml
    (
        [
            {"quantity": 5, "weight": 220, "length": 6, "height": 14, "depth": 4},
            {"quantity": 1, "weight": 10500, "length": 23, "height": 38, "depth": 19}
        ],
        {
            "total_weight": 12528,
            "max_item_side": 40,
            "max_item_weight": 11025,
            "cubic_sum_of_sides": 95
        }
    ),

    # Test 4: empty cart
    (
        [],
        {
            "total_weight": 0,
            "max_item_side": 0,
            "max_item_weight": 0,
            "cubic_sum_of_sides": 0
        }
    )
]

@pytest.mark.parametrize("cart_items, expected", DIMENSIONS_TEST_DATA)
def test_calculate_order_dimensions_logic(cart_items, expected):
    """Smart test for calculate_order_dimensions function"""
    result = calculate_order_dimensions(cart_items)

    assert result["total_weight"] == expected["total_weight"], "Ошибка в расчете общего веса"
    assert result["max_item_side"] == expected["max_item_side"], "Ошибка в расчете максимальной стороны"
    assert result["max_item_weight"] == expected["max_item_weight"], "Ошибка в расчете максимального веса единицы"
    assert result["cubic_sum_of_sides"] == expected["cubic_sum_of_sides"], "Ошибка в расчете кубического корня сторон"
    
    assert isinstance(result["total_weight"], int)
    assert isinstance(result["max_item_side"], int)
    assert isinstance(result["max_item_weight"], int)
    assert isinstance(result["cubic_sum_of_sides"], int)

def test_yandex_profiles_for_normal_region():
    """Test: normal region and light order - all points should be allowed"""
    light_order = {
        "total_weight": 2000,
        "cubic_sum_of_sides": 50,
        "max_item_side": 15,
        "max_item_weight": 500
    }

    allowed = get_allowed_yandex_profiles(light_order, dadata_region_fias_id=MOSCOW_REGION_FIAS)
    
    assert "point" in allowed
    assert "postamat" in allowed
    assert "five_post_postamat" in allowed

def test_yandex_profiles_for_remote_region_light_order():
    """Test: remote region and light order - all points should be allowed"""
    light_order = {
        "total_weight": 2000,
        "cubic_sum_of_sides": 50,
        "max_item_side": 15,
        "max_item_weight": 500
    }

    allowed = get_allowed_yandex_profiles(light_order, dadata_region_fias_id=AMUR_REGION_FIAS)

    assert "point" in allowed
    assert "postamat" in allowed
    assert "five_post_postamat" in allowed


def test_yandex_profiles_for_remote_region_heavy_order():
    """Test: remote region and heavy order - all points should be blocked"""
    heavy_order = {
        "total_weight": 16201,         # 16.2 кг
        "cubic_sum_of_sides": 178,
        "max_item_side": 21,
        "max_item_weight": 525
    }

    allowed = get_allowed_yandex_profiles(heavy_order, dadata_region_fias_id=AMUR_REGION_FIAS)

    assert len(allowed) == 0
    assert "point" not in allowed
    assert "five_post_postamat" not in allowed

def test_yandex_profiles_only_one_allowed_in_remote_region():
    """Test: remote region and heavy order - only  points and five_post_postamat should be allowed"""
    high_canister_order = {
        "total_weight": 11500,
        "cubic_sum_of_sides": 85,
        "max_item_side": 45,
        "max_item_weight": 11500
    }

    allowed = get_allowed_yandex_profiles(high_canister_order, dadata_region_fias_id=AMUR_REGION_FIAS)

    assert "point" in allowed
    assert "five_post_postamat" in allowed
    assert "postamat" not in allowed

def test_filter_pickup_points_by_name():
    """
    Тест: Проверяем, что функция фильтрации конкретных адресов ПВЗ
    правильно распознает текстовые названия (name) в разном регистре.
    """
    # Искусственный список точек, прилетевший как бы от Яндекса
    mock_raw_points = [
        {"id": 1, "name": "Пункт выдачи заказов ул. Ленина, 10"},
        {"id": 2, "name": "Постамат Яндекс Маркет (ТЦ Космос)"},
        {"id": 3, "name": "Магазин Пятерочка (5 Post)"},
        {"id": 4, "name": "ПВЗ на Красной, 42"},
        {"id": 5, "name": "Какой-то другой СДЭК или Боксберри"} 
    ]

    # Case 1 
    allowed_profiles_1 = ["point", "five_post_postamat"]
    result_1 = get_filtered_yandex_points(mock_raw_points, allowed_profiles_1)

    result_ids_1 = [point["id"] for point in result_1]
    
    assert 1 in result_ids_1
    assert 3 in result_ids_1
    assert 4 in result_ids_1
    assert 2 not in result_ids_1
    assert 5 not in result_ids_1

    # Case 2
    allowed_profiles_2 = ["postamat"]
    result_2 = get_filtered_yandex_points(mock_raw_points, allowed_profiles_2)
    result_ids_2 = [point["id"] for point in result_2]
    
    assert len(result_ids_2) == 1
    assert 2 in result_ids_2

    # Case 3
    allowed_profiles_3 = []
    result_3 = get_filtered_yandex_points(mock_raw_points, allowed_profiles_3)
    
    assert len(result_3) == 0