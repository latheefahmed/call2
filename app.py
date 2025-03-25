from flask import Flask, jsonify, send_from_directory, abort
from flask_cors import CORS
import pandas as pd
from twilio.rest import Client
import os

app = Flask(__name__)
CORS(app)

# Twilio configuration
# Environment variables can override these defaults if set.
account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')

# Use a dedicated number for SMS/Calls (must be a valid Twilio number enabled for these channels)
twilio_call_sms_number = os.getenv('twilio_call_sms_number', '+16812532416')

# Use the WhatsApp Sandbox number (with the whatsapp: prefix)
twilio_whatsapp_number = 'whatsapp:+14155238886'

# URL for Twilio to fetch TwiML instructions for calls
twilio_bin_url = os.getenv('twilio_bin_url')

client = Client(account_sid, auth_token)

# Load CSV data (ensure the file exists with the proper columns)
data_path = 'Statement8_Dataset.csv'
data = None
if os.path.exists(data_path):
    try:
        data = pd.read_csv(data_path)
    except Exception as e:
        print(f"Error loading CSV file: {e}")
else:
    print(f"CSV file not found at {data_path}. Please check the file path.")

@app.route('/')
def index():
    file_path = os.path.join(os.getcwd(), 'index.html')
    if os.path.exists(file_path):
        return send_from_directory(os.getcwd(), 'index.html')
    else:
        abort(404, description="Index file not found.")

@app.route('/send-calls', methods=['POST'])
def send_calls():
    if data is None:
        return jsonify(["Data not loaded. Check CSV path."])
    
    results = []
    grouped_data = data.groupby('RationCardNumber')
    for ration_card_number, group in grouped_data:
        cardholder_row = group[group['RelationToCardHolder'] == 'Self']
        if not cardholder_row.empty:
            gender = cardholder_row['Gender'].values[0].strip().lower()
            num_family = cardholder_row['NumberOfFamilyMembers'].values[0]
            phone = cardholder_row['PhoneNumber'].values[0]
            head_name = cardholder_row['MemberName'].values[0]

            if gender == 'male' and num_family > 1:
                has_spouse = not group[
                    (group['RelationToCardHolder'] == 'Spouse') &
                    (group['Gender'].str.lower() == 'female')
                ].empty
                if has_spouse:
                    try:
                        call = client.calls.create(
                            to=phone,
                            from_=twilio_call_sms_number,
                            url=twilio_bin_url
                        )
                        results.append(f"Call initiated to {head_name} at {phone}")
                    except Exception as e:
                        results.append(f"Failed to call {head_name} at {phone}: {str(e)}")
                else:
                    results.append(f"No call made to {head_name} (no spouse available).")
            elif gender == 'male' and num_family == 1:
                results.append(f"No call made to {head_name} (only 1 family member).")
            else:
                results.append(f"No action needed for {head_name} (already updated).")
    return jsonify(results)

@app.route('/send-messages', methods=['POST'])
def send_messages():
    if data is None:
        return jsonify(["Data not loaded. Check CSV path."])
    
    results = []
    grouped_data = data.groupby('RationCardNumber')
    for ration_card_number, group in grouped_data:
        cardholder_row = group[group['RelationToCardHolder'] == 'Self']
        if not cardholder_row.empty:
            gender = cardholder_row['Gender'].values[0].strip().lower()
            num_family = cardholder_row['NumberOfFamilyMembers'].values[0]
            phone = cardholder_row['PhoneNumber'].values[0]
            head_name = cardholder_row['MemberName'].values[0]

            if gender == 'male' and num_family > 1:
                has_spouse = not group[
                    (group['RelationToCardHolder'] == 'Spouse') &
                    (group['Gender'].str.lower() == 'female')
                ].empty
                if has_spouse:
                    try:
                        message = client.messages.create(
                            to=phone,
                            from_=twilio_call_sms_number,
                            body=f"Hello {head_name}, please update your household head to your spouse. Visit: https://tnpds.gov.in/"
                        )
                        results.append(f"SMS sent to {head_name} at {phone}")
                    except Exception as e:
                        results.append(f"Failed to send SMS to {head_name} at {phone}: {str(e)}")
                else:
                    results.append(f"No SMS sent to {head_name} (no spouse available).")
            elif gender == 'male' and num_family == 1:
                results.append(f"No SMS sent to {head_name} (only 1 family member).")
            else:
                results.append(f"No action needed for {head_name} (already updated).")
    return jsonify(results)

@app.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    if data is None:
        return jsonify(["Data not loaded. Check CSV path."])
    
    results = []
    grouped_data = data.groupby('RationCardNumber')
    for ration_card_number, group in grouped_data:
        cardholder_row = group[group['RelationToCardHolder'] == 'Self']
        if not cardholder_row.empty:
            gender = cardholder_row['Gender'].values[0].strip().lower()
            num_family = cardholder_row['NumberOfFamilyMembers'].values[0]
            phone = cardholder_row['PhoneNumber'].values[0]
            head_name = cardholder_row['MemberName'].values[0]

            if gender == 'male' and num_family > 1:
                has_spouse = not group[
                    (group['RelationToCardHolder'] == 'Spouse') &
                    (group['Gender'].str.lower() == 'female')
                ].empty
                if has_spouse:
                    try:
                        message = client.messages.create(
                            to=f'whatsapp:{phone}',
                            from_=twilio_whatsapp_number,
                            body=f"Hello {head_name}, please update your household head to your spouse. Visit: https://tnpds.gov.in/"
                        )
                        results.append(f"WhatsApp message sent to {head_name} at {phone}")
                    except Exception as e:
                        results.append(f"Failed to send WhatsApp message to {head_name} at {phone}: {str(e)}")
                else:
                    results.append(f"No WhatsApp message sent to {head_name} (no spouse available).")
            elif gender == 'male' and num_family == 1:
                results.append(f"No WhatsApp message sent to {head_name} (only 1 family member).")
            else:
                results.append(f"No action needed for {head_name} (already updated).")
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
