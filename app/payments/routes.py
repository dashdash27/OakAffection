from flask import Blueprint, request, jsonify
import json
from app import csrf

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/api/ozon-pay-webhook', methods=['POST'], strict_slashes=False)
@csrf.exempt
def ozon_pay_webhook():
    print("\n[FLASK] В РОУТ КТО-ТО ПОСТУЧАЛСЯ!", flush=True)
    data = request.get_json(silent=True)

    # if data is None:
    #     print("Получен пустой запрос или данные не в формате JSON")
    #     return "Invalid JSON", 400
    
    pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
    print(
        f"\n==== ПОЛУЧЕН ВЕБХУК ОТ OZON PAY ====\n"
        f"{pretty_json}\n"
        f"===================================="
    )

    return "OK", 200
