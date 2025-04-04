from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_swagger_ui import get_swaggerui_blueprint
from flask import jsonify

# Create an APISpec
spec = APISpec(
    title="BB Expense App API",
    version="1.0.0",
    openapi_version="3.0.2",
    info={
        "description": """
        API for the BB Expense App. This API allows you to:
        * Upload and manage expense receipts
        * Process receipts with OCR
        * Retrieve receipt information
        
        All endpoints require authentication via Google OAuth.
        """,
        "contact": {
            "name": "BB Support",
            "email": "support@bakkenbaeck.no"
        }
    },
    plugins=[MarshmallowPlugin()],
)

# Define Swagger UI blueprint
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "BB Expense App API"
    }
)

# Define schemas
spec.components.schema("Receipt", {
    "properties": {
        "id": {"type": "integer"},
        "user_id": {"type": "integer"},
        "amount": {"type": "number"},
        "currency": {"type": "string"},
        "category": {"type": "string"},
        "date_submitted": {"type": "string", "format": "date-time"},
        "status": {"type": "string", "enum": ["pending", "approved", "rejected"]},
        "file_path_db": {"type": "string"},
    }
})

spec.components.schema("User", {
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
        "name": {"type": "string"},
        "is_admin": {"type": "boolean"},
        "is_reviewer": {"type": "boolean"},
    }
})

# Define routes for documentation
def register_swagger_routes(app):
    @app.route(API_URL)
    def swagger_json():
        # Add security scheme to components
        spec.components.security_scheme('GoogleOAuth', {
            'type': 'oauth2',
            'flows': {
                'implicit': {
                    'authorizationUrl': 'https://accounts.google.com/o/oauth2/auth',
                    'scopes': {
                        'openid': 'OpenID Connect',
                        'email': 'Email access',
                        'profile': 'Profile information'
                    }
                }
            }
        })
        
        return jsonify(spec.to_dict())
    
    # Document receipt endpoints
    spec.path(
        path="/api/receipts",
        operations={
            "get": {
                "summary": "Get all receipts",
                "description": "Retrieve a list of all receipts for the authenticated user",
                "tags": ["Receipts"],
                "responses": {
                    "200": {
                        "description": "List of receipts",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Receipt"}
                                }
                            }
                        }
                    },
                    "401": {"description": "Not authenticated"},
                    "403": {"description": "Not authorized to view receipts"}
                }
            },
            "post": {
                "summary": "Create a new receipt",
                "description": "Upload a new receipt with expense details",
                "tags": ["Receipts"],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "amount": {
                                        "type": "number",
                                        "description": "Total amount of the expense",
                                        "minimum": 0
                                    },
                                    "currency": {
                                        "type": "string",
                                        "description": "Three-letter currency code (e.g., EUR, USD, NOK)",
                                        "example": "EUR"
                                    },
                                    "category": {
                                        "type": "string",
                                        "description": "Type of expense",
                                        "enum": ["travel", "food", "equipment", "other"]
                                    },
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "Receipt image or PDF file"
                                    }
                                },
                                "required": ["amount", "currency", "category", "file"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Receipt created successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Receipt"}
                            }
                        }
                    },
                    "400": {"description": "Invalid input data"},
                    "401": {"description": "Not authenticated"},
                    "415": {"description": "Unsupported file type"}
                }
            }
        }
    )
    
    # Document single receipt endpoint
    spec.path(
        path="/api/receipts/{receipt_id}",
        operations={
            "get": {
                "summary": "Get receipt by ID",
                "tags": ["Receipts"],
                "parameters": [
                    {
                        "name": "receipt_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Receipt details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Receipt"}
                            }
                        }
                    }
                }
            }
        }
    )
    
    # Document OCR endpoint
    spec.path(
        path="/api/ocr",
        operations={
            "post": {
                "summary": "Process receipt with OCR",
                "description": "Extract information from a receipt image using OCR",
                "tags": ["OCR"],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "Receipt image to process (PNG, JPG, PDF)"
                                    }
                                },
                                "required": ["file"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "OCR results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "amount": {
                                            "type": "number",
                                            "description": "Extracted amount from receipt"
                                        },
                                        "currency": {
                                            "type": "string",
                                            "description": "Detected currency"
                                        },
                                        "date": {
                                            "type": "string",
                                            "description": "Receipt date in YYYY-MM-DD format"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Invalid file"},
                    "415": {"description": "Unsupported file type"},
                    "429": {"description": "Rate limit exceeded"},
                    "500": {"description": "OCR processing failed"}
                }
            }
        }
    ) 