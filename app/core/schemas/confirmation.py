from pydantic import BaseModel


# Confirmation
class ConfirmationEmail(BaseModel):
    email: str
    code: str 
