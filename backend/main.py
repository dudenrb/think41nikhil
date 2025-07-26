# backend/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field # Used for data validation and schema definition
from pymongo import MongoClient
from bson import ObjectId # Required for handling MongoDB's default _id field
from datetime import datetime
from typing import List, Optional
import uuid # For generating unique session IDs
import os
import json # For debugging/printing structured data

# For loading environment variables (like API keys in Milestone 5)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- MongoDB Configuration ---
# Default MongoDB URI for a local instance.
# Ensure your MongoDB server is running on localhost:27017
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "ecommerce_chatbot_db" # The database name where you loaded your CSV data

# --- Initialize MongoDB client ---
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    # Ping the database to ensure a successful connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"ERROR: Could not connect to MongoDB. Please ensure MongoDB server is running: {e}")
    # In a production app, you might want to log this error and gracefully exit or retry.
    # For now, we'll let the app start but API calls might fail if connection isn't resolved.
    db = None # Set db to None if connection fails, so subsequent operations will fail
    # sys.exit(1) # Uncomment this in production to prevent app from starting if DB is down

# --- FastAPI App Initialization ---
app = FastAPI(
    title="E-commerce Chatbot Backend",
    description="Backend service for conversational AI agent for an e-commerce site.",
    version="1.0.0"
)

# --- Pydantic Models for Data Validation (Request/Response Schemas) ---

# Custom type for MongoDB's ObjectId to work seamlessly with Pydantic
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        # Allow Pydantic to represent ObjectId as a string in OpenAPI schema
        field_schema.update(type="string")

# Model for a single message in a conversation (user or assistant)
class Message(BaseModel):
    role: str = Field(..., description="Role of the sender (e.g., 'user', 'assistant')")
    content: str = Field(..., description="The textual content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of when the message was created")

# Model for a full conversation session document stored in MongoDB
class Conversation(BaseModel):
    # _id is MongoDB's unique ID, aliased to 'id' for Pydantic/API use
    id: Optional[PyObjectId] = Field(alias="_id", default=None, description="Unique MongoDB document ID for the conversation session")
    user_id: str = Field(..., description="Identifier for the user who initiated or is part of this conversation")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique UUID for this specific conversation session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp when this conversation session was created")
    messages: List[Message] = Field(default_factory=list, description="Ordered list of messages in this conversation session")

    class Config:
        # This allows Pydantic to populate fields by their alias (_id -> id)
        allow_population_by_field_name = True
        # Required for PyObjectId to be treated as a valid type
        arbitrary_types_allowed = True
        # Serializer for ObjectId to string when returning JSON
        json_encoders = {ObjectId: str}
        # Example schema for documentation (Swagger UI)
        schema_extra = {
            "example": {
                "user_id": "test_user_456",
                "session_id": "b8a9c0d1-e2f3-4567-890a-bcdef0123456",
                "created_at": "2025-07-26T11:00:00.000Z",
                "messages": [
                    {"role": "user", "content": "Hi there!", "timestamp": "2025-07-26T11:00:10.000Z"},
                    {"role": "assistant", "content": "Hello! How can I help you?", "timestamp": "2025-07-26T11:00:15.000Z"},
                ]
            }
        }

# Model for the incoming chat request from the frontend
class ChatRequest(BaseModel):
    user_id: str = Field(..., description="The ID of the user sending the message")
    message: str = Field(..., description="The user's message text")
    session_id: Optional[str] = Field(None, description="Optional: The ID of an existing conversation session to continue")

# Model for the outgoing chat response to the frontend
class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The session ID of the conversation (new or existing)")
    assistant_response: str = Field(..., description="The AI's response to the user's message")
    conversation_history: List[Message] = Field(..., description="The full updated conversation history for the session")

# --- API Endpoints ---

@app.get("/")
async def root():
    """
    Root endpoint for a basic health check of the backend service.
    """
    return {"message": "E-commerce Chatbot Backend is running!"}

