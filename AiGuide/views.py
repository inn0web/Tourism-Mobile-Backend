from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import WebSocketPlaceMessageSerializer, ThreadSerializer, ThreadMessageSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import Thread

class WebSocketMockAPIView(APIView):
    """
    Mock view for documenting the WebSocket endpoint `/ws/ai-guide/<city_name>/<user_id>/[<thread_id>/]`
    """

    @swagger_auto_schema(
        operation_summary="WebSocket Endpoint for AI Place Guide",
        tags=["Ai Chat"],
        operation_description="""
        **WebSocket Endpoint Description:**

        Connect via WebSocket to:

        - `ws://203.161.57.186:8003/ai-guide/<city_name>/<user_id>/`  
        ➤ Used to start a **new chat thread** (create a new conversation).

        - `ws://203.161.57.186:8003/ai-guide/<city_name>/<user_id>/<thread_id>/`  
        ➤ Used to **resume an existing chat thread** by providing the previously saved `thread_id`.

        ---
        **Message Format (Client to Server):**

        Once connected, the client **must send a message** in the following JSON format:
        ```json
        {
            "message": "I want to go touring, specifically places like old buildings or castles or places of the sort"
        }
        ```

        ---
        **Response Format (Server to Client):**

        The server will return a list of recommended places, each represented as a JSON object containing a message and an array of photo URLs:
        ```json
        [
            {
                "message": "Pogradec Castle is a historical landmark...",
                "photos": [
                    "https://lh3.googleusercontent.com/...",
                    "https://lh3.googleusercontent.com/..."
                ]
            }
        ]
        ```

        ---
        **Test the WebSocket Endpoint:**

        You can test this endpoint live using our demo tester at:  
        🔗 [http://203.161.57.186:8000/api/v1/ai/ai-test/](http://203.161.57.186:8000/api/v1/ai/ai-test/)

        ---
        **Source Code for Socket Test (HTML + JS):**

        View the implementation code used in the WebSocket tester:  
        📄 [ai_guide_test.html on GitHub](https://github.com/inn0web/Tourism-Mobile-Backend/blob/main/templates/ai_guide_test.html)
        """,
        responses={200: WebSocketPlaceMessageSerializer(many=True)}
    )
    def get(self, request, format=None):
        example_response = [
            {
                "message": "Pogradec Castle is a historical landmark...",
                "photos": [
                    "https://lh3.googleusercontent.com/example1",
                    "https://lh3.googleusercontent.com/example2"
                ]
            }
        ]
        return Response(example_response, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_summary="Get User Threads",
    tags=["Ai Chat"],
    operation_description="""
    Retrieve all threads (chat sessions) belonging to the authenticated user.
    Each thread includes its name, unique thread ID, and creation timestamp.
    This endpoint is useful for listing all previous AI guide conversations initiated by the user.
    """,
    responses={200: ThreadSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_threads(request):

    user = request.user
    user_threads = user.get_user_threads()
    serializer = ThreadSerializer(user_threads, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_summary="Retrieve Messages in a Thread",
    tags=["Ai Chat"],
    operation_description="""
    **Get Thread Messages**

    This endpoint retrieves the list of messages in a specified thread. It returns a JSON array of messages, which may either be:

    - **User Message**: Sent by the user to the AI.
    - **AI Message**: Sent by the AI to the user, containing additional content such as photos and descriptions of recommended places.

    **Message Formats:**

    1. **AI Message:**
    The AI response will contain a message and an array of photo URLs:
    
    ```json
    [
        {
            "message": "Pogradec Castle is a historical landmark located at WJ5W+9F8, Rruga e Kalasë, Pogradec, Albania. With a rating of 4.2, it offers visitors a glimpse into the region's rich history. The castle is currently open 24 hours, making it accessible for exploration at any time. You can find directions to this location [here](https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x1350943c7c71ff1f:0x5828a40ccb0912f5!3e0).",
            "photos": [
                "https://lh3.googleusercontent.com/a-/ALV-UjW4j1bXphVuz-qF_KUBfCXEfJo4cPTkkrdAOjeOcqCygZQQqD8uaw=s100-p-k-no-mo",
                "https://lh3.googleusercontent.com/a-/ALV-UjXb_KHCROnffhX_zKA3Th3vT2nYv8bZ0wU8UU5Y1hoRdWIcsC3sAA=s100-p-k-no-mo"
            ]
        }
    ]
    ```
    
    2. **User Message:**
    The user's message will contain a simple text string:

    ```json
    {
        "message": "I want to go touring, specifically places like old buildings or castles or places of the sort"
    }
    ```

    **Note**: The AI will respond with relevant recommendations based on the user's message.

    This endpoint requires authentication, and the user must be logged in.

    **Responses:**
    - 200: Successful retrieval of thread messages.
    - 404: If the thread is not found.

    """,
    responses={
        200: openapi.Response(
            description="List of thread messages",
            schema=ThreadMessageSerializer(many=True)
        ),
        404: openapi.Response(
            description="Thread not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Thread not found")
                }
            )
        ),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_thread_messages(request, thread_id):

    user = request.user
    try:
        thread = Thread.objects.get(thread_id=thread_id, user=user)

        thread_messages = thread.get_messages()
        serializer = ThreadMessageSerializer(thread_messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Thread.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Thread not found"
        }, status=status.HTTP_404_NOT_FOUND)


def test_ai_guide(request):

    return render(request, 'ai_guide_test.html')