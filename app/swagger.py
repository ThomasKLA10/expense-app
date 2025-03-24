from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_swagger_ui import get_swaggerui_blueprint
from flask import jsonify

# Create an APISpec
spec = APISpec(
    title="BB Expense App API",
    version="1.0.0",
    openapi_version="3.0.2",
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
        return jsonify(spec.to_dict())
    
    # Document receipt endpoints
    spec.path(
        path="/api/receipts",
        operations={
            "get": {
                "summary": "Get all receipts",
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
                    }
                }
            },
            "post": {
                "summary": "Create a new receipt",
                "tags": ["Receipts"],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "amount": {"type": "number"},
                                    "currency": {"type": "string"},
                                    "category": {"type": "string"},
                                    "file": {"type": "string", "format": "binary"}
                                },
                                "required": ["amount", "currency", "category", "file"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Receipt created",
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
                "tags": ["OCR"],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"}
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
                                        "amount": {"type": "number"},
                                        "currency": {"type": "string"},
                                        "date": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    ) 