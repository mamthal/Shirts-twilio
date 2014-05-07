#! /usr/bin/python
from flask import Flask,request,redirect
import twilio.twiml
import requests,re,json

# Your Account Sid and Auth Token from twilio.com/user/account
twilio_account_sid = "ACd614094e486f4db89cd4cbbc4f15b885"
twilio_auth_token  = "e93f804e510265bb2d6253195370092c"
shirts_auth_token = "f64427501001ae2b3be8f618b757c7767febe00f"

Quote_Num = 0 #This can be stored in some database or file and when the server needs to be restarted this can be written back to the file
app = Flask(__name__)

@app.route("/", methods=['GET','POST'])
def quote():
    shirt_type = None
    quantity = None
    print_type = None
    resp = twilio.twiml.Response()
    message_body = request.values.get('Body',None)
    search = re.search('NEW QUOTE',message_body)
    if search is None:
        resp.message("Invalid request")
        return str(resp)
    else:
        data = message_body.split(';')
        for line in data:
            if re.search('TYPE', line) is not None:
                if re.search('White T-Shirt \(G500\)',line) is not None:
                    shirt_type = 1
                elif re.search('Colored T-Shirt \(G500\)',line) is not None:
                    shirt_type = 3
                elif re.search('American Apparel T-Shirt \(2001\)',line) is not None:
                    shirt_type = 31
                elif re.search('Sweatshirt \(G180\)',line) is not None:
                    shirt_type = 5
                elif re.search('Hoodie \(G950\)',line) is not None:
                    shirt_type = 7
                else:
                    #User has provided a garment type that we cannot handle
                    resp.message("Invalid shirt type. Please choose a type from\n White T-Shirt (G500)\n Colored T-Shirt (G500)\n American Apparel T-Shirt (2001)\n Sweatshirt (G180)\n Hoodie (G950).\n Please try again with NEW QUOTE.")
                    return str(resp)
            elif re.search("QTY", line) is not None:
                tag, quantity = line.split(':')
            elif re.search("PRINTTYPE",line) is not None:#This is to provide the type of print used for the shirts
                tag, print_type = line.split(':')
            else:
                #This can be a place-holder for adding more options
                #We dont add a print message because it does not affect the quote in anyway
                print line #we simply print the line to standard-out for this demo
        if quantity is None:
            resp.message("Please specify the number of shirts for the quote.")
            return str(resp)
        if print_type is None:
            print_type = 'Screenprint'
        quote_str = "https://www.shirts.io/api/v1/quote/?api_key=%s&test=True&print_type=%s&garment[0][product_id]=%d" % (shirts_auth_token,print_type,shirt_type)
        quote_str = quote_str + "&garment[0][color]=White&garment[0][sizes][med]=%s&print[front][color_count]=1" % (quantity)

    print quote_str
    shirts_resp = requests.get(quote_str)

    if shirts_resp.status_code != 200:
        resp.message("Shirts.io server error. Please try again later or check your quote message and try again!")
        return str(resp)
    
    try:
        quote_obj = json.loads(str(shirts_resp.text)) # Converts the response which is a json string to a python object
        global Quote_Num
        Quote_Num = Quote_Num + 1
        
        #Printing the response. Additional information can be added to the response later if needed
        resp.message("Quote " + str(Quote_Num) + "\nSub-Total price - " + str(quote_obj["result"]["subtotal"]) + "\nDiscount - " + str(quote_obj["result"]["discount"]) + "\nShipping price - " + str(quote_obj["result"]["shipping_price"]) + "\nTotal price - " + str(quote_obj["result"]["total"]))
        
        return str(resp)
    except ValueError:
        resp.message("Shirts.io server error. Please try again later or check your quote message and try again!")
        return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