@app.post("/api/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_bot(request: ChatRequest):
    """
    Handles a user's chat message, manages conversation history,
    and returns a placeholder AI response.
    (LLM integration will be added in Milestone 5)
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not connected.")

    user_id = request.user_id
    user_message_content = request.message
    session_id = request.session_id

    conversations_collection = db.conversations

    # 1. Find or create a conversation session
    # If a session_id is provided, try to find it.
    # If not found (or not provided), create a new session.
    conversation_doc = None
    if session_id:
        conversation_doc = conversations_collection.find_one({"user_id": user_id, "session_id": session_id})
        if not conversation_doc:
            # If session_id was provided but doesn't exist for this user, treat as new.
            print(f"INFO: Provided session_id '{session_id}' not found for user '{user_id}'. Starting a new session.")
            session_id = str(uuid.uuid4()) # Generate a new UUID
            new_conversation = Conversation(user_id=user_id, session_id=session_id)
            conversation_doc = new_conversation.dict(by_alias=True, exclude_none=True)
            conversations_collection.insert_one(conversation_doc)
            print(f"INFO: Created new conversation session: {session_id}")
    else:
        # No session_id provided, so always start a new session.
        session_id = str(uuid.uuid4())
        new_conversation = Conversation(user_id=user_id, session_id=session_id)
        conversation_doc = new_conversation.dict(by_alias=True, exclude_none=True)
        conversations_collection.insert_one(conversation_doc)
        print(f"INFO: Created new conversation session: {session_id}")

    # Convert the MongoDB document (dict) to our Pydantic Conversation model
    # This allows us to use .append() on the messages list easily
    conversation = Conversation(**conversation_doc)

    # 2. Add the user's message to the conversation history
    user_message = Message(role="user", content=user_message_content)
    conversation.messages.append(user_message)
    print(f"DEBUG: User message added to session {session_id}.")

    # 3. Generate a placeholder AI response (This will be replaced in Milestone 5)
    assistant_response_content = f"Acknowledged: '{user_message_content}'. (Placeholder AI response for session {session_id})."
    assistant_message = Message(role="assistant", content=assistant_response_content)
    conversation.messages.append(assistant_message)
    print(f"DEBUG: Placeholder assistant response generated for session {session_id}.")

    # 4. Update the conversation document in MongoDB
    try:
        # We use $set to update the entire 'messages' array, which is efficient here.
        update_result = conversations_collection.update_one(
            {"_id": conversation.id}, # Query by the MongoDB _id
            {"$set": {"messages": [msg.dict() for msg in conversation.messages]}} # Convert Pydantic Message objects back to dicts
        )
        if update_result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation document not found for update.")
        print(f"INFO: Updated conversation session {session_id} for user {user_id} in MongoDB.")
    except Exception as e:
        print(f"ERROR: Failed to update conversation in database: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save conversation: {e}")

    # 5. Return the response to the frontend
    return ChatResponse(
        session_id=conversation.session_id,
        assistant_response=assistant_response_content,
        conversation_history=conversation.messages
    )

@app.get("/api/conversations/{user_id}", response_model=List[Conversation])
async def get_user_conversations(user_id: str):
    """
    Retrieves all conversation sessions for a given user, sorted by creation date.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not connected.")

    conversations_collection = db.conversations
    # Find all documents for the user, sorted by 'created_at' in descending order
    user_conversations_docs = list(conversations_collection.find({"user_id": user_id}).sort("created_at", -1))

    if not user_conversations_docs:
        # If no conversations found, return an empty list
        return []

    # Convert MongoDB documents to Pydantic Conversation models
    return [Conversation(**doc) for doc in user_conversations_docs]

@app.get("/api/conversation/{session_id}", response_model=Conversation)
async def get_conversation_by_session_id(session_id: str):
    """
    Retrieves a specific conversation session by its unique session ID.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not connected.")

    conversations_collection = db.conversations
    conversation_doc = conversations_collection.find_one({"session_id": session_id})

    if not conversation_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation session '{session_id}' not found.")

    return Conversation(**conversation_doc)

# --- How to Run This Application (for local development) ---
# 1. Save this code as 'main.py' inside your 'backend' directory.
# 2. Open your terminal, navigate to your 'backend' directory.
# 3. Run the command: uvicorn main:app --reload
#
# Access the API documentation at: http://127.0.0.1:8000/docs
# Access the API at: http://127.0.0.1:8000