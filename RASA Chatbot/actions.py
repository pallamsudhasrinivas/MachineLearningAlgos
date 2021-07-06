from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import zomatopy
import json

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

tier1_2 = ['ahmedabad', 'bengaluru', 'chennai', 'delhi', 'hyderabad', 'kolkata', 'mumbai', 'pune', 'agra', 'ajmer',
           'aligarh', 'amravati', 'amritsar', 'asansol', 'aurangabad', 'bareilly', 'belgaum', 'bhavnagar', 'bhiwandi',
           'bhopal', 'bhubaneswar', 'bikaner', 'bilaspur', 'bokaro steel city', 'chandigarh', 'coimbatore', 'cuttack',
           'dehradun', 'dhanbad', 'bhilai', 'durgapur', 'dindigul', 'erode', 'faridabad', 'firozabad', 'ghaziabad',
           'gorakhpur', 'gulbarga', 'guntur', 'gwalior', 'gurgaon', 'guwahati', 'hamirpur', 'hubli–dharwad', 'indore',
           'jabalpur', 'jaipur', 'jalandhar', 'jammu', 'jamnagar', 'jamshedpur', 'jhansi', 'jodhpur', 'kakinada',
           'kannur', 'kanpur', 'karnal', 'kochi', 'kolhapur', 'kollam', 'kozhikode', 'kurnool', 'ludhiana', 'lucknow',
           'madurai', 'malappuram', 'mathura', 'mangalore', 'meerut', 'moradabad', 'mysore', 'nagpur', 'nanded',
           'nashik', 'nellore', 'noida', 'patna', 'pondicherry', 'purulia', 'prayagraj', 'raipur', 'rajkot',
           'rajahmundry', 'ranchi', 'rourkela', 'salem', 'sangli', 'shimla', 'siliguri', 'solapur', 'srinagar',
           'surat', 'thanjavur', 'thiruvananthapuram', 'thrissur', 'tiruchirappalli', 'tirunelveli', 'ujjain',
           'bijapur', 'vadodara', 'varanasi', 'vasai-virar city', 'vijayawada', 'visakhapatnam', 'vellore', 'warangal']


class ActionSearchRestaurants(Action):
    def name(self):
        return 'action_search_restaurants'

    def run(self, dispatcher, tracker, domain):
        config = {"user_key": "1eb231cb1eb260c5fd373f092a2dd2dd"}
        # config = {"user_key": "f4924dc9ad672ee8c4f8c84743301af5"}
        # config = {'user_key':"455c41499144739a6f131347a8130495"}
        zomato = zomatopy.initialize_app(config)
        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine').lower()
        if tracker.get_slot('price') is not None:
            price_range = tracker.get_slot('price')
        else:
            price_range = 'no_constraint'
        # Declaring the different price ranges for cuisines
        # print("Location: {0}, Cuisine: {1}, Price Range: {2}".format(loc, cuisine, price_range))
        price_dict = {'low': {'lower': 0, 'upper': 300},
                      'mid': {'lower': 300, 'upper': 700},
                      'high': {'lower': 700, 'upper': 500000},
                      'no_constraint': {'lower': 0, 'upper': 500000}
                      }
        location_detail = zomato.get_location(loc, 1)
        d1 = json.loads(location_detail)
        lat = d1["location_suggestions"][0]["latitude"]
        lon = d1["location_suggestions"][0]["longitude"]
        cuisines_dict = {'chinese': 25, 'italian': 55, 'north indian': 50,
                         'south indian': 85, 'american': 1, 'mexican': 73}
        offset = 0
        result_counter = 0
        response_chat = ""
        response_mail = ""
        while result_counter < 10 and offset < 100:
            # print('result_counter, offset: ', result_counter, offset)
            # while calling the zomato API offset is also used inorder to search for restaurants in subsequent pages
            results = zomato.restaurant_search(offset, "", lat, lon, str(cuisines_dict.get(cuisine)), 20)
            # with open('response.txt', 'w') as resp_file:
            #     resp_file.write(results)
            d = json.loads(results)
            if d['results_found'] == 0:
                response_chat = "no results"
                response_mail = "no results"
                print(results)
            else:
                for restaurant in d['restaurants']:
                    average_cost = restaurant['restaurant']['average_cost_for_two']
                    # print("{0} average cost is {1}".format(restaurant['restaurant']['name'], average_cost))
                    # enters this condition only if the restaurant price range is between the ranges provided
                    if (price_dict[price_range.lower()]['lower'] <= average_cost <= price_dict[price_range.lower()]['upper']) & \
                            (result_counter < 10):
                        if result_counter < 5:
                            response_chat = response_chat + str(result_counter+1) + ". " + "Resturant Name: "+restaurant['restaurant']['name'] + ", Resturant Address:" + \
                                           restaurant['restaurant']['location']['address'] + ", Resturant Rating: " + \
                                           restaurant['restaurant']['user_rating']['aggregate_rating'] + ", Average cost for 2: " + \
                                           str(average_cost) + "\n"
                        response_mail = response_mail + str(result_counter+1) + ". " + "Resturant Name: "+restaurant['restaurant']['name'] + " Resturant Address: " + \
                                        restaurant['restaurant']['location']['address'] + " , Resturant Rating: " + \
                                        restaurant['restaurant']['user_rating']['aggregate_rating'] + " , Average cost for 2:" + \
                                        str(average_cost) + "\n"
                        result_counter += 1
                        print(result_counter, restaurant['restaurant']['name'])
            offset += 20

        dispatcher.utter_message("---------\n" + str(response_chat))
        if result_counter < 5:
            # if the number of results are less than 5 the following message will be displayed
            dispatcher.utter_message("There are only {0} restaurants in the Top 100 for your budget".format(result_counter))

        return [SlotSet('restaurant_dict', response_mail)]


class CheckLocation(Action):
    def name(self):
        return 'action_check_location'

    def run(self, dispatcher, tracker, domain):

        loc = tracker.get_slot('location')
        if loc.lower() in tier1_2:
            return [SlotSet('check_op', True)]
        else:
            return [SlotSet('check_op', False)]


class SendMail(Action):
    def name(self):
        return 'send_email'

    def run(self, dispatcher, tracker, domain):
        email = tracker.get_slot('email')
        restaurant_result = tracker.get_slot('restaurant_dict')
        location = tracker.get_slot('location')
        print("Email : ",email)
        #check email is valid or not
        #if re.match("\A(?P<name>[\w\-_]+)@(?P<domain>[\w\-_]+).(?P<toplevel>[\w]+)\Z",email,re.IGNORECASE):
        print("Email is valid")
        mail_content = '''Hello User,\n \n Welcome to Foodie Chatbot!! \n \n Following are the top 10 resturants search results in '''+location+'''\n \n Results:\n \n'''+restaurant_result+''' \n Thanks, \n Team Foodie '''

        #The mail addresses and password
        sender_address = 'sandmupgrad@gmail.com'
        sender_pass = 'Upgrad$1234'
        receiver_address = email
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = 'Foodie Search Results: Top 10 Restaurant results in '+location   #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'plain'))
        #Create SMTP session for sending the mail
        session = smtplib.SMTP_SSL('smtp.gmail.com:465') #use gmail with port
        session.ehlo()
        #session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
        dispatcher.utter_message("Mail Sent. Bon Appetit!")
        return [SlotSet('check_mail',True)]