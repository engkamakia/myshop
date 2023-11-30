from decimal import Decimal
#import stripe
from django.conf import settings
from django.shortcuts import render, redirect, reverse, get_object_or_404
from orders.models import Order  
    



import requests
from datetime import datetime
import json
import base64
from django.http import JsonResponse
from . utils import get_access_token
from django.conf import settings
from . utils import query_stk_status
from django.shortcuts import render, redirect




def initiate_stk_push(request, ph_number,total_amount):
    access_token_response = get_access_token(request)
    if isinstance(access_token_response, JsonResponse):
        access_token = access_token_response.content.decode('utf-8')
        access_token_json = json.loads(access_token)
        access_token = access_token_json.get('access_token')
        if access_token:
            amount = total_amount
            phone = ph_number
            process_request_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            callback_url = 'https://mydomain.com/pat'
            passkey = settings.MPESA_PASSKEY
            business_short_code = '174379'
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode((business_short_code + passkey + timestamp).encode()).decode()
            party_a = phone
            party_b = '254708374149'
            account_reference = 'George-Gadgets'
            transaction_desc = f'Do you want to pay {amount} kshs to account {account_reference}?'
            stk_push_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token
            }
            
            stk_push_payload = {
                'BusinessShortCode': business_short_code,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': amount,
                'PartyA': party_a,
                'PartyB': business_short_code,
                'PhoneNumber': party_a,
                'CallBackURL': callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }

            try:
                response = requests.post(process_request_url, headers=stk_push_headers, json=stk_push_payload)
                response.raise_for_status()   
                # Raise exception for non-2xx status codes
                response_data = response.json()
                checkout_request_id = response_data['CheckoutRequestID']
                response_code = response_data['ResponseCode']
                
                if response_code == "0":
                    return JsonResponse({'CheckoutRequestID': checkout_request_id})
                else:
                    return JsonResponse({'error': 'STK push failed.'})
            except requests.exceptions.RequestException as e:
                return JsonResponse({'error': str(e)})
        else:
            return JsonResponse({'error': 'Access token not found.'})
    else:
        return JsonResponse({'error': 'Failed to retrieve access token.'})
    
    
def payment (request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)
    
    order_items = order.items.all()  # Fetch all related OrderItems for this order

    # Now, let's calculate the total cost for this order
    total_cost = sum(item.price * item.quantity for item in order_items)
    
    if request.method == 'POST':
        name=request.POST.get('fname')
        phone_number=request.POST.get('phone_number')
        amount = total_cost #request.POST.get("amount")
        ph_number = None
        total_amount = int(amount)
        if phone_number[0] == '0':
            ph_number = '254'+ phone_number[1:]
        elif phone_number[0:2] == '254':
            ph_number = phone_number
        else:
            # messages.error(request, 'Check you Phone Number format 2547xxxxxxxx')
            return redirect(request.get_full_path())


        initiate_stk_push(request, ph_number,total_amount)

        return render (request,'payment/success.html')
        # return HttpResponse(f'Stk Push for {phone_number}')
    
    return render (request,'payment/payment.html', {'title': 'Payment'})
    
    
def process_stk_callback(request):
    stk_callback_response = json.loads(request.body)
    log_file = "Mpesastkresponse.json"
    with open(log_file, "a") as log:
        json.dump(stk_callback_response, log)
    
    merchant_request_id = stk_callback_response['Body']['stkCallback']['MerchantRequestID']
    checkout_request_id = stk_callback_response['Body']['stkCallback']['CheckoutRequestID']
    result_code = stk_callback_response['Body']['stkCallback']['ResultCode']
    result_desc = stk_callback_response['Body']['stkCallback']['ResultDesc']
    amount = stk_callback_response['Body']['stkCallback']['CallbackMetadata']['Item'][0]['Value']
    transaction_id = stk_callback_response['Body']['stkCallback']['CallbackMetadata']['Item'][1]['Value']
    user_phone_number = stk_callback_response['Body']['stkCallback']['CallbackMetadata']['Item'][4]['Value']
    
    #if result_code == 0:
     #  store the transaction details in the database
    
    