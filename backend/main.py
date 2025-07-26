# backend/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
import uuid
import os
import json # For debugging/pretty-printing JSON

# LLM Integration imports
import google.generativeai as genai
from dotenv import load_dotenv

# --- NEW IMPORT FOR CORS ---
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file (if it exists)
load_dotenv()

# --- MongoDB Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "ecommerce_chatbot_db"

# --- Initialize MongoDB client ---
db = None
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    client.admin.command('ping') # Test connection
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"ERROR: Could not connect to MongoDB. Please ensure MongoDB server is running on {MONGO_URI}: {e}")
    # In a real application, you might exit here or implement a retry mechanism.

# --- Gemini API Configuration ---
# The API key for Gemini. For this Canvas environment, leaving it empty
# allows the system to inject it. In a real setup, load from .env.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configure the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel('gemini-2.0-flash') # Using gemini-2.0-flash for efficiency

# --- FastAPI App Initialization ---
app = FastAPI(
    title="E-commerce Chatbot Backend",
    description="Backend service for conversational AI agent for an e-commerce site.",
    version="1.0.0"
)

# --- CORS Configuration (NEW ADDITION FOR MILESTONE 9) ---
# Define origins that are allowed to make requests to your backend.
# For development, we allow the React app's development server URL.
# In production, this should be your actual frontend domain(s).
origins = [
    "http://localhost:5173",  # React app (Vite default)
    "http://127.0.0.1:5173",  # React app (alternative localhost IP)
    # You might add other ports if Vite/React runs on a different port sometimes.
    # E.g., "http://localhost:3000" if using Create React App
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # List of allowed origins
    allow_credentials=True,         # Allow cookies to be sent with cross-origin requests (if needed later)
    allow_methods=["*"],            # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],            # Allow all headers in the request
)

# --- Pydantic Models for Data Validation ---

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
        field_schema.update(type="string")

class Message(BaseModel):
    role: str = Field(..., description="Role of the sender (e.g., 'user', 'assistant')")
    content: str = Field(..., description="The textual content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of when the message was created")

class Conversation(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None, description="Unique MongoDB document ID for the conversation session")
    user_id: str = Field(..., description="Identifier for the user")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique UUID for this specific conversation session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp when this conversation session was created")
    messages: List[Message] = Field(default_factory=list, description="Ordered list of messages in this conversation session")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
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

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="The ID of the user sending the message")
    message: str = Field(..., description="The user's message text")
    session_id: Optional[str] = Field(None, description="Optional: The ID of an existing conversation session to continue")

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The session ID of the conversation (new or existing)")
    assistant_response: str = Field(..., description="The AI's response to the user's message")
    conversation_history: List[Message] = Field(..., description="The full updated conversation history for the session")

# --- Helper function to query the database ---
def query_database(query_type: str, **kwargs):
    """
    Queries the e-commerce MongoDB database based on the intent and parameters
    identified by the LLM.
    """
    if db is None:
        print("ERROR: Database connection not available for query_database.")
        return {"error": "Database not connected."}

    print(f"DEBUG: Executing database query type: {query_type} with params: {kwargs}")

    if query_type == "top_sold_products":
        try:
            pipeline = [
                {"$group": {"_id": "$product_id", "sold_count": {"$sum": 1}}},
                {"$sort": {"sold_count": -1}},
                {"$limit": 5},
                {"$lookup": {
                    "from": "products",
                    "localField": "_id",
                    "foreignField": "id",
                    "as": "product_info"
                }},
                {"$unwind": "$product_info"},
                {"$project": {"_id": 0, "product_name": "$product_info.name", "sold_count": 1, "category": "$product_info.category"}}
            ]
            top_products = list(db.order_items.aggregate(pipeline))
            if top_products:
                return {"products": top_products}
            else:
                return {"products": []}
        except Exception as e:
            print(f"Error querying top sold products: {e}")
            return {"error": "Failed to retrieve top sold products."}

    elif query_type == "order_status":
        order_id_str = kwargs.get("order_id")
        if not order_id_str:
            return {"error": "Order ID is required."}
        try:
            order = db.orders.find_one({"order_id": order_id_str})
            if not order:
                order = db.orders.find_one({"order_id": int(order_id_str)})

            if order:
                return {
                    "order_id": order.get("order_id"),
                    "status": order.get("status"),
                    "created_at": order.get("created_at"),
                    "shipped_at": order.get("shipped_at"),
                    "delivered_at": order.get("delivered_at")
                }
            else:
                return {"error": "Order not found."}
        except (ValueError, TypeError):
            return {"error": "Invalid order ID format. Please provide a numeric ID."}
        except Exception as e:
            print(f"Error querying order status: {e}")
            return {"error": "Failed to retrieve order status."}

    elif query_type == "product_stock":
        product_name = kwargs.get("product_name")
        if not product_name:
            return {"error": "Product name is required."}
        try:
            product = db.products.find_one({"name": {"$regex": product_name, "$options": "i"}})
            if product:
                product_id = product["id"]
                available_stock = db.inventory_items.count_documents({
                    "product_id": product_id,
                    "sold_at": {"$exists": False}
                })
                return {"product_name": product["name"], "stock": available_stock}
            else:
                return {"error": "Product not found."}
        except Exception as e:
            print(f"Error querying product stock: {e}")
            return {"error": "Failed to retrieve product stock."}

    elif query_type == "product_details":
        product_name = kwargs.get("product_name")
        if not product_name:
            return {"error": "Product name is required."}
        try:
            product = db.products.find_one({"name": {"$regex": product_name, "$options": "i"}})
            if product:
                return {
                    "name": product.get("name"),
                    "category": product.get("category"),
                    "brand": product.get("brand"),
                    "retail_price": product.get("retail_price"),
                    "department": product.get("department"),
                    "sku": product.get("sku")
                }
            else:
                return {"error": "Product not found."}
        except Exception as e:
            print(f"Error querying product details: {e}")
            return {"error": "Failed to retrieve product details."}

    return {"error": "Unknown query type or insufficient parameters."}


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
    integrates with the LLM for intelligence, and formulates responses
    based on database queries and conversational context.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not connected. Please check server logs.")

    user_id = request.user_id
    user_message_content = request.message
    session_id = request.session_id

    conversations_collection = db.conversations

    # 1. Find or create a conversation session
    conversation_doc = None
    if session_id:
        conversation_doc = conversations_collection.find_one({"user_id": user_id, "session_id": session_id})
        if not conversation_doc:
            print(f"INFO: Provided session_id '{session_id}' not found for user '{user_id}'. Starting a new session.")
            session_id = str(uuid.uuid4())
            new_conversation = Conversation(user_id=user_id, session_id=session_id)
            conversation_doc = new_conversation.dict(by_alias=True, exclude_none=True)
            conversations_collection.insert_one(conversation_doc)
            print(f"INFO: Created new conversation session: {session_id}")
    else:
        session_id = str(uuid.uuid4())
        new_conversation = Conversation(user_id=user_id, session_id=session_id)
        conversation_doc = new_conversation.dict(by_alias=True, exclude_none=True)
        conversations_collection.insert_one(conversation_doc)
        print(f"INFO: Created new conversation session: {session_id}")

    conversation = Conversation(**conversation_doc)

    # Add the user's message to the conversation history
    user_message = Message(role="user", content=user_message_content)
    conversation.messages.append(user_message)
    print(f"DEBUG: User message added to session {session_id}.")

    assistant_response_content = "I'm sorry, I couldn't process your request at this moment."

    try:
        system_instruction_content = """
        You are an e-commerce customer support chatbot named 'ShopAssist'. Your primary goal is to provide helpful and accurate information to users about products, orders, and inventory from our e-commerce database.

        You have access to the following data through internal 'tools' (database queries):
        - `top_sold_products`: To get a list of the top 5 most sold products. No parameters needed.
        - `order_status` (requires 'order_id'): To check the status of a specific order.
        - `product_stock` (requires 'product_name'): To find out how many units of a specific product are in stock.
        - `product_details` (requires 'product_name'): To get general information about a specific product (category, brand, price, department, SKU).

        Your response strategy:
        1.  **Identify User Intent and Parameters:** Based on the user's message, determine if they are asking for a specific piece of information that can be retrieved from the database. Extract any necessary parameters (like product name or order ID).
        2.  **Request Clarification:** If you detect an intent to query data but lack a crucial parameter (e.g., "What's the order status?" without an order ID), respond naturally by asking the user for the missing information.
        3.  **Formulate Database Query (JSON Output):** If you can identify a clear intent and have all required parameters for a database query, you must respond with a **JSON object** indicating the `query_type` and its `parameters`.
            * Example for "What are the top 5 most sold products?":
                ```json
                {"intent": "query_data", "query_type": "top_sold_products", "parameters": {}}
                ```
            * Example for "What is the status of order 12345?":
                ```json
                {"intent": "query_data", "query_type": "order_status", "parameters": {"order_id": "12345"}}
                ```
            * Example for "How many Classic T-Shirts are left in stock?":
                ```json
                {"intent": "query_data", "query_type": "product_stock", "parameters": {"product_name": "Classic T-Shirt"}}
                ```
            * Example for "Tell me about the Super comfortable jeans":
                ```json
                {"intent": "query_data", "query_type": "product_details", "parameters": {"product_name": "Super comfortable jeans"}}
                ```
        4.  **Natural Language Response:** For general conversational questions (e.g., "Hello", "How are you?"), or if you've performed a database query, synthesize the information you've gathered into a helpful, concise, and friendly natural language response. Do NOT include technical details of the query in the user-facing response.
        5.  **Maintain Context:** Use the conversation history to understand follow-up questions.

        Always try to be helpful and direct. If you cannot fulfill a request, explain why politely.
        """

        # Prepare chat history for the LLM
        llm_input_messages = [
            {"role": "user", "parts": [{"text": system_instruction_content}]}
        ]
        for msg in conversation.messages:
            llm_input_messages.append({"role": msg.role, "parts": [{"text": msg.content}]})

        # The prompt for structured intent recognition and response generation
        combined_prompt = f"""
        {system_instruction_content}

        Based on the conversation history below and the user's latest message, generate the appropriate response.

        Conversation History (User and Assistant messages):
        {json.dumps([{"role": msg.role, "content": msg.content} for msg in conversation.messages], indent=2)}

        User's latest message: "{user_message_content}"

        Your final response should be ONLY a JSON object if it's a tool call (query_data or clarify), otherwise, if it's a general conversation, the JSON should specify "general_chat" and the "response".
        """

        print(f"DEBUG: Sending combined prompt to LLM for intent/response:\n{combined_prompt}")

        llm_response_raw = llm_model.generate_content(
            combined_prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        llm_output_text = llm_response_raw.text
        print(f"DEBUG: LLM raw response: {llm_output_text}")

        llm_data = {}
        try:
            llm_data = json.loads(llm_output_text)
            print(f"DEBUG: Parsed LLM structured data: {llm_data}")
        except json.JSONDecodeError:
            print(f"WARNING: LLM did not return valid JSON. Falling back to simple general chat response.")
            llm_data = {"intent": "general_chat", "response": "I'm having a bit of trouble understanding your request. Could you please rephrase it?"}

        intent = llm_data.get("intent")
        query_type = llm_data.get("query_type")
        parameters = llm_data.get("parameters", {})

        if intent == "query_data":
            db_result = query_database(query_type, **parameters)
            if "error" in db_result:
                assistant_response_content = f"I encountered an issue retrieving that information: {db_result['error']}"
            else:
                synthesis_prompt = f"""
                The user asked about '{query_type}'.
                Here is the data retrieved from the database:
                {json.dumps(db_result, indent=2)}

                Based on this data, formulate a helpful, concise, and friendly answer for the user.
                Do not include technical details of the query. If the data is insufficient to fully answer, state that politely.

                Examples:
                - Products: "The top 5 most sold products are: Running Shoes, Classic T-Shirt, etc."
                - Order Status: "Order ID {db_result.get('order_id')} is currently in {db_result.get('status')} status. It was created on {db_result.get('created_at')}."
                - Product Stock: "There are {db_result.get('stock')} units of {db_result.get('product_name')} left in stock."
                - Product Details: "The {db_result.get('name')} is a {db_result.get('brand')} brand product in the {db_result.get('category')} category, priced at ${db_result.get('retail_price')}."
                """
                print(f"DEBUG: Sending synthesis prompt to LLM:\n{synthesis_prompt}")
                synthesis_response = llm_model.generate_content(synthesis_prompt)
                assistant_response_content = synthesis_response.text

        elif intent == "clarify":
            assistant_response_content = llm_data.get("clarification_needed", "Could you please provide more details?")

        elif intent == "general_chat":
            assistant_response_content = llm_data.get("response", "Hello! How can I help you today?")

        else:
            assistant_response_content = "I'm still learning and couldn't process that request. Can you rephrase?"
            print(f"WARNING: Unexpected intent received from LLM: {intent}. Full LLM data: {llm_data}")


    except Exception as e:
        print(f"ERROR: An error occurred during LLM interaction or intent processing: {e}")
        assistant_response_content = "I apologize, an unexpected error occurred. Please try again later."


    # Add assistant message to history
    assistant_message = Message(role="assistant", content=assistant_response_content)
    conversation.messages.append(assistant_message)
    print(f"DEBUG: Assistant response generated for session {session_id}.")

    # Update the conversation document in MongoDB
    try:
        update_result = conversations_collection.update_one(
            {"_id": conversation.id},
            {"$set": {"messages": [msg.dict() for msg in conversation.messages]}}
        )
        if update_result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation document not found for update after AI processing.")
        print(f"INFO: Updated conversation session {session_id} for user {user_id} in MongoDB after AI response.")
    except Exception as e:
        print(f"ERROR: Failed to update conversation in database after AI processing: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save conversation history after AI response: {e}")

    # Return the response to the frontend
    return ChatResponse(
        session_id=conversation.session_id,
        assistant_response=assistant_response_content,
        conversation_history=conversation.messages
    )

@app.get("/api/conversations/{user_id}", response_model=List[Conversation])
async def get_user_conversations(user_id: str):
    """
    Retrieves all conversation sessions for a given user, sorted by creation date (most recent first).
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not connected. Please check server logs.")

    conversations_collection = db.conversations
    user_conversations_docs = list(conversations_collection.find({"user_id": user_id}).sort("created_at", -1))

    if not user_conversations_docs:
        return []

    return [Conversation(**doc) for doc in user_conversations_docs]

@app.get("/api/conversation/{session_id}", response_model=Conversation)
async def get_conversation_by_session_id(session_id: str):
    """
    Retrieves a specific conversation session by its unique session ID.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not connected. Please check server logs.")

    conversations_collection = db.conversations
    conversation_doc = conversations_collection.find_one({"session_id": session_id})

    if not conversation_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation session '{session_id}' not found.")

    return Conversation(**conversation_doc)