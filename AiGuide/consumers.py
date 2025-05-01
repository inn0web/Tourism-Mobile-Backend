import json
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import OpenAI
from decouple import config
from channels.db import database_sync_to_async
from decouple import config
from .models import Thread
from Places.utils import Feed
from Places.models import City
class EuroTripAiConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        # initialise open ai and the assistants 
        self.client = OpenAI(
            api_key=config("OPENAI_API_KEY") 
        )
        
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.current_city_name = self.scope['url_route']['kwargs']['city_name']
        
        try:
            self.thread_id = self.scope['url_route']['kwargs']['thread_id']
            self.thread = self.client.beta.threads.retrieve(thread_id=self.thread_id)
            
            await self.set_current_city_name_and_location()

            self.room_name = f"eurotrip_chat_session_{self.user_id}_{self.thread_id}"
        except Exception as e:
            self.thread_id = None
            # If thread_id is not provided, create a new thread
            self.room_name = f"eurotrip_chat_session_{self.user_id}"
        
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        self.assistant = self.client.beta.assistants.retrieve(
            assistant_id = config('OPENAI_ASSISTANT_ID'),
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    def generate_thread_name(self, message):

        instruction = f"""
        You are an assistant that generates a concise and catchy 
        thread name based on the user’s message. The thread name 
        should reflect the main topic or intent of the message by
        incorporating relevant keywords or phrases. Focus on 
        summarizing the essence of the message in a few words, similar 
        to how AI assistants like ChatGPT or Claude title new conversations. 
        Return only the generated thread name, without any additional 
        explanation or formatting.

        Message: 

        {message}
        """

        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=instruction
        )

        return response.output_text.strip('"')

    def extract_google_places_searchable_keywords_from_user_message(self, message):

        instruction = f"""
        You are an assistant designed to extract relevant and concise 
        searchable keywords from a user's message. These keywords will be 
        used to query the Google Places API for location-based results.

        Focus on nouns and key descriptors relevant to location searches, 
        such as types of places, amenities, and specific geographic locations 
        (e.g., city names). Avoid filler words like "near", "with", "looking for", 
        "want", etc.

        Return only the most useful and specific keywords that best represent 
        the user's intent. Format your response as a simple, comma-separated list, 
        with no additional text or explanation.

        Example format: coffee shop, Wi-Fi, bookstore, Amsterdam

        Message:
        {message}
        """

        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=instruction
        )

        return response.output_text.strip('"').split(',')

    async def create_new_open_ai_thread(self, message):

        self.thread = self.client.beta.threads.create()
        self.thread_id = self.thread.id

        await self.create_new_user_thread_in_database(
            thread_id = self.thread_id,
            thread_name = self.generate_thread_name(message)
        )

    async def get_places_based_on_user_message(self, message):
        
        places = Feed().get_places_from_google_maps_for_ai_request(
            city_name = self.current_city_name,
            city_location = self.current_city_location,
            extracted_search_interests_from_message = self.extract_google_places_searchable_keywords_from_user_message(message)
        )

        return places
    
    async def receive(self, text_data):

        # get payload from client(frontend)
        payload = json.loads(text_data)
        message = payload['message']

        # If thread_id is not provided, create a new thread
        if (len(message) > 0) and (self.thread_id == None):
            
            await self.create_new_open_ai_thread(message)
            await self.set_current_city_name_and_location()
        
        places = await self.get_places_based_on_user_message(message)
        places = json.dumps(places, indent=4)
        
        # create a new message to ve sent to openai
        construct_message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=places
        )

        # run the assistant and poll the responses from ai
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )

        if run.status == 'completed': 

            # grab the last message sent in the thread (which is the AI's message)
            ai_message = self.client.beta.threads.messages.list(
                thread_id=self.thread.id,
                limit=1,
                order='desc'
            )

            ai_response = ai_message.data[0].content[0].text.value

            # parse the AI response to a JSON object if it is a string
            # This is to ensure that the response is in a valid JSON format
            if isinstance(ai_response, str):
                try:
                    # Attempt to parse the string as JSON
                    ai_response = json.loads(ai_response)
                except json.JSONDecodeError:
                    print("Error: Invalid AI response format.")
                    return
           
            # send message back to client
            event = {
                'type': 'send_message',
                'ai_response': ai_response
            }

            # call event to send message to client
            await self.channel_layer.group_send(self.room_name, event)

            # save this message/response to the database as a new user thread message
            await self.save_user_message_to_a_new_thread_message_in_database(user_message={"message": message})
            
            # save this message/response to the database as a new ai guide thread message
            await self.save_ai_response_to_a_new_thread_message_in_database(ai_response)

        else:

            event = {
                'type': 'send_message',
                'ai_response': 'TripAi is not available right now. Please try again later.',
            }

            # call event to send message to client
            await self.channel_layer.group_send(self.room_name, event)

    async def send_message(self, event):

       data = event['ai_response']
       await self.send(text_data=json.dumps({'message': data}))

    @database_sync_to_async
    def create_new_user_thread_in_database(self, thread_id, thread_name):

        # Create a new thread in the database
        Thread.objects.create(
            user_id=self.user_id,
            thread_name=thread_name,
            thread_id=thread_id
        )

    @database_sync_to_async
    def save_ai_response_to_a_new_thread_message_in_database(self, ai_response):

        # Create a new thread in the database
        thread = Thread.objects.get(thread_id=self.thread_id)
        thread.create_new_message(sent_by="ai", message_content=ai_response)

    @database_sync_to_async
    def save_user_message_to_a_new_thread_message_in_database(self, user_message):

        # Create a new thread in the database
        thread = Thread.objects.get(thread_id=self.thread_id)
        thread.create_new_message(sent_by="user", message_content=user_message)

    @database_sync_to_async
    def set_current_city_name_and_location(self):
        
        try:

            city = City.objects.get(name=self.current_city_name)
            self.current_city_name = city.name
            self.current_city_location = (city.latitude, city.longitude)

        except City.DoesNotExist:
            self.current_city_name = ""
            self.current_city_location = ()